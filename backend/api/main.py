"""
Sentinel Backend Central Hub - Flask REST & WebSocket API.
Provides asynchronous fingerprinting, candidate triage, detection, and DMCA generation.
"""

import sys
from pathlib import Path

# Fix import paths - add backend directory to Python path
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

import os
import json
import uuid
import time
import logging
import sqlite3
import threading
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse

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

from utils.redis_utils import redis_manager

# Configure comprehensive logging
LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
ERROR_LOG = LOG_DIR / "error.log"
ACCESS_LOG = LOG_DIR / "access.log"

# File handler for errors
file_handler = logging.FileHandler(ERROR_LOG)
file_handler.setLevel(logging.ERROR)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
))

# Console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter('%(message)s'))

# Root logger configuration
logging.basicConfig(
    level=logging.INFO,
    handlers=[file_handler, console_handler]
)

logger = logging.getLogger(__name__)

try:
    import requests
except ImportError:
    requests = None

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
FLASK_DEBUG_MODE = os.getenv("FLASK_DEBUG", "0").strip().lower() in {"1", "true", "yes", "on"}

hash_engine = None
matcher = None
audio_engine = None
ai_engine = None
generator = None
dual_mode_engine = None

engine_init_error = None
generator_init_error = None

NOTICES_DIR.mkdir(parents=True, exist_ok=True)
TEMP_DIR.mkdir(parents=True, exist_ok=True)

executor = ThreadPoolExecutor(max_workers=MAX_ASYNC_WORKERS)
jobs = {}
jobs_lock = threading.Lock()
monitor_sessions = {}
monitor_lock = threading.Lock()

logging.basicConfig(level=logging.INFO, format="%(message)s")
telemetry_logger = logging.getLogger("sentinel.telemetry")


def get_ai_engine():
    """Lazily initialize AI engine so API boots even without AI key."""
    global ai_engine
    if ai_engine is None:
        try:
            from engines.ai_engine import SentinelAI
            ai_engine = SentinelAI()
        except Exception:
            ai_engine = False
    return ai_engine if ai_engine else None


def get_media_engines():
    """Lazily initialize media engines to avoid hard import dependency at boot."""
    global hash_engine, matcher, audio_engine, engine_init_error

    if hash_engine and matcher and audio_engine:
        return hash_engine, matcher, audio_engine

    if engine_init_error is not None:
        raise RuntimeError(f"Media engines unavailable: {engine_init_error}")

    try:
        from engines.hash_engine import VideoHashEngine
        from engines.audio_engine import AudioHashEngine
        from engines.matcher import VideoMatcher

        hash_engine = VideoHashEngine(frame_sample_rate=10, hash_size=8)
        matcher = VideoMatcher(threshold=85.0, hash_size=8)
        audio_engine = AudioHashEngine()
        return hash_engine, matcher, audio_engine
    except Exception as e:
        engine_init_error = str(e)
        raise RuntimeError(f"Media engines unavailable: {e}") from e


def get_dmca_generator():
    """Lazily initialize DMCA generator for environments without reportlab."""
    global generator, generator_init_error

    if generator is not None:
        return generator

    if generator_init_error is not None:
        raise RuntimeError(f"DMCA generator unavailable: {generator_init_error}")

    try:
        from generators.dmca_generator import DMCAGenerator

        generator = DMCAGenerator(output_dir=str(NOTICES_DIR))
        return generator
    except Exception as e:
        generator_init_error = str(e)
        raise RuntimeError(f"DMCA generator unavailable: {e}") from e


def get_dual_mode_engine():
    """Lazily initialize the dual-mode engine for piracy benchmark analytics."""
    global dual_mode_engine
    if dual_mode_engine is None:
        from engines.dual_engine import DualModeEngine

        dual_mode_engine = DualModeEngine()
    return dual_mode_engine


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


def update_candidate_record(candidate_id: str, status: str = None, verification_job_id: str = None, notes: str = None):
    """Update candidate lifecycle fields for auditability."""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    fields = []
    params = []
    if status is not None:
        fields.append("status = ?")
        params.append(status)
    if verification_job_id is not None:
        fields.append("verification_job_id = ?")
        params.append(verification_job_id)
    if notes is not None:
        fields.append("notes = COALESCE(notes, '') || ?")
        params.append(f"\n{notes}")

    if fields:
        fields.append("updated_at = CURRENT_TIMESTAMP")
        params.append(candidate_id)
        cursor.execute(f"UPDATE candidates SET {', '.join(fields)} WHERE id = ?", params)
        conn.commit()
    conn.close()


def resolve_candidate_media(url: str) -> Path | None:
    """Resolve candidate URL to a local media file when possible.

    Supports:
    - local absolute/relative file path
    - direct media URL (.mp4/.mov/.mkv/.webm/.m4v)
    - streaming platforms via yt-dlp (YouTube, Twitch, Facebook, Twitter, etc.)
    """
    media_ext = (".mp4", ".mov", ".mkv", ".webm", ".m4v")

    # Local path support for hackathon demos
    local_candidate = Path(url)
    if local_candidate.exists() and local_candidate.is_file():
        return local_candidate

    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return None

    # Try yt-dlp for streaming platforms (YouTube, Twitch, etc.)
    try:
        from engines.video_downloader import VideoDownloader
        downloader = VideoDownloader(output_dir=str(TEMP_DIR))
        
        platform = downloader.identify_platform(url)
        if platform and platform not in ("unknown", "direct"):
            logger.info(f"Attempting yt-dlp download from {platform}: {url}")
            downloaded_path, metadata = downloader.download(url)
            if downloaded_path and downloaded_path.exists():
                logger.info(f"Successfully downloaded: {downloaded_path}")
                return downloaded_path
            else:
                logger.warning(f"yt-dlp download failed: {metadata.get('error', 'Unknown error')}")
    except ImportError:
        logger.warning("VideoDownloader not available, falling back to direct download")
    except Exception as e:
        logger.warning(f"yt-dlp download error: {e}")

    # Fallback: Direct download for direct video URLs
    if not parsed.path.lower().endswith(media_ext):
        return None

    if requests is None:
        return None

    filename = f"candidate_{uuid.uuid4()}{Path(parsed.path).suffix.lower() or '.mp4'}"
    dest = TEMP_DIR / filename

    try:
        with requests.get(url, stream=True, timeout=30) as r:
            r.raise_for_status()
            with open(dest, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
        return dest
    except Exception:
        try:
            if dest.exists():
                dest.unlink()
        except Exception:
            pass
        return None


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
    local_hash_engine, _, local_audio_engine = get_media_engines()
    video_path_str = str(video_path)

    if progress_cb:
        progress_cb("hashing_video")
    if cancel_cb and cancel_cb():
        raise RuntimeError("Job cancelled")

    video_hashes, video_metadata = local_hash_engine.hash_video(video_path_str)

    if progress_cb:
        progress_cb("hashing_audio")
    if cancel_cb and cancel_cb():
        raise RuntimeError("Job cancelled")

    audio_hash = local_audio_engine.extract_audio_hash(video_path_str)

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
        "duration_seconds": video_metadata.get("duration_seconds", 0),
        "processing_time_seconds": video_metadata["processing_time_seconds"],
        "latency_ms": round(elapsed * 1000, 2),
    }


def process_suspect_video(video_path: Path, stream_url: str, progress_cb=None, cancel_cb=None):
    start = time.perf_counter()
    local_hash_engine, local_matcher, local_audio_engine = get_media_engines()
    video_path_str = str(video_path)

    if progress_cb:
        progress_cb("hashing_video")
    if cancel_cb and cancel_cb():
        raise RuntimeError("Job cancelled")

    suspect_hashes, suspect_metadata = local_hash_engine.hash_video(video_path_str)

    if progress_cb:
        progress_cb("hashing_audio")
    if cancel_cb and cancel_cb():
        raise RuntimeError("Job cancelled")

    suspect_audio_hash = local_audio_engine.extract_audio_hash(video_path_str)

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

        video_result = local_matcher.match_video_sequences(suspect_hashes, protected_hashes)
        video_confidence = float(video_result.get("confidence_score", 0.0))

        audio_confidence = 0.0
        if suspect_audio_hash and protected_audio_hash:
            _, audio_confidence = local_matcher.compare_hashes(suspect_audio_hash, protected_audio_hash)

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


def process_piracy_benchmark(video_path: Path, title: str, league: str, progress_cb=None, cancel_cb=None):
    """Run protected ingest + 17 piracy-variant analytics as a main API workflow."""
    if progress_cb:
        progress_cb("processing_protected")

    protected_result = process_protected_video(
        video_path=video_path,
        title=title,
        league=league,
        progress_cb=progress_cb,
        cancel_cb=cancel_cb,
    )

    if cancel_cb and cancel_cb():
        raise RuntimeError("Job cancelled")

    from utils.piracy_benchmark import run_piracy_benchmark

    benchmark_dir = TEMP_DIR / "benchmarks" / f"bench_{uuid.uuid4().hex[:10]}"
    benchmark_dir.mkdir(parents=True, exist_ok=True)

    benchmark_result = run_piracy_benchmark(
        original_video=video_path,
        output_dir=benchmark_dir,
        dual_engine=get_dual_mode_engine(),
        progress_cb=progress_cb,
        cancel_cb=cancel_cb,
    )

    duration_seconds = float(protected_result.get("duration_seconds", 0) or 0)
    split_chunk_seconds = 5
    estimated_chunks = int((duration_seconds + split_chunk_seconds - 1) // split_chunk_seconds) if duration_seconds > 0 else 0

    return {
        "message": "Piracy benchmark completed",
        "protected": protected_result,
        "split_plan": {
            "chunk_duration_seconds": split_chunk_seconds,
            "estimated_chunks": estimated_chunks,
            "duration_seconds": round(duration_seconds, 2),
        },
        **benchmark_result,
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
        elif job_type == "candidate_verify":
            candidate_id = payload.get("candidate_id")
            candidate_url = payload.get("candidate_url", "")
            update_job(job_id, stage="resolving_media")
            media_path = resolve_candidate_media(candidate_url)
            if media_path is None:
                result = {
                    "message": "Candidate queued but media download/clip resolver not available for this URL.",
                    "candidate_id": candidate_id,
                    "candidate_url": candidate_url,
                    "detections": [],
                }
            else:
                result = process_suspect_video(
                    video_path=media_path,
                    stream_url=candidate_url,
                    progress_cb=lambda s: update_job(job_id, stage=s),
                    cancel_cb=lambda: should_abort(job_id),
                )
                if media_path != video_path:
                    try:
                        if media_path.exists():
                            media_path.unlink()
                    except Exception:
                        pass
        elif job_type == "piracy_benchmark":
            result = process_piracy_benchmark(
                video_path=video_path,
                title=payload.get("title", "Protected Benchmark Content"),
                league=payload.get("league", "Benchmark League"),
                progress_cb=lambda s: update_job(job_id, stage=s),
                cancel_cb=lambda: should_abort(job_id),
            )
        else:
            raise ValueError(f"Unsupported job type: {job_type}")

        if should_abort(job_id):
            update_job(job_id, status="cancelled", stage="cancelled")
            if payload.get("candidate_id"):
                update_candidate_record(payload["candidate_id"], status="cancelled")
        else:
            update_job(job_id, status="completed", stage="completed", result=result, completed_at=datetime.now().isoformat())
            if payload.get("candidate_id"):
                if result.get("detections"):
                    update_candidate_record(payload["candidate_id"], status="verified_piracy")
                else:
                    update_candidate_record(payload["candidate_id"], status="verified_clean")

    except Exception as e:
        if "cancelled" in str(e).lower() or should_abort(job_id):
            update_job(job_id, status="cancelled", stage="cancelled")
            if payload.get("candidate_id"):
                update_candidate_record(payload["candidate_id"], status="cancelled")
        else:
            update_job(job_id, status="failed", stage="failed", error=str(e))
            if payload.get("candidate_id"):
                update_candidate_record(payload["candidate_id"], status="verification_failed", notes=f"verification error: {e}")

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
        logger.error(f"Error uploading protected content: {e}", exc_info=True)
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
        "candidate_id": request.form.get("candidate_id"),
    }
    job_id = create_job("suspect_upload", payload)
    executor.submit(submit_background_job, job_id, "suspect_upload", video_path, payload)

    candidate_id = request.form.get("candidate_id")
    if candidate_id:
        update_candidate_record(candidate_id, status="verifying", verification_job_id=job_id)

    return jsonify({"job_id": job_id, "status": "queued", "job_type": "suspect_upload"}), 202


@app.route("/analysis/piracy-benchmark/async", methods=["POST"])
def run_piracy_benchmark_async():
    """Main-project API: process protected video and evaluate 17 generated piracy variants."""
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
        "title": request.form.get("title", Path(video_file.filename).stem),
        "league": request.form.get("league", "BENCHMARK"),
        "filename": video_file.filename,
    }

    job_id = create_job("piracy_benchmark", payload)
    executor.submit(submit_background_job, job_id, "piracy_benchmark", video_path, payload)

    return jsonify({"job_id": job_id, "status": "queued", "job_type": "piracy_benchmark"}), 202


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

        verification_job_id = None
        if status == "queued":
            if get_active_job_count() < MAX_QUEUE_SIZE:
                payload = {
                    "candidate_id": candidate_id,
                    "candidate_url": url,
                    "stream_url": url,
                }
                verification_job_id = create_job("candidate_verify", payload)
                update_candidate_record(candidate_id, status="verifying", verification_job_id=verification_job_id)
                placeholder = TEMP_DIR / f"candidate_placeholder_{verification_job_id}.tmp"
                placeholder.write_text("candidate-verification")
                executor.submit(submit_background_job, verification_job_id, "candidate_verify", placeholder, payload)
            else:
                update_candidate_record(candidate_id, notes="queue full: verification deferred")

        return jsonify(
            {
                "candidate_id": candidate_id,
                "url": url,
                "platform": platform,
                "suspicion_score": round(suspicion_score, 3),
                "status": "verifying" if verification_job_id else status,
                "verification_job_id": verification_job_id,
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


@app.route("/monitor/start", methods=["POST"])
def monitor_start():
    """Start a lightweight in-memory monitor session for discovery orchestration."""
    data = request.get_json(silent=True) or {}
    session_id = str(uuid.uuid4())
    session = {
        "session_id": session_id,
        "event_context": data.get("event_context", ""),
        "keywords": data.get("keywords", []),
        "platforms": data.get("platforms", ["manual"]),
        "poll_interval_seconds": int(data.get("poll_interval_seconds", 30)),
        "status": "running",
        "started_at": datetime.now().isoformat(),
        "stopped_at": None,
    }
    with monitor_lock:
        monitor_sessions[session_id] = session
    return jsonify(session), 201


@app.route("/monitor/stop", methods=["POST"])
def monitor_stop():
    """Stop an existing monitor session."""
    data = request.get_json(silent=True) or {}
    session_id = data.get("session_id")
    if not session_id:
        return jsonify({"error": "session_id is required"}), 400

    with monitor_lock:
        session = monitor_sessions.get(session_id)
        if not session:
            return jsonify({"error": "Monitor session not found"}), 404
        session["status"] = "stopped"
        session["stopped_at"] = datetime.now().isoformat()

    return jsonify(session), 200


@app.route("/monitor/status", methods=["GET"])
def monitor_status():
    """List monitor sessions and summary counts."""
    with monitor_lock:
        sessions = list(monitor_sessions.values())

    running = sum(1 for s in sessions if s.get("status") == "running")
    stopped = sum(1 for s in sessions if s.get("status") == "stopped")

    return jsonify({
        "sessions": sessions,
        "summary": {
            "total": len(sessions),
            "running": running,
            "stopped": stopped,
        },
    }), 200


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
        local_generator = get_dmca_generator()
        pdf_path = local_generator.create_notice(row[0], content_info, infringer_info)

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
    engines_status = []
    try:
        get_media_engines()
        engines_status.extend(["hashing", "matching", "audio"])
    except Exception:
        engines_status.append("media_unavailable")

    try:
        get_dmca_generator()
        engines_status.append("generator")
    except Exception:
        engines_status.append("generator_unavailable")

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
    logger.info("="*80)
    logger.info("SENTINEL BACKEND STARTING")
    logger.info("="*80)
    logger.info(f"Error logs: {ERROR_LOG}")
    logger.info(f"Access logs: {ACCESS_LOG}")
    logger.info(f"Database: {DB_PATH}")
    logger.info(f"Temp directory: {TEMP_DIR}")
    logger.info(f"Notices directory: {NOTICES_DIR}")
    logger.info("="*80)
    app.run(debug=FLASK_DEBUG_MODE, use_reloader=False, port=8000)
