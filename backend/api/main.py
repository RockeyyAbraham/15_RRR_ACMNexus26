"""
Sentinel Backend Central Hub - Flask REST & WebSocket API.
Connecting Video pHash Hashing, Groq AI Summaries, and DMCA PDF Generation.
"""

import os
import json
import sqlite3
import uuid
import time
import logging
import threading
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from flask import Flask, request, jsonify, send_file
from flask_sock import Sock

# Import module classes
from engines.hash_engine import VideoHashEngine
from engines.matcher import VideoMatcher
from engines.ai_engine import SentinelAI
from engines.audio_engine import AudioHashEngine
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
MAX_QUEUE_SIZE = int(os.getenv("MAX_QUEUE_SIZE", "20"))

# Initialize engine instances
hash_engine = VideoHashEngine(frame_sample_rate=10, hash_size=8)
matcher = VideoMatcher(threshold=85.0, hash_size=8)
audio_engine = AudioHashEngine()
ai_engine = None
generator = DMCAGenerator(output_dir=str(NOTICES_DIR))

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
            "stage": "queued",
            "cancel_requested": False,
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


def get_active_job_count():
    with jobs_lock:
        return sum(1 for j in jobs.values() if j.get("status") in ["queued", "running"]) 


def request_job_cancel(job_id: str):
    with jobs_lock:
        job = jobs.get(job_id)
        if not job:
            return None
        if job.get("status") in ["completed", "failed", "cancelled"]:
            return job
        job["cancel_requested"] = True
        if job.get("status") == "queued":
            job["status"] = "cancelled"
            job["stage"] = "cancelled"
        else:
            job["stage"] = "cancel_requested"
        job["updated_at"] = datetime.now().isoformat()
        return job


def set_job_stage(job_id: str, stage: str):
    update_job(job_id, stage=stage)


def should_abort(job_id: str):
    job = get_job(job_id)
    return bool(job and job.get("cancel_requested"))


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
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
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
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_detections_detected_at ON detections(detected_at)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_detections_content_id ON detections(protected_content_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_protected_uploaded_at ON protected_content(uploaded_at)")
    conn.commit()
    conn.close()


def process_protected_video(video_path: Path, title: str, league: str, progress_cb=None, cancel_cb=None):
    """Core protected-content processing logic used by sync and async routes."""
    start = time.perf_counter()

    if progress_cb:
        progress_cb("hashing_video")
    if cancel_cb and cancel_cb():
        raise RuntimeError("Job cancelled")

    video_hashes, video_metadata = hash_engine.hash_video(video_path)

    if progress_cb:
        progress_cb("hashing_audio")
    if cancel_cb and cancel_cb():
        raise RuntimeError("Job cancelled")

    audio_hash = audio_engine.extract_audio_hash(video_path)

    if progress_cb:
        progress_cb("persisting")
    if cancel_cb and cancel_cb():
        raise RuntimeError("Job cancelled")

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


def process_suspect_video(video_path: Path, stream_url: str, progress_cb=None, cancel_cb=None):
    """Core suspect-content processing logic used by sync and async routes."""
    start = time.perf_counter()

    if progress_cb:
        progress_cb("hashing_video")
    if cancel_cb and cancel_cb():
        raise RuntimeError("Job cancelled")

    suspect_hashes, suspect_metadata = hash_engine.hash_video(video_path)

    if progress_cb:
        progress_cb("hashing_audio")
    if cancel_cb and cancel_cb():
        raise RuntimeError("Job cancelled")

    suspect_audio_hash = audio_engine.extract_audio_hash(video_path)

    if progress_cb:
        progress_cb("matching")
    if cancel_cb and cancel_cb():
        raise RuntimeError("Job cancelled")

    protected_ids = redis_manager.get_all_protected_content_ids()
    if not protected_ids:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM protected_content")
        protected_ids = [row[0] for row in cursor.fetchall()]
        conn.close()

    detections = []
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    for content_id in protected_ids:
        title = "Unknown"
        league = "Unknown"
        protected_hashes = []
        protected_audio_hash = None

        cached_hashes = redis_manager.get_protected_hashes(content_id)
        if cached_hashes is not None:
            protected_hashes = cached_hashes
            cursor.execute(
                "SELECT title, league, audio_hash FROM protected_content WHERE id = ?",
                (content_id,),
            )
            row = cursor.fetchone()
            if row is not None:
                title, league, protected_audio_hash = row
        else:
            cursor.execute(
                "SELECT title, league, video_hashes, audio_hash FROM protected_content WHERE id = ?",
                (content_id,),
            )
            row = cursor.fetchone()
            if row is None:
                continue
            title, league, video_hashes_json, protected_audio_hash = row
            protected_hashes = json.loads(video_hashes_json)

        video_match_result = matcher.match_video_sequences(suspect_hashes, protected_hashes)

        audio_match_score = 0.0
        if suspect_audio_hash and protected_audio_hash:
            _, audio_match_score = matcher.compare_hashes(suspect_audio_hash, protected_audio_hash)

        video_confidence = video_match_result["confidence_score"]
        audio_confidence = audio_match_score
        combined_confidence = (video_confidence * 0.7) + (audio_confidence * 0.3) if audio_confidence > 0 else video_confidence

        decision_tier, decision_reason = classify_detection_tier(combined_confidence)

        is_match = decision_tier != "no_match"

        video_match_result["confidence_score"] = combined_confidence
        video_match_result["audio_match_score"] = audio_confidence
        video_match_result["video_match_score"] = video_confidence
        video_match_result["multi_modal"] = audio_confidence > 0
        video_match_result["is_match"] = is_match
        video_match_result["decision_tier"] = decision_tier
        video_match_result["decision_reason"] = decision_reason

        if is_match:
            cursor.execute(
                """
                INSERT INTO detections (protected_content_id, stream_url, confidence_score)
                VALUES (?, ?, ?)
            """,
                (content_id, stream_url, combined_confidence),
            )
            detection_id = cursor.lastrowid

            if detection_id is not None:
                detection_data = {
                    "detection_id": detection_id,
                    "content_id": content_id,
                    "confidence_score": combined_confidence,
                    "decision_tier": decision_tier,
                    "decision_reason": decision_reason,
                    "stream_url": stream_url,
                    "detected_at": datetime.now().isoformat(),
                    "match_details": video_match_result,
                }
                redis_manager.cache_detection_result(detection_id, detection_data, ttl=1800)

            detections.append(
                {
                    "detection_id": detection_id,
                    "content_id": content_id,
                    "title": title,
                    "league": league,
                    "confidence_score": combined_confidence,
                    "audio_match_score": audio_confidence,
                    "video_match_score": video_confidence,
                    "multi_modal": audio_confidence > 0,
                    "decision_tier": decision_tier,
                    "decision_reason": decision_reason,
                    "stream_url": stream_url,
                }
            )

            log_event(
                "detection_created",
                detection_id=detection_id,
                protected_content_id=content_id,
                stream_url=stream_url,
                confidence_score=combined_confidence,
                video_score=video_confidence,
                audio_score=audio_confidence,
                decision_tier=decision_tier,
                decision_reason=decision_reason,
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
    job = get_job(job_id)
    if not job or job.get("status") == "cancelled":
        return

    update_job(job_id, status="running", stage="starting", started_at=datetime.now().isoformat())
    try:
        if job_type == "protected_upload":
            result = process_protected_video(
                video_path=video_path,
                title=payload.get("title", "Unknown"),
                league=payload.get("league", "Unknown"),
                progress_cb=lambda s: set_job_stage(job_id, s),
                cancel_cb=lambda: should_abort(job_id),
            )
        elif job_type == "suspect_upload":
            result = process_suspect_video(
                video_path=video_path,
                stream_url=payload.get("stream_url", "unknown"),
                progress_cb=lambda s: set_job_stage(job_id, s),
                cancel_cb=lambda: should_abort(job_id),
            )
        else:
            raise ValueError(f"Unsupported job type: {job_type}")

        if should_abort(job_id):
            update_job(job_id, status="cancelled", stage="cancelled")
        else:
            update_job(job_id, status="completed", stage="completed", result=result, completed_at=datetime.now().isoformat())
    except Exception as e:
        if "cancelled" in str(e).lower() or should_abort(job_id):
            update_job(job_id, status="cancelled", stage="cancelled")
        else:
            update_job(job_id, status="failed", stage="failed", error=str(e))
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
        if get_active_job_count() >= MAX_QUEUE_SIZE:
            return jsonify({"error": "Async queue is full. Try again shortly."}), 429

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
        if get_active_job_count() >= MAX_QUEUE_SIZE:
            return jsonify({"error": "Async queue is full. Try again shortly."}), 429

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


@app.route("/jobs/<job_id>/cancel", methods=["POST"])
def cancel_job(job_id):
    """Request cancellation for a queued or running async job."""
    job = request_job_cancel(job_id)
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
                    "max_queue_size": MAX_QUEUE_SIZE,
                    "tracked_jobs": len(jobs),
                    "active_jobs": get_active_job_count(),
                },
            }
        ), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/detections", methods=["GET"])
def get_detections():
    """Retrieve all logged piracy events."""
    try:
        conn = sqlite3.connect(str(DB_PATH))
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
        conn = sqlite3.connect(str(DB_PATH))
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
        conn = sqlite3.connect(str(DB_PATH))
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
    engines_status = ["hashing", "matching", "generator"]
    if get_ai_engine() is not None:
        engines_status.append("ai")
    else:
        engines_status.append("ai_unavailable")

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
                "max_queue_size": MAX_QUEUE_SIZE,
                "tracked_jobs": len(jobs),
                "active_jobs": get_active_job_count(),
            },
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
            conn = sqlite3.connect(str(DB_PATH))
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
