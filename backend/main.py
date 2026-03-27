from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
import uuid
from typing import List, Dict
from sqlalchemy.orm import Session
from datetime import datetime

from database import engine, SessionLocal, init_db, get_db, ProtectedContent, DetectionEvent
from hash_engine import VideoHashEngine
from matcher import VideoMatcher
from ai_engine import SentinelAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Database
init_db()

app = FastAPI(title="Sentinel - Media Fingerprinting Engine")

# CORS for Flutter Web
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Engines
hash_engine = VideoHashEngine()
matcher = VideoMatcher()
try:
    ai_engine = SentinelAI()
except Exception as e:
    print(f"⚠ AI Engine initialization failed: {e}")
    ai_engine = None

# WebSocket Manager for Real-time Dashboard
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            await connection.send_json(message)

manager = ConnectionManager()

@app.get("/")
async def root():
    return {"status": "online", "engine": "Sentinel v1.0"}

@app.post("/ingest")
async def ingest_content(file: UploadFile = File(...), title: str = None, db: Session = Depends(get_db)):
    """Ingest a reference video file, generate hashes, and store in DB."""
    if not title:
        title = file.filename
        
    # Save temporary file
    temp_path = f"temp_{uuid.uuid4()}.mp4"
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    try:
        # Generate Hashes
        print(f"Processing reference content: {title}")
        results = hash_engine.process_video_parallel(temp_path)
        hashes = results['hashes']
        
        # Save to DB
        content = ProtectedContent(
            title=title,
            original_hashes=hashes,
            content_metadata={"fps": results['fps'], "frames_processed": results['frames_processed']}
        )
        db.add(content)
        db.commit()
        db.refresh(content)
        
        return {
            "id": content.id,
            "title": content.title,
            "frames": len(hashes),
            "status": "protected"
        }
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

@app.post("/detect")
async def detect_piracy(suspect_hashes: List[str], platform: str, stream_url: str = None, db: Session = Depends(get_db)):
    """Check a clip (list of hashes) against all protected content."""
    protected_database = db.query(ProtectedContent).all()
    
    # Matching Logic
    best_match_content = None
    best_result = {'confidence_score': 0.0}
    
    for content in protected_database:
        result = matcher.sliding_window_match(suspect_hashes, content.original_hashes)
        if result['confidence_score'] > best_result['confidence_score']:
            best_result = result
            best_match_content = content
            
    if best_result.get('is_match'):
        # Generate AI Insight
        detection_data = {
            'content_title': best_match_content.title,
            'platform': platform,
            'stream_url': stream_url,
            'confidence_score': best_result['confidence_score'],
            'timestamp': datetime.utcnow().isoformat()
        }
        
        ai_summary = "AI Engine Offline"
        dmca_notice = "N/A"
        
        if ai_engine:
            ai_summary = ai_engine.generate_detection_summary(detection_data)
            rights_holder = {
                'name': 'Sentinel Client',
                'email': 'legal@sentinel.ai',
                'address': 'Rights Protection HQ',
                'phone': '+1-800-SENTINEL'
            }
            dmca_notice = ai_engine.generate_dmca_notice(detection_data, rights_holder)
            
        # Save Detection Event
        event = DetectionEvent(
            content_id=best_match_content.id,
            platform=platform,
            stream_url=stream_url,
            confidence_score=best_result['confidence_score'],
            ai_summary=ai_summary,
            dmca_notice=dmca_notice
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        
        # Broadcast to dashboard
        await manager.broadcast({
            "type": "DETECTION",
            "content": best_match_content.title,
            "platform": platform,
            "confidence": best_result['confidence_score'],
            "summary": ai_summary
        })
        
        return {
            "is_piracy": True,
            "match": best_match_content.title,
            "confidence": best_result['confidence_score'],
            "summary": ai_summary,
            "notice": dmca_notice
        }
        
    return {"is_piracy": False, "confidence": best_result['confidence_score']}

@app.get("/events")
async def get_events(db: Session = Depends(get_db)):
    """Retrieve all detection events."""
    return db.query(DetectionEvent).order_by(DetectionEvent.timestamp.desc()).all()

@app.websocket("/ws/monitor")
async def websocket_endpoint(websocket: WebSocket):
    """Real-time monitoring channel for the dashboard."""
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
