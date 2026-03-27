"""
Sentinel Dual-Mode Detection Engine
Combines video and audio fingerprinting for maximum accuracy.
"""

import os
import sys
import math
from hash_engine import VideoHashEngine
from audio_engine import AudioHashEngine
from matcher import VideoMatcher
from redis_utils import redis_manager


class DualModeEngine:
    """
    Dual-mode piracy detection using both video and audio fingerprinting.
    Provides higher confidence and catches more sophisticated piracy attempts.
    """
    
    def __init__(self, video_config=None, audio_config=None, matcher_config=None):
        """
        Initialize dual-mode engine.
        
        Args:
            video_config: Dict of VideoHashEngine parameters
            audio_config: Dict of AudioHashEngine parameters
            matcher_config: Dict of VideoMatcher parameters
        """
        # Initialize video engine with enhanced features
        video_params = video_config or {
            'frame_sample_rate': 10,
            'adaptive_sampling': True,
            'use_multi_hash': True,
            'parallel_processing': True,
            'max_workers': 4
        }
        self.video_engine = VideoHashEngine(**video_params)
        
        # Initialize audio engine
        audio_params = audio_config or {
            'sample_rate': 22050,
            'n_mels': 128,
            'hash_size': 8,
            'chunk_duration': 5
        }
        self.audio_engine = AudioHashEngine(**audio_params)
        
        # Initialize matcher
        matcher_params = matcher_config or {
            'threshold': 85.0,
            'consistency_threshold': 0.8
        }
        self.matcher = VideoMatcher(**matcher_params)
        self._local_cache = {}
        self.degraded_threshold = 74.0

    @staticmethod
    def _cache_key(video_path: str, mode: str) -> str:
        """Build a stable cache key from path, mtime and mode."""
        stat = os.stat(video_path)
        return f"engine:{mode}:{video_path}:{int(stat.st_mtime)}:{stat.st_size}"
    
    def process_video(self, video_path: str, mode: str = 'dual') -> dict:
        """
        Process video with specified mode.
        
        Args:
            video_path: Path to video file
            mode: 'video', 'audio', or 'dual'
            
        Returns:
            Dict with hashes and metadata
        """
        result = {
            'video_path': video_path,
            'mode': mode,
            'video_hashes': None,
            'audio_hashes': None,
            'video_metadata': None,
            'audio_metadata': None
        }

        cache_key = self._cache_key(video_path, mode)

        # Fast in-process fallback cache (works even when Redis server is down)
        if cache_key in self._local_cache:
            print(f"  ✓ Local cache hit: {os.path.basename(video_path)} ({mode})")
            return self._local_cache[cache_key]

        cached = redis_manager.get_cache(cache_key)
        if cached:
            print(f"  ✓ Cache hit: {os.path.basename(video_path)} ({mode})")
            self._local_cache[cache_key] = cached
            return cached
        
        if mode in ['video', 'dual']:
            print(f"  Processing video fingerprints...")
            result['video_hashes'], result['video_metadata'] = self.video_engine.hash_video(video_path)
            print(f"  ✓ Video: {len(result['video_hashes'])} hashes")
        
        if mode in ['audio', 'dual']:
            print(f"  Processing audio fingerprints...")
            result['audio_hashes'], result['audio_metadata'] = self.audio_engine.hash_audio(video_path)
            print(f"  ✓ Audio: {len(result['audio_hashes'])} hashes")

        self._local_cache[cache_key] = result
        redis_manager.set_cache(cache_key, result, ttl=3600)
        
        return result

    def _pattern_recognition_decision(
        self,
        video_confidence: float,
        audio_confidence: float,
        audio_available: bool,
    ) -> dict:
        """
        Perceptron-style decision layer for robust piracy detection.
        Uses adaptive thresholding for degraded/no-audio scenarios.
        """
        # Feature fusion
        if audio_available:
            fused_score = (video_confidence * 0.65) + (audio_confidence * 0.35)
        else:
            fused_score = video_confidence

        # Perceptron-style activation over confidence features
        z = (-55.0) + (0.9 * video_confidence) + (0.35 * audio_confidence) + (5.0 if not audio_available else 0.0)
        probability = 1.0 / (1.0 + math.exp(-0.08 * z))
        pattern_score = max(fused_score, probability * 100.0)

        adaptive_threshold = self.matcher.threshold
        reason = "primary_threshold"

        # If audio modality is unavailable, relax threshold slightly
        if not audio_available:
            adaptive_threshold = min(adaptive_threshold, 78.0)
            reason = "audio_unavailable_adaptive"

        is_match = pattern_score >= adaptive_threshold

        # Final degraded-content catch-all path
        if not is_match and video_confidence >= self.degraded_threshold:
            is_match = True
            reason = "degraded_content_lenient"

        return {
            'is_match': is_match,
            'pattern_score': pattern_score,
            'adaptive_threshold': adaptive_threshold,
            'decision_reason': reason,
            'probability': probability,
        }
    
    def detect_piracy(self, suspect_path: str, protected_path: str, mode: str = 'dual') -> dict:
        """
        Detect piracy using dual-mode verification.
        
        Args:
            suspect_path: Path to suspect video
            protected_path: Path to protected video
            mode: 'video', 'audio', or 'dual'
            
        Returns:
            Detection result with confidence scores
        """
        print(f"\n{'='*80}")
        print(f"DUAL-MODE PIRACY DETECTION")
        print(f"{'='*80}")
        print(f"Mode: {mode.upper()}")
        print(f"Suspect: {os.path.basename(suspect_path)}")
        print(f"Protected: {os.path.basename(protected_path)}")
        
        # Process both videos
        print(f"\n[1/3] Processing protected content...")
        protected = self.process_video(protected_path, mode)
        
        print(f"\n[2/3] Processing suspect content...")
        suspect = self.process_video(suspect_path, mode)
        
        print(f"\n[3/3] Analyzing matches...")
        
        result = {
            'is_match': False,
            'video_confidence': 0.0,
            'audio_confidence': 0.0,
            'combined_confidence': 0.0,
            'pattern_score': 0.0,
            'adaptive_threshold': self.matcher.threshold,
            'decision_reason': 'uninitialized',
            'mode': mode,
            'details': {}
        }
        
        # Video matching
        if mode in ['video', 'dual'] and suspect['video_hashes'] and protected['video_hashes']:
            video_result = self.matcher.match_video_sequences(
                suspect['video_hashes'],
                protected['video_hashes']
            )
            result['video_confidence'] = video_result['confidence_score']
            result['details']['video'] = video_result
            print(f"  Video confidence: {result['video_confidence']:.2f}%")
        
        # Audio matching
        if mode in ['audio', 'dual'] and suspect['audio_hashes'] and protected['audio_hashes']:
            audio_result = self.matcher.match_video_sequences(
                suspect['audio_hashes'],
                protected['audio_hashes']
            )
            result['audio_confidence'] = audio_result['confidence_score']
            result['details']['audio'] = audio_result
            print(f"  Audio confidence: {result['audio_confidence']:.2f}%")
        
        # Combined decision
        if mode == 'dual':
            # Weighted average with graceful fallback when one modality is unavailable
            video_available = suspect.get('video_hashes') and protected.get('video_hashes')
            audio_available = suspect.get('audio_hashes') and protected.get('audio_hashes')

            if video_available and audio_available:
                result['combined_confidence'] = (
                    result['video_confidence'] * 0.6 +
                    result['audio_confidence'] * 0.4
                )
            elif video_available:
                result['combined_confidence'] = result['video_confidence']
            elif audio_available:
                result['combined_confidence'] = result['audio_confidence']
            else:
                result['combined_confidence'] = 0.0

            audio_available = bool(audio_available)
            decision = self._pattern_recognition_decision(
                result['video_confidence'],
                result['audio_confidence'],
                audio_available,
            )
            result['pattern_score'] = decision['pattern_score']
            result['adaptive_threshold'] = decision['adaptive_threshold']
            result['decision_reason'] = decision['decision_reason']
            result['is_match'] = decision['is_match']
            print(f"  Combined confidence: {result['combined_confidence']:.2f}%")
            print(f"  Pattern score: {result['pattern_score']:.2f}%")
            print(f"  Adaptive threshold: {result['adaptive_threshold']:.2f}% ({result['decision_reason']})")
        elif mode == 'video':
            result['combined_confidence'] = result['video_confidence']
            decision = self._pattern_recognition_decision(
                result['video_confidence'],
                0.0,
                False,
            )
            result['pattern_score'] = decision['pattern_score']
            result['adaptive_threshold'] = decision['adaptive_threshold']
            result['decision_reason'] = decision['decision_reason']
            result['is_match'] = decision['is_match']
        elif mode == 'audio':
            result['combined_confidence'] = result['audio_confidence']
            decision = self._pattern_recognition_decision(
                0.0,
                result['audio_confidence'],
                True,
            )
            result['pattern_score'] = decision['pattern_score']
            result['adaptive_threshold'] = decision['adaptive_threshold']
            result['decision_reason'] = decision['decision_reason']
            result['is_match'] = decision['is_match']
        
        print(f"\n{'='*80}")
        if result['is_match']:
            print(f"🔴 PIRACY DETECTED - {result['combined_confidence']:.2f}% confidence")
        else:
            print(f"✅ NO MATCH - {result['combined_confidence']:.2f}% confidence")
        print(f"{'='*80}")

        # Cache detection result for dashboard/API reads
        detection_id = abs(hash((suspect_path, protected_path, mode))) % 10_000_000
        result['detection_id'] = detection_id
        redis_manager.cache_detection_result(detection_id, result, ttl=1800)
        
        return result


if __name__ == "__main__":
    print("\n" + "="*80)
    print("SENTINEL DUAL-MODE ENGINE - DEMO")
    print("="*80)
    
    # Initialize engine
    engine = DualModeEngine()
    
    # Test paths
    original = r"c:\Users\rishi\Documents\GitHub\-TeamId-_RRR_ACMNexus26\assets\videos\Race Highlights  2026 Australian Grand Prix - FORMULA 1 (720p, h264, youtube).mp4"
    pirated = r"c:\Users\rishi\Documents\GitHub\-TeamId-_RRR_ACMNexus26\assets\videos\pirated\Race Highlights  2026 Australian Grand Prix - FORMULA 1 (720p, h264, youtube)_240p.mp4"
    
    if os.path.exists(original) and os.path.exists(pirated):
        # Test dual-mode detection
        result = engine.detect_piracy(pirated, original, mode='dual')
        
        print(f"\n📊 DETAILED RESULTS:")
        print(f"  Video-only: {result['video_confidence']:.2f}%")
        print(f"  Audio-only: {result['audio_confidence']:.2f}%")
        print(f"  Dual-mode: {result['combined_confidence']:.2f}%")
        print(f"  Detection: {'✓ MATCH' if result['is_match'] else '✗ NO MATCH'}")
    else:
        print("⚠ Test videos not found")
