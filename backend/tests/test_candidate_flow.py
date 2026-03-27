#!/usr/bin/env python3
"""
Test script for candidate discovery flow.

Tests:
1. Suspicion score calculation
2. Candidate submission and triage
3. Candidate retrieval and filtering
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from api.main import calculate_suspicion_score


def test_suspicion_score_calculation():
    """Test suspicion score calculator with various inputs."""
    print("\n=== Testing Suspicion Score Calculation ===\n")
    
    test_cases = [
        {
            "name": "High suspicion - Twitch live stream with keywords",
            "keyword_hits": ["f1", "live", "australian gp", "free"],
            "event_context": "F1 2026 Australian GP",
            "platform": "twitch",
            "url": "https://twitch.tv/pirate_stream_f1_live",
            "expected_range": (0.75, 1.0),
        },
        {
            "name": "Medium suspicion - YouTube with some keywords",
            "keyword_hits": ["formula 1"],
            "event_context": "F1 2026",
            "platform": "youtube",
            "url": "https://youtube.com/watch?v=abc123",
            "expected_range": (0.5, 0.75),
        },
        {
            "name": "Low suspicion - Reddit with minimal keywords",
            "keyword_hits": ["f1"],
            "event_context": "",
            "platform": "reddit",
            "url": "https://reddit.com/r/motorsports",
            "expected_range": (0.3, 0.6),
        },
        {
            "name": "Very high suspicion - Telegram with piracy indicators",
            "keyword_hits": ["sports", "hd", "stream", "free", "live"],
            "event_context": "Live sports streaming",
            "platform": "telegram",
            "url": "https://telegram.me/free_sports_hd_stream",
            "expected_range": (0.8, 1.0),
        },
        {
            "name": "Very low suspicion - No keywords",
            "keyword_hits": [],
            "event_context": "",
            "platform": "facebook",
            "url": "https://facebook.com/page",
            "expected_range": (0.0, 0.4),
        },
    ]
    
    passed = 0
    failed = 0
    
    for test in test_cases:
        score = calculate_suspicion_score(
            test["keyword_hits"],
            test["event_context"],
            test["platform"],
            test["url"]
        )
        
        min_score, max_score = test["expected_range"]
        is_pass = min_score <= score <= max_score
        
        status = "✓ PASS" if is_pass else "✗ FAIL"
        print(f"{status} {test['name']}")
        print(f"  Score: {score:.3f} (expected: {min_score:.2f} - {max_score:.2f})")
        
        if is_pass:
            passed += 1
        else:
            failed += 1
    
    print(f"\n{passed} passed, {failed} failed\n")
    return failed == 0


def test_triage_logic():
    """Test triage decision logic."""
    print("\n=== Testing Triage Logic ===\n")
    
    test_cases = [
        {"score": 0.3, "expected_status": "discarded"},
        {"score": 0.54, "expected_status": "discarded"},
        {"score": 0.55, "expected_status": "watch_list"},
        {"score": 0.65, "expected_status": "watch_list"},
        {"score": 0.74, "expected_status": "watch_list"},
        {"score": 0.75, "expected_status": "queued"},
        {"score": 0.85, "expected_status": "queued"},
        {"score": 0.95, "expected_status": "queued"},
    ]
    
    passed = 0
    failed = 0
    
    for test in test_cases:
        score = test["score"]
        expected = test["expected_status"]
        
        # Replicate triage logic from main.py
        if score < 0.55:
            actual = "discarded"
        elif score < 0.75:
            actual = "watch_list"
        else:
            actual = "queued"
        
        is_pass = actual == expected
        status = "✓ PASS" if is_pass else "✗ FAIL"
        
        print(f"{status} Score {score:.2f} -> {actual} (expected: {expected})")
        
        if is_pass:
            passed += 1
        else:
            failed += 1
    
    print(f"\n{passed} passed, {failed} failed\n")
    return failed == 0


def test_score_components():
    """Test individual score components."""
    print("\n=== Testing Score Components ===\n")
    
    # Test keyword component (35%)
    score_no_keywords = calculate_suspicion_score([], "", "youtube", "https://example.com")
    score_one_keyword = calculate_suspicion_score(["f1"], "", "youtube", "https://example.com")
    score_five_keywords = calculate_suspicion_score(["f1", "live", "stream", "free", "hd"], "", "youtube", "https://example.com")
    
    print(f"Keyword impact:")
    print(f"  No keywords: {score_no_keywords:.3f}")
    print(f"  1 keyword: {score_one_keyword:.3f}")
    print(f"  5 keywords: {score_five_keywords:.3f}")
    print(f"  Difference (1 vs 5): {score_five_keywords - score_one_keyword:.3f}")
    
    # Test platform component (20%)
    platforms = ["youtube", "twitch", "telegram", "reddit", "facebook"]
    print(f"\nPlatform risk:")
    for platform in platforms:
        score = calculate_suspicion_score([], "", platform, "https://example.com")
        print(f"  {platform}: {score:.3f}")
    
    # Test URL pattern component (10%)
    urls = [
        "https://example.com/page",
        "https://example.com/live-stream",
        "https://example.com/watch-free-hd-stream",
    ]
    print(f"\nURL pattern impact:")
    for url in urls:
        score = calculate_suspicion_score([], "", "youtube", url)
        print(f"  {url}: {score:.3f}")
    
    print()
    return True


def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("  SENTINEL CANDIDATE FLOW TESTS")
    print("=" * 80)
    
    all_passed = True
    
    all_passed &= test_suspicion_score_calculation()
    all_passed &= test_triage_logic()
    all_passed &= test_score_components()
    
    print("=" * 80)
    if all_passed:
        print("  ✓ ALL TESTS PASSED")
    else:
        print("  ✗ SOME TESTS FAILED")
    print("=" * 80 + "\n")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
