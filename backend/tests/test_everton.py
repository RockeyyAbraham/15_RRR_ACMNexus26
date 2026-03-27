import os
import sys
import time

# Add parent directory to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dual_engine import DualModeEngine
from matcher import VideoMatcher
from hash_engine import VideoHashEngine

def test_everton_robustness():
    """Test detection against the new Everton highlights video."""
    original = r"assets/videos/EVERTON 3-0 CHELSEA  Premier League highlights - Everton Football Club (720p, h264, youtube).mp4"
    pirated_dir = r"assets/videos/pirated"
    
    if not os.path.exists(original):
        print(f"✗ Original video not found: {original}")
        return

    test_cases = [
        ("EVERTON 3-0 CHELSEA  Premier League highlights - Everton Football Club (720p, h264, youtube)_240p.mp4", "240p"),
        ("EVERTON 3-0 CHELSEA  Premier League highlights - Everton Football Club (720p, h264, youtube)_colorshift.mp4", "Color Shift"),
        ("EVERTON 3-0 CHELSEA  Premier League highlights - Everton Football Club (720p, h264, youtube)_cropped.mp4", "Cropped"),
        ("EVERTON 3-0 CHELSEA  Premier League highlights - Everton Football Club (720p, h264, youtube)_extreme.mp4", "Extreme"),
        ("EVERTON 3-0 CHELSEA  Premier League highlights - Everton Football Club (720p, h264, youtube)_letterbox.mp4", "Letterbox"),
        ("EVERTON 3-0 CHELSEA  Premier League highlights - Everton Football Club (720p, h264, youtube)_mirrored.mp4", "Mirrored")
    ]

    engine = DualModeEngine()
    
    results = []
    for filename, label in test_cases:
        suspect_path = os.path.join(pirated_dir, filename)
        if not os.path.exists(suspect_path):
            print(f"✗ Suspect not found: {filename}")
            continue

        print(f"\n────────────────────────────────────────────────────────────────────────────────")
        print(f"Testing: {label}")
        print(f"────────────────────────────────────────────────────────────────────────────────")
        
        start_time = time.time()
        res = engine.detect_piracy(suspect_path, original, mode='dual')
        duration = time.time() - start_time

        is_match = res.get('is_match', False)
        confidence = res.get('combined_confidence', 0)
        pattern_score = res.get('pattern_score', 0)
        
        status = "✅ DETECTED" if is_match else "❌ MISSED"
        msg = f"{status} | Combined Confidence: {confidence:.2f}% | Pattern Score: {pattern_score:.2f}% | Time: {duration:.2f}s"
        print(msg)
        results.append(is_match)

    print("\n" + "="*80)
    success_rate = (sum(results) / len(results)) * 100 if results else 0
    print(f"FINAL RESULT: {sum(results)}/{len(results)} detected ({success_rate:.1f}%)")
    print("="*80)

if __name__ == "__main__":
    test_everton_robustness()
