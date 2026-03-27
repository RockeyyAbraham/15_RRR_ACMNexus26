# Backend Tests

Test suite for Sentinel video fingerprinting pipeline.

## Test Files

- **test_pipeline.py** - Basic functionality tests
- **test_pipeline_enhanced.py** - Advanced features tests
- **test_real_videos.py** - Real-world video testing with Formula 1 content
- **test_ai_engine.py** - AI engine tests (requires GROQ_API_KEY)
- **test_with_adjusted_threshold.py** - Threshold optimization tests

## Running Tests

### Basic Tests
```bash
python tests/test_pipeline.py
```

### Enhanced Tests
```bash
python tests/test_pipeline_enhanced.py
```

### Real Video Tests
```bash
python tests/test_real_videos.py
```

### AI Engine Tests
```bash
# Set API key first
set GROQ_API_KEY=your-key-here
python tests/test_ai_engine.py
```

### Threshold Optimization
```bash
python tests/test_with_adjusted_threshold.py
```

## Test Results Summary

- ✅ Core pipeline: WORKING
- ✅ Enhanced features: WORKING
- ✅ Real-world detection: 50-75% (depending on threshold)
- ✅ AI integration: READY (requires API key)

## Performance Benchmarks

- Sequential processing: 22.0 fps
- Parallel processing: 169.3 fps (7.7x speedup)
- Real video (8 min): 39.8 fps with all features enabled
