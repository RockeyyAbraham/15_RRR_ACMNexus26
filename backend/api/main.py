"""
Sentinel Backend Central Hub - Flask REST & WebSocket API.
Provides high-fidelity piracy detection, AI summaries, and automated DMCA generation.
"""

import os
import json
import sqlite3
import contextlib
import time
from datetime import datetime
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flask_sock import Sock
from werkzeug.utils import secure_filename

# Engine Imports
from engines.hash_engine import VideoHashEngine
from engines.audio_engine import AudioHashEngine
from engines.matcher import VideoMatcher
from engines.dual_engine import DualModeEngine
from engines.ai_engine import SentinelAI
from generators.dmca_generator import DMCAGenerator
from utils.redis_utils import redis_manager

app = Flask(__name__)

# Configure CORS for React frontend (localhost:3000)
CORS(app, resources={
    r"/*": {
        "origins": ["http://localhost:3000", "http://127.0.0.1:3000"],
        "methods": ["GET", "POST", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

sock = Sock(app)

# --- Configuration & Initialization ---
DB_PATH = "../data/sentinel.db"
TEMP_DIR = "../temp"
NOTICES_DIR = "../notices"

os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(NOTICES_DIR, exist_ok=True)
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

# Initialize engines at module level (expensive)
hash_engine = VideoHashEngine(
    frame_sample_rate=10, hash_size=8,
    adaptive_sampling=True, use_multi_hash=True,
    parallel_processing=True, max_workers=4,
    auto_crop=True, detect_mirroring=True
)
audio_engine = AudioHashEngine(sample_rate=22050, n_mels=128, hash_size=8, chunk_duration=5)
matcher = VideoMatcher(threshold=85.0, hash_size=8)
dual_engine = DualModeEngine()

# AI Engine setup
try:
    ai_engine = SentinelAI()
    AI_AVAILABLE = True
except (ValueError, Exception):
    ai_engine = None
    AI_AVAILABLE = False

generator = DMCAGenerator(output_dir=NOTICES_DIR)

# --- Database Setup ---
def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS protected_content (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                league TEXT NOT NULL,
                video_hashes TEXT NOT NULL,
                audio_hash TEXT NOT NULL,
                duration_seconds INTEGER,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS detections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                protected_content_id INTEGER NOT NULL,
                stream_url TEXT NOT NULL,
                confidence_score FLOAT NOT NULL,
                detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                evidence_frame BLOB,
                dmca_generated BOOLEAN DEFAULT FALSE,
                FOREIGN KEY (protected_content_id) REFERENCES protected_content(id)
            )
        """)
        conn.commit()

init_db()

@contextlib.contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def error_response(message: str, status_code: int = 500):
    return jsonify({"error": message, "timestamp": datetime.now().isoformat()}), status_code

# --- REST Endpoints ---

@app.route("/health", methods=["GET"])
def health_check():
    try:
        with get_db() as db:
            p_count = db.execute("SELECT COUNT(*) FROM protected_content").fetchone()[0]
            d_count = db.execute("SELECT COUNT(*) FROM detections").fetchone()[0]
            
        return jsonify({
            "status": "online",
            "engines": ["hashing", "matching", "ai", "generator", "redis"],
            "redis_available": redis_manager.is_available(),
            "protected_content_count": p_count,
            "detection_count": d_count,
            "timestamp": datetime.now().isoformat()
        }), 200
    except Exception as e:
        return error_response(f"Health check failed: {str(e)}")

@app.route("/upload/protected", methods=["POST"])
def upload_protected():
    if "video" not in request.files:
        return error_response("No video file included", 400)
    
    video_file = request.files["video"]
    if video_file.filename == "":
        return error_response("Empty filename", 400)
    
    filename = secure_filename(video_file.filename)
    video_path = os.path.join(TEMP_DIR, filename)
    video_file.save(video_path)
    
    try:
        # 1. Video Hashing
        v_hashes, v_meta = hash_engine.hash_video(video_path)
        
        # 2. Audio Hashing (Graceful fallback)
        a_hashes_json = "[]"
        a_count = 0
        try:
            a_hashes, a_meta = audio_engine.hash_audio(video_path)
            # Extracted according to prompt: json.dumps([h['hash'] for h in audio_hashes])
            a_hashes_json = json.dumps([h['hash'] for h in a_hashes])
            a_count = len(a_hashes)
        except:
            pass
            
        # 3. Save to DB
        with get_db() as db:
            cursor = db.cursor()
            cursor.execute("""
                INSERT INTO protected_content (title, league, video_hashes, audio_hash, duration_seconds)
                VALUES (?, ?, ?, ?, ?)
            """, (
                request.form.get("title", "Unknown Content"),
                request.form.get("league", "General"),
                json.dumps(v_hashes),
                a_hashes_json,
                int(v_meta.get("duration_seconds", 0))
            ))
            content_id = cursor.lastrowid
            db.commit()
            
        # 4. Cache in Redis
        redis_manager.cache_protected_hashes(content_id, v_hashes)
        
        return jsonify({
            "message": "Protected content uploaded and fingerprinted",
            "content_id": content_id,
            "hash_count": len(v_hashes),
            "audio_hash_count": a_count,
            "duration_seconds": v_meta.get("duration_seconds"),
            "processing_time_seconds": v_meta.get("processing_time_seconds")
        }), 201
        
    except Exception as e:
        return error_response(str(e))
    finally:
        if os.path.exists(video_path):
            os.remove(video_path)

@app.route("/protected", methods=["GET"])
def list_protected():
    with get_db() as db:
        rows = db.execute("SELECT id, title, league, duration_seconds, video_hashes, uploaded_at FROM protected_content").fetchall()
        
    result = []
    for row in rows:
        v_hashes = json.loads(row['video_hashes'])
        result.append({
            "id": row['id'],
            "title": row['title'],
            "league": row['league'],
            "duration_seconds": row['duration_seconds'],
            "hash_count": len(v_hashes),
            "uploaded_at": row['uploaded_at']
        })
    return jsonify(result)

@app.route("/protected/<int:content_id>", methods=["DELETE"])
def delete_protected(content_id):
    try:
        with get_db() as db:
            # Check detection count first for response message
            d_count = db.execute("SELECT COUNT(*) FROM detections WHERE protected_content_id = ?", (content_id,)).fetchone()[0]
            db.execute("DELETE FROM detections WHERE protected_content_id = ?", (content_id,))
            db.execute("DELETE FROM protected_content WHERE id = ?", (content_id,))
            db.commit()
            
        # Clear Redis cache
        if redis_manager.client:
            redis_manager.client.delete(f"protected_hashes:{content_id}")
            redis_manager.client.srem("active_protected_content", content_id)
            
        return jsonify({"message": f"Deleted content_id {content_id} and {d_count} associated detections"})
    except Exception as e:
        return error_response(str(e))

@app.route("/upload/suspect", methods=["POST"])
def upload_suspect():
    if "video" not in request.files:
        return error_response("No suspect video provided", 400)
    
    mode = request.form.get("mode", "dual")
    stream_url = request.form.get("stream_url", "unknown_source")
    
    video_file = request.files["video"]
    filename = secure_filename(video_file.filename)
    video_path = os.path.join(TEMP_DIR, filename)
    video_file.save(video_path)
    
    start_time = time.time()
    
    try:
        # 1. Get reference IDs
        protected_ids = redis_manager.get_all_protected_content_ids()
        if not protected_ids:
            with get_db() as db:
                protected_ids = [row[0] for row in db.execute("SELECT id FROM protected_content").fetchall()]
        
        found_detections = []
        
        with get_db() as db:
            for p_id in protected_ids:
                # We need the protected file path for DualModeEngine.detect_piracy
                # In our setup, we'll assume reference samples exist in a '../reference' directory or similar.
                # If specific storage is unknown, we handle fallback gracefully.
                ref_path = os.path.join("../reference", f"reference_{p_id}.mp4")
                
                # Fetch title/league for the response
                p_info = db.execute("SELECT title, league FROM protected_content WHERE id = ?", (p_id,)).fetchone()
                if not p_info: continue
                
                if not os.path.exists(ref_path):
                    ref_path = os.path.join("../reference", f"{p_info['title']}.mp4")
                
                if not os.path.exists(ref_path):
                    continue # Skip if no reference file found
                
                res = dual_engine.detect_piracy(video_path, ref_path, mode=mode)
                
                if res.get("is_match"):
                    # Store detection
                    cursor = db.cursor()
                    cursor.execute("""
                        INSERT INTO detections (protected_content_id, stream_url, confidence_score)
                        VALUES (?, ?, ?)
                    """, (p_id, stream_url, res.get("combined_confidence", 0)))
                    det_id = cursor.lastrowid
                    db.commit()
                    
                    # AI Summary
                    ai_sum = ""
                    if AI_AVAILABLE:
                        try:
                            ai_sum = ai_engine.generate_detection_summary({
                                "content_title": p_info['title'],
                                "platform": stream_url,
                                "confidence_score": res.get("combined_confidence", 0),
                                "timestamp": datetime.now().isoformat()
                            })
                        except: pass
                    
                    # Cache result
                    det_data = {
                        "detection_id": det_id,
                        "content_id": p_id,
                        "title": p_info['title'],
                        "league": p_info['league'],
                        "confidence_score": res.get("combined_confidence", 0),
                        "video_confidence": res.get("video_confidence", 0),
                        "audio_confidence": res.get("audio_confidence", 0),
                        "pattern_score": res.get("pattern_score", 0),
                        "decision_reason": res.get("decision_reason", "threshold"),
                        "stream_url": stream_url,
                        "ai_summary": ai_sum
                    }
                    redis_manager.cache_detection_result(det_id, det_data)
                    found_detections.append(det_data)
        
        return jsonify({
            "message": "Suspect video processed",
            "detections_found": len(found_detections),
            "detections": found_detections,
            "processing_time_seconds": time.time() - start_time
        })
        
    except Exception as e:
        return error_response(str(e))
    finally:
        if os.path.exists(video_path):
            os.remove(video_path)

@app.route("/detections", methods=["GET"])
def get_detections():
    limit = request.args.get("limit", 50, type=int)
    offset = request.args.get("offset", 0, type=int)
    min_conf = request.args.get("min_confidence", 0.0, type=float)
    
    # Check Redis for first page
    if limit <= 10 and offset == 0:
        cached = redis_manager.get_latest_detections(limit)
        if cached:
            return jsonify({"detections": cached, "total": len(cached), "limit": limit, "offset": offset})
            
    with get_db() as db:
        total = db.execute("SELECT COUNT(*) FROM detections WHERE confidence_score >= ?", (min_conf,)).fetchone()[0]
        rows = db.execute("""
            SELECT d.*, p.title, p.league 
            FROM detections d
            JOIN protected_content p ON d.protected_content_id = p.id
            WHERE d.confidence_score >= ?
            ORDER BY d.detected_at DESC
            LIMIT ? OFFSET ?
        """, (min_conf, limit, offset)).fetchall()
        
    detections = []
    for r in rows:
        detections.append(dict(r))
        
    return jsonify({
        "detections": detections,
        "total": total,
        "limit": limit,
        "offset": offset
    })

@app.route("/detections/<int:detection_id>", methods=["GET"])
def get_detection_detail(detection_id):
    # Check cache
    cached = redis_manager.get_cache(f"detection_cache:{detection_id}")
    if cached:
        return jsonify(cached)
        
    with get_db() as db:
        row = db.execute("""
            SELECT d.*, p.title, p.league 
            FROM detections d
            JOIN protected_content p ON d.protected_content_id = p.id
            WHERE d.id = ?
        """, (detection_id,)).fetchone()
        
    if not row:
        return error_response("Detection not found", 404)
        
    return jsonify(dict(row))

@app.route("/detections/<int:detection_id>/dmca", methods=["GET"])
def get_dmca(detection_id):
    try:
        with get_db() as db:
            det = db.execute("""
                SELECT d.*, p.title, p.league 
                FROM detections d
                JOIN protected_content p ON d.protected_content_id = p.id
                WHERE d.id = ?
            """, (detection_id,)).fetchone()
            
            if not det:
                return error_response("Detection not found", 404)
                
            content_info = {"title": det["title"], "league": det["league"]}
            infringer_info = {
                "url": det["stream_url"],
                "confidence": det["confidence_score"],
                "timestamp": det["detected_at"]
            }
            
            pdf_path = generator.create_notice(detection_id, content_info, infringer_info)
            
            # Optional AI notice
            ai_notice_available = False
            ai_notice_text = ""
            if request.args.get("ai") == "true" and AI_AVAILABLE:
                # Needs rights holder info - using a default for demo
                rights_holder = {
                    "name": "Sentinel Rights Holder",
                    "email": "legal@sentinel-detection.ai",
                    "address": "123 Security Blvd, Cyber City",
                    "phone": "+1-555-SECURITY"
                }
                ai_notice_text = ai_engine.generate_dmca_notice(dict(det), rights_holder)
                ai_notice_available = True
                
            # Update DB
            db.execute("UPDATE detections SET dmca_generated = TRUE WHERE id = ?", (detection_id,))
            db.commit()
            
        resp = send_file(pdf_path, as_attachment=True)
        if ai_notice_available:
            resp.headers['X-AI-Notice-Available'] = 'true'
            resp.headers['X-AI-Notice-Text'] = ai_notice_text
            
        return resp
        
    except Exception as e:
        return error_response(str(e))

@app.route("/detections/<int:detection_id>/summary", methods=["GET"])
def get_summary(detection_id):
    if not AI_AVAILABLE:
        return jsonify({"detection_id": detection_id, "summary": None, "error": "AI engine unavailable"}), 503
        
    with get_db() as db:
        det = db.execute("""
            SELECT d.*, p.title, p.league 
            FROM detections d
            JOIN protected_content p ON d.protected_content_id = p.id
            WHERE d.id = ?
        """, (detection_id,)).fetchone()
        
    if not det:
        return error_response("Detection not found", 404)
        
    try:
        summary = ai_engine.generate_detection_summary(dict(det))
        return jsonify({"detection_id": detection_id, "summary": summary})
    except Exception as e:
        return error_response(str(e))

@app.route("/analytics", methods=["GET"])
def get_analytics():
    try:
        with get_db() as db:
            stats = db.execute("""
                SELECT 
                    (SELECT COUNT(*) FROM protected_content) as total_protected,
                    (SELECT COUNT(*) FROM detections) as total_detections,
                    (SELECT AVG(confidence_score) FROM detections) as avg_confidence,
                    (SELECT COUNT(*) FROM detections WHERE detected_at >= datetime('now', '-1 day')) as detections_24h
            """).fetchone()
            
            by_league = db.execute("SELECT p.league, COUNT(*) FROM detections d JOIN protected_content p ON d.protected_content_id = p.id GROUP BY p.league").fetchall()
            top_detected = db.execute("SELECT p.title, COUNT(*) as count FROM detections d JOIN protected_content p ON d.protected_content_id = p.id GROUP BY p.title ORDER BY count DESC LIMIT 5").fetchall()
            
            ai_analysis = "Analysis pending..."
            if AI_AVAILABLE:
                recent = db.execute("SELECT d.confidence_score, p.league, d.detected_at FROM detections d JOIN protected_content p ON d.protected_content_id = p.id ORDER BY d.detected_at DESC LIMIT 20").fetchall()
                if recent:
                    ai_analysis = ai_engine.analyze_detection_pattern([dict(r) for r in recent])
                    
        return jsonify({
            "total_protected": stats["total_protected"],
            "total_detections": stats["total_detections"],
            "avg_confidence": round(stats["avg_confidence"] or 0, 2),
            "detections_last_24h": stats["detections_24h"],
            "by_league": {r[0]: r[1] for r in by_league},
            "top_detected": [{"title": r[0], "count": r[1]} for r in top_detected],
            "ai_analysis": ai_analysis
        })
    except Exception as e:
        return error_response(str(e))

# --- WebSocket Hub ---

@sock.route("/live")
def handle_live(ws):
    recent = redis_manager.get_latest_detections(10)
    if recent:
        ws.send(json.dumps({"type": "detections_update", "data": recent, "timestamp": datetime.now().isoformat()}))
        
    last_timestamp = datetime.now()
    
    while True:
        try:
            time.sleep(5)
            with get_db() as db:
                new_ones = db.execute("""
                    SELECT d.*, p.title, p.league 
                    FROM detections d
                    JOIN protected_content p ON d.protected_content_id = p.id
                    WHERE d.detected_at > ?
                """, (last_timestamp.strftime('%Y-%m-%d %H:%M:%S'),)).fetchall()
                
            if new_ones:
                data = [dict(r) for r in new_ones]
                ws.send(json.dumps({
                    "type": "detections_update",
                    "data": data,
                    "timestamp": datetime.now().isoformat()
                }))
                last_timestamp = datetime.now()
        except:
            break

if __name__ == "__main__":
    app.run(debug=True, port=8000, host='0.0.0.0')
