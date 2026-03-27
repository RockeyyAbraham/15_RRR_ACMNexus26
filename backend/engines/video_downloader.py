"""
Sentinel Video Downloader

Downloads videos from various platforms using yt-dlp.
Supports: YouTube, Twitch, Facebook, Twitter, Reddit, and 1000+ other sites.

This fixes Gap #3: "Download similar video from streaming platforms"
"""

import os
import sys
import uuid
import subprocess
import shutil
from pathlib import Path
from typing import Optional, Dict, Tuple
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)

# Supported platforms and their patterns
PLATFORM_PATTERNS = {
    "youtube": ["youtube.com", "youtu.be", "youtube-nocookie.com"],
    "twitch": ["twitch.tv", "clips.twitch.tv"],
    "facebook": ["facebook.com", "fb.watch", "fb.com"],
    "twitter": ["twitter.com", "x.com", "t.co"],
    "reddit": ["reddit.com", "v.redd.it", "i.redd.it"],
    "tiktok": ["tiktok.com", "vm.tiktok.com"],
    "instagram": ["instagram.com", "instagr.am"],
    "vimeo": ["vimeo.com"],
    "dailymotion": ["dailymotion.com", "dai.ly"],
    "streamable": ["streamable.com"],
    "telegram": ["t.me", "telegram.me"],
}

# Direct video extensions
DIRECT_VIDEO_EXTENSIONS = (".mp4", ".mov", ".mkv", ".webm", ".m4v", ".avi", ".flv")


class VideoDownloader:
    """
    Downloads videos from streaming platforms and direct URLs.
    Uses yt-dlp for platform support.
    """
    
    def __init__(self, output_dir: str = None, max_duration: int = 3600):
        """
        Initialize video downloader.
        
        Args:
            output_dir: Directory to save downloaded videos
            max_duration: Maximum video duration in seconds (default: 1 hour)
        """
        self.output_dir = Path(output_dir) if output_dir else Path(__file__).parent.parent / "temp"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.max_duration = max_duration
        
        # Check if yt-dlp is available
        self.ytdlp_available = self._check_ytdlp()
        
    def _check_ytdlp(self) -> bool:
        """Check if yt-dlp is installed and accessible."""
        try:
            result = subprocess.run(
                ["yt-dlp", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                logger.info(f"yt-dlp version: {result.stdout.strip()}")
                return True
        except FileNotFoundError:
            logger.warning("yt-dlp not found in PATH")
        except subprocess.TimeoutExpired:
            logger.warning("yt-dlp check timed out")
        except Exception as e:
            logger.warning(f"yt-dlp check failed: {e}")
        
        return False
    
    def identify_platform(self, url: str) -> Optional[str]:
        """
        Identify which platform a URL belongs to.
        
        Args:
            url: The URL to check
            
        Returns:
            Platform name or None if unknown
        """
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower().replace("www.", "")
            
            for platform, patterns in PLATFORM_PATTERNS.items():
                for pattern in patterns:
                    if pattern in domain:
                        return platform
            
            # Check if it's a direct video URL
            if parsed.path.lower().endswith(DIRECT_VIDEO_EXTENSIONS):
                return "direct"
            
            return "unknown"
        except Exception:
            return None
    
    def download(self, url: str, filename: str = None) -> Tuple[Optional[Path], Dict]:
        """
        Download video from URL.
        
        Args:
            url: URL to download from
            filename: Optional custom filename (without extension)
            
        Returns:
            Tuple of (path to downloaded file or None, metadata dict)
        """
        metadata = {
            "url": url,
            "platform": self.identify_platform(url),
            "success": False,
            "error": None,
            "method": None,
            "duration": None,
            "title": None,
        }
        
        # Generate filename if not provided
        if not filename:
            filename = f"download_{uuid.uuid4().hex[:8]}"
        
        # Try different download methods
        
        # Method 1: Direct download for direct video URLs
        if metadata["platform"] == "direct":
            result = self._download_direct(url, filename)
            if result:
                metadata["success"] = True
                metadata["method"] = "direct"
                return result, metadata
        
        # Method 2: yt-dlp for streaming platforms
        if self.ytdlp_available:
            result, ytdlp_meta = self._download_ytdlp(url, filename)
            if result:
                metadata["success"] = True
                metadata["method"] = "yt-dlp"
                metadata["duration"] = ytdlp_meta.get("duration")
                metadata["title"] = ytdlp_meta.get("title")
                return result, metadata
            else:
                metadata["error"] = ytdlp_meta.get("error", "yt-dlp download failed")
        else:
            metadata["error"] = "yt-dlp not installed. Install with: pip install yt-dlp"
        
        # Method 3: Fallback to direct download for any URL
        result = self._download_direct(url, filename)
        if result:
            metadata["success"] = True
            metadata["method"] = "direct_fallback"
            return result, metadata
        
        return None, metadata
    
    def _download_direct(self, url: str, filename: str) -> Optional[Path]:
        """
        Download video directly via HTTP.
        
        Args:
            url: Direct video URL
            filename: Base filename
            
        Returns:
            Path to downloaded file or None
        """
        try:
            import requests
        except ImportError:
            logger.error("requests library not available")
            return None
        
        try:
            # Get file extension from URL
            parsed = urlparse(url)
            ext = Path(parsed.path).suffix.lower()
            if ext not in DIRECT_VIDEO_EXTENSIONS:
                ext = ".mp4"
            
            output_path = self.output_dir / f"{filename}{ext}"
            
            # Download with streaming
            response = requests.get(url, stream=True, timeout=60)
            response.raise_for_status()
            
            # Check content type
            content_type = response.headers.get("Content-Type", "")
            if "video" not in content_type and "octet-stream" not in content_type:
                logger.warning(f"Unexpected content type: {content_type}")
            
            # Write to file
            with open(output_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            # Verify file was created and has content
            if output_path.exists() and output_path.stat().st_size > 0:
                logger.info(f"Direct download successful: {output_path}")
                return output_path
            
        except Exception as e:
            logger.error(f"Direct download failed: {e}")
        
        return None
    
    def _download_ytdlp(self, url: str, filename: str) -> Tuple[Optional[Path], Dict]:
        """
        Download video using yt-dlp.
        
        Args:
            url: Video URL
            filename: Base filename
            
        Returns:
            Tuple of (path to downloaded file or None, metadata dict)
        """
        output_template = str(self.output_dir / f"{filename}.%(ext)s")
        
        # yt-dlp command with optimal settings for fingerprinting
        cmd = [
            "yt-dlp",
            "--no-playlist",  # Don't download playlists
            "--max-filesize", "500M",  # Limit file size
            "--format", "best[height<=720]/best",  # 720p max for faster processing
            "--output", output_template,
            "--no-warnings",
            "--quiet",
            "--print-json",  # Output metadata as JSON
            url
        ]
        
        # Add duration limit if set
        if self.max_duration:
            cmd.extend(["--match-filter", f"duration<={self.max_duration}"])
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                # Parse metadata from JSON output
                import json
                try:
                    metadata = json.loads(result.stdout.strip().split('\n')[-1])
                    downloaded_file = metadata.get("_filename") or metadata.get("filename")
                    
                    if downloaded_file and Path(downloaded_file).exists():
                        return Path(downloaded_file), {
                            "title": metadata.get("title"),
                            "duration": metadata.get("duration"),
                            "uploader": metadata.get("uploader"),
                            "view_count": metadata.get("view_count"),
                        }
                except json.JSONDecodeError:
                    pass
                
                # Fallback: find the downloaded file
                for ext in [".mp4", ".webm", ".mkv", ".m4v"]:
                    potential_file = self.output_dir / f"{filename}{ext}"
                    if potential_file.exists():
                        return potential_file, {}
            
            return None, {"error": result.stderr or "Download failed"}
            
        except subprocess.TimeoutExpired:
            return None, {"error": "Download timed out (5 minutes)"}
        except Exception as e:
            return None, {"error": str(e)}
    
    def cleanup(self, file_path: Path):
        """Remove a downloaded file."""
        try:
            if file_path and file_path.exists():
                file_path.unlink()
                logger.info(f"Cleaned up: {file_path}")
        except Exception as e:
            logger.warning(f"Cleanup failed: {e}")


def install_ytdlp():
    """Install yt-dlp using pip."""
    print("Installing yt-dlp...")
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-U", "yt-dlp"],
            check=True
        )
        print("✓ yt-dlp installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install yt-dlp: {e}")
        return False


def demo():
    """Demonstrate the video downloader."""
    print("\n" + "="*80)
    print("🎬 SENTINEL VIDEO DOWNLOADER - DEMO")
    print("="*80)
    
    downloader = VideoDownloader()
    
    print(f"\n📂 Output directory: {downloader.output_dir}")
    print(f"🔧 yt-dlp available: {'✓ Yes' if downloader.ytdlp_available else '✗ No'}")
    
    if not downloader.ytdlp_available:
        print("\n⚠️  yt-dlp is not installed.")
        print("   To enable platform downloads, run:")
        print("   pip install yt-dlp")
        print("\n   Or run this script with --install flag:")
        print("   python video_downloader.py --install")
    
    # Test platform identification
    test_urls = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://twitch.tv/clips/example",
        "https://twitter.com/user/status/123456",
        "https://example.com/video.mp4",
        "https://reddit.com/r/videos/comments/abc123",
    ]
    
    print("\n📋 Platform Identification Test:")
    for url in test_urls:
        platform = downloader.identify_platform(url)
        print(f"   {platform:12} ← {url[:50]}...")
    
    print("\n" + "="*80)
    print("To download a video, use:")
    print("   from engines.video_downloader import VideoDownloader")
    print("   downloader = VideoDownloader()")
    print("   path, meta = downloader.download('https://youtube.com/watch?v=...')")
    print("="*80 + "\n")


if __name__ == "__main__":
    if "--install" in sys.argv:
        install_ytdlp()
    else:
        demo()
