"""
FastAPI compatibility entrypoint for Sentinel.

This app mounts the existing Flask API for REST endpoints and serves
native FastAPI WebSocket updates at /live.
"""

import asyncio
import sqlite3
from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.wsgi import WSGIMiddleware

from api.main import DB_PATH, app as flask_app

app = FastAPI(title="Sentinel API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def fetch_recent_detections(limit: int = 10):
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT d.id, p.title, p.league, d.stream_url, d.confidence_score, d.detected_at
        FROM detections d
        JOIN protected_content p ON d.protected_content_id = p.id
        ORDER BY d.detected_at DESC
        LIMIT ?
        """,
        (limit,),
    )
    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "id": row[0],
            "title": row[1],
            "league": row[2],
            "stream_url": row[3],
            "confidence_score": row[4],
            "detected_at": row[5],
        }
        for row in rows
    ]


@app.websocket("/live")
async def websocket_live_detections(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            detections = fetch_recent_detections(limit=10)
            await websocket.send_json(
                {
                    "type": "detections_update",
                    "data": detections,
                    "timestamp": datetime.now().isoformat(),
                }
            )
            await asyncio.sleep(5)
    except WebSocketDisconnect:
        return
    except Exception:
        await websocket.close()


# Mount Flask API under root so existing REST routes continue to work unchanged.
app.mount("/", WSGIMiddleware(flask_app))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api.fastapi_main:app", host="0.0.0.0", port=8000, reload=True)
