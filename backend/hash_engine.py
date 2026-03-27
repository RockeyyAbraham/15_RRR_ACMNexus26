import cv2
import imagehash
from PIL import Image
import numpy as np
from typing import List, Tuple, Dict, Optional
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import time


class VideoHashEngine:
    """
    Core video fingerprinting engine for Sentinel.
    Handles frame extraction and perceptual hash (pHash) generation.
    Enhanced with adaptive sampling, multi-hash fusion, and parallel processing.
    """
    
    def __init__(self, frame_sample_rate: int = 10, hash_size: int = 8, 
                 adaptive_sampling: bool = False, scene_threshold: float = 30.0,
                 use_multi_hash: bool = False, parallel_processing: bool = False,
                 max_workers: int = 4, auto_crop: bool = True, 
                 detect_mirroring: bool = True):
        """
        Initialize the hash engine.
        
        Args:
            frame_sample_rate: Extract hash every Nth frame (default: 10)
            hash_size: Size of the pHash matrix (default: 8 = 64-bit hash)
            adaptive_sampling: Enable scene change detection for dynamic sampling
            scene_threshold: Threshold for scene change detection (0-100)
            use_multi_hash: Generate both pHash and dHash for robustness
            parallel_processing: Enable multi-threaded hash generation
            max_workers: Number of threads for parallel processing
        """
        self.frame_sample_rate = frame_sample_rate
        self.hash_size = hash_size
        self.adaptive_sampling = adaptive_sampling
        self.scene_threshold = scene_threshold
        self.use_multi_hash = use_multi_hash
        self.parallel_processing = parallel_processing
        self.max_workers = max_workers
        self.auto_crop = auto_crop
        self.detect_mirroring = detect_mirroring
    
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
    
    def detect_scene_change(self, frame1: np.ndarray, frame2: np.ndarray) -> Tuple[bool, float]:
        """
        Detect scene change between two frames using histogram comparison.
        
        Args:
            frame1: First frame (BGR format)
            frame2: Second frame (BGR format)
            
        Returns:
            Tuple of (is_scene_change, difference_score)
        """
        gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
        
        hist1 = cv2.calcHist([gray1], [0], None, [256], [0, 256])
        hist2 = cv2.calcHist([gray2], [0], None, [256], [0, 256])
        
        hist1 = cv2.normalize(hist1, hist1).flatten()
        hist2 = cv2.normalize(hist2, hist2).flatten()
        
        correlation = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
        difference_score = (1 - correlation) * 100
        
        is_scene_change = difference_score > self.scene_threshold
        
        return is_scene_change, difference_score
    
    def get_autocrop_rect(self, frame: np.ndarray) -> Tuple[int, int, int, int]:
        """
        Detect the content rectangle by removing black borders (letterboxing).
        
        Args:
            frame: BGR frame array
            
        Returns:
            Tuple of (x, y, w, h)
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 10, 255, cv2.THRESH_BINARY)
        coords = cv2.findNonZero(thresh)
        if coords is not None:
            x, y, w, h = cv2.boundingRect(coords)
            return x, y, w, h
        return 0, 0, frame.shape[1], frame.shape[0]

    def _prepare_frame(self, frame: np.ndarray) -> Image.Image:
        """Apply auto-crop and convert to PIL Image."""
        if self.auto_crop:
            x, y, w, h = self.get_autocrop_rect(frame)
            frame = frame[y:y+h, x:x+w]
        
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return Image.fromarray(rgb_frame)

    def generate_phash(self, frame: np.ndarray) -> str:
        """
        Generate perceptual hash (pHash) for a single frame.
        Supports mirroring if self.detect_mirroring is True.
        """
        img = self._prepare_frame(frame)
        phash = imagehash.phash(img, hash_size=self.hash_size)
        
        if self.detect_mirroring:
            flipped_img = img.transpose(Image.FLIP_LEFT_RIGHT)
            flipped_phash = imagehash.phash(flipped_img, hash_size=self.hash_size)
            return f"{phash}m{flipped_phash}"
        
        return str(phash)
    
    def generate_dhash(self, frame: np.ndarray) -> str:
        """
        Generate difference hash (dHash) for a single frame.
        """
        img = self._prepare_frame(frame)
        dhash = imagehash.dhash(img, hash_size=self.hash_size)
        
        if self.detect_mirroring:
            flipped_img = img.transpose(Image.FLIP_LEFT_RIGHT)
            flipped_dhash = imagehash.dhash(flipped_img, hash_size=self.hash_size)
            return f"{dhash}m{flipped_dhash}"
            
        return str(dhash)
    
    def generate_fused_hash(self, frame: np.ndarray) -> Dict[str, str]:
        """
        Generate multiple hash types and fuse them for robustness.
        
        Args:
            frame: Frame array in BGR format
            
        Returns:
            Dictionary with 'phash', 'dhash', and 'fused' keys
        """
        phash = self.generate_phash(frame)
        dhash = self.generate_dhash(frame)
        
        fused = f"{phash}:{dhash}"
        
        return {
            'phash': phash,
            'dhash': dhash,
            'fused': fused
        }
    
    def _hash_frame_worker(self, frame_data: Tuple[int, np.ndarray]) -> Tuple[int, str]:
        """
        Worker function for parallel hash generation.
        
        Args:
            frame_data: Tuple of (frame_index, frame_array)
            
        Returns:
            Tuple of (frame_index, hash_string)
        """
        idx, frame = frame_data
        if self.use_multi_hash:
            hash_result = self.generate_fused_hash(frame)['fused']
        else:
            hash_result = self.generate_phash(frame)
        return idx, hash_result
    
    def hash_video(self, video_path: str) -> Tuple[List[str], dict]:
        """
        Complete pipeline: Extract frames and generate pHashes.
        Enhanced with adaptive sampling and parallel processing.
        
        Args:
            video_path: Path to video file
            
        Returns:
            Tuple of (list of pHash strings, metadata dict)
            
        Example:
            >>> engine = VideoHashEngine(adaptive_sampling=True, parallel_processing=True)
            >>> hashes, metadata = engine.hash_video("video.mp4")
            >>> print(f"Generated {len(hashes)} hashes")
            >>> print(f"Video duration: {metadata['duration_seconds']}s")
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        start_time = time.time()
        
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            raise ValueError(f"Cannot open video file: {video_path}")
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration_seconds = total_frames / fps if fps > 0 else 0
        
        frames = []
        frame_count = 0
        prev_frame = None
        scene_changes = 0
        
        while cap.isOpened():
            ret, frame = cap.read()
            
            if not ret:
                break
            
            should_sample = False
            
            if self.adaptive_sampling and prev_frame is not None:
                is_scene_change, diff_score = self.detect_scene_change(prev_frame, frame)
                if is_scene_change:
                    should_sample = True
                    scene_changes += 1
                elif frame_count % self.frame_sample_rate == 0:
                    should_sample = True
            else:
                if frame_count % self.frame_sample_rate == 0:
                    should_sample = True
            
            if should_sample:
                frames.append(frame.copy())
            
            prev_frame = frame
            frame_count += 1
        
        cap.release()
        
        if self.parallel_processing and len(frames) > 10:
            hashes = self._hash_frames_parallel(frames)
        else:
            hashes = []
            for frame in frames:
                if self.use_multi_hash:
                    hash_result = self.generate_fused_hash(frame)['fused']
                else:
                    hash_result = self.generate_phash(frame)
                hashes.append(hash_result)
        
        processing_time = time.time() - start_time
        
        metadata = {
            'total_frames': total_frames,
            'sampled_frames': len(frames),
            'fps': fps,
            'duration_seconds': duration_seconds,
            'sample_rate': self.frame_sample_rate,
            'hash_size': self.hash_size,
            'adaptive_sampling': self.adaptive_sampling,
            'scene_changes_detected': scene_changes if self.adaptive_sampling else 0,
            'multi_hash': self.use_multi_hash,
            'parallel_processing': self.parallel_processing,
            'processing_time_seconds': processing_time
        }
        
        return hashes, metadata
    
    def _hash_frames_parallel(self, frames: List[np.ndarray]) -> List[str]:
        """
        Hash frames in parallel using ThreadPoolExecutor.
        
        Args:
            frames: List of frame arrays
            
        Returns:
            List of hash strings in original order
        """
        frame_data = [(i, frame) for i, frame in enumerate(frames)]
        results = {}
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(self._hash_frame_worker, data): data[0] 
                      for data in frame_data}
            
            for future in as_completed(futures):
                idx, hash_str = future.result()
                results[idx] = hash_str
        
        hashes = [results[i] for i in sorted(results.keys())]
        return hashes
    
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
