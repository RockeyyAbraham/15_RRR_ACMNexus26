# Sentinel Backend

Video fingerprinting and piracy detection engine.

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
