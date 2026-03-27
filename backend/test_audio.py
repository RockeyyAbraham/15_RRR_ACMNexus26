#!/usr/bin/env python3
"""
Test audio fingerprinting functionality.
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engines.audio_engine import AudioHashEngine

def test_audio_fingerprinting():
    """Test audio fingerprinting on available videos."""
    
    video_dir = r"c:\Users\rishi\Documents\GitHub\-TeamId-_RRR_ACMNexus26\assets\videos"
    
    # Find a test video
    test_videos = []
    for f in os.listdir(video_dir):
        if f.endswith('.mp4'):
            test_videos.append(os.path.join(video_dir, f))
    
    if not test_videos:
        print("No test videos found")
        return
    
    print(f"Testing audio fingerprinting...")
    print(f"Found {len(test_videos)} videos")
    
    engine = AudioHashEngine()
    
    for video_path in test_videos[:1]:  # Test first video only
        print(f"\nTesting: {os.path.basename(video_path)}")
        
        try:
            hashes, metadata = engine.hash_audio(video_path)
            
            print(f"✓ Audio fingerprinting successful!")
            print(f"  Hashes generated: {len(hashes)}")
            print(f"  Duration: {metadata.get('duration_seconds', 0):.2f}s")
            print(f"  Processing time: {metadata.get('processing_time_seconds', 0):.2f}s")
            
            # Show sample hashes
            if hashes:
                print(f"  Sample hash: {hashes[0]['hash'][:16]}...")
                print(f"  Timestamp: {hashes[0]['timestamp']:.2f}s")
            
        except Exception as e:
            print(f"✗ Audio fingerprinting failed: {e}")
            print(f"  This is expected if ffmpeg is not installed")

if __name__ == "__main__":
    test_audio_fingerprinting()
