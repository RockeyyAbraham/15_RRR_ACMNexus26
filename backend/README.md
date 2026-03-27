# Sentinel Backend

Video fingerprinting and piracy detection engine for Sentinel.

## Core Components

- **hash_engine.py** - Video frame extraction and pHash/dHash generation
- **matcher.py** - Video sequence matching with statistical confidence
- **ai_engine.py** - AI-powered detection summaries and DMCA generation
- **audio_engine.py** - Audio fingerprinting (future enhancement)

## Testing

Run tests from the `/tests` directory:
```bash
python tests/test_pipeline.py
python tests/test_real_videos.py
python tests/test_ai_engine.py
```

## Installation

```bash
pip install -r requirements.txt
```

## Features

- Adaptive frame sampling with scene change detection
- Multi-hash fusion (pHash + dHash)
- Parallel processing (7.7x speedup)
- Sliding window temporal matching
- Statistical confidence scoring
- AI-powered detection summaries
- Automated DMCA notice generation
