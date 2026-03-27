#!/usr/bin/env python3
"""
Quick test of audio fingerprinting with generated variants.
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engines.dual_engine import DualModeEngine

def test_audio_variants():
    """Test audio fingerprinting on generated variants."""
    
    original = r"c:\Users\rishi\Documents\GitHub\-TeamId-_RRR_ACMNexus26\assets\videos\EVERTON 3-0 CHELSEA  Premier League highlights - Everton Football Club (720p, h264, youtube).mp4"
    pirated_dir = r"c:\Users\rishi\Documents\GitHub\-TeamId-_RRR_ACMNexus26\assets\videos\pirated\EVERTON_3_0_CHELSEA__Premier_League_highlights___Everton_Football_Club_(720p,_h264,_youtube)"
    
    # Test only audio variants
    audio_variants = [
        ("lowbitrate.mp4", "Low Bitrate (64kbps)"),
        ("speed_audio.mp4", "Speed Change (1.5x audio)"),
        ("mono.mp4", "Mono Conversion"),
        ("equalized.mp4", "Bass Boosted"),
        ("trimmed.mp4", "Trimmed (30s audio)")
    ]
    
    engine = DualModeEngine()
    
    print("🎵 AUDIO FINGERPRINTING TEST")
    print("=" * 60)
    
    for filename, description in audio_variants:
        suspect_path = os.path.join(pirated_dir, filename)
        
        if not os.path.exists(suspect_path):
            print(f"\n⚠ Missing: {filename}")
            continue
        
        print(f"\n{'─' * 50}")
        print(f"Testing: {description}")
        print(f"{'─' * 50}")
        
        try:
            result = engine.detect_piracy(suspect_path, original, mode='dual')
            
            video_conf = result.get('video_confidence', 0.0)
            audio_conf = result.get('audio_confidence', 0.0)
            combined_conf = result.get('combined_confidence', 0.0)
            pattern_score = result.get('pattern_score', 0.0)
            
            print(f"  Video: {video_conf:.2f}%")
            print(f"  Audio: {audio_conf:.2f}%")
            print(f"  Combined: {combined_conf:.2f}%")
            print(f"  Pattern: {pattern_score:.2f}%")
            print(f"  Status: {'✓ DETECTED' if result.get('is_match') else '✗ MISSED'}")
            
        except Exception as e:
            print(f"  ✗ ERROR: {e}")

if __name__ == "__main__":
    test_audio_variants()
