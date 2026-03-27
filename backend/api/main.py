"""
Sentinel Backend Central Hub - Flask REST & WebSocket API.
Provides high-fidelity piracy detection, AI summaries, and automated DMCA generation.
"""

import os
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
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
sock = Sock(app)  # Initialize WebSocket support

# Stable paths based on repository layout
API_DIR = Path(__file__).resolve().parent
BACKEND_DIR = API_DIR.parent
DB_PATH = BACKEND_DIR / "data" / "sentinel.db"
TEMP_DIR = BACKEND_DIR / "temp"
NOTICES_DIR = BACKEND_DIR.parent / "notices"

# Detection policy (hackathon-safe defaults)
AUTO_ACTION_THRESHOLD = float(os.getenv("AUTO_ACTION_THRESHOLD", "85"))
MANUAL_REVIEW_THRESHOLD = float(os.getenv("MANUAL_REVIEW_THRESHOLD", "75"))
MAX_ASYNC_WORKERS = int(os.getenv("MAX_ASYNC_WORKERS", "2"))

# Initialize engine instances
hash_engine = VideoHashEngine(frame_sample_rate=10, hash_size=8)
matcher = VideoMatcher(threshold=85.0, hash_size=8)
audio_engine = AudioHashEngine()
ai_engine = SentinelAI()
generator = DMCAGenerator(output_dir="../notices")

# Ensure notices directory exists
NOTICES_DIR.mkdir(parents=True, exist_ok=True)

# Async processing state
executor = ThreadPoolExecutor(max_workers=MAX_ASYNC_WORKERS)
jobs = {}
jobs_lock = threading.Lock()

# Structured telemetry logger
logging.basicConfig(level=logging.INFO, format="%(message)s")
telemetry_logger = logging.getLogger("sentinel.telemetry")


def get_ai_engine():
    """Lazily initialize AI engine so API can boot without optional AI config."""
    global ai_engine
    if ai_engine is None:
        try:
            ai_engine = SentinelAI()
        except Exception:
            ai_engine = False
    return ai_engine if ai_engine else None


def log_event(event_type: str, **payload):
    """Emit structured telemetry for detections and pipeline stages."""
    event = {
        "timestamp": datetime.now().isoformat(),
        "event_type": event_type,
        **payload,
    }
    telemetry_logger.info(json.dumps(event, default=str))


def create_job(job_type: str, payload: dict):
    job_id = str(uuid.uuid4())
    with jobs_lock:
        jobs[job_id] = {
            "job_id": job_id,
            "job_type": job_type,
            "status": "queued",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "payload": payload,
            "result": None,
            "error": None,
        }
    return job_id


def update_job(job_id: str, **updates):
    with jobs_lock:
        if job_id not in jobs:
            return
        jobs[job_id].update(updates)
        jobs[job_id]["updated_at"] = datetime.now().isoformat()


def get_job(job_id: str):
    with jobs_lock:
        return jobs.get(job_id)


def classify_detection_tier(score: float):
    """Classify a confidence score into action tiers using configured thresholds."""
    if score >= AUTO_ACTION_THRESHOLD:
        return "auto_action", "score_above_auto_threshold"
    if score >= MANUAL_REVIEW_THRESHOLD:
        return "manual_review", "score_above_review_threshold"
    return "no_match", "score_below_review_threshold"


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


def process_protected_video(video_path: Path, title: str, league: str):
    """Core protected-content processing logic used by sync and async routes."""
    start = time.perf_counter()

    video_hashes, video_metadata = hash_engine.hash_video(video_path)
    audio_hash = audio_engine.extract_audio_hash(video_path)

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO protected_content (title, league, video_hashes, audio_hash, duration_seconds)
        VALUES (?, ?, ?, ?, ?)
    """,
        (
            title or "Unknown",
            league or "Unknown",
            json.dumps(video_hashes),
            audio_hash or "",
            video_metadata["duration_seconds"],
        ),
    )
    content_id = cursor.lastrowid
    conn.commit()
    conn.close()

        # Cache hashes in Redis for fast retrieval
        if content_id is not None:
            redis_manager.cache_protected_hashes(content_id, video_hashes, ttl=3600)

    elapsed = time.perf_counter() - start
    log_event(
        "protected_content_processed",
        content_id=content_id,
        title=title,
        league=league,
        video_hash_count=len(video_hashes),
        audio_hash_extracted=audio_hash is not None,
        latency_ms=round(elapsed * 1000, 2),
    )

    return {
        "message": "Protected content uploaded and hashed",
        "content_id": content_id,
        "video_hash_count": len(video_hashes),
        "audio_hash_extracted": audio_hash is not None,
        "processing_time_seconds": video_metadata["processing_time_seconds"],
        "latency_ms": round(elapsed * 1000, 2),
    }


def process_suspect_video(video_path: Path, stream_url: str):
    """Core suspect-content processing logic used by sync and async routes."""
    start = time.perf_counter()

    suspect_hashes, suspect_metadata = hash_engine.hash_video(video_path)
    suspect_audio_hash = audio_engine.extract_audio_hash(video_path)

    protected_ids = redis_manager.get_all_protected_content_ids()
    if not protected_ids:
        conn = sqlite3.connect(str(DB_PATH))
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
            protected_audio_hash = None

            # Try to get hashes from Redis cache first
            cached_hashes = redis_manager.get_protected_hashes(content_id)
            if cached_hashes is not None:
                protected_hashes = cached_hashes
                # Get title and league from database since we don't cache them
                cursor.execute(
                    "SELECT title, league, audio_hash FROM protected_content WHERE id = ?",
                    (content_id,),
                )
                row = cursor.fetchone()
                if row is not None:
                    title, league, protected_audio_hash = row
            else:
                # Fallback to database
                cursor.execute(
                    "SELECT title, league, video_hashes, audio_hash, duration_seconds FROM protected_content WHERE id = ?",
                    (content_id,),
                )
                row = cursor.fetchone()
                if row is None:
                    continue
                title, league, video_hashes_json, protected_audio_hash, duration = row
                protected_hashes = json.loads(video_hashes_json)

            # Match suspect hashes against protected hashes
            video_match_result = matcher.match_video_sequences(
                suspect_hashes, protected_hashes
            )
            
            # Audio matching if both hashes exist
            audio_match_score = 0.0
            if suspect_audio_hash and protected_audio_hash:
                _, audio_match_score = matcher.compare_hashes(suspect_audio_hash, protected_audio_hash)
            
            # Multi-modal confidence scoring
            # Weight video matching more heavily (70%) than audio (30%)
            video_confidence = video_match_result["confidence_score"]
            audio_confidence = audio_match_score
            
            if audio_confidence > 0:  # Audio match available
                combined_confidence = (video_confidence * 0.7) + (audio_confidence * 0.3)
            else:  # Video only
                combined_confidence = video_confidence
            
            # Adjust match result with combined confidence
            video_match_result["confidence_score"] = combined_confidence
            video_match_result["audio_match_score"] = audio_confidence
            video_match_result["video_match_score"] = video_confidence
            video_match_result["multi_modal"] = audio_confidence > 0

            if video_match_result["is_match"]:
                # Store detection event
                cursor.execute(
                    """
                    INSERT INTO detections (protected_content_id, stream_url, confidence_score)
                    VALUES (?, ?, ?)
                """,
                    (
                        content_id,
                        request.form.get("stream_url", "unknown"),
                        video_match_result["confidence_score"],
                    ),
                )
                detection_id = cursor.lastrowid

                # Cache detection result in Redis
                if detection_id is not None:
                    detection_data = {
                        "detection_id": detection_id,
                        "content_id": content_id,
                        "confidence_score": video_match_result["confidence_score"],
                        "stream_url": request.form.get("stream_url", "unknown"),
                        "detected_at": datetime.now().isoformat(),
                        "match_details": video_match_result,
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
                        "confidence_score": video_match_result["confidence_score"],
                        "audio_match_score": video_match_result.get("audio_match_score", 0.0),
                        "video_match_score": video_match_result.get("video_match_score", 0.0),
                        "multi_modal": video_match_result.get("multi_modal", False),
                        "stream_url": request.form.get("stream_url", "unknown"),
                    }
                )

        conn.commit()
        conn.close()

    elapsed = time.perf_counter() - start
    log_event(
        "suspect_processed",
        stream_url=stream_url,
        detections_count=len(detections),
        latency_ms=round(elapsed * 1000, 2),
    )

    return {
        "message": "Suspect video processed",
        "detections": detections,
        "thresholds": {
            "auto_action": AUTO_ACTION_THRESHOLD,
            "manual_review": MANUAL_REVIEW_THRESHOLD,
        },
        "processing_time_seconds": suspect_metadata["processing_time_seconds"],
        "latency_ms": round(elapsed * 1000, 2),
    }


def submit_background_job(job_id: str, job_type: str, video_path: Path, payload: dict):
    """Execute fingerprinting work asynchronously and persist status in-memory."""
    update_job(job_id, status="running")
    try:
        if job_type == "protected_upload":
            result = process_protected_video(
                video_path=video_path,
                title=payload.get("title", "Unknown"),
                league=payload.get("league", "Unknown"),
            )
        elif job_type == "suspect_upload":
            result = process_suspect_video(
                video_path=video_path,
                stream_url=payload.get("stream_url", "unknown"),
            )
        else:
            raise ValueError(f"Unsupported job type: {job_type}")

        update_job(job_id, status="completed", result=result)
    except Exception as e:
        update_job(job_id, status="failed", error=str(e))
    finally:
        try:
            if os.path.exists(video_path):
                os.remove(video_path)
        except Exception:
            pass


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

    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    video_path = TEMP_DIR / f"{uuid.uuid4()}_{video_file.filename}"
    video_file.save(video_path)

    try:
        result = process_protected_video(
            video_path=video_path,
            title=request.form.get("title", "Unknown"),
            league=request.form.get("league", "Unknown"),
        )
        os.remove(video_path)
        return jsonify(result), 201

    except Exception as e:
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

    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    video_path = TEMP_DIR / f"{uuid.uuid4()}_{video_file.filename}"
    video_file.save(video_path)

    try:
        result = process_suspect_video(
            video_path=video_path,
            stream_url=request.form.get("stream_url", "unknown"),
        )
        os.remove(video_path)
        return jsonify(result), 200

    except Exception as e:
        if os.path.exists(video_path):
            os.remove(video_path)
        return jsonify({"error": str(e)}), 500


@app.route("/upload/protected/async", methods=["POST"])
def upload_protected_async():
    """Queue protected-content hashing in background and return a job handle."""
    if "video" not in request.files:
        return jsonify({"error": "No video file provided"}), 400

    video_file = request.files["video"]
    if video_file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    video_path = TEMP_DIR / f"{uuid.uuid4()}_{video_file.filename}"
    video_file.save(video_path)

    payload = {
        "title": request.form.get("title", "Unknown"),
        "league": request.form.get("league", "Unknown"),
        "filename": video_file.filename,
    }
    job_id = create_job("protected_upload", payload)
    executor.submit(submit_background_job, job_id, "protected_upload", video_path, payload)

    return jsonify({"job_id": job_id, "status": "queued", "job_type": "protected_upload"}), 202


@app.route("/upload/suspect/async", methods=["POST"])
def upload_suspect_async():
    """Queue suspect-content fingerprinting in background and return a job handle."""
    if "video" not in request.files:
        return jsonify({"error": "No video file provided"}), 400

    video_file = request.files["video"]
    if video_file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    video_path = TEMP_DIR / f"{uuid.uuid4()}_{video_file.filename}"
    video_file.save(video_path)

    payload = {
        "stream_url": request.form.get("stream_url", "unknown"),
        "filename": video_file.filename,
    }
    job_id = create_job("suspect_upload", payload)
    executor.submit(submit_background_job, job_id, "suspect_upload", video_path, payload)

    return jsonify({"job_id": job_id, "status": "queued", "job_type": "suspect_upload"}), 202


@app.route("/jobs/<job_id>", methods=["GET"])
def get_job_status(job_id):
    """Get status and result/error for an async fingerprinting job."""
    job = get_job(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    return jsonify(job), 200


@app.route("/metrics/summary", methods=["GET"])
def get_metrics_summary():
    """Judge-facing metrics for detections, confidence, and triage breakdown."""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM protected_content")
        protected_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM detections")
        detection_count = cursor.fetchone()[0]

        cursor.execute("SELECT COALESCE(AVG(confidence_score), 0) FROM detections")
        avg_confidence = float(cursor.fetchone()[0] or 0.0)

        cursor.execute(
            """
            SELECT
                SUM(CASE WHEN confidence_score >= ? THEN 1 ELSE 0 END) AS auto_action_count,
                SUM(CASE WHEN confidence_score >= ? AND confidence_score < ? THEN 1 ELSE 0 END) AS manual_review_count
            FROM detections
            """,
            (AUTO_ACTION_THRESHOLD, MANUAL_REVIEW_THRESHOLD, AUTO_ACTION_THRESHOLD),
        )
        row = cursor.fetchone()
        auto_action_count = row[0] or 0
        manual_review_count = row[1] or 0

        conn.close()

        return jsonify(
            {
                "protected_content_count": protected_count,
                "detections_count": detection_count,
                "average_confidence": round(avg_confidence, 2),
                "auto_action_count": auto_action_count,
                "manual_review_count": manual_review_count,
                "thresholds": {
                    "auto_action": AUTO_ACTION_THRESHOLD,
                    "manual_review": MANUAL_REVIEW_THRESHOLD,
                },
                "async": {
                    "max_workers": MAX_ASYNC_WORKERS,
                    "tracked_jobs": len(jobs),
                },
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
        return error_response(str(e))

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
            "async": {
                "max_workers": MAX_ASYNC_WORKERS,
                "tracked_jobs": len(jobs),
            },
            "timestamp": datetime.now().isoformat(),
        }
    ), 200


# --- WEBSOCKETS ---
@sock.route("/live")
def handle_live(ws):
    recent = redis_manager.get_latest_detections(10)
    if recent:
        ws.send(json.dumps({"type": "detections_update", "data": recent, "timestamp": datetime.now().isoformat()}))
        
    last_timestamp = datetime.now()
    
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
    app.run(debug=True, port=8000, host='0.0.0.0')
