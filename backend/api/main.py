"""
Sentinel Backend Central Hub - Flask REST & WebSocket API.
Provides asynchronous fingerprinting, candidate triage, detection, and DMCA generation.
"""

import os
import json
import uuid
import time
import logging
import sqlite3
import threading
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

from flask import Flask, request, jsonify, send_file

try:
    from flask_cors import CORS
except ImportError:
    def CORS(_app):
        return None

try:
    from flask_sock import Sock
except ImportError:
    class Sock:
        def __init__(self, _app):
            pass

        def route(self, _path):
            def decorator(func):
                return func

            return decorator

from engines.hash_engine import VideoHashEngine
from engines.audio_engine import AudioHashEngine
from engines.matcher import VideoMatcher
from engines.ai_engine import SentinelAI
from generators.dmca_generator import DMCAGenerator
from utils.redis_utils import redis_manager

app = Flask(__name__)
CORS(app)
sock = Sock(app)

API_DIR = Path(__file__).resolve().parent
BACKEND_DIR = API_DIR.parent
DB_PATH = BACKEND_DIR / "data" / "sentinel.db"
TEMP_DIR = BACKEND_DIR / "temp"
NOTICES_DIR = BACKEND_DIR.parent / "notices"

AUTO_ACTION_THRESHOLD = float(os.getenv("AUTO_ACTION_THRESHOLD", "85"))
MANUAL_REVIEW_THRESHOLD = float(os.getenv("MANUAL_REVIEW_THRESHOLD", "75"))
MAX_ASYNC_WORKERS = int(os.getenv("MAX_ASYNC_WORKERS", "2"))
MAX_QUEUE_SIZE = int(os.getenv("MAX_QUEUE_SIZE", "20"))

hash_engine = VideoHashEngine(frame_sample_rate=10, hash_size=8)
matcher = VideoMatcher(threshold=85.0, hash_size=8)
audio_engine = AudioHashEngine()
ai_engine = None
generator = DMCAGenerator(output_dir=str(NOTICES_DIR))

NOTICES_DIR.mkdir(parents=True, exist_ok=True)
TEMP_DIR.mkdir(parents=True, exist_ok=True)

executor = ThreadPoolExecutor(max_workers=MAX_ASYNC_WORKERS)
jobs = {}
jobs_lock = threading.Lock()

logging.basicConfig(level=logging.INFO, format="%(message)s")
telemetry_logger = logging.getLogger("sentinel.telemetry")


def get_ai_engine():
    """Lazily initialize AI engine so API boots even without AI key."""
    global ai_engine
    if ai_engine is None:
        try:
            ai_engine = SentinelAI()
        except Exception:
            ai_engine = False
    return ai_engine if ai_engine else None


def log_event(event_type: str, **payload):
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


def should_abort(job_id: str):
    job = get_job(job_id)
    return bool(job and job.get("cancel_requested"))


def classify_detection_tier(score: float):
    if score >= AUTO_ACTION_THRESHOLD:
        return "auto_action", "score_above_auto_threshold"
    if score >= MANUAL_REVIEW_THRESHOLD:
        return "manual_review", "score_above_review_threshold"
    return "no_match", "score_below_review_threshold"


def calculate_suspicion_score(keyword_hits: list, event_context: str, platform: str, url: str) -> float:
    """Heuristic candidate suspicion score in [0.0, 1.0]."""
    score = 0.0

    if keyword_hits:
        keyword_score = min(len(keyword_hits) / 5.0, 1.0)
        score += 0.35 * keyword_score

    if event_context:
        score += 0.20

    platform_risk = {
        "youtube": 0.6,
        "twitch": 0.7,
        "reddit": 0.5,
        "telegram": 0.9,
        "facebook": 0.5,
        "twitter": 0.6,
        "manual": 0.8,
    }
    score += 0.20 * platform_risk.get((platform or "").lower(), 0.5)

    suspicious_patterns = ["live", "stream", "watch", "free", "hd", "full"]
    url_lower = (url or "").lower()
    pattern_matches = sum(1 for p in suspicious_patterns if p in url_lower)
    score += 0.10 * min(pattern_matches / 3.0, 1.0)

    score += 0.15 * 0.5
    return min(score, 1.0)


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS protected_content (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            league TEXT NOT NULL,
            video_hashes TEXT NOT NULL,
            audio_hash TEXT NOT NULL,
            duration_seconds INTEGER,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cursor.execute(
        """
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
        """
    )

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_detections_detected_at ON detections(detected_at)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_detections_content_id ON detections(protected_content_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_protected_uploaded_at ON protected_content(uploaded_at)")

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS candidates (
            id TEXT PRIMARY KEY,
            url TEXT NOT NULL,
            platform TEXT NOT NULL,
            keyword_hits TEXT,
            event_context TEXT,
            suspicion_score FLOAT NOT NULL,
            source_timestamp TIMESTAMP,
            status TEXT DEFAULT 'queued',
            verification_job_id TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_candidates_status ON candidates(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_candidates_score ON candidates(suspicion_score)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_candidates_created ON candidates(created_at)")

    conn.commit()
    conn.close()


def process_protected_video(video_path: Path, title: str, league: str, progress_cb=None, cancel_cb=None):
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

    detections = []
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    cursor.execute("SELECT id, title, league, video_hashes, audio_hash FROM protected_content")
    protected_rows = cursor.fetchall()

    for content_id, title, league, video_hashes_json, protected_audio_hash in protected_rows:
        try:
            protected_hashes = json.loads(video_hashes_json)
        except Exception:
            continue

        if not protected_hashes:
            continue

        video_result = matcher.match_video_sequences(suspect_hashes, protected_hashes)
        video_confidence = float(video_result.get("confidence_score", 0.0))

        audio_confidence = 0.0
        if suspect_audio_hash and protected_audio_hash:
            _, audio_confidence = matcher.compare_hashes(suspect_audio_hash, protected_audio_hash)

        combined_confidence = (video_confidence * 0.7 + audio_confidence * 0.3) if audio_confidence > 0 else video_confidence

        decision_tier, decision_reason = classify_detection_tier(combined_confidence)
        is_match = decision_tier != "no_match"

        if not is_match:
            continue

        cursor.execute(
            """
            INSERT INTO detections (protected_content_id, stream_url, confidence_score)
            VALUES (?, ?, ?)
            """,
            (content_id, stream_url, combined_confidence),
        )
        detection_id = cursor.lastrowid

        detection_data = {
            "detection_id": detection_id,
            "content_id": content_id,
            "confidence_score": combined_confidence,
            "decision_tier": decision_tier,
            "decision_reason": decision_reason,
            "stream_url": stream_url,
            "detected_at": datetime.now().isoformat(),
            "match_details": {
                "video_match_score": video_confidence,
                "audio_match_score": audio_confidence,
                "multi_modal": audio_confidence > 0,
                "confidence_score": combined_confidence,
            },
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
        "processing_time_seconds": suspect_metadata.get("processing_time_seconds", 0),
        "latency_ms": round(elapsed * 1000, 2),
    }


def submit_background_job(job_id: str, job_type: str, video_path: Path, payload: dict):
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
                progress_cb=lambda s: update_job(job_id, stage=s),
                cancel_cb=lambda: should_abort(job_id),
            )
        elif job_type == "suspect_upload":
            result = process_suspect_video(
                video_path=video_path,
                stream_url=payload.get("stream_url", "unknown"),
                progress_cb=lambda s: update_job(job_id, stage=s),
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


init_db()


@app.route("/upload/protected", methods=["POST"])
def upload_protected():
    if "video" not in request.files:
        return jsonify({"error": "No video file provided"}), 400

    video_file = request.files["video"]
    if video_file.filename == "":
        return jsonify({"error": "No selected file"}), 400

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
    if "video" not in request.files:
        return jsonify({"error": "No video file provided"}), 400

    video_file = request.files["video"]
    if video_file.filename == "":
        return jsonify({"error": "No selected file"}), 400

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
    if "video" not in request.files:
        return jsonify({"error": "No video file provided"}), 400

    video_file = request.files["video"]
    if video_file.filename == "":
        return jsonify({"error": "No selected file"}), 400

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
    if "video" not in request.files:
        return jsonify({"error": "No video file provided"}), 400

    video_file = request.files["video"]
    if video_file.filename == "":
        return jsonify({"error": "No selected file"}), 400

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
    job = get_job(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    return jsonify(job), 200


@app.route("/jobs/<job_id>/cancel", methods=["POST"])
def cancel_job(job_id):
    job = request_job_cancel(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    return jsonify(job), 200


@app.route("/candidates/submit", methods=["POST"])
def submit_candidate():
    data = request.get_json(silent=True) or {}
    if "url" not in data:
        return jsonify({"error": "URL is required"}), 400

    url = data.get("url")
    platform = data.get("platform", "manual")
    keyword_hits = data.get("keyword_hits", [])
    event_context = data.get("event_context", "")
    source_timestamp = data.get("source_timestamp")
    notes = data.get("notes", "")

    suspicion_score = calculate_suspicion_score(keyword_hits, event_context, platform, url)

    if suspicion_score < 0.55:
        status = "discarded"
    elif suspicion_score < 0.75:
        status = "watch_list"
    else:
        status = "queued"

    candidate_id = str(uuid.uuid4())

    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO candidates (id, url, platform, keyword_hits, event_context,
                                   suspicion_score, source_timestamp, status, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                candidate_id,
                url,
                platform,
                json.dumps(keyword_hits) if keyword_hits else None,
                event_context,
                suspicion_score,
                source_timestamp,
                status,
                notes,
            ),
        )
        conn.commit()
        conn.close()

        log_event(
            "candidate_submitted",
            candidate_id=candidate_id,
            url=url,
            platform=platform,
            suspicion_score=suspicion_score,
            status=status,
        )

        return jsonify(
            {
                "candidate_id": candidate_id,
                "url": url,
                "platform": platform,
                "suspicion_score": round(suspicion_score, 3),
                "status": status,
                "verification_job_id": None,
                "triage_thresholds": {
                    "discard": 0.55,
                    "watch_list": 0.75,
                },
            }
        ), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/candidates", methods=["GET"])
def get_candidates():
    try:
        status_filter = request.args.get("status")
        min_score = request.args.get("min_score", type=float)
        max_score = request.args.get("max_score", type=float)
        limit = request.args.get("limit", 50, type=int)
        offset = request.args.get("offset", 0, type=int)

        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()

        query = "SELECT * FROM candidates WHERE 1=1"
        params = []

        if status_filter:
            query += " AND status = ?"
            params.append(status_filter)

        if min_score is not None:
            query += " AND suspicion_score >= ?"
            params.append(min_score)

        if max_score is not None:
            query += " AND suspicion_score <= ?"
            params.append(max_score)

        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        candidates = []
        for row in rows:
            candidates.append(
                {
                    "candidate_id": row[0],
                    "url": row[1],
                    "platform": row[2],
                    "keyword_hits": json.loads(row[3]) if row[3] else [],
                    "event_context": row[4],
                    "suspicion_score": row[5],
                    "source_timestamp": row[6],
                    "status": row[7],
                    "verification_job_id": row[8],
                    "notes": row[9],
                    "created_at": row[10],
                    "updated_at": row[11],
                }
            )

        return jsonify(
            {
                "candidates": candidates,
                "count": len(candidates),
                "limit": limit,
                "offset": offset,
            }
        ), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/metrics/summary", methods=["GET"])
def get_metrics_summary():
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM protected_content")
        protected_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM detections")
        detection_count = cursor.fetchone()[0]

        cursor.execute("SELECT COALESCE(AVG(confidence_score), 0) FROM detections")
        avg_confidence = float(cursor.fetchone()[0] or 0.0)

        cursor.execute("SELECT COUNT(*) FROM candidates")
        candidate_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM candidates WHERE status = 'queued'")
        queued_candidates = cursor.fetchone()[0]

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
                "candidate_count": candidate_count,
                "queued_candidates": queued_candidates,
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
    try:
        min_conf = request.args.get("min_conf", 0.0, type=float)
        limit = request.args.get("limit", 100, type=int)
        offset = request.args.get("offset", 0, type=int)

        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT d.id, p.title, p.league, d.stream_url, d.confidence_score, d.detected_at
            FROM detections d
            JOIN protected_content p ON d.protected_content_id = p.id
            WHERE d.confidence_score >= ?
            ORDER BY d.detected_at DESC
            LIMIT ? OFFSET ?
            """,
            (min_conf, limit, offset),
        )
        rows = cursor.fetchall()

        cursor.execute("SELECT COUNT(*) FROM detections WHERE confidence_score >= ?", (min_conf,))
        total = cursor.fetchone()[0]

        conn.close()

        detections = [
            {
                "id": r[0],
                "title": r[1],
                "league": r[2],
                "stream_url": r[3],
                "confidence_score": r[4],
                "detected_at": r[5],
            }
            for r in rows
        ]

        return jsonify({"detections": detections, "total": total, "limit": limit, "offset": offset}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/detections/<int:detection_id>/dmca", methods=["GET"])
def generate_dmca(detection_id):
    try:
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

        content_info = {"title": row[4], "league": row[5]}
        infringer_info = {"url": row[1], "confidence": row[2], "timestamp": row[3]}
        pdf_path = generator.create_notice(row[0], content_info, infringer_info)

        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        cursor.execute("UPDATE detections SET dmca_generated = TRUE WHERE id = ?", (detection_id,))
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


@sock.route("/live")
def handle_live_detections(ws):
    """Push recent detections every 5 seconds for dashboard clients."""
    while True:
        try:
            conn = sqlite3.connect(str(DB_PATH))
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT d.id, p.title, p.league, d.stream_url, d.confidence_score, d.detected_at
                FROM detections d
                JOIN protected_content p ON d.protected_content_id = p.id
                ORDER BY d.detected_at DESC
                LIMIT 10
                """
            )
            rows = cursor.fetchall()
            conn.close()

            detections = [
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

            ws.send(json.dumps({"type": "detections_update", "data": detections}))
            time.sleep(5)
        except Exception:
            break


if __name__ == "__main__":
    app.run(debug=True, port=8000)
