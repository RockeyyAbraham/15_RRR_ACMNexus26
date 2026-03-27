# Sentinel Backend - Video Processing Pipeline

## Overview

This is the core video processing pipeline for **Sentinel**, a real-time media fingerprinting engine for detecting live sports piracy.

## Components

### 1. `hash_engine.py` - Video Frame Extraction & pHash Generation

**Responsibilities:**
- Extract frames from video files using OpenCV
- Generate perceptual hashes (pHash) for each sampled frame
- Support chunked processing for real-time simulation

**Key Features:**
- Configurable frame sampling rate (default: every 10th frame)
- 8x8 pHash generation (64-bit hash)
- Video metadata extraction (FPS, duration, resolution)
- Chunked processing for streaming scenarios

**Usage:**
```python
from hash_engine import VideoHashEngine

engine = VideoHashEngine(frame_sample_rate=10, hash_size=8)

# Hash entire video
hashes, metadata = engine.hash_video("video.mp4")
print(f"Generated {len(hashes)} hashes")

# Get video info without processing
info = engine.get_video_info("video.mp4")
print(f"Duration: {info['duration_seconds']}s")

# Process in chunks (simulates real-time)
chunks = engine.hash_video_chunked("stream.mp4", chunk_duration=5)
for hashes, timestamp in chunks:
    print(f"Chunk at {timestamp}s: {len(hashes)} hashes")
```

### 2. `matcher.py` - Matching Logic & Similarity Scoring

**Responsibilities:**
- Compare pHashes using Hamming distance
- Calculate similarity scores
- Match video sequences against protected content database
- Find best matches from multiple candidates

**Key Features:**
- Configurable similarity threshold (default: 85%)
- Hamming distance calculation
- Multi-frame validation
- Database search with best-match selection

**Usage:**
```python
from matcher import VideoMatcher

matcher = VideoMatcher(threshold=85.0, hash_size=8)

# Compare two hashes
is_match, similarity = matcher.compare_hashes(hash1, hash2)
print(f"Similarity: {similarity:.2f}%")

# Match video sequences
result = matcher.match_video_sequences(suspect_hashes, protected_hashes)
if result['is_match']:
    print(f"PIRACY DETECTED! Confidence: {result['confidence_score']:.1f}%")

# Find best match in database
best_match, result = matcher.find_best_match(suspect_hashes, database)
if result['is_match']:
    print(f"Matched: {best_match['title']}")
```

## Installation

### Prerequisites
- Python 3.10+
- ffmpeg (must be in PATH)

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Verify Installation

```bash
# Test ffmpeg
ffmpeg -version

# Test OpenCV
python -c "import cv2; print('OpenCV:', cv2.__version__)"

# Test imagehash
python -c "import imagehash; print('ImageHash: OK')"
```

## Testing

Run the test suite:

```bash
# Basic tests (no video required)
python test_pipeline.py

# Test with real video
python test_pipeline.py path/to/video.mp4
```

**Expected Output:**
```
SENTINEL VIDEO PROCESSING PIPELINE - TEST SUITE
============================================================
TEST 1: Hash Engine
✓ Hash engine initialized

TEST 2: Matcher
✓ Matcher initialized
✓ Identical hash comparison: 100.00%
✓ Similar hash comparison: 98.44%

TEST 3: Video Sequence Matching
🔴 PIRACY DETECTED!
Confidence Score: 98.44%

TEST 4: Database Matching
🔴 PIRACY DETECTED!
Infringing content matches: Super Bowl LVIII

✓ All core components tested successfully
🎯 Pipeline is ready for integration!
```

## How It Works

### Perceptual Hashing (pHash)

Unlike pixel-by-pixel comparison, pHash captures the **structure** of an image:

1. **Resize** image to 32x32
2. **Convert** to grayscale
3. **Apply DCT** (Discrete Cosine Transform)
4. **Extract** low-frequency components (8x8)
5. **Generate** 64-bit hash based on DCT coefficients

**Why it works:**
- Survives JPEG compression
- Resistant to resizing
- Tolerates color shifts
- Handles aspect ratio changes

### Hamming Distance Matching

Compare two hashes by counting differing bits:

```
Hash 1: a3f2c1b4e5d6a7b8
Hash 2: a3f2c1b4e5d6a7b9
         ^^^^^^^^^^^^^^^ (1 bit different)

Hamming Distance: 1
Similarity: (1 - 1/64) × 100 = 98.44%
```

**Threshold Tuning:**
- **95%+** = Too strict, misses degraded streams
- **75%-** = Too loose, false positives
- **85%** = Sweet spot (recommended)

## Performance

### Frame Extraction
- **Speed:** ~200 FPS on modern CPU
- **Memory:** ~50MB per 60-second video

### Hash Generation
- **Speed:** ~1000 hashes/second
- **Memory:** ~1KB per hash

### Matching
- **Speed:** ~10,000 comparisons/second
- **Complexity:** O(N×M) where N=suspect frames, M=protected frames

## Integration with FastAPI

Example endpoint:

```python
from fastapi import FastAPI, UploadFile
from hash_engine import VideoHashEngine
from matcher import VideoMatcher

app = FastAPI()
engine = VideoHashEngine()
matcher = VideoMatcher()

@app.post("/upload/protected")
async def upload_protected(file: UploadFile):
    # Save file
    video_path = f"uploads/{file.filename}"
    
    # Extract hashes
    hashes, metadata = engine.hash_video(video_path)
    
    # Store in database
    # ... (database code)
    
    return {"hashes": len(hashes), "duration": metadata['duration_seconds']}

@app.post("/upload/suspect")
async def upload_suspect(file: UploadFile):
    # Save file
    video_path = f"uploads/{file.filename}"
    
    # Extract hashes
    suspect_hashes, _ = engine.hash_video(video_path)
    
    # Get protected content from database
    protected_hashes = get_from_database()
    
    # Match
    result = matcher.match_video_sequences(suspect_hashes, protected_hashes)
    
    if result['is_match']:
        # PIRACY DETECTED!
        return {"detected": True, "confidence": result['confidence_score']}
    
    return {"detected": False}
```

## Troubleshooting

### OpenCV won't open video
- **Check:** ffmpeg is installed and in PATH
- **Try:** `ffmpeg -i video.mp4` to verify file is valid

### Low similarity scores on identical videos
- **Check:** Frame sample rate is consistent
- **Try:** Lower threshold to 80%

### Out of memory errors
- **Solution:** Process video in chunks using `hash_video_chunked()`

## Next Steps

1. **Database Integration** - Store hashes in SQLite/PostgreSQL
2. **FastAPI Endpoints** - Create REST API for upload/detection
3. **WebSocket Support** - Real-time detection streaming
4. **DMCA Generator** - Auto-generate takedown notices

## License

MIT License - See LICENSE file for details
