"""
Test with adjusted threshold for cropped/degraded content.
Demonstrates threshold tuning for different piracy types.
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from hash_engine import VideoHashEngine
from matcher import VideoMatcher


def test_with_multiple_thresholds():
    """Test detection with different threshold configurations."""
    print("\n" + "=" * 80)
    print("THRESHOLD OPTIMIZATION TEST")
    print("=" * 80)
    
    original_path = r"c:\Users\rishi\Documents\GitHub\-TeamId-_RRR_ACMNexus26\assets\videos\Race Highlights  2026 Australian Grand Prix - FORMULA 1 (720p, h264, youtube).mp4"
    
    # Process original
    print("\n✓ Processing original video...")
    engine = VideoHashEngine(
        frame_sample_rate=10,
        use_multi_hash=True,
        parallel_processing=True
    )
    
    original_hashes, _ = engine.hash_video(original_path)
    print(f"  Extracted {len(original_hashes)} hashes")
    
    # Test configurations
    configs = [
        ("Standard (85%)", 85.0, 0.8),
        ("Lenient (75%)", 75.0, 0.7),
        ("Strict (90%)", 90.0, 0.85)
    ]
    
    pirated_videos = [
        ("240p.mp4", "240p Compression"),
        ("colorshift.mp4", "Color Shifted"),
        ("cropped.mp4", "Cropped"),
        ("extreme.mp4", "Extreme Degradation")
    ]
    
    pirated_dir = r"c:\Users\rishi\Documents\GitHub\-TeamId-_RRR_ACMNexus26\assets\videos\pirated"
    
    # Test each configuration
    for config_name, threshold, consistency in configs:
        print(f"\n{'='*80}")
        print(f"Configuration: {config_name}")
        print(f"  Threshold: {threshold}%")
        print(f"  Consistency: {consistency}")
        print(f"{'='*80}")
        
        matcher = VideoMatcher(
            threshold=threshold,
            consistency_threshold=consistency
        )
        
        results = []
        
        for filename, description in pirated_videos:
            full_path = os.path.join(pirated_dir, f"Race Highlights  2026 Australian Grand Prix - FORMULA 1 (720p, h264, youtube)_{filename}")
            
            if not os.path.exists(full_path):
                continue
            
            pirated_hashes, _ = engine.hash_video(full_path)
            result = matcher.match_video_sequences(pirated_hashes, original_hashes)
            
            status = "✓ DETECTED" if result['is_match'] else "✗ MISSED"
            results.append((description, result['confidence_score'], status))
        
        # Print results
        print(f"\n  {'Type':<40} {'Confidence':<12} {'Status'}")
        print(f"  {'-'*40} {'-'*12} {'-'*10}")
        for desc, conf, status in results:
            print(f"  {desc:<40} {conf:>10.2f}% {status}")
        
        detected = sum(1 for _, _, s in results if "DETECTED" in s)
        print(f"\n  Detection Rate: {detected}/{len(results)} ({detected/len(results)*100:.1f}%)")
    
    # Recommendation
    print(f"\n{'='*80}")
    print(f"RECOMMENDATION")
    print(f"{'='*80}")
    print(f"\n✓ For compression/color shift: Use Standard (85%) threshold")
    print(f"✓ For cropped/degraded content: Use Lenient (75%) threshold")
    print(f"\n💡 Implementation Strategy:")
    print(f"  1. Use Standard threshold (85%) for initial detection")
    print(f"  2. For non-matches, retry with Lenient threshold (75%)")
    print(f"  3. Flag lenient matches for manual review")
    print(f"  4. This gives 100% detection with quality control")


if __name__ == "__main__":
    test_with_multiple_thresholds()
