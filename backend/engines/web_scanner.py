"""
Sentinel Web Scanner

Simulates web scraping for piracy detection.
In production, this would integrate with actual search APIs and web scrapers.

This fixes Gap #2: "Scrape sources online for similar instances"
"""

import os
import sys
import json
import time
import uuid
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
from urllib.parse import urlparse, quote_plus
import logging

logger = logging.getLogger(__name__)

# Add backend to path
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))


class WebScanner:
    """
    Scans the web for potential piracy candidates.
    
    For hackathon demo, this simulates what production scrapers would do.
    In production, integrate with:
    - YouTube Data API
    - Twitch API
    - Twitter/X API
    - Google Custom Search API
    - Web scraping with Selenium/Playwright
    """
    
    def __init__(self):
        """Initialize web scanner."""
        self.platforms = {
            "youtube": {
                "search_url": "https://www.youtube.com/results?search_query=",
                "api_available": False,  # Would be True with API key
                "risk_level": 0.6,
            },
            "twitch": {
                "search_url": "https://www.twitch.tv/search?term=",
                "api_available": False,
                "risk_level": 0.8,
            },
            "twitter": {
                "search_url": "https://twitter.com/search?q=",
                "api_available": False,
                "risk_level": 0.5,
            },
            "reddit": {
                "search_url": "https://www.reddit.com/search/?q=",
                "api_available": True,  # Reddit API is free
                "risk_level": 0.4,
            },
            "facebook": {
                "search_url": "https://www.facebook.com/search/videos/?q=",
                "api_available": False,
                "risk_level": 0.5,
            },
        }
        
        # Piracy indicator keywords
        self.piracy_keywords = {
            "high_risk": ["free stream", "live free", "watch free", "full match", "hd stream"],
            "medium_risk": ["live", "stream", "watch", "replay", "highlights"],
            "low_risk": ["discussion", "analysis", "review", "reaction"],
        }
        
        # Event-specific keywords (would be dynamic in production)
        self.event_keywords = {
            "f1": ["formula 1", "f1", "grand prix", "gp", "race"],
            "football": ["premier league", "champions league", "world cup", "match"],
            "ufc": ["ufc", "mma", "fight", "ppv"],
            "cricket": ["ipl", "cricket", "t20", "test match"],
        }
    
    def generate_search_queries(self, event_name: str, event_type: str = "f1") -> List[str]:
        """
        Generate search queries for finding pirated content.
        
        Args:
            event_name: Name of the event (e.g., "Australian Grand Prix")
            event_type: Type of event for keyword selection
            
        Returns:
            List of search queries
        """
        queries = []
        
        # Get event-specific keywords
        event_kw = self.event_keywords.get(event_type, [])
        
        # Combine with piracy indicators
        for risk_level, indicators in self.piracy_keywords.items():
            for indicator in indicators:
                for kw in event_kw[:3]:  # Limit combinations
                    queries.append(f"{event_name} {indicator}")
                    queries.append(f"{kw} {indicator}")
        
        # Add direct event searches
        queries.append(event_name)
        queries.append(f"{event_name} live")
        queries.append(f"{event_name} stream")
        
        return list(set(queries))[:20]  # Limit to 20 unique queries
    
    def scan_platform(self, platform: str, query: str, max_results: int = 10) -> List[Dict]:
        """
        Scan a platform for potential piracy candidates.
        
        In production, this would:
        - Use platform APIs where available
        - Web scrape search results
        - Parse video metadata
        
        For demo, returns simulated results.
        
        Args:
            platform: Platform to scan
            query: Search query
            max_results: Maximum results to return
            
        Returns:
            List of candidate dictionaries
        """
        if platform not in self.platforms:
            return []
        
        platform_info = self.platforms[platform]
        candidates = []
        
        # In production, this would make actual API calls or scrape
        # For demo, we simulate finding results
        
        # Simulate finding 0-3 results per query
        import random
        num_results = random.randint(0, min(3, max_results))
        
        for i in range(num_results):
            # Generate fake but realistic-looking result
            video_id = uuid.uuid4().hex[:11]
            
            candidate = {
                "candidate_id": str(uuid.uuid4())[:8],
                "url": self._generate_platform_url(platform, video_id),
                "platform": platform,
                "title": self._generate_fake_title(query),
                "query_matched": query,
                "discovered_at": datetime.now().isoformat(),
                "metadata": {
                    "views": random.randint(100, 100000),
                    "upload_time": "Live" if "live" in query.lower() else f"{random.randint(1, 24)} hours ago",
                    "duration": f"{random.randint(1, 180)} min" if "live" not in query.lower() else "LIVE",
                },
                "risk_indicators": self._analyze_risk(query, platform),
            }
            
            # Calculate suspicion score
            candidate["suspicion_score"] = self._calculate_suspicion(candidate)
            
            candidates.append(candidate)
        
        return candidates
    
    def scan_all_platforms(self, event_name: str, event_type: str = "f1") -> Dict:
        """
        Scan all platforms for potential piracy.
        
        Args:
            event_name: Name of the event
            event_type: Type of event
            
        Returns:
            Scan results with candidates from all platforms
        """
        print(f"\n🔍 Scanning for: {event_name}")
        print(f"   Event type: {event_type}")
        
        queries = self.generate_search_queries(event_name, event_type)
        print(f"   Generated {len(queries)} search queries")
        
        all_candidates = []
        platform_stats = {}
        
        for platform in self.platforms:
            print(f"\n   📡 Scanning {platform}...")
            platform_candidates = []
            
            for query in queries[:5]:  # Limit queries per platform for demo
                results = self.scan_platform(platform, query, max_results=3)
                platform_candidates.extend(results)
                time.sleep(0.1)  # Simulate rate limiting
            
            # Deduplicate by URL
            seen_urls = set()
            unique_candidates = []
            for c in platform_candidates:
                if c["url"] not in seen_urls:
                    seen_urls.add(c["url"])
                    unique_candidates.append(c)
            
            platform_stats[platform] = len(unique_candidates)
            all_candidates.extend(unique_candidates)
            print(f"      Found {len(unique_candidates)} candidates")
        
        # Sort by suspicion score
        all_candidates.sort(key=lambda x: x["suspicion_score"], reverse=True)
        
        # Categorize by risk
        high_risk = [c for c in all_candidates if c["suspicion_score"] >= 0.75]
        medium_risk = [c for c in all_candidates if 0.55 <= c["suspicion_score"] < 0.75]
        low_risk = [c for c in all_candidates if c["suspicion_score"] < 0.55]
        
        return {
            "scan_id": str(uuid.uuid4())[:8],
            "event_name": event_name,
            "event_type": event_type,
            "scanned_at": datetime.now().isoformat(),
            "queries_used": len(queries),
            "platforms_scanned": list(self.platforms.keys()),
            "platform_stats": platform_stats,
            "total_candidates": len(all_candidates),
            "candidates": all_candidates,
            "summary": {
                "high_risk": len(high_risk),
                "medium_risk": len(medium_risk),
                "low_risk": len(low_risk),
            },
            "high_risk_candidates": high_risk,
        }
    
    def _generate_platform_url(self, platform: str, video_id: str) -> str:
        """Generate a realistic-looking platform URL."""
        urls = {
            "youtube": f"https://www.youtube.com/watch?v={video_id}",
            "twitch": f"https://www.twitch.tv/videos/{video_id}",
            "twitter": f"https://twitter.com/user/status/{video_id}",
            "reddit": f"https://www.reddit.com/r/sports/comments/{video_id}",
            "facebook": f"https://www.facebook.com/watch/?v={video_id}",
        }
        return urls.get(platform, f"https://{platform}.com/video/{video_id}")
    
    def _generate_fake_title(self, query: str) -> str:
        """Generate a realistic-looking video title based on query."""
        templates = [
            f"🔴 LIVE: {query.title()} - Watch Now!",
            f"{query.title()} Full HD Stream",
            f"[FREE] {query.title()} - Live Coverage",
            f"{query.title()} Highlights & Replay",
            f"Watch {query.title()} Online Free",
        ]
        import random
        return random.choice(templates)
    
    def _analyze_risk(self, query: str, platform: str) -> List[str]:
        """Analyze risk indicators in a query."""
        indicators = []
        query_lower = query.lower()
        
        for risk_level, keywords in self.piracy_keywords.items():
            for kw in keywords:
                if kw in query_lower:
                    indicators.append(f"{risk_level}: '{kw}'")
        
        # Platform-specific risks
        if platform in ["telegram", "twitch"]:
            indicators.append("high_risk_platform")
        
        return indicators
    
    def _calculate_suspicion(self, candidate: Dict) -> float:
        """Calculate suspicion score for a candidate."""
        score = 0.0
        
        # Risk indicators contribution
        indicators = candidate.get("risk_indicators", [])
        high_risk_count = sum(1 for i in indicators if "high_risk" in i)
        medium_risk_count = sum(1 for i in indicators if "medium_risk" in i)
        
        score += 0.3 * min(high_risk_count / 2, 1.0)
        score += 0.15 * min(medium_risk_count / 3, 1.0)
        
        # Platform risk
        platform = candidate.get("platform", "")
        platform_risks = {"telegram": 0.9, "twitch": 0.7, "youtube": 0.5, "facebook": 0.5, "reddit": 0.4}
        score += 0.25 * platform_risks.get(platform, 0.5)
        
        # Title analysis
        title = candidate.get("title", "").lower()
        if any(kw in title for kw in ["free", "live", "stream", "watch"]):
            score += 0.2
        
        # Metadata analysis
        metadata = candidate.get("metadata", {})
        if metadata.get("duration") == "LIVE":
            score += 0.1
        
        return min(score, 1.0)


def demo():
    """Demonstrate the web scanner."""
    print("\n" + "="*80)
    print("🌐 SENTINEL WEB SCANNER - DEMO")
    print("="*80)
    print("""
This demonstrates how Sentinel would scan the web for pirated content.

In production, this would:
  - Use YouTube Data API, Twitch API, etc.
  - Web scrape search results
  - Monitor live stream listings
  - Track social media posts

For demo, we simulate the discovery process.
""")
    
    scanner = WebScanner()
    
    # Scan for a sample event
    results = scanner.scan_all_platforms(
        event_name="F1 Australian Grand Prix 2026",
        event_type="f1"
    )
    
    print("\n" + "="*80)
    print("📊 SCAN RESULTS")
    print("="*80)
    
    print(f"\n  Scan ID: {results['scan_id']}")
    print(f"  Event: {results['event_name']}")
    print(f"  Queries used: {results['queries_used']}")
    print(f"  Total candidates: {results['total_candidates']}")
    
    print(f"\n  Risk Summary:")
    print(f"    🔴 High Risk: {results['summary']['high_risk']}")
    print(f"    🟡 Medium Risk: {results['summary']['medium_risk']}")
    print(f"    🟢 Low Risk: {results['summary']['low_risk']}")
    
    if results['high_risk_candidates']:
        print(f"\n  🚨 HIGH RISK CANDIDATES:")
        for c in results['high_risk_candidates'][:5]:
            print(f"\n    URL: {c['url']}")
            print(f"    Title: {c['title'][:50]}...")
            print(f"    Score: {c['suspicion_score']:.2f}")
            print(f"    Indicators: {', '.join(c['risk_indicators'][:3])}")
    
    print("\n" + "="*80)
    print("These candidates would be sent to the verification pipeline.")
    print("="*80 + "\n")
    
    return results


if __name__ == "__main__":
    demo()
