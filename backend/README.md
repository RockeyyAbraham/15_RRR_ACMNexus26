# Sentinel Backend

Video fingerprinting and piracy detection engine.

## Runtime Modes

- Flask mode (legacy, existing): `python api/main.py`
- FastAPI mode (Northstar-aligned): `uvicorn api.fastapi_main:app --host 0.0.0.0 --port 8000 --reload`

FastAPI mode mounts the existing Flask REST API and serves native WebSocket updates at `/live`.

## Core Components

- **hash_engine.py** - Video processing (pHash/dHash, adaptive sampling, parallel processing)
- **matcher.py** - Sequence matching with statistical confidence scoring
- **ai_engine.py** - AI-powered summaries and DMCA generation (Groq)
- **audio_engine.py** - Audio fingerprinting (future)

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run comprehensive test
python tests/test_sentinel.py
```

## Features

✅ Adaptive frame sampling (scene change detection)  
✅ Multi-hash fusion (pHash + dHash)  
✅ Parallel processing (20x speedup)  
✅ Sliding window temporal matching  
✅ Statistical confidence scoring  
✅ AI-powered detection summaries  
✅ Automated DMCA generation
