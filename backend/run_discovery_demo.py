#!/usr/bin/env python3
"""
Sentinel Discovery Demo - Full Use Case Demonstration

This script demonstrates the complete piracy detection flow:
1. User uploads a protected video (fingerprinting)
2. System scans for similar content online (discovery)
3. Downloads/accesses suspicious videos
4. Compares using fingerprinting
5. Returns results and generates DMCA

Usage:
    python run_discovery_demo.py
"""

import sys
from pathlib import Path

# Add backend to path
BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

from engines.discovery_engine import DiscoveryEngine


def main():
    print("\n" + "="*80)
    print("🛡️  SENTINEL - COMPLETE USE CASE DEMONSTRATION")
    print("="*80)
    print("""
This demo shows the full piracy detection pipeline:

  1️⃣  INGEST: User uploads protected video → Generate fingerprints
  2️⃣  DISCOVER: Scan platforms for suspicious content
  3️⃣  DOWNLOAD: Access/download candidate videos
  4️⃣  COMPARE: Fingerprint comparison against protected content
  5️⃣  ACTION: Generate DMCA notices for matches

""")
    
    # Setup paths
    project_root = BACKEND_DIR.parent
    protected_dir = project_root / "assets" / "videos"
    pirated_dir = project_root / "assets" / "videos" / "pirated"
    
    # Check if directories exist
    if not protected_dir.exists():
        print(f"❌ Protected videos directory not found: {protected_dir}")
        print("\nPlease add a video file to: assets/videos/")
        return
    
    # Check for videos
    video_extensions = ('.mp4', '.mkv', '.mov', '.avi', '.webm')
    protected_videos = [f for f in protected_dir.glob('*') if f.suffix.lower() in video_extensions and f.is_file()]
    
    if not protected_videos:
        print(f"❌ No video files found in: {protected_dir}")
        print("\nPlease add a video file to demonstrate the pipeline.")
        return
    
    print(f"📂 Found {len(protected_videos)} protected video(s)")
    
    # Check for pirated videos
    if pirated_dir.exists():
        pirated_videos = [f for f in pirated_dir.glob('*') if f.suffix.lower() in video_extensions]
        print(f"📂 Found {len(pirated_videos)} candidate video(s) to verify")
    else:
        print(f"⚠️  No pirated videos directory. Creating: {pirated_dir}")
        pirated_dir.mkdir(parents=True, exist_ok=True)
        print("\nTo test the full pipeline, add suspected pirated videos to:")
        print(f"  {pirated_dir}")
        print("\nContinuing with protected content indexing only...")
    
    # Initialize discovery engine
    print("\n" + "-"*80)
    print("Initializing Discovery Engine...")
    print("-"*80)
    
    engine = DiscoveryEngine(
        protected_videos_dir=str(protected_dir),
        pirated_videos_dir=str(pirated_dir) if pirated_dir.exists() else None
    )
    
    # Run the full pipeline
    results = engine.run_full_pipeline(
        keywords=["f1", "formula", "race", "highlights", "live", "stream", "free"],
        event_context="Live Sports Event"
    )
    
    # Final summary
    print("\n" + "="*80)
    print("🎯 USE CASE DEMONSTRATION COMPLETE")
    print("="*80)
    
    if results["detections"]:
        print("\n✅ PIRACY DETECTED!")
        print("\nDetections ready for DMCA generation:")
        for d in results["detections"]:
            print(f"\n  📄 Detection ID: {d['detection_id']}")
            print(f"     Platform: {d['platform']}")
            print(f"     Confidence: {d['confidence']:.1f}%")
            print(f"     Action: {d['action'].upper()}")
            print(f"     Protected Content: {d['protected_content']}")
        
        print("\n💡 Next Steps:")
        print("   1. Review detections in the frontend dashboard")
        print("   2. Click 'Generate DMCA' for each detection")
        print("   3. Download and send DMCA notices")
    else:
        print("\n✅ No piracy detected in scanned candidates.")
        print("\n💡 To test detection:")
        print(f"   1. Add pirated video variants to: {pirated_dir}")
        print("   2. Run this demo again")
    
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    main()
