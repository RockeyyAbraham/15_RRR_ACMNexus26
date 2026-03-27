# 🚀 Sentinel - Setup Guide

## Quick Start (5 Minutes)

### Prerequisites
- Python 3.10+
- Node.js 18+ (for frontend)
- ffmpeg (must be in PATH)

### Backend Setup

```bash
# Navigate to backend
cd backend

# Install dependencies
pip install -r requirements.txt

# Create environment file
cp ../.env.example .env

# Edit .env and add your Groq API key (optional but recommended)
# Get free API key from: https://console.groq.com/keys

# Run the Flask API server
python api/main.py
```

The backend will start on `http://localhost:8000`

### Frontend Setup

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The frontend will start on `http://localhost:5173`

---

## 🧪 Testing the System

### Option 1: Run Comprehensive Test Suite

```bash
cd backend
python tests/test_sentinel.py
```

This will:
- Process the Formula 1 video (if available)
- Test all pirated variants
- Show detection accuracy
- Verify all enhanced features

### Option 2: Quick API Test

```bash
# Check health
curl http://localhost:8000/health

# Upload protected content
curl -X POST http://localhost:8000/upload/protected \
  -F "video=@path/to/video.mp4" \
  -F "title=Test Video" \
  -F "league=Test League"

# Upload suspect content
curl -X POST http://localhost:8000/upload/suspect \
  -F "video=@path/to/suspect.mp4" \
  -F "stream_url=https://example.com/stream"
```

---

## 📁 Project Structure

```
sentinel/
├── backend/
│   ├── api/
│   │   └── main.py              # Flask REST API
│   ├── engines/
│   │   ├── hash_engine.py       # Video fingerprinting
│   │   ├── audio_engine.py      # Audio fingerprinting
│   │   ├── matcher.py           # Advanced matching
│   │   ├── dual_engine.py       # Dual-mode detection
│   │   └── ai_engine.py         # AI intelligence
│   ├── generators/
│   │   └── dmca_generator.py    # DMCA notice generation
│   ├── tests/
│   │   └── test_sentinel.py     # Comprehensive tests
│   └── utils/
│       └── redis_utils.py       # Caching layer
├── frontend/
│   └── src/
│       ├── pages/               # React pages
│       └── components/          # React components
└── assets/
    └── videos/                  # Test videos
```

---

## 🔧 Configuration

### Environment Variables (.env)

```bash
# Required for AI features
GROQ_API_KEY=your_api_key_here

# Optional Redis configuration
REDIS_HOST=localhost
REDIS_PORT=6379

# Detection thresholds
AUTO_ACTION_THRESHOLD=85
MANUAL_REVIEW_THRESHOLD=75
```

### Detection Thresholds

- **AUTO_ACTION_THRESHOLD (85%)**: High-confidence detections → Auto-flag for DMCA
- **MANUAL_REVIEW_THRESHOLD (75%)**: Medium-confidence → Manual review queue
- Below 75%: Ignored

---

## 🎯 Key Features

### Backend
✅ **Dual-Mode Detection**: Video + Audio fingerprinting  
✅ **Adaptive Sampling**: Scene-aware frame extraction  
✅ **Multi-Hash Fusion**: pHash + dHash for robustness  
✅ **Parallel Processing**: 20x speedup on multi-core systems  
✅ **Statistical Confidence**: Reduces false positives  
✅ **AI Integration**: Groq-powered summaries and DMCA generation  
✅ **Redis Caching**: Fast hash lookups (with fakeredis fallback)  
✅ **Async Job Processing**: Non-blocking video processing  

### Frontend
✅ **Modern React UI**: TypeScript + TailwindCSS  
✅ **Real-time Dashboard**: Live detection feed  
✅ **Evidence Viewer**: Side-by-side comparison  
✅ **DMCA Generator**: One-click notice creation  
✅ **Smooth Animations**: Framer Motion  

---

## 🧪 Test Results

**Real-world validation with Formula 1 video (8 minutes, 720p):**

| Piracy Type | Confidence | Status |
|-------------|-----------|--------|
| 240p Compression | 95.08% | ✅ DETECTED |
| Color Shifted | 92.42% | ✅ DETECTED |
| Cropped | 75.89% | ⚠️ Manual Review |
| Extreme Degradation | 74.90% | ⚠️ Manual Review |

**Performance:**
- Processing Speed: 39.8 fps
- Scene Changes Detected: 161
- Parallel Speedup: 20x
- Detection Rate: 50% (standard) / 75% (lenient) / 100% (two-tier)

---

## 🐛 Troubleshooting

### "ffmpeg not found"
```bash
# Windows (using winget)
winget install ffmpeg

# macOS
brew install ffmpeg

# Linux
sudo apt install ffmpeg
```

### "Redis connection failed"
Don't worry! The system automatically falls back to `fakeredis` for local testing.

### "Groq API error"
AI features are optional. The core detection works without it. Get a free API key from https://console.groq.com/keys

### "Import errors"
```bash
# Reinstall dependencies
pip install -r backend/requirements.txt --force-reinstall
```

---

## 📊 API Endpoints

### Core Endpoints
- `POST /upload/protected` - Upload protected content
- `POST /upload/suspect` - Upload suspect content
- `GET /detections` - List all detections
- `GET /detections/<id>/dmca` - Generate DMCA notice

### Async Endpoints
- `POST /upload/protected/async` - Async upload
- `POST /upload/suspect/async` - Async upload
- `GET /jobs/<job_id>` - Check job status
- `POST /jobs/<job_id>/cancel` - Cancel job

### Monitoring
- `GET /health` - System health check
- `GET /metrics/summary` - System metrics
- `WS /live` - WebSocket for real-time updates

---

## 🏆 Hackathon Compliance

✅ **Hourly Commits**: All progress tracked in `/progress/`  
✅ **Sequential Files**: 1.png → 8.txt  
✅ **Changelog**: Complete with HH:MM timestamps  
✅ **Team Collaboration**: All members contributed  
✅ **Working Demo**: Tested with real Formula 1 content  
✅ **Documentation**: Comprehensive guides and reports  

---

## 📝 License

Built for ACM NEXUS 2026 Hackathon - Digital Asset Protection Domain

**Team RRR** | March 27-28, 2026
