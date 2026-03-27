#!/usr/bin/env python3
"""
Sentinel Full Pipeline Demo

Demonstrates the COMPLETE use case:
1. User uploads protected video → Fingerprinting
2. System scans web for similar content → Discovery
3. Downloads suspicious videos → yt-dlp
4. Compares using fingerprinting → Detection
5. Returns results and generates DMCA → Action

Usage:
    python run_full_pipeline.py
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# Add backend to path
BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

from engines.discovery_engine import DiscoveryEngine
from engines.web_scanner import WebScanner
from engines.video_downloader import VideoDownloader
from generators.dmca_generator import DMCAGenerator


def run_full_pipeline():
    """Run the complete piracy detection pipeline."""
    
    print("\n" + "="*80)
    print("🛡️  SENTINEL - COMPLETE PIRACY DETECTION PIPELINE")
    print("="*80)
    print("""
This demonstrates the FULL use case you described:

  1️⃣  INGEST     → User uploads protected video, generate fingerprints
  2️⃣  SCAN       → Scrape/search web for similar content  
  3️⃣  DOWNLOAD   → Download suspicious videos (yt-dlp)
  4️⃣  COMPARE    → Fingerprint comparison
  5️⃣  ACTION     → Generate DMCA notices

""")
    
    # Setup paths
    project_root = BACKEND_DIR.parent
    protected_dir = project_root / "assets" / "videos"
    pirated_dir = project_root / "assets" / "videos" / "pirated"
    output_dir = BACKEND_DIR / "data"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results = {
        "pipeline_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "steps": {},
        "detections": [],
        "dmca_notices": [],
    }
    
    # =========================================================================
    # STEP 1: INGEST - Process Protected Content
    # =========================================================================
    print("\n" + "="*80)
    print("📁 STEP 1: INGEST - Processing Protected Content")
    print("="*80)
    
    # Initialize discovery engine (handles fingerprinting)
    discovery = DiscoveryEngine(
        protected_videos_dir=str(protected_dir),
        pirated_videos_dir=str(pirated_dir)
    )
    
    # Scan and fingerprint protected content
    protected_content = discovery.scan_protected_content()
    
    results["steps"]["ingest"] = {
        "status": "complete",
        "protected_videos": len(protected_content),
        "details": protected_content
    }
    
    if not protected_content:
        print("\n⚠️  No protected videos found!")
        print(f"   Add videos to: {protected_dir}")
        return results
    
    print(f"\n✅ Indexed {len(protected_content)} protected video(s)")
    
    # =========================================================================
    # STEP 2: SCAN - Search Web for Pirated Content
    # =========================================================================
    print("\n" + "="*80)
    print("🌐 STEP 2: SCAN - Searching Web for Pirated Content")
    print("="*80)
    
    scanner = WebScanner()
    
    # Scan for the event (using first protected video as reference)
    event_name = protected_content[0]["title"] if protected_content else "Live Sports Event"
    scan_results = scanner.scan_all_platforms(
        event_name=event_name,
        event_type="f1"  # Adjust based on content
    )
    
    results["steps"]["scan"] = {
        "status": "complete",
        "candidates_found": scan_results["total_candidates"],
        "high_risk": scan_results["summary"]["high_risk"],
        "platforms_scanned": scan_results["platforms_scanned"],
    }
    
    print(f"\n✅ Found {scan_results['total_candidates']} candidates")
    print(f"   🔴 High Risk: {scan_results['summary']['high_risk']}")
    print(f"   🟡 Medium Risk: {scan_results['summary']['medium_risk']}")
    
    # =========================================================================
    # STEP 3: DOWNLOAD - Get Suspicious Videos
    # =========================================================================
    print("\n" + "="*80)
    print("⬇️  STEP 3: DOWNLOAD - Fetching Suspicious Videos")
    print("="*80)
    
    downloader = VideoDownloader(output_dir=str(BACKEND_DIR / "temp"))
    
    print(f"\n   yt-dlp available: {'✅ Yes' if downloader.ytdlp_available else '❌ No'}")
    
    if not downloader.ytdlp_available:
        print("\n   ⚠️  yt-dlp not installed. Install with: pip install yt-dlp")
        print("   Using local pirated videos for demo instead...")
    
    # For demo, we use local pirated videos
    # In production, we would download from the discovered URLs
    downloaded_videos = []
    
    if pirated_dir.exists():
        video_extensions = ('.mp4', '.mkv', '.mov', '.avi', '.webm')
        for video_file in pirated_dir.glob('*'):
            if video_file.suffix.lower() in video_extensions:
                downloaded_videos.append({
                    "path": str(video_file),
                    "filename": video_file.name,
                    "source": "local_demo",
                    "platform": "simulated",
                })
    
    results["steps"]["download"] = {
        "status": "complete",
        "videos_downloaded": len(downloaded_videos),
        "yt_dlp_available": downloader.ytdlp_available,
    }
    
    print(f"\n✅ {len(downloaded_videos)} videos ready for verification")
    
    # =========================================================================
    # STEP 4: COMPARE - Fingerprint Matching
    # =========================================================================
    print("\n" + "="*80)
    print("🔬 STEP 4: COMPARE - Fingerprint Analysis")
    print("="*80)
    
    detections = []
    
    for video in downloaded_videos:
        print(f"\n   Analyzing: {video['filename']}")
        
        # Create a candidate dict for verification
        candidate = {
            "candidate_id": video["filename"][:8],
            "local_path": video["path"],
            "url": f"https://simulated.com/{video['filename']}",
            "platform": video["platform"],
            "filename": video["filename"],
        }
        
        # Verify against protected content
        verification = discovery.verify_candidate(candidate)
        
        if verification.get("matches"):
            for match in verification["matches"]:
                detection = {
                    "detection_id": f"DET-{len(detections)+1:04d}",
                    "suspect_video": video["filename"],
                    "protected_content": match["protected_title"],
                    "confidence": match["combined_confidence"],
                    "video_confidence": match["video_confidence"],
                    "audio_confidence": match["audio_confidence"],
                    "action": match["action"],
                    "detected_at": datetime.now().isoformat(),
                }
                detections.append(detection)
                
                icon = "🚨" if match["action"] == "auto_dmca" else "⚠️"
                print(f"   {icon} MATCH: {match['combined_confidence']:.1f}% → {match['action'].upper()}")
        else:
            print(f"   ✅ No match found")
    
    results["steps"]["compare"] = {
        "status": "complete",
        "videos_analyzed": len(downloaded_videos),
        "detections_found": len(detections),
    }
    results["detections"] = detections
    
    print(f"\n✅ Analysis complete: {len(detections)} detection(s)")
    
    # =========================================================================
    # STEP 5: ACTION - Generate DMCA Notices
    # =========================================================================
    print("\n" + "="*80)
    print("📄 STEP 5: ACTION - Generating DMCA Notices")
    print("="*80)
    
    dmca_notices = []
    notices_dir = project_root / "notices"
    notices_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        dmca_generator = DMCAGenerator(output_dir=str(notices_dir))
        
        for detection in detections:
            if detection["action"] == "auto_dmca":
                print(f"\n   Generating DMCA for: {detection['suspect_video']}")
                
                content_info = {
                    "title": detection["protected_content"],
                    "league": "Protected Content",
                }
                infringer_info = {
                    "url": f"https://pirate-site.com/{detection['suspect_video']}",
                    "confidence": detection["confidence"],
                    "timestamp": detection["detected_at"],
                }
                
                try:
                    pdf_path = dmca_generator.create_notice(
                        detection_id=detection["detection_id"],
                        content_info=content_info,
                        infringer_info=infringer_info
                    )
                    
                    dmca_notices.append({
                        "detection_id": detection["detection_id"],
                        "pdf_path": str(pdf_path),
                        "generated_at": datetime.now().isoformat(),
                    })
                    print(f"   ✅ DMCA generated: {pdf_path}")
                except Exception as e:
                    print(f"   ⚠️  DMCA generation failed: {e}")
            else:
                print(f"\n   ⏸️  {detection['suspect_video']} → Manual review required")
    
    except Exception as e:
        print(f"\n   ⚠️  DMCA generator error: {e}")
    
    results["steps"]["action"] = {
        "status": "complete",
        "dmca_notices_generated": len(dmca_notices),
    }
    results["dmca_notices"] = dmca_notices
    
    # =========================================================================
    # SUMMARY
    # =========================================================================
    print("\n" + "="*80)
    print("📊 PIPELINE SUMMARY")
    print("="*80)
    
    print(f"""
  Pipeline ID: {results['pipeline_id']}
  
  Step 1 - INGEST:   {results['steps']['ingest']['protected_videos']} protected videos indexed
  Step 2 - SCAN:     {results['steps']['scan']['candidates_found']} candidates discovered
  Step 3 - DOWNLOAD: {results['steps']['download']['videos_downloaded']} videos fetched
  Step 4 - COMPARE:  {results['steps']['compare']['detections_found']} detections found
  Step 5 - ACTION:   {results['steps']['action']['dmca_notices_generated']} DMCA notices generated
""")
    
    if detections:
        print("  🚨 DETECTIONS:")
        for d in detections:
            icon = "🔴" if d["action"] == "auto_dmca" else "🟡"
            print(f"    {icon} {d['suspect_video']}: {d['confidence']:.1f}% match")
    
    if dmca_notices:
        print("\n  📄 DMCA NOTICES:")
        for n in dmca_notices:
            print(f"    ✅ {n['pdf_path']}")
    
    print("\n" + "="*80)
    print("✅ PIPELINE COMPLETE")
    print("="*80)
    
    # Save results
    results_file = output_dir / f"pipeline_results_{results['pipeline_id']}.json"
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n📁 Results saved to: {results_file}\n")
    
    return results


if __name__ == "__main__":
    run_full_pipeline()
