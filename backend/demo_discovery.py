#!/usr/bin/env python3
"""
Sentinel Discovery Demo Script

Simulates the discovery pipeline by:
1. Submitting candidate URLs with varying suspicion scores
2. Showing triage decisions (discard, watch_list, queued)
3. Demonstrating the full candidate-to-detection flow

Usage:
    python demo_discovery.py
"""

import requests
import json
import time
from datetime import datetime

# Backend API base URL
API_BASE = "http://localhost:8000"

# Demo candidate URLs with different characteristics
DEMO_CANDIDATES = [
    {
        "url": "https://twitch.tv/pirate_stream_f1_live",
        "platform": "twitch",
        "keyword_hits": ["f1", "live", "australian gp", "free"],
        "event_context": "F1 2026 Australian GP",
        "notes": "High suspicion - multiple keywords, live stream pattern",
    },
    {
        "url": "https://youtube.com/watch?v=abc123",
        "platform": "youtube",
        "keyword_hits": ["formula 1", "highlights"],
        "event_context": "F1 2026 Australian GP",
        "notes": "Medium suspicion - some keywords but could be legitimate highlights",
    },
    {
        "url": "https://reddit.com/r/motorsports/comments/xyz",
        "platform": "reddit",
        "keyword_hits": ["f1"],
        "event_context": "",
        "notes": "Low suspicion - single keyword, discussion platform",
    },
    {
        "url": "https://telegram.me/free_sports_hd",
        "platform": "telegram",
        "keyword_hits": ["sports", "hd", "stream", "free"],
        "event_context": "Live sports streaming channel",
        "notes": "Very high suspicion - telegram + multiple piracy indicators",
    },
    {
        "url": "https://facebook.com/sports-fan-page",
        "platform": "facebook",
        "keyword_hits": [],
        "event_context": "",
        "notes": "Very low suspicion - no keywords, legitimate platform",
    },
]


def print_header(text):
    """Print formatted section header."""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80)


def print_candidate_result(result):
    """Print formatted candidate submission result."""
    print(f"\n  Candidate ID: {result['candidate_id']}")
    print(f"  URL: {result['url']}")
    print(f"  Platform: {result['platform']}")
    print(f"  Suspicion Score: {result['suspicion_score']:.3f}")
    print(f"  Status: {result['status'].upper()}")
    
    if result.get('verification_job_id'):
        print(f"  Verification Job: {result['verification_job_id']}")
    
    thresholds = result.get('triage_thresholds', {})
    print(f"\n  Triage Thresholds:")
    print(f"    - Discard: < {thresholds.get('discard', 0.55)}")
    print(f"    - Watch List: {thresholds.get('discard', 0.55)} - {thresholds.get('watch_list', 0.75)}")
    print(f"    - Deep Verification: >= {thresholds.get('watch_list', 0.75)}")


def submit_candidate(candidate):
    """Submit a candidate URL to the discovery endpoint."""
    try:
        response = requests.post(
            f"{API_BASE}/candidates/submit",
            json=candidate,
            headers={"Content-Type": "application/json"},
        )
        
        if response.status_code == 201:
            return response.json()
        else:
            print(f"  ERROR: {response.status_code} - {response.text}")
            return None
            
    except requests.exceptions.ConnectionError:
        print(f"  ERROR: Cannot connect to backend at {API_BASE}")
        print("  Make sure the backend is running: python backend/api/main.py")
        return None
    except Exception as e:
        print(f"  ERROR: {str(e)}")
        return None


def get_candidates(status=None, min_score=None):
    """Retrieve candidates from the API."""
    try:
        params = {}
        if status:
            params['status'] = status
        if min_score is not None:
            params['min_score'] = min_score
        
        response = requests.get(f"{API_BASE}/candidates", params=params)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"  ERROR: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"  ERROR: {str(e)}")
        return None


def get_metrics():
    """Retrieve system metrics."""
    try:
        response = requests.get(f"{API_BASE}/metrics/summary")
        
        if response.status_code == 200:
            return response.json()
        else:
            return None
            
    except Exception as e:
        return None


def main():
    """Run the discovery demo."""
    print_header("SENTINEL DISCOVERY PIPELINE DEMO")
    print("\nThis demo simulates the candidate discovery and triage process.")
    print("It will submit various URLs with different suspicion characteristics.")
    
    # Check backend connectivity
    print_header("STEP 1: Backend Health Check")
    try:
        response = requests.get(f"{API_BASE}/health")
        if response.status_code == 200:
            health = response.json()
            print(f"\n  ✓ Backend is online")
            print(f"  Engines: {', '.join(health.get('engines', []))}")
        else:
            print(f"\n  ✗ Backend health check failed")
            return
    except:
        print(f"\n  ✗ Cannot connect to backend at {API_BASE}")
        print("  Please start the backend: python backend/api/main.py")
        return
    
    # Submit demo candidates
    print_header("STEP 2: Submitting Candidate URLs")
    
    submitted_ids = []
    for i, candidate in enumerate(DEMO_CANDIDATES, 1):
        print(f"\n[{i}/{len(DEMO_CANDIDATES)}] Submitting: {candidate['url']}")
        print(f"  Keywords: {', '.join(candidate['keyword_hits']) if candidate['keyword_hits'] else 'None'}")
        
        result = submit_candidate(candidate)
        if result:
            print_candidate_result(result)
            submitted_ids.append(result['candidate_id'])
        
        time.sleep(0.5)  # Brief pause for readability
    
    # Retrieve and display candidates by status
    print_header("STEP 3: Candidate Triage Summary")
    
    statuses = ['queued', 'watch_list', 'discarded']
    for status in statuses:
        result = get_candidates(status=status)
        if result:
            count = result.get('count', 0)
            print(f"\n  {status.upper()}: {count} candidates")
            
            if count > 0 and result.get('candidates'):
                for candidate in result['candidates'][:3]:  # Show first 3
                    print(f"    - {candidate['url']} (score: {candidate['suspicion_score']:.3f})")
    
    # Show high-priority candidates
    print_header("STEP 4: High-Priority Candidates (Score >= 0.75)")
    
    result = get_candidates(min_score=0.75)
    if result and result.get('candidates'):
        print(f"\n  Found {result['count']} high-priority candidates:")
        for candidate in result['candidates']:
            print(f"\n  URL: {candidate['url']}")
            print(f"  Platform: {candidate['platform']}")
            print(f"  Score: {candidate['suspicion_score']:.3f}")
            print(f"  Status: {candidate['status']}")
            print(f"  Keywords: {', '.join(candidate.get('keyword_hits', []))}")
    else:
        print("\n  No high-priority candidates found.")
    
    # Display system metrics
    print_header("STEP 5: System Metrics")
    
    metrics = get_metrics()
    if metrics:
        print(f"\n  Protected Content: {metrics.get('protected_content_count', 0)}")
        print(f"  Detections: {metrics.get('detections_count', 0)}")
        print(f"  Average Confidence: {metrics.get('average_confidence', 0):.2f}%")
        print(f"  Auto-Action Detections: {metrics.get('auto_action_count', 0)}")
        print(f"  Manual Review Detections: {metrics.get('manual_review_count', 0)}")
        
        async_info = metrics.get('async', {})
        print(f"\n  Async Workers: {async_info.get('max_workers', 0)}")
        print(f"  Active Jobs: {async_info.get('active_jobs', 0)}")
        print(f"  Tracked Jobs: {async_info.get('tracked_jobs', 0)}")
    
    # Summary
    print_header("DEMO COMPLETE")
    print(f"\n  ✓ Submitted {len(submitted_ids)} candidate URLs")
    print(f"  ✓ Demonstrated automatic triage based on suspicion scores")
    print(f"  ✓ Candidates are now in the database for verification")
    
    print("\n  Next Steps:")
    print("    1. High-priority candidates (score >= 0.75) are ready for deep verification")
    print("    2. Use the React frontend to view and manage candidates")
    print("    3. Trigger verification jobs for queued candidates")
    print("    4. Monitor detections via the live feed")
    
    print("\n  API Endpoints Used:")
    print(f"    - POST {API_BASE}/candidates/submit")
    print(f"    - GET {API_BASE}/candidates")
    print(f"    - GET {API_BASE}/metrics/summary")
    print(f"    - GET {API_BASE}/health")
    
    print("\n" + "=" * 80 + "\n")


if __name__ == "__main__":
    main()
