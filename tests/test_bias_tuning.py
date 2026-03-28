import math
import sys
import os

# Add backend to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = os.path.join(PROJECT_ROOT, 'backend')
if BACKEND_DIR not in sys.path:
    sys.path.append(BACKEND_DIR)

from engines.dual_engine import DualModeEngine

def test_bias_sensitivity():
    print("\n--- Testing Detection Bias Sensitivity ---")
    engine = DualModeEngine()
    baseline = engine._pattern_recognition_decision(70, 70, True)
    
    test_cases = [
        # (video, audio, expected_at_default_bias)
        (70, 70, True),   # Current "aggressive" behavior
        (50, 50, False),  # Low confidence should not match
        (90, 10, True),   # Strong video, weak audio
        (10, 90, True),   # Weak video, strong audio
    ]
    
    print(f"\nDefault Bias: {engine.bias}")
    for v, a, expected in test_cases:
        decision = engine._pattern_recognition_decision(v, a, True)
        print(f"Video: {v}%, Audio: {a}% -> Score: {decision['pattern_score']:.2f}% | Match: {decision['is_match']}")

    # Test Conservative Bias
    print("\n--- Testing Conservative Bias (-65.0) ---")
    engine.bias = -65.0
    # Conservative bias should lower score for the same evidence.
    decision = engine._pattern_recognition_decision(70, 70, True)
    print(f"Video: 70%, Audio: 70% -> Score: {decision['pattern_score']:.2f}% | Match: {decision['is_match']}")
    assert decision['pattern_score'] < baseline['pattern_score'], "Conservative bias should lower confidence score."

    # Test Aggressive Bias
    print("\n--- Testing Aggressive Bias (-45.0) ---")
    engine.bias = -45.0
    # Aggressive bias should raise confidence for the same evidence.
    decision = engine._pattern_recognition_decision(60, 60, True)
    print(f"Video: 60%, Audio: 60% -> Score: {decision['pattern_score']:.2f}% | Match: {decision['is_match']}")

    engine.bias = -65.0
    conservative_60 = engine._pattern_recognition_decision(60, 60, True)
    engine.bias = -45.0
    aggressive_60 = engine._pattern_recognition_decision(60, 60, True)
    assert aggressive_60['pattern_score'] > conservative_60['pattern_score'], "Aggressive bias should increase confidence score."
    
    print("\n✅ Sensitivity tests passed!")

if __name__ == "__main__":
    test_bias_sensitivity()
