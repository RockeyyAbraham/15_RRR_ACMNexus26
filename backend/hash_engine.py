import cv2
import imagehash
from PIL import Image
import numpy as np
from typing import List, Tuple
import os


class VideoHashEngine:
    """
    Core video fingerprinting engine for Sentinel.
    Handles frame extraction and perceptual hash (pHash) generation.
    """
    
    def __init__(self, frame_sample_rate: int = 10, hash_size: int = 8):
        """
        Initialize the hash engine.
        
        Args:
            frame_sample_rate: Extract hash every Nth frame (default: 10)
            hash_size: Size of the pHash matrix (default: 8 = 64-bit hash)
        """
        self.frame_sample_rate = frame_sample_rate
        self.hash_size = hash_size
    
    def extract_frames(self, video_path: str) -> List[np.ndarray]:
        """
        Extract frames from video file using OpenCV.
        
        Args:
            video_path: Path to video file
            
        Returns:
            List of frame arrays (BGR format)
            
        Raises:
            FileNotFoundError: If video file doesn't exist
            ValueError: If video cannot be opened
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            raise ValueError(f"Cannot open video file: {video_path}")
        
        frames = []
        frame_count = 0
        
        while cap.isOpened():
            ret, frame = cap.read()
            
            if not ret:
                break
            
            if frame_count % self.frame_sample_rate == 0:
                frames.append(frame)
            
            frame_count += 1
        
        cap.release()
        
        return frames
    
    def generate_phash(self, frame: np.ndarray) -> str:
        """
        Generate perceptual hash (pHash) for a single frame.
        
        Args:
            frame: Frame array in BGR format (OpenCV default)
            
        Returns:
            Hex string representation of pHash (e.g., "a3f2c1b4...")
        """
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(rgb_frame)
        phash = imagehash.phash(pil_image, hash_size=self.hash_size)
        
        return str(phash)
    
    def hash_video(self, video_path: str) -> Tuple[List[str], dict]:
        """
        Complete pipeline: Extract frames and generate pHashes.
        
        Args:
            video_path: Path to video file
            
        Returns:
            Tuple of (list of pHash strings, metadata dict)
            
        Example:
            >>> engine = VideoHashEngine()
            >>> hashes, metadata = engine.hash_video("video.mp4")
            >>> print(f"Generated {len(hashes)} hashes")
            >>> print(f"Video duration: {metadata['duration_seconds']}s")
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            raise ValueError(f"Cannot open video file: {video_path}")
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration_seconds = total_frames / fps if fps > 0 else 0
        
        cap.release()
        
        frames = self.extract_frames(video_path)
        
        hashes = []
        for frame in frames:
            phash = self.generate_phash(frame)
            hashes.append(phash)
        
        metadata = {
            'total_frames': total_frames,
            'sampled_frames': len(frames),
            'fps': fps,
            'duration_seconds': duration_seconds,
            'sample_rate': self.frame_sample_rate,
            'hash_size': self.hash_size
        }
        
        return hashes, metadata
    
    def hash_video_chunked(self, video_path: str, chunk_duration: int = 5) -> List[Tuple[List[str], float]]:
        """
        Hash video in chunks (simulates real-time processing).
        
        Args:
            video_path: Path to video file
            chunk_duration: Duration of each chunk in seconds
            
        Returns:
            List of (chunk_hashes, timestamp) tuples
            
        Example:
            >>> engine = VideoHashEngine()
            >>> chunks = engine.hash_video_chunked("stream.mp4", chunk_duration=5)
            >>> for hashes, timestamp in chunks:
            ...     print(f"Chunk at {timestamp}s: {len(hashes)} hashes")
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            raise ValueError(f"Cannot open video file: {video_path}")
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        frames_per_chunk = int(fps * chunk_duration)
        
        chunks = []
        frame_count = 0
        chunk_hashes = []
        chunk_start_time = 0.0
        
        while cap.isOpened():
            ret, frame = cap.read()
            
            if not ret:
                if chunk_hashes:
                    chunks.append((chunk_hashes, chunk_start_time))
                break
            
            if frame_count % self.frame_sample_rate == 0:
                phash = self.generate_phash(frame)
                chunk_hashes.append(phash)
            
            frame_count += 1
            
            if frame_count % frames_per_chunk == 0:
                chunks.append((chunk_hashes, chunk_start_time))
                chunk_hashes = []
                chunk_start_time = frame_count / fps
        
        cap.release()
        
        return chunks
    
    def get_video_info(self, video_path: str) -> dict:
        """
        Get video metadata without processing frames.
        
        Args:
            video_path: Path to video file
            
        Returns:
            Dictionary with video metadata
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            raise ValueError(f"Cannot open video file: {video_path}")
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration_seconds = total_frames / fps if fps > 0 else 0
        
        cap.release()
        
        return {
            'fps': fps,
            'total_frames': total_frames,
            'width': width,
            'height': height,
            'duration_seconds': duration_seconds,
            'estimated_hashes': total_frames // self.frame_sample_rate
        }


if __name__ == "__main__":
    engine = VideoHashEngine(frame_sample_rate=10, hash_size=8)
    
    print("Sentinel Video Hash Engine - Test Mode")
    print("=" * 50)
    print(f"Frame sample rate: Every {engine.frame_sample_rate}th frame")
    print(f"Hash size: {engine.hash_size}x{engine.hash_size} ({engine.hash_size**2}-bit)")
    print("=" * 50)
