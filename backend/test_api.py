import requests
import json
import os
from hash_engine import VideoHashEngine

def test_api():
    print("🚀 Testing Sentinel Backend API")
    print("=" * 50)
    
    BASE_URL = "http://127.0.0.1:8000"
    engine = VideoHashEngine()
    
    # 1. Root Check
    print("\n🔍 Checking API status...")
    response = requests.get(f"{BASE_URL}/")
    print(f"Status: {response.json()}")
    
    # 2. Ingest Reference Content
    print("\n📤 Ingesting reference content...")
    video_path = "assets/videos/Race Highlights  2026 Australian Grand Prix - FORMULA 1 (720p, h264, youtube).mp4"
    if os.path.exists(video_path):
        with open(video_path, "rb") as f:
            response = requests.post(f"{BASE_URL}/ingest", files={"file": f}, data={"title": "F1 Race Highlights"})
        print(f"Ingest Result: {response.json()}")
        content_id = response.json().get('id')
    else:
        print("⚠ skipping ingestion: video not found")
        content_id = None
        
    # 3. Detect Piracy
    print("\n🕵️ Attempting piracy detection...")
    # Generate some hashes from the 240p pirated copy
    pirated_path = "assets/videos/pirated/Race Highlights  2026 Australian Grand Prix - FORMULA 1 (720p, h264, youtube)_240p.mp4"
    if os.path.exists(pirated_path):
        res = engine.process_video(pirated_path)
        suspect_hashes = res['hashes'][:20] # Test with first 20 frames
        
        response = requests.post(f"{BASE_URL}/detect", json=suspect_hashes, params={"platform": "Twitch", "stream_url": "https://twitch.tv/fake_stream"})
        print(f"Detection Result: {json.dumps(response.json(), indent=2)}")
    else:
        print("⚠ skipping detection: pirated video not found")
        
    # 4. Fetch Events
    print("\n📜 Fetching detection events...")
    response = requests.get(f"{BASE_URL}/events")
    print(f"Events Found: {len(response.json())}")
    
    print("\n" + "=" * 50)
    print("✅ API Test Complete!")

if __name__ == "__main__":
    test_api()
