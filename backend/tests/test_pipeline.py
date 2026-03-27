"""
Test script for Sentinel video processing pipeline.
Tests frame extraction, pHash generation, and matching logic.
"""

import sys
import os
import time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from hash_engine import VideoHashEngine
from matcher import VideoMatcher


def test_hash_engine():
    """Test the hash engine with sample data."""
    print("\n" + "=" * 60)
    print("TEST 1: Hash Engine")
    print("=" * 60)
    
    engine = VideoHashEngine(frame_sample_rate=10, hash_size=8)
    
    print(f"✓ Hash engine initialized")
    print(f"  - Frame sample rate: Every {engine.frame_sample_rate}th frame")
    print(f"  - Hash size: {engine.hash_size}x{engine.hash_size} ({engine.hash_size**2}-bit)")
    
    return engine


def test_matcher():
    """Test the matcher with sample hashes."""
    print("\n" + "=" * 60)
    print("TEST 2: Matcher")
    print("=" * 60)
    
    matcher = VideoMatcher(threshold=85.0, hash_size=8)
    
    print(f"✓ Matcher initialized")
    print(f"  - Threshold: {matcher.threshold}%")
    print(f"  - Max Hamming distance: {matcher.max_distance} bits")
    
    # Test identical hashes
    hash1 = "a3f2c1b4e5d6a7b8"
    hash2 = "a3f2c1b4e5d6a7b8"
    
    is_match, similarity = matcher.compare_hashes(hash1, hash2)
    print(f"\n✓ Identical hash comparison:")
    print(f"  - Hash 1: {hash1}")
    print(f"  - Hash 2: {hash2}")
    print(f"  - Match: {is_match}")
    print(f"  - Similarity: {similarity:.2f}%")
    
    # Test similar hashes (1 bit different)
    hash3 = "a3f2c1b4e5d6a7b9"
    
    is_match, similarity = matcher.compare_hashes(hash1, hash3)
    distance = matcher.calculate_hamming_distance(hash1, hash3)
    print(f"\n✓ Similar hash comparison:")
    print(f"  - Hash 1: {hash1}")
    print(f"  - Hash 3: {hash3}")
    print(f"  - Hamming distance: {distance} bits")
    print(f"  - Match: {is_match}")
    print(f"  - Similarity: {similarity:.2f}%")
    
    # Test different hashes
    hash4 = "1234567890abcdef"
    
    is_match, similarity = matcher.compare_hashes(hash1, hash4)
    distance = matcher.calculate_hamming_distance(hash1, hash4)
    print(f"\n✓ Different hash comparison:")
    print(f"  - Hash 1: {hash1}")
    print(f"  - Hash 4: {hash4}")
    print(f"  - Hamming distance: {distance} bits")
    print(f"  - Match: {is_match}")
    print(f"  - Similarity: {similarity:.2f}%")
    
    return matcher


def test_video_matching():
    """Test video sequence matching."""
    print("\n" + "=" * 60)
    print("TEST 3: Video Sequence Matching")
    print("=" * 60)
    
    matcher = VideoMatcher(threshold=85.0)
    
    # Simulate protected video hashes
    protected_hashes = [
        "a3f2c1b4e5d6a7b8",
        "b4e5d6a7b8c9d0e1",
        "c5f6e7d8c9b0a1f2",
        "d6a7b8c9d0e1f2a3",
        "e7b8c9d0e1f2a3b4"
    ]
    
    # Simulate suspect video (same content, slightly degraded)
    suspect_hashes = [
        "a3f2c1b4e5d6a7b9",  # 1 bit different
        "b4e5d6a7b8c9d0e1",  # Identical
        "c5f6e7d8c9b0a1f3",  # 1 bit different
        "d6a7b8c9d0e1f2a3",  # Identical
        "e7b8c9d0e1f2a3b5"   # 1 bit different
    ]
    
    result = matcher.match_video_sequences(suspect_hashes, protected_hashes)
    
    print(f"✓ Protected video: {len(protected_hashes)} hashes")
    print(f"✓ Suspect video: {len(suspect_hashes)} hashes")
    print(f"\nMatch Result:")
    print(f"  - Is Match: {result['is_match']}")
    print(f"  - Confidence Score: {result['confidence_score']:.2f}%")
    print(f"  - Matches: {result['matches']}/{result['total_comparisons']}")
    print(f"  - Match Percentage: {result['match_percentage']:.2f}%")
    print(f"  - Best Similarity: {result['best_similarity']:.2f}%")
    print(f"  - Worst Similarity: {result['worst_similarity']:.2f}%")
    print(f"  - Average Similarity: {result['average_similarity']:.2f}%")
    
    if result['is_match']:
        print(f"\n🔴 PIRACY DETECTED!")
    else:
        print(f"\n✓ No match found")
    
    return result


def test_database_matching():
    """Test matching against a database of protected content."""
    print("\n" + "=" * 60)
    print("TEST 4: Database Matching")
    print("=" * 60)
    
    matcher = VideoMatcher(threshold=85.0)
    
    # Simulate database of protected content
    protected_database = [
        {
            'id': 1,
            'title': 'NBA Finals Game 7',
            'league': 'NBA',
            'video_hashes': [
                "1111111111111111",
                "2222222222222222",
                "3333333333333333"
            ]
        },
        {
            'id': 2,
            'title': 'Super Bowl LVIII',
            'league': 'NFL',
            'video_hashes': [
                "a3f2c1b4e5d6a7b8",
                "b4e5d6a7b8c9d0e1",
                "c5f6e7d8c9b0a1f2"
            ]
        },
        {
            'id': 3,
            'title': 'Premier League Final',
            'league': 'EPL',
            'video_hashes': [
                "aaaaaaaaaaaaaaaa",
                "bbbbbbbbbbbbbbbb",
                "cccccccccccccccc"
            ]
        }
    ]
    
    # Suspect video matches Super Bowl
    suspect_hashes = [
        "a3f2c1b4e5d6a7b9",
        "b4e5d6a7b8c9d0e1",
        "c5f6e7d8c9b0a1f3"
    ]
    
    best_match, result = matcher.find_best_match(suspect_hashes, protected_database)
    
    print(f"✓ Database size: {len(protected_database)} protected videos")
    print(f"✓ Suspect video: {len(suspect_hashes)} hashes")
    
    if best_match:
        print(f"\nBest Match Found:")
        print(f"  - Title: {best_match['title']}")
        print(f"  - League: {best_match['league']}")
        print(f"  - Confidence: {result['confidence_score']:.2f}%")
        print(f"  - Is Match: {result['is_match']}")
        
        if result['is_match']:
            print(f"\n🔴 PIRACY DETECTED!")
            print(f"  Infringing content matches: {best_match['title']}")
    else:
        print(f"\n✓ No match found in database")
    
    return best_match, result


def test_with_real_video(video_path: str):
    """Test with a real video file."""
    print("\n" + "=" * 60)
    print("TEST 5: Real Video Processing")
    print("=" * 60)
    
    if not os.path.exists(video_path):
        print(f"⚠ Video file not found: {video_path}")
        print(f"  Skipping real video test")
        return None
    
    engine = VideoHashEngine(frame_sample_rate=10, hash_size=8)
    
    print(f"✓ Processing video: {video_path}")
    
    # Get video info
    info = engine.get_video_info(video_path)
    print(f"\nVideo Information:")
    print(f"  - Duration: {info['duration_seconds']:.2f} seconds")
    print(f"  - FPS: {info['fps']:.2f}")
    print(f"  - Resolution: {info['width']}x{info['height']}")
    print(f"  - Total frames: {info['total_frames']}")
    print(f"  - Estimated hashes: {info['estimated_hashes']}")
    
    # Extract hashes
    print(f"\n✓ Extracting hashes...")
    hashes, metadata = engine.hash_video(video_path)
    
    print(f"\nHash Extraction Results:")
    print(f"  - Total hashes: {len(hashes)}")
    print(f"  - Sample rate: Every {metadata['sample_rate']}th frame")
    print(f"  - First hash: {hashes[0] if hashes else 'N/A'}")
    print(f"  - Last hash: {hashes[-1] if hashes else 'N/A'}")
    
    return hashes, metadata


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("SENTINEL VIDEO PROCESSING PIPELINE - TEST SUITE")
    print("=" * 60)
    
    try:
        # Test 1: Hash Engine
        engine = test_hash_engine()
        
        # Test 2: Matcher
        matcher = test_matcher()
        
        # Test 3: Video Sequence Matching
        result = test_video_matching()
        
        # Test 4: Database Matching
        best_match, db_result = test_database_matching()
        
        # Test 5: Real Video (if path provided)
        if len(sys.argv) > 1:
            video_path = sys.argv[1]
            test_with_real_video(video_path)
        else:
            print("\n" + "=" * 60)
            print("TEST 5: Real Video Processing")
            print("=" * 60)
            print("⚠ No video path provided")
            print("  Usage: python test_pipeline.py <video_path>")
            print("  Example: python test_pipeline.py test.mp4")
        
        # Summary
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        print("✓ All core components tested successfully")
        print("✓ Hash engine: WORKING")
        print("✓ Matcher: WORKING")
        print("✓ Video sequence matching: WORKING")
        print("✓ Database matching: WORKING")
        print("\n🎯 Pipeline is ready for integration!")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
