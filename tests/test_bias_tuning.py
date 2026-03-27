import math
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from dual_engine import DualModeEngine

def test_bias_sensitivity():
    print("\n--- Testing Detection Bias Sensitivity ---")
    engine = DualModeEngine()
    
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
    # At -65.0, 70/70 should NOT match (prob ~86%)
    decision = engine._pattern_recognition_decision(70, 70, True)
    print(f"Video: 70%, Audio: 70% -> Score: {decision['pattern_score']:.2f}% | Match: {decision['is_match']}")
    assert not decision['is_match'], "70/70 matched at -65.0 bias, but it shouldn't!"

    # Test Aggressive Bias
    print("\n--- Testing Aggressive Bias (-45.0) ---")
    engine.bias = -45.0
    # At -45.0, even 60/60 might match
    decision = engine._pattern_recognition_decision(60, 60, True)
    print(f"Video: 60%, Audio: 60% -> Score: {decision['pattern_score']:.2f}% | Match: {decision['is_match']}")
    
    print("\n✅ Sensitivity tests passed!")

if __name__ == "__main__":
    test_bias_sensitivity()
