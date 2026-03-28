#!/usr/bin/env python3
"""Test script to verify progress system works"""

import requests
import json
import time

def main() -> int:
    """Run progress smoke test against a live backend service."""
    # Test backend health
    print("🔍 Testing backend health...")
    try:
        response = requests.get("http://localhost:8000/health")
        print(f"✅ Backend health: {response.status_code}")
        print(f"📊 Active jobs: {response.json().get('async', {}).get('active_jobs', 0)}")
    except Exception as e:
        print(f"❌ Backend health failed: {e}")
        return 1

    # Test creating a simple job
    print("\n🔍 Testing job creation...")
    try:
        # Use a real video file for testing
        temp_path = r"c:\Users\rishi\Documents\GitHub\-TeamId-_RRR_ACMNexus26\assets\videos\EVERTON 3-0 CHELSEA  Premier League highlights - Everton Football Club (720p, h264, youtube).mp4"

        # Submit job
        with open(temp_path, 'rb') as f:
            files = {'video': f}
            data = {
                'title': 'Test Progress',
                'league': 'TEST_LEAGUE',
                'broadcast_date': '2026-03-28'
            }
            response = requests.post("http://localhost:8000/analysis/piracy-benchmark/async", files=files, data=data)

        if response.status_code == 202:
            job_id = response.json()['job_id']
            print(f"✅ Job created: {job_id}")

            # Poll job status
            print("\n🔍 Testing job polling...")
            for i in range(10):
                try:
                    status_response = requests.get(f"http://localhost:8000/jobs/{job_id}")
                    if status_response.status_code == 200:
                        job_data = status_response.json()
                        print(f"📊 Poll {i+1}: {job_data.get('status')} - {job_data.get('stage')} - progress_data: {job_data.get('progress_data')}")
                    else:
                        print(f"❌ Status check failed: {status_response.status_code}")
                        break
                except Exception as e:
                    print(f"❌ Status check error: {e}")
                    break

                time.sleep(2)
        else:
            print(f"❌ Job creation failed: {response.status_code}")
            print(f"Response: {response.text}")

    except Exception as e:
        print(f"❌ Test failed: {e}")

    print("\n🏁 Test complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
