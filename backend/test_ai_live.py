import os
from dotenv import load_dotenv
from ai_engine import SentinelAI

# Load env variables from .env
load_dotenv()

def run_live_ai_test():
    print("🚀 Running Live Sentinel AI Test (Groq)")
    print("=" * 50)
    
    try:
        ai = SentinelAI()
        
        # Test 1: Detection Summary
        print("\n📝 Test 1: Generating Detection Summary...")
        detection_data = {
            'content_title': 'F1 Australian Grand Prix 2026',
            'platform': 'Twitch',
            'confidence_score': 97.66,
            'consistency_ratio': 0.92,
            'temporal_location': {'start': 1200, 'end': 1500},
            'timestamp': '2026-03-27T19:30:00Z'
        }
        
        summary = ai.generate_detection_summary(detection_data)
        print(f"\nAI Summary:\n{summary}")
        
        # Test 2: DMCA Notice
        print("\n⚖️ Test 2: Generating DMCA Notice...")
        rights_holder = {
            'name': 'Formula One World Championship Limited',
            'email': 'legal@f1.com',
            'address': 'No. 2 St James’s Market, London SW1Y 4AH',
            'phone': '+44 20 1234 5678'
        }
        
        notice = ai.generate_dmca_notice(detection_data, rights_holder)
        print(f"\nAI DMCA Notice (Excerpt):\n{notice[:500]}...")
        
        print("\n" + "=" * 50)
        print("✅ Live AI Test Completed Successfully!")
        
    except Exception as e:
        print(f"❌ Error during AI test: {e}")

if __name__ == "__main__":
    run_live_ai_test()
