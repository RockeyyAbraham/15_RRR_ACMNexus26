"""
Sentinel Backend Central Hub - Flask REST & WebSocket API.
Connecting Video pHash Hashing, Groq AI Summaries, and DMCA PDF Generation.
"""

import os
import json
import sqlite3
from datetime import datetime
from flask import Flask, request, jsonify, send_file
from flask_sock import Sock

# Import module classes
from engines.hash_engine import VideoHashEngine
from engines.matcher import VideoMatcher
from engines.ai_engine import SentinelAI
from generators.dmca_generator import DMCAGenerator
from utils.redis_utils import redis_manager

app = Flask(__name__)
sock = Sock(app)  # Initialize WebSocket support

# Initialize engine instances
hash_engine = VideoHashEngine(frame_sample_rate=10, hash_size=8)
matcher = VideoMatcher(threshold=85.0, hash_size=8)
ai_engine = SentinelAI()
generator = DMCAGenerator(output_dir="../notices")

# Ensure notices directory exists
os.makedirs("../notices", exist_ok=True)


# Database setup
def init_db():
    """Initialize SQLite database with required tables."""
    conn = sqlite3.connect("../data/sentinel.db")
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
    conn.close()


# Initialize database on startup
init_db()

# --- ROUTES ---


@app.route("/upload/protected", methods=["POST"])
def upload_protected():
    """Endpoint for rights-holders to upload reference footage."""
    if "video" not in request.files:
        return jsonify({"error": "No video file provided"}), 400

    video_file = request.files["video"]
    if video_file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    # Save uploaded file temporarily
    video_path = f"temp/{video_file.filename}"
    os.makedirs("temp", exist_ok=True)
    video_file.save(video_path)

    try:
        # Extract pHashes using hash_engine
        hashes, metadata = hash_engine.hash_video(video_path)

        # Store in database
        conn = sqlite3.connect("../data/sentinel.db")
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO protected_content (title, league, video_hashes, audio_hash, duration_seconds)
            VALUES (?, ?, ?, ?, ?)
        """,
            (
                request.form.get("title", "Unknown"),
                request.form.get("league", "Unknown"),
                json.dumps(hashes),
                "",  # Audio hash would be extracted separately if needed
                metadata["duration_seconds"],
            ),
        )
        content_id = cursor.lastrowid
        conn.commit()
        conn.close()

        # Cache hashes in Redis for fast retrieval
        if content_id is not None:
            redis_manager.cache_protected_hashes(content_id, hashes, ttl=3600)

        # Clean up temp file
        os.remove(video_path)

        return jsonify(
            {
                "message": "Protected content uploaded and hashed",
                "content_id": content_id,
                "hash_count": len(hashes),
                "processing_time_seconds": metadata["processing_time_seconds"],
            }
        ), 201

    except Exception as e:
        # Clean up temp file on error
        if os.path.exists(video_path):
            os.remove(video_path)
        return jsonify({"error": str(e)}), 500


@app.route("/upload/suspect", methods=["POST"])
def upload_suspect():
    """Endpoint for potential piracy streams."""
    if "video" not in request.files:
        return jsonify({"error": "No video file provided"}), 400

    video_file = request.files["video"]
    if video_file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    # Save uploaded file temporarily
    video_path = f"temp/{video_file.filename}"
    os.makedirs("temp", exist_ok=True)
    video_file.save(video_path)

    try:
        # Extract pHashes from suspect video
        suspect_hashes, suspect_metadata = hash_engine.hash_video(video_path)

        # Get all protected content IDs from Redis (fallback to database)
        protected_ids = redis_manager.get_all_protected_content_ids()
        if not protected_ids:
            # Fallback to database
            conn = sqlite3.connect("../data/sentinel.db")
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM protected_content")
            protected_ids = [row[0] for row in cursor.fetchall()]
            conn.close()

        # Get protected content details and hashes
        detections = []
        conn = sqlite3.connect("../data/sentinel.db")
        cursor = conn.cursor()

        for content_id in protected_ids:
            # Initialize variables to avoid UnboundLocalError
            title = "Unknown"
            league = "Unknown"
            protected_hashes = []

            # Try to get hashes from Redis cache first
            cached_hashes = redis_manager.get_protected_hashes(content_id)
            if cached_hashes is not None:
                protected_hashes = cached_hashes
                # Get title and league from database since we don't cache them
                cursor.execute(
                    "SELECT title, league FROM protected_content WHERE id = ?",
                    (content_id,),
                )
                row = cursor.fetchone()
                if row is not None:
                    title, league = row
            else:
                # Fallback to database
                cursor.execute(
                    "SELECT title, league, video_hashes, duration_seconds FROM protected_content WHERE id = ?",
                    (content_id,),
                )
                row = cursor.fetchone()
                if row is None:
                    continue
                title, league, video_hashes_json, duration = row
                protected_hashes = json.loads(video_hashes_json)

            # Match suspect hashes against protected hashes
            match_result = matcher.match_video_sequences(
                suspect_hashes, protected_hashes
            )

            if match_result["is_match"]:
                # Store detection event
                cursor.execute(
                    """
                    INSERT INTO detections (protected_content_id, stream_url, confidence_score)
                    VALUES (?, ?, ?)
                """,
                    (
                        content_id,
                        request.form.get("stream_url", "unknown"),
                        match_result["confidence_score"],
                    ),
                )
                detection_id = cursor.lastrowid

                # Cache detection result in Redis
                if detection_id is not None:
                    detection_data = {
                        "detection_id": detection_id,
                        "content_id": content_id,
                        "confidence_score": match_result["confidence_score"],
                        "stream_url": request.form.get("stream_url", "unknown"),
                        "detected_at": datetime.now().isoformat(),
                        "match_details": match_result,
                    }
                    redis_manager.cache_detection_result(
                        detection_id, detection_data, ttl=1800
                    )

                detections.append(
                    {
                        "detection_id": detection_id,
                        "content_id": content_id,
                        "title": title,
                        "league": league,
                        "confidence_score": match_result["confidence_score"],
                        "stream_url": request.form.get("stream_url", "unknown"),
                    }
                )

        conn.commit()
        conn.close()

        # Clean up temp file
        os.remove(video_path)

        return jsonify(
            {
                "message": "Suspect video processed",
                "detections": detections,
                "processing_time_seconds": suspect_metadata["processing_time_seconds"],
            }
        ), 200

    except Exception as e:
        # Clean up temp file on error
        if os.path.exists(video_path):
            os.remove(video_path)
        return jsonify({"error": str(e)}), 500


@app.route("/detections", methods=["GET"])
def get_detections():
    """Retrieve all logged piracy events."""
    try:
        conn = sqlite3.connect("../data/sentinel.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT d.id, p.title, p.league, d.stream_url, d.confidence_score, d.detected_at
            FROM detections d
            JOIN protected_content p ON d.protected_content_id = p.id
            ORDER BY d.detected_at DESC
        """)
        rows = cursor.fetchall()
        conn.close()

        detections = []
        for row in rows:
            detections.append(
                {
                    "id": row[0],
                    "title": row[1],
                    "league": row[2],
                    "stream_url": row[3],
                    "confidence_score": row[4],
                    "detected_at": row[5],
                }
            )

        return jsonify(detections), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/detections/<int:detection_id>/dmca", methods=["GET"])
def generate_dmca(detection_id):
    """Programmatically create and download a DMCA Notice PDF."""
    try:
        # Fetch detection details from DB
        conn = sqlite3.connect("../data/sentinel.db")
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT d.id, d.stream_url, d.confidence_score, d.detected_at,
                   p.title, p.league, p.duration_seconds
            FROM detections d
            JOIN protected_content p ON d.protected_content_id = p.id
            WHERE d.id = ?
        """,
            (detection_id,),
        )
        row = cursor.fetchone()
        conn.close()

        if row is None:
            return jsonify({"error": "Detection not found"}), 404

        detection_data = {
            "id": row[0],
            "stream_url": row[1],
            "confidence_score": row[2],
            "detected_at": row[3],
            "title": row[4],
            "league": row[5],
            "duration_seconds": row[6],
        }

        # Generate PDF using dmca_generator
        content_info = {
            "title": detection_data["title"],
            "league": detection_data["league"],
        }
        infringer_info = {
            "url": detection_data["stream_url"],
            "confidence": detection_data["confidence_score"],
            "timestamp": detection_data["detected_at"],
        }
        pdf_path = generator.create_notice(
            detection_data["id"], content_info, infringer_info
        )

        # Update database to mark DMCA as generated
        conn = sqlite3.connect("../data/sentinel.db")
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE detections SET dmca_generated = TRUE WHERE id = ?", (detection_id,)
        )
        conn.commit()
        conn.close()

        return send_file(
            pdf_path,
            as_attachment=True,
            download_name=f"dmca_notice_{detection_id}.pdf",
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/health", methods=["GET"])
def health_check():
    """System health check for monitor status."""
    engines_status = ["hashing", "matching", "ai", "generator"]
    if redis_manager.is_available():
        engines_status.append("redis")
    else:
        engines_status.append("redis_unavailable")

    return jsonify(
        {
            "status": "online",
            "engines": engines_status,
            "timestamp": datetime.now().isoformat(),
        }
    ), 200


# --- WEBSOCKETS ---
@sock.route("/live")
def handle_live_detections(ws):
    """Push real-time detection events to the Flutter dashboard."""
    # Simple implementation: send current detections every 5 seconds
    # In a production system, we would listen for database changes or use a queue
    import time

    while True:
        try:
            conn = sqlite3.connect("../data/sentinel.db")
            cursor = conn.cursor()
            cursor.execute("""
                SELECT d.id, p.title, p.league, d.stream_url, d.confidence_score, d.detected_at
                FROM detections d
                JOIN protected_content p ON d.protected_content_id = p.id
                ORDER BY d.detected_at DESC
                LIMIT 10
            """)
            rows = cursor.fetchall()
            conn.close()

            detections = []
            for row in rows:
                detections.append(
                    {
                        "id": row[0],
                        "title": row[1],
                        "league": row[2],
                        "stream_url": row[3],
                        "confidence_score": row[4],
                        "detected_at": row[5],
                    }
                )

            ws.send(json.dumps({"type": "detections_update", "data": detections}))
            time.sleep(5)  # Update every 5 seconds
        except Exception as e:
            print(f"WebSocket error: {e}")
            break


if __name__ == "__main__":
    # Start the Flask development server on port 8000
    app.run(debug=True, port=8000)
