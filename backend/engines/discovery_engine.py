"""
Sentinel Discovery Engine

Simulates the discovery pipeline for hackathon demonstration.
In production, this would integrate with actual platform APIs and web scrapers.

The flow:
1. Monitor keywords/events across platforms
2. Score candidates based on suspicion heuristics
3. Queue high-suspicion candidates for verification
4. Download/capture media for fingerprint comparison
5. Compare against protected content
6. Generate DMCA if match found
"""

import os
import sys
import json
import time
import uuid
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any

# Add backend to path
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from engines.hash_engine import VideoHashEngine
from engines.matcher import VideoMatcher
from engines.audio_engine import AudioHashEngine


class DiscoveryEngine:
    """
    Simulates platform discovery and candidate verification.
    
    For hackathon demo purposes, this uses local files to simulate
    what would be scraped/downloaded from streaming platforms.
    """
    
    def __init__(self, protected_videos_dir: str = None, pirated_videos_dir: str = None):
        """
        Initialize discovery engine.
        
        Args:
            protected_videos_dir: Directory containing original protected videos
            pirated_videos_dir: Directory containing suspected pirated videos (for demo)
        """
        self.protected_dir = Path(protected_videos_dir) if protected_videos_dir else None
        self.pirated_dir = Path(pirated_videos_dir) if pirated_videos_dir else None
        
        # Initialize fingerprinting engines
        self.hash_engine = VideoHashEngine(
            frame_sample_rate=10,
            adaptive_sampling=True,
            use_multi_hash=True,
            parallel_processing=True,
            max_workers=4
        )
        self.matcher = VideoMatcher(threshold=85.0, consistency_threshold=0.7)
        self.audio_engine = AudioHashEngine()
        
        # Simulated platform sources
        self.platforms = {
            "youtube": {"risk": 0.6, "downloadable": True},
            "twitch": {"risk": 0.8, "downloadable": True},
            "telegram": {"risk": 0.9, "downloadable": False},
            "facebook": {"risk": 0.5, "downloadable": True},
            "reddit": {"risk": 0.4, "downloadable": False},
            "twitter": {"risk": 0.5, "downloadable": True},
        }
        
        # Keywords that indicate potential piracy
        self.piracy_keywords = [
            "live", "stream", "free", "watch", "hd", "full",
            "720p", "1080p", "4k", "replay", "highlights",
            "f1", "formula", "premier league", "nfl", "nba",
            "ufc", "boxing", "cricket", "ipl"
        ]
        
        # Cache for protected content fingerprints
        self.protected_fingerprints = {}
        
    def scan_protected_content(self) -> List[Dict]:
        """
        Scan and fingerprint all protected content.
        Returns list of protected content with their fingerprints.
        """
        if not self.protected_dir or not self.protected_dir.exists():
            print("⚠ No protected content directory configured")
            return []
        
        protected_content = []
        video_extensions = ('.mp4', '.mkv', '.mov', '.avi', '.webm')
        
        for video_file in self.protected_dir.glob('*'):
            if video_file.suffix.lower() in video_extensions:
                print(f"\n📹 Processing protected: {video_file.name}")
                
                try:
                    # Generate fingerprints
                    video_hashes, metadata = self.hash_engine.hash_video(str(video_file))
                    audio_hash = self.audio_engine.extract_audio_hash(str(video_file))
                    
                    content_id = str(uuid.uuid4())[:8]
                    
                    self.protected_fingerprints[content_id] = {
                        "video_hashes": video_hashes,
                        "audio_hash": audio_hash,
                        "metadata": metadata,
                        "path": str(video_file),
                        "title": video_file.stem
                    }
                    
                    protected_content.append({
                        "content_id": content_id,
                        "title": video_file.stem,
                        "hash_count": len(video_hashes),
                        "duration": metadata.get("duration_seconds", 0)
                    })
                    
                    print(f"  ✓ Generated {len(video_hashes)} hashes")
                    
                except Exception as e:
                    print(f"  ✗ Error: {e}")
        
        return protected_content
    
    def simulate_platform_scan(self, keywords: List[str] = None, event_context: str = "") -> List[Dict]:
        """
        Simulate scanning platforms for potential piracy.
        
        In production, this would:
        - Use platform APIs (YouTube Data API, Twitch API, etc.)
        - Web scrape search results
        - Monitor live stream listings
        - Check social media posts
        
        For demo, we scan the pirated_videos_dir and create fake "discoveries".
        """
        if not self.pirated_dir or not self.pirated_dir.exists():
            print("⚠ No pirated videos directory configured for simulation")
            return []
        
        keywords = keywords or self.piracy_keywords[:5]
        candidates = []
        video_extensions = ('.mp4', '.mkv', '.mov', '.avi', '.webm')
        
        print(f"\n🔍 Scanning platforms for: {', '.join(keywords)}")
        print(f"   Event context: {event_context or 'General'}")
        
        for video_file in self.pirated_dir.glob('*'):
            if video_file.suffix.lower() in video_extensions:
                # Simulate discovery from different platforms
                platform = self._assign_fake_platform(video_file.name)
                
                # Calculate suspicion score
                keyword_hits = self._find_keyword_hits(video_file.name, keywords)
                suspicion_score = self._calculate_suspicion(
                    keyword_hits, event_context, platform, video_file.name
                )
                
                candidate = {
                    "candidate_id": str(uuid.uuid4())[:8],
                    "url": f"https://{platform}.com/watch/{uuid.uuid4().hex[:8]}",
                    "local_path": str(video_file),  # For demo - actual path
                    "platform": platform,
                    "keyword_hits": keyword_hits,
                    "suspicion_score": suspicion_score,
                    "discovered_at": datetime.now().isoformat(),
                    "status": self._triage_candidate(suspicion_score),
                    "filename": video_file.name
                }
                
                candidates.append(candidate)
                
                status_icon = "🔴" if suspicion_score >= 0.75 else "🟡" if suspicion_score >= 0.55 else "🟢"
                print(f"  {status_icon} Found: {video_file.name}")
                print(f"     Platform: {platform} | Score: {suspicion_score:.2f} | Status: {candidate['status']}")
        
        return candidates
    
    def verify_candidate(self, candidate: Dict) -> Dict:
        """
        Verify a candidate against all protected content.
        
        This is the core comparison step:
        1. Download/access the candidate video
        2. Generate fingerprints
        3. Compare against all protected content
        4. Return match results
        """
        print(f"\n🔬 Verifying candidate: {candidate.get('filename', candidate['url'])}")
        
        # Get video path (in demo, we use local_path; in production, we'd download)
        video_path = candidate.get("local_path")
        if not video_path or not Path(video_path).exists():
            return {
                "candidate_id": candidate["candidate_id"],
                "status": "error",
                "error": "Could not access video file",
                "matches": []
            }
        
        try:
            # Generate fingerprints for suspect video
            print("  📊 Generating fingerprints...")
            suspect_hashes, suspect_metadata = self.hash_engine.hash_video(video_path)
            suspect_audio = self.audio_engine.extract_audio_hash(video_path)
            
            print(f"  ✓ Generated {len(suspect_hashes)} hashes")
            
            # Compare against all protected content
            matches = []
            for content_id, protected in self.protected_fingerprints.items():
                print(f"  🔍 Comparing against: {protected['title']}")
                
                # Video matching
                match_result = self.matcher.match_video_sequences(
                    suspect_hashes,
                    protected["video_hashes"],
                    use_sliding_window=True
                )
                
                video_confidence = match_result["confidence_score"]
                
                # Audio matching (if available)
                audio_confidence = 0.0
                if suspect_audio and protected.get("audio_hash"):
                    # Simple audio comparison
                    audio_confidence = 50.0  # Placeholder - actual comparison would be more complex
                
                # Combined confidence
                combined_confidence = video_confidence * 0.7 + audio_confidence * 0.3
                
                # Determine if it's a match
                is_match = combined_confidence >= 75.0  # Manual review threshold
                is_auto_action = combined_confidence >= 85.0  # Auto-action threshold
                
                if is_match:
                    match_info = {
                        "protected_content_id": content_id,
                        "protected_title": protected["title"],
                        "video_confidence": round(video_confidence, 2),
                        "audio_confidence": round(audio_confidence, 2),
                        "combined_confidence": round(combined_confidence, 2),
                        "is_match": True,
                        "action": "auto_dmca" if is_auto_action else "manual_review",
                        "match_details": {
                            "best_match_position": match_result.get("best_match_position", 0),
                            "consistency_ratio": match_result.get("consistency_ratio", 0),
                            "matched_frames": match_result.get("matched_count", 0)
                        }
                    }
                    matches.append(match_info)
                    
                    action_icon = "🚨" if is_auto_action else "⚠️"
                    print(f"    {action_icon} MATCH: {combined_confidence:.2f}% confidence")
                else:
                    print(f"    ✓ No match: {combined_confidence:.2f}% confidence")
            
            return {
                "candidate_id": candidate["candidate_id"],
                "url": candidate["url"],
                "platform": candidate["platform"],
                "status": "matched" if matches else "cleared",
                "matches": matches,
                "suspect_hash_count": len(suspect_hashes),
                "verified_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "candidate_id": candidate["candidate_id"],
                "status": "error",
                "error": str(e),
                "matches": []
            }
    
    def run_full_pipeline(self, keywords: List[str] = None, event_context: str = "") -> Dict:
        """
        Run the complete discovery-to-detection pipeline.
        
        This demonstrates the full use case:
        1. Scan protected content
        2. Discover candidates from platforms
        3. Verify high-suspicion candidates
        4. Generate results for DMCA
        """
        print("\n" + "="*80)
        print("🛡️  SENTINEL DISCOVERY PIPELINE")
        print("="*80)
        
        results = {
            "pipeline_id": str(uuid.uuid4())[:8],
            "started_at": datetime.now().isoformat(),
            "protected_content": [],
            "candidates_discovered": [],
            "candidates_verified": [],
            "detections": [],
            "summary": {}
        }
        
        # Step 1: Scan protected content
        print("\n📁 STEP 1: Scanning Protected Content")
        print("-"*40)
        results["protected_content"] = self.scan_protected_content()
        print(f"\n✓ Indexed {len(results['protected_content'])} protected videos")
        
        # Step 2: Discover candidates
        print("\n🔍 STEP 2: Discovering Candidates")
        print("-"*40)
        candidates = self.simulate_platform_scan(keywords, event_context)
        results["candidates_discovered"] = candidates
        
        # Filter high-suspicion candidates
        high_suspicion = [c for c in candidates if c["suspicion_score"] >= 0.55]
        print(f"\n✓ Found {len(candidates)} candidates, {len(high_suspicion)} high-suspicion")
        
        # Step 3: Verify candidates
        print("\n🔬 STEP 3: Verifying High-Suspicion Candidates")
        print("-"*40)
        
        for candidate in high_suspicion:
            verification = self.verify_candidate(candidate)
            results["candidates_verified"].append(verification)
            
            if verification["matches"]:
                for match in verification["matches"]:
                    detection = {
                        "detection_id": str(uuid.uuid4())[:8],
                        "candidate_url": candidate["url"],
                        "platform": candidate["platform"],
                        "protected_content": match["protected_title"],
                        "confidence": match["combined_confidence"],
                        "action": match["action"],
                        "detected_at": datetime.now().isoformat()
                    }
                    results["detections"].append(detection)
        
        # Summary
        print("\n" + "="*80)
        print("📊 PIPELINE SUMMARY")
        print("="*80)
        
        results["summary"] = {
            "protected_content_count": len(results["protected_content"]),
            "candidates_discovered": len(candidates),
            "candidates_verified": len(results["candidates_verified"]),
            "detections_found": len(results["detections"]),
            "auto_dmca_count": sum(1 for d in results["detections"] if d["action"] == "auto_dmca"),
            "manual_review_count": sum(1 for d in results["detections"] if d["action"] == "manual_review"),
            "completed_at": datetime.now().isoformat()
        }
        
        print(f"\n  Protected Content: {results['summary']['protected_content_count']}")
        print(f"  Candidates Found:  {results['summary']['candidates_discovered']}")
        print(f"  Candidates Verified: {results['summary']['candidates_verified']}")
        print(f"  Detections: {results['summary']['detections_found']}")
        print(f"    - Auto DMCA: {results['summary']['auto_dmca_count']}")
        print(f"    - Manual Review: {results['summary']['manual_review_count']}")
        
        if results["detections"]:
            print("\n  🚨 DETECTIONS:")
            for d in results["detections"]:
                icon = "🔴" if d["action"] == "auto_dmca" else "🟡"
                print(f"    {icon} {d['platform']}: {d['confidence']:.1f}% match to '{d['protected_content']}'")
        
        print("\n" + "="*80)
        
        return results
    
    def _assign_fake_platform(self, filename: str) -> str:
        """Assign a fake platform based on filename patterns."""
        filename_lower = filename.lower()
        if "twitch" in filename_lower or "stream" in filename_lower:
            return "twitch"
        elif "youtube" in filename_lower or "yt" in filename_lower:
            return "youtube"
        elif "telegram" in filename_lower or "tg" in filename_lower:
            return "telegram"
        elif "fb" in filename_lower or "facebook" in filename_lower:
            return "facebook"
        else:
            # Random assignment for demo
            import random
            return random.choice(["youtube", "twitch", "telegram", "facebook"])
    
    def _find_keyword_hits(self, text: str, keywords: List[str]) -> List[str]:
        """Find which keywords appear in text."""
        text_lower = text.lower()
        return [kw for kw in keywords if kw.lower() in text_lower]
    
    def _calculate_suspicion(self, keyword_hits: List[str], event_context: str, 
                            platform: str, url: str) -> float:
        """Calculate suspicion score for a candidate."""
        score = 0.0
        
        # Keyword contribution (35%)
        if keyword_hits:
            keyword_score = min(len(keyword_hits) / 5.0, 1.0)
            score += 0.35 * keyword_score
        
        # Event context (20%)
        if event_context:
            score += 0.20
        
        # Platform risk (25%)
        platform_info = self.platforms.get(platform.lower(), {"risk": 0.5})
        score += 0.25 * platform_info["risk"]
        
        # URL patterns (20%)
        suspicious_patterns = ["live", "stream", "free", "hd", "full", "watch"]
        url_lower = url.lower()
        pattern_matches = sum(1 for p in suspicious_patterns if p in url_lower)
        score += 0.20 * min(pattern_matches / 3.0, 1.0)
        
        return min(score, 1.0)
    
    def _triage_candidate(self, score: float) -> str:
        """Determine candidate status based on suspicion score."""
        if score >= 0.75:
            return "queued"  # High priority - verify immediately
        elif score >= 0.55:
            return "watch_list"  # Medium priority - monitor
        else:
            return "discarded"  # Low priority - ignore


def demo():
    """Run a demonstration of the discovery pipeline."""
    # Default paths for the hackathon project
    project_root = Path(__file__).resolve().parent.parent.parent
    protected_dir = project_root / "assets" / "videos"
    pirated_dir = project_root / "assets" / "videos" / "pirated"
    
    print(f"\n📂 Protected videos: {protected_dir}")
    print(f"📂 Pirated videos: {pirated_dir}")
    
    if not protected_dir.exists():
        print(f"\n⚠ Protected videos directory not found: {protected_dir}")
        return
    
    # Initialize engine
    engine = DiscoveryEngine(
        protected_videos_dir=str(protected_dir),
        pirated_videos_dir=str(pirated_dir)
    )
    
    # Run full pipeline
    results = engine.run_full_pipeline(
        keywords=["f1", "formula", "race", "highlights", "live"],
        event_context="F1 2026 Australian Grand Prix"
    )
    
    # Save results
    output_file = project_root / "backend" / "data" / "discovery_results.json"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Results saved to: {output_file}")


if __name__ == "__main__":
    demo()
