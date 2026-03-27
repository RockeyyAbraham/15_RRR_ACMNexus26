# Sentinel Discovery System

## Overview

The Discovery System is the front-end of Sentinel's piracy detection pipeline. It identifies, scores, and triages suspicious URLs before they enter deep verification.

## Architecture

```
Discovery → Triage → Verification → Detection → Enforcement
```

### Components

1. **Candidate Submission** - Accept URLs from manual input or automated monitors
2. **Suspicion Scoring** - Calculate risk score using weighted heuristics
3. **Automatic Triage** - Route candidates based on score thresholds
4. **Database Persistence** - Track all candidates for audit trail

## Suspicion Score Algorithm

### Formula

```
score = (0.35 × keyword_match)
      + (0.20 × event_time_proximity)
      + (0.20 × platform_risk)
      + (0.15 × prior_repeat_offender)
      + (0.10 × url_pattern_analysis)
```

### Components

| Component | Weight | Description |
|-----------|--------|-------------|
| Keyword Match | 35% | Ratio of protected keywords found in metadata |
| Event Proximity | 20% | Temporal relevance to protected events |
| Platform Risk | 20% | Platform-specific piracy likelihood |
| Prior Offender | 15% | Historical repeat infringement rate |
| URL Pattern | 10% | Suspicious URL patterns (live, stream, free, hd) |

### Platform Risk Scores

| Platform | Risk Score | Rationale |
|----------|------------|-----------|
| Telegram | 0.9 | High piracy prevalence, encrypted channels |
| Twitch | 0.7 | Live streaming platform, re-streaming common |
| YouTube | 0.6 | Mixed legitimate/pirated content |
| Twitter | 0.6 | Link sharing, clip distribution |
| Reddit | 0.5 | Discussion platform, some link sharing |
| Facebook | 0.5 | Mixed content, some piracy groups |
| Manual | 0.8 | User-submitted, pre-vetted |

## Triage Thresholds

### Decision Tiers

| Score Range | Status | Action |
|-------------|--------|--------|
| < 0.55 | `discarded` | Ignore, too low confidence |
| 0.55 - 0.74 | `watch_list` | Monitor, no immediate action |
| ≥ 0.75 | `queued` | Ready for deep verification |

### Rationale

- **Discard threshold (0.55)**: Filters out noise and false positives
- **Watch list (0.55-0.74)**: Captures borderline cases for manual review
- **Verification threshold (0.75)**: High enough confidence to justify compute cost

## API Endpoints

### POST /candidates/submit

Submit a candidate URL for triage.

**Request:**
```json
{
  "url": "https://twitch.tv/suspicious_stream",
  "platform": "twitch",
  "keyword_hits": ["f1", "live", "australian gp"],
  "event_context": "F1 2026 Australian GP",
  "source_timestamp": "2026-03-28T02:00:00Z",
  "notes": "Flagged by automated monitor"
}
```

**Response (201):**
```json
{
  "candidate_id": "uuid",
  "url": "https://twitch.tv/suspicious_stream",
  "platform": "twitch",
  "suspicion_score": 0.823,
  "status": "queued",
  "verification_job_id": null,
  "triage_thresholds": {
    "discard": 0.55,
    "watch_list": 0.75
  }
}
```

### GET /candidates

Retrieve candidates with optional filtering.

**Query Parameters:**
- `status` - Filter by status (queued, watch_list, discarded, verified)
- `min_score` - Minimum suspicion score (0.0-1.0)
- `max_score` - Maximum suspicion score (0.0-1.0)
- `limit` - Max results (default: 50)
- `offset` - Pagination offset (default: 0)

**Response (200):**
```json
{
  "candidates": [
    {
      "candidate_id": "uuid",
      "url": "https://...",
      "platform": "twitch",
      "keyword_hits": ["f1", "live"],
      "event_context": "F1 2026 Australian GP",
      "suspicion_score": 0.823,
      "source_timestamp": "2026-03-28T02:00:00Z",
      "status": "queued",
      "verification_job_id": null,
      "notes": "...",
      "created_at": "2026-03-28T02:15:00Z",
      "updated_at": "2026-03-28T02:15:00Z"
    }
  ],
  "count": 1,
  "limit": 50,
  "offset": 0
}
```

## Database Schema

```sql
CREATE TABLE candidates (
    id TEXT PRIMARY KEY,
    url TEXT NOT NULL,
    platform TEXT NOT NULL,
    keyword_hits TEXT,  -- JSON array
    event_context TEXT,
    suspicion_score FLOAT NOT NULL,
    source_timestamp TIMESTAMP,
    status TEXT DEFAULT 'queued',
    verification_job_id TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_candidates_status ON candidates(status);
CREATE INDEX idx_candidates_score ON candidates(suspicion_score);
CREATE INDEX idx_candidates_created ON candidates(created_at);
```

## Usage Examples

### Manual Submission

```python
import requests

response = requests.post(
    "http://localhost:5000/candidates/submit",
    json={
        "url": "https://twitch.tv/pirate_stream",
        "platform": "twitch",
        "keyword_hits": ["f1", "live", "free"],
        "event_context": "F1 2026 Australian GP",
        "notes": "Reported by user"
    }
)

result = response.json()
print(f"Suspicion score: {result['suspicion_score']}")
print(f"Status: {result['status']}")
```

### Retrieve High-Priority Candidates

```python
response = requests.get(
    "http://localhost:5000/candidates",
    params={"min_score": 0.75, "status": "queued"}
)

candidates = response.json()["candidates"]
for candidate in candidates:
    print(f"{candidate['url']} - Score: {candidate['suspicion_score']}")
```

## Demo Script

Run the discovery demo to see the full pipeline:

```bash
cd backend
python demo_discovery.py
```

The demo will:
1. Submit 5 candidate URLs with varying characteristics
2. Show automatic triage decisions
3. Display candidates by status
4. Highlight high-priority candidates
5. Show system metrics

## Testing

Run unit tests for the discovery system:

```bash
cd backend
python tests/test_candidate_flow.py
```

Tests cover:
- Suspicion score calculation
- Triage logic
- Score component weights
- Edge cases

## Integration with Verification

### Workflow

1. **Discovery** submits candidate → `status: queued`
2. **Manual trigger** or **automated scheduler** creates verification job
3. **Verification job** downloads media and runs fingerprinting
4. **Match result** updates candidate → `status: verified`
5. **Detection** links back to original candidate for audit trail

### Future Enhancement: Auto-Verification

```python
# In submit_candidate endpoint
if suspicion_score >= 0.75 and get_active_job_count() < MAX_QUEUE_SIZE:
    # Auto-trigger verification for high-confidence candidates
    job_id = create_job("suspect_upload", {
        "stream_url": url,
        "candidate_id": candidate_id
    })
    executor.submit(submit_background_job, job_id, "suspect_upload", ...)
    verification_job_id = job_id
```

## Monitoring and Metrics

### Key Metrics

- **Candidate submission rate** - URLs/hour
- **Score distribution** - Histogram of suspicion scores
- **Triage breakdown** - Percentage in each tier
- **Verification conversion** - Queued → Verified rate
- **Detection rate** - Verified → Detected rate

### Telemetry Events

```json
{
  "timestamp": "2026-03-28T02:15:00Z",
  "event_type": "candidate_submitted",
  "candidate_id": "uuid",
  "url": "https://...",
  "platform": "twitch",
  "suspicion_score": 0.823,
  "status": "queued"
}
```

## Best Practices

### For Hackathon Demo

1. **Pre-load protected content** - Upload reference videos first
2. **Submit diverse candidates** - Show different score ranges
3. **Highlight triage automation** - Emphasize no manual intervention needed
4. **Show metrics** - Demonstrate system intelligence

### For Production

1. **Tune thresholds** - Adjust based on false positive/negative rates
2. **Implement monitors** - Automate candidate discovery from platforms
3. **Add feedback loop** - Update scores based on verification outcomes
4. **Scale workers** - Increase async workers for high volume

## Troubleshooting

### Low Suspicion Scores

- **Issue**: All candidates scoring < 0.55
- **Fix**: Check keyword_hits are being passed correctly
- **Fix**: Verify event_context is populated

### High False Positive Rate

- **Issue**: Too many queued candidates are not piracy
- **Fix**: Increase verification threshold (e.g., 0.80)
- **Fix**: Improve keyword matching logic

### Candidates Not Appearing

- **Issue**: Submitted candidates not in database
- **Fix**: Check database initialization: `init_db()` called
- **Fix**: Verify DB_PATH is correct
- **Fix**: Check for SQL errors in logs

## Future Enhancements

1. **Machine Learning Scoring** - Replace heuristic with trained model
2. **Platform API Integration** - Direct monitoring of Twitch, YouTube, etc.
3. **Temporal Analysis** - Score boost for live events
4. **Network Analysis** - Track repeat offender channels
5. **Automated Verification** - Auto-trigger jobs for high scores
6. **Feedback Loop** - Update scores based on detection outcomes

## References

- Main API: `backend/api/main.py`
- Demo Script: `backend/demo_discovery.py`
- Tests: `backend/tests/test_candidate_flow.py`
- Blueprint: Root `SENTINEL_NORTHSTAR.md`
