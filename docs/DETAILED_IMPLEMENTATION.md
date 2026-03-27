# Sentinel Detailed Implementation Blueprint

## 1. Objective
Build a near real-time digital asset protection pipeline where:
1. A rights-holder uploads protected media.
2. Discovery workers find suspicious public links.
3. Suspicious items are triaged and verified asynchronously.
4. Confirmed piracy triggers evidence capture and DMCA generation.

This document is implementation-first and aligned to the current backend architecture.

---

## 2. End-to-End Flow

### 2.1 Protected Content Ingest
1. User uploads protected video via async ingest endpoint.
2. Backend creates a job with status queued.
3. Worker stages run:
- hashing_video
- hashing_audio
- persisting
4. Fingerprints are stored in SQLite and cached.

### 2.2 Discovery and Candidate Intake
1. Discovery service monitors platform APIs or receives manually submitted candidate URLs.
2. Each candidate gets a suspicion score based on metadata and context.
3. If score passes triage threshold, candidate is enqueued for deep verification.

### 2.3 Deep Verification
1. Worker downloads or clips suspect media.
2. Generates suspect video and audio fingerprints.
3. Matches suspect hashes against protected references.
4. Computes final confidence and decision tier:
- auto_action
- manual_review
- no_match

### 2.4 Enforcement
1. For confirmed piracy, save evidence metadata.
2. Expose detection in live feed and dashboard.
3. Generate DMCA notice for legal team.

---

## 3. Backend Architecture

### 3.1 Core Components
1. API layer
- Flask routes for ingest, job status, detections, DMCA, metrics.

2. Async execution
- ThreadPoolExecutor workers.
- In-memory job registry for stage and status tracking.

3. Fingerprinting and matching
- Video hashing engine.
- Audio hashing engine.
- Multi-modal matching and decision policy.

4. Persistence
- SQLite for protected content and detections.
- Optional Redis cache for faster reads.

5. Telemetry
- Structured event logs for stage latency and detection outcomes.

### 3.2 Current Async Job States
1. queued
2. running
3. completed
4. failed
5. cancelled

### 3.3 Current Async Job Stages
1. queued
2. starting
3. hashing_video
4. hashing_audio
5. matching
6. persisting
7. completed
8. failed
9. cancelled

---

## 4. Data Contracts

### 4.1 Protected Upload Job Result
```json
{
  "message": "Protected content uploaded and hashed",
  "content_id": 17,
  "video_hash_count": 921,
  "audio_hash_extracted": true,
  "processing_time_seconds": 13.42,
  "latency_ms": 13754.12
}
```

### 4.2 Suspect Verification Job Result
```json
{
  "message": "Suspect video processed",
  "detections": [
    {
      "detection_id": 88,
      "content_id": 17,
      "title": "F1 Highlights",
      "league": "Formula 1",
      "confidence_score": 92.11,
      "audio_match_score": 89.27,
      "video_match_score": 93.45,
      "multi_modal": true,
      "decision_tier": "auto_action",
      "decision_reason": "score_above_auto_threshold",
      "stream_url": "https://example.com/stream"
    }
  ],
  "thresholds": {
    "auto_action": 85.0,
    "manual_review": 75.0
  },
  "processing_time_seconds": 8.76,
  "latency_ms": 9221.33
}
```

### 4.3 Async Job Object
```json
{
  "job_id": "uuid",
  "job_type": "suspect_upload",
  "status": "running",
  "stage": "matching",
  "cancel_requested": false,
  "created_at": "ISO",
  "updated_at": "ISO",
  "payload": {},
  "result": null,
  "error": null
}
```

---

## 5. API Blueprint

### 5.1 Implemented Routes
1. POST /upload/protected
2. POST /upload/suspect
3. POST /upload/protected/async
4. POST /upload/suspect/async
5. GET /jobs/{job_id}
6. POST /jobs/{job_id}/cancel
7. GET /detections
8. GET /detections/{id}/dmca
9. GET /metrics/summary
10. GET /health
11. WS /live

### 5.2 Recommended New Routes for Discovery
1. POST /candidates/submit
- Accept URL, platform, source metadata, suspicion score.
- If above threshold, enqueue deep verification job.

2. GET /candidates
- Paginated candidate audit trail.

3. POST /monitor/start
- Start monitor session for event keywords and platforms.

4. POST /monitor/stop
- Stop monitor session.

5. GET /monitor/status
- Return active monitors, polling intervals, last seen events.

---

## 6. Discovery Layer Design

### 6.1 Candidate Schema
```json
{
  "candidate_id": "uuid",
  "url": "https://...",
  "platform": "youtube|twitch|reddit|telegram|manual",
  "keyword_hits": ["f1", "australian gp"],
  "event_context": "F1 2026 AUS GP",
  "suspicion_score": 0.82,
  "source_timestamp": "ISO",
  "status": "queued|discarded|verified",
  "notes": "optional"
}
```

### 6.2 Suspicion Score Heuristics
Compute score from weighted features:
1. Event keyword match ratio.
2. Presence of protected team/league names.
3. Stream recency.
4. URL/channel reputation.
5. Prior detection history.

Example:
```text
score = (0.35 * keyword_match)
      + (0.20 * event_time_proximity)
      + (0.20 * channel_risk)
      + (0.15 * prior_repeat_offender)
      + (0.10 * metadata_anomaly)
```

### 6.3 Triage Thresholds
1. score < 0.55: discard
2. 0.55 <= score < 0.75: watch list
3. score >= 0.75: deep verification queue

---

## 7. Async Worker Pipeline

### 7.1 Worker Types
1. Ingest worker
- Protected media hashing and storage.

2. Candidate verifier worker
- Download or clip suspect media.
- Fingerprint and match.

3. Legal worker
- Generate DMCA package when decision tier is auto_action.

### 7.2 Queue Controls
1. MAX_ASYNC_WORKERS
2. MAX_QUEUE_SIZE
3. Active job count checks
4. Graceful 429 when queue is full

### 7.3 Cancellation Rules
1. Queued jobs can be cancelled immediately.
2. Running jobs set cancel_requested.
3. Worker checks cancel flag between stages.
4. Final state becomes cancelled.

---

## 8. Matching and Policy

### 8.1 Multi-Modal Confidence
1. Video confidence from hash matching.
2. Audio confidence when available.
3. Combined confidence default:
- 70 percent video
- 30 percent audio

### 8.2 Decision Policy
1. score >= AUTO_ACTION_THRESHOLD: auto_action
2. score >= MANUAL_REVIEW_THRESHOLD and < AUTO_ACTION_THRESHOLD: manual_review
3. score < MANUAL_REVIEW_THRESHOLD: no_match

### 8.3 Suggested Hackathon Defaults
1. AUTO_ACTION_THRESHOLD: 85
2. MANUAL_REVIEW_THRESHOLD: 75

---

## 9. Evidence and Legal

### 9.1 Evidence Package Minimum
1. Protected content id and metadata.
2. Suspect URL and timestamp.
3. Confidence breakdown:
- video_match_score
- audio_match_score
- combined confidence
4. Decision tier and reason.

### 9.2 DMCA Generation Trigger
1. Auto-generate for auto_action.
2. Manual trigger for manual_review.

### 9.3 Legal Safety
1. Keep human-in-loop for manual_review.
2. Log immutable decision artifacts.

---

## 10. React Integration Contract

### 10.1 Ingest Page
1. POST /upload/protected/async
2. Poll GET /jobs/{job_id}
3. Render stage timeline and completion summary

### 10.2 Monitoring Page
1. Submit candidate URLs via POST /candidates/submit
2. Show queued and running verification jobs

### 10.3 Detections Page
1. Subscribe to WS /live
2. Show confidence, tier, timestamp, and action buttons

### 10.4 Legal Page
1. List detections eligible for action
2. Download DMCA via GET /detections/{id}/dmca

---

## 11. Metrics and SLOs

### 11.1 Must-Have Metrics
1. detection_count
2. average_confidence
3. auto_action_count
4. manual_review_count
5. active_jobs
6. queue_full_rejections

### 11.2 Latency Metrics
1. ingest enqueue to start
2. start to detection
3. detection to DMCA generation

### 11.3 Target SLOs for Demo
1. Job enqueue response under 500 ms
2. Suspect verification under 30 seconds for clip-based checks
3. Live feed update under 5 seconds

---

## 12. Implementation Plan

### Phase A: Already Implemented
1. Async upload jobs and status endpoint
2. Stage tracking and cancellation
3. Queue size protection
4. Multi-modal decision policy
5. Metrics summary endpoint

### Phase B: 1-2 Hour MVP Completion
1. Add candidate submission endpoint.
2. Map candidate submit to suspect verification job.
3. Persist candidate records in SQLite.
4. Expose candidate list endpoint.
5. Add one demo script to simulate discovery events.

### Phase C: Optional Extensions
1. Official source adapters (Twitch, Reddit, YouTube quota-aware).
2. Monitor session scheduler.
3. Better evidence capture (thumbnails, frame offsets).

---

## 13. Test Strategy

### 13.1 Fast Deterministic Tests
Use unit tests for:
1. tier classification
2. async state transitions
3. cancel flow
4. queue pressure behavior

### 13.2 Heavy Media Tests
Use integration tests for:
1. video hashing quality
2. degraded content matching
3. temporal localization
4. performance and robustness metrics

### 13.3 Demo Runbook
1. Run deterministic tests.
2. Start backend.
3. Upload protected content async.
4. Submit suspect candidate.
5. Wait for detection result.
6. Generate DMCA.
7. Show metrics and live feed.

---

## 14. Risks and Mitigations

1. Large media processing time
- Mitigation: clip-based verification and bounded worker pool.

2. False positives
- Mitigation: two-tier policy with manual review lane.

3. Queue overload
- Mitigation: MAX_QUEUE_SIZE and 429 backpressure.

4. Platform API constraints
- Mitigation: abstract source adapters and fallback manual candidate submission.

---

## 15. Deliverable Checklist

1. Async ingest and suspect verification working.
2. Candidate intake endpoint working.
3. Detection tiers visible in API and UI.
4. DMCA generation linked to confirmed detections.
5. Metrics endpoint proving throughput and quality.
6. Demo script showing full loop in under 3 minutes.
