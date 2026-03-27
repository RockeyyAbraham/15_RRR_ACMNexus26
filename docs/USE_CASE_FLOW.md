# 🎯 Sentinel - Complete Use Case Flow

## The Use Case You Asked About

```
1. User uploads a protected video
2. System scrapes sources online for similar instances
3. If one looks similar, download it
4. Compare videos using fingerprinting
5. Return result and generate DMCA
```

---

## ✅ Current Implementation Status

| Step | Description | Status | How It Works |
|------|-------------|--------|--------------|
| 1 | Upload protected video | ✅ **COMPLETE** | Frontend upload → Backend fingerprinting |
| 2 | Scrape online sources | ⚠️ **SIMULATED** | Manual candidate submission + demo discovery engine |
| 3 | Download similar video | ⚠️ **PARTIAL** | Direct URLs work; streaming platforms need yt-dlp |
| 4 | Compare using fingerprinting | ✅ **COMPLETE** | Dual-mode (video + audio) comparison |
| 5 | Return result + DMCA | ✅ **COMPLETE** | Detection results + PDF DMCA generation |

---

## 🔄 How the Pipeline Works

### Step 1: Ingest Protected Content
```
User uploads video → Generate fingerprints (pHash + dHash + audio)
                   → Store in database
                   → Cache in Redis for fast lookup
```

**API Endpoint:** `POST /upload/protected`

### Step 2: Discovery (Candidate Submission)
```
Option A: Manual submission via API
Option B: Run discovery_engine.py for automated demo
Option C: Frontend candidate submission
```

**API Endpoint:** `POST /candidates/submit`

**Suspicion Scoring:**
- Keywords in URL/title (35%)
- Event context match (20%)
- Platform risk level (25%)
- URL patterns (20%)

**Triage:**
- Score ≥ 0.75 → **Queued** for immediate verification
- Score 0.55-0.75 → **Watch List** for monitoring
- Score < 0.55 → **Discarded**

### Step 3: Download/Access Video
```
resolve_candidate_media() handles:
  ✅ Local file paths
  ✅ Direct video URLs (.mp4, .mov, .mkv, .webm)
  ⚠️ Streaming platforms (needs yt-dlp integration)
```

### Step 4: Fingerprint Comparison
```
Suspect video → Generate fingerprints
             → Compare against ALL protected content
             → Calculate confidence scores
             → Apply two-tier thresholds
```

**Comparison Features:**
- Multi-hash fusion (pHash + dHash)
- Sliding window temporal matching
- Statistical confidence scoring
- Audio spectrogram comparison

**Thresholds:**
- ≥ 85% → **Auto-Action** (immediate DMCA)
- 75-85% → **Manual Review**
- < 75% → **No Match**

### Step 5: Results & DMCA
```
Detection created → Store in database
                 → Generate AI summary (Groq)
                 → Create DMCA PDF (ReportLab)
                 → Return to user
```

**API Endpoint:** `GET /detections/{id}/dmca`

---

## 🚀 How to Run the Complete Use Case

### Option 1: Full Demo Script
```bash
cd backend
python run_discovery_demo.py
```

This will:
1. Scan protected videos in `assets/videos/`
2. Scan pirated videos in `assets/videos/pirated/`
3. Compare and detect matches
4. Show results

### Option 2: Step-by-Step via API

**1. Upload protected content:**
```bash
curl -X POST http://localhost:8000/upload/protected \
  -F "video=@original_video.mp4" \
  -F "title=F1 Australian GP" \
  -F "league=Formula 1"
```

**2. Submit candidate:**
```bash
curl -X POST http://localhost:8000/candidates/submit \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/suspect.mp4",
    "platform": "youtube",
    "keyword_hits": ["f1", "live", "stream"],
    "event_context": "F1 2026 Australian GP"
  }'
```

**3. Upload suspect for verification:**
```bash
curl -X POST http://localhost:8000/upload/suspect \
  -F "video=@suspect_video.mp4" \
  -F "stream_url=https://pirate-site.com/stream"
```

**4. Check detections:**
```bash
curl http://localhost:8000/detections
```

**5. Generate DMCA:**
```bash
curl http://localhost:8000/detections/1/dmca --output dmca_notice.pdf
```

### Option 3: Frontend UI

1. Go to `http://localhost:5173`
2. **Ingest Page:** Upload protected video
3. **Detection Page:** View live detections
4. **Legal Page:** Generate DMCA notices

---

## 📁 Key Files for This Use Case

| File | Purpose |
|------|---------|
| `backend/api/main.py` | REST API with all endpoints |
| `backend/engines/discovery_engine.py` | Full pipeline demo |
| `backend/engines/hash_engine.py` | Video fingerprinting |
| `backend/engines/audio_engine.py` | Audio fingerprinting |
| `backend/engines/matcher.py` | Fingerprint comparison |
| `backend/engines/dual_engine.py` | Combined video+audio detection |
| `backend/generators/dmca_generator.py` | PDF DMCA generation |
| `backend/run_discovery_demo.py` | One-click demo script |
| `backend/demo_discovery.py` | API-based demo |

---

## ⚠️ Limitations (Hackathon Scope)

### What's NOT Implemented:
1. **Real web scraping** - No actual crawling of YouTube, Twitch, etc.
2. **Platform API integration** - No YouTube Data API, Twitch API, etc.
3. **yt-dlp integration** - Can't download from streaming platforms
4. **Live stream capture** - No real-time stream monitoring

### Why These Limitations:
- **Legal concerns** - Scraping platforms may violate ToS
- **API costs** - Platform APIs require paid access
- **Time constraints** - 16-hour hackathon scope
- **Demo focus** - Local files demonstrate the same algorithms

### Production Roadmap:
1. Integrate yt-dlp for video downloads
2. Add platform APIs (YouTube, Twitch, Facebook)
3. Implement web scraping with proper rate limiting
4. Add live stream monitoring (HLS/DASH capture)
5. Deploy distributed workers for scale

---

## 🧪 Test the Use Case Now

**Prerequisites:**
1. Backend running: `python backend/api/main.py`
2. Original video in: `assets/videos/`
3. Pirated variants in: `assets/videos/pirated/`

**Run:**
```bash
cd backend
python run_discovery_demo.py
```

**Expected Output:**
```
🛡️  SENTINEL DISCOVERY PIPELINE
================================================================================

📁 STEP 1: Scanning Protected Content
----------------------------------------
📹 Processing protected: Race Highlights...mp4
  ✓ Generated 2591 hashes

🔍 STEP 2: Discovering Candidates
----------------------------------------
  🔴 Found: 240p.mp4
     Platform: youtube | Score: 0.82 | Status: queued

🔬 STEP 3: Verifying High-Suspicion Candidates
----------------------------------------
  📊 Generating fingerprints...
  ✓ Generated 2591 hashes
  🔍 Comparing against: Race Highlights...
    🚨 MATCH: 95.08% confidence

📊 PIPELINE SUMMARY
================================================================================
  Detections: 1
    - Auto DMCA: 1
```

---

## ✅ Summary

**Your use case DOES work**, with these caveats:

| Component | Works? | Notes |
|-----------|--------|-------|
| Upload protected video | ✅ Yes | Full implementation |
| Scrape online sources | ⚠️ Simulated | Manual submission or demo script |
| Download video | ⚠️ Partial | Direct URLs only |
| Compare fingerprints | ✅ Yes | Full dual-mode implementation |
| Generate DMCA | ✅ Yes | Full PDF generation |

**For the hackathon demo**, use local files to simulate the online discovery. The fingerprinting and comparison algorithms are production-ready and work exactly the same whether the video comes from a local file or a downloaded stream.

---

**Run `python backend/run_discovery_demo.py` to see the complete flow!**
