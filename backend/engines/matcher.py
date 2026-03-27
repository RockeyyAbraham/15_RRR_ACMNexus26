import imagehash
from typing import List, Tuple, Dict, Optional
import json
import numpy as np
from collections import deque


class VideoMatcher:
    """
    Matching engine for comparing video fingerprints.
    Uses Hamming distance to calculate similarity between pHashes.
    Enhanced with sliding window matching and statistical confidence scoring.
    """
    
    def __init__(self, threshold: float = 85.0, hash_size: int = 8,
                 window_size: int = 5, consistency_threshold: float = 0.8):
        """
        Initialize the matcher.
        
        Args:
            threshold: Minimum similarity percentage to consider a match (default: 85%)
            hash_size: Size of the pHash matrix (default: 8 = 64-bit hash)
            window_size: Size of sliding window for temporal matching (default: 5)
            consistency_threshold: Minimum consistency ratio for statistical confidence (default: 0.8)
        """
        self.threshold = threshold
        self.hash_size = hash_size
        self.max_distance = hash_size ** 2
        self.window_size = window_size
        self.consistency_threshold = consistency_threshold
    
    def compare_hashes(self, hash1: str, hash2: str) -> Tuple[bool, float]:
        """
        Compare two pHashes using Hamming distance.
        Supports both single hashes and fused hashes (phash:dhash format).
        
        Args:
            hash1: First pHash as hex string (e.g., "a3f2c1b4..." or "phash:dhash")
            hash2: Second pHash as hex string
            
        Returns:
            Tuple of (is_match, similarity_percentage)
            
        Example:
            >>> matcher = VideoMatcher(threshold=85.0)
            >>> is_match, score = matcher.compare_hashes("a3f2c1b4", "a3f2c1b5")
            >>> print(f"Match: {is_match}, Similarity: {score:.2f}%")
        """
        try:
            # Check if hashes are fused (phash:dhash format)
            if ':' in hash1 and ':' in hash2:
                parts1 = hash1.split(':')
                parts2 = hash2.split(':')
                
                # Compare both phash and dhash
                _, phash_sim = self._compare_single_hash(parts1[0], parts2[0])
                _, dhash_sim = self._compare_single_hash(parts1[1], parts2[1])
                
                # Average similarity
                similarity = (phash_sim + dhash_sim) / 2
            else:
                _, similarity = self._compare_single_hash(hash1, hash2)
            
            is_match = similarity >= self.threshold
            
            return is_match, similarity
            
        except Exception as e:
            raise ValueError(f"Error comparing hashes: {e}")
    
    def _compare_single_hash(self, hash1: str, hash2: str) -> Tuple[bool, float]:
        """
        Compare two single hashes using Hamming distance.
        Supports mirrored hashes (format: "hashmflipped_hash").
        
        Args:
            hash1: First hash (suspect)
            hash2: Second hash (protected)
            
        Returns:
            Tuple of (is_match, similarity_percentage)
        """
        # If protected hash (hash2) has a mirrored version, compare against both
        if 'm' in hash2:
            p_normal, p_flipped = hash2.split('m')
            
            # Compare suspect (hash1) against normal
            _, sim_normal = self._compare_calculation(hash1, p_normal)
            
            # Compare suspect (hash1) against flipped
            _, sim_flipped = self._compare_calculation(hash1, p_flipped)
            
            similarity = max(sim_normal, sim_flipped)
        else:
            _, similarity = self._compare_calculation(hash1, hash2)
            
        is_match = similarity >= self.threshold
        return is_match, similarity

    def _compare_calculation(self, hash1: str, hash2: str) -> Tuple[bool, float]:
        """Core Hamming distance calculation."""
        # Strip mirror info from suspect if present (for symmetry)
        h1_str = hash1.split('m')[0] if 'm' in hash1 else hash1
        
        try:
            # Try imagehash format (video hashes)
            h1 = imagehash.hex_to_hash(h1_str)
            h2 = imagehash.hex_to_hash(hash2)
            
            distance = h1 - h2
            similarity = (1 - (distance / self.max_distance)) * 100
            return True, similarity
            
        except (ValueError, TypeError) as e:
            # Handle non-imagehash formats (audio hashes)
            try:
                # For audio hashes, use string similarity
                if len(h1_str) != len(hash2):
                    # Different lengths - normalize
                    min_len = min(len(h1_str), len(hash2))
                    h1_str = h1_str[:min_len]
                    hash2 = hash2[:min_len]
                
                # Simple character-by-character similarity
                matches = sum(c1 == c2 for c1, c2 in zip(h1_str, hash2))
                similarity = (matches / len(h1_str)) * 100
                return True, similarity
                
            except Exception as e2:
                print(f"Hash comparison failed: {e2}")
                return False, 0.0
    
    def match_video_sequences(self, suspect_hashes: List[str], protected_hashes: List[str], 
                              use_sliding_window: bool = False) -> Dict:
        """
        Match a suspect video sequence against a protected video sequence.
        
        Args:
            suspect_hashes: List of pHashes from suspect video
            protected_hashes: List of pHashes from protected video
            use_sliding_window: If True, uses sliding window for suspect clips
            
        Returns:
            Dictionary with match results
        """
        if use_sliding_window and len(suspect_hashes) < len(protected_hashes) * 0.8:
            return self.sliding_window_match(suspect_hashes, protected_hashes)

        if not suspect_hashes or not protected_hashes:
            return {
                'is_match': False,
                'confidence_score': 0.0,
                'matches': 0,
                'total_comparisons': 0,
                'match_percentage': 0.0,
                'best_similarity': 0.0,
                'worst_similarity': 0.0,
                'average_similarity': 0.0
            }
        
        matches = 0
        total_comparisons = len(suspect_hashes)
        similarities = []
        
        for suspect_hash in suspect_hashes:
            best_match_for_frame = 0.0
            
            for protected_hash in protected_hashes:
                is_match, similarity = self.compare_hashes(suspect_hash, protected_hash)
                
                if similarity > best_match_for_frame:
                    best_match_for_frame = similarity
                
                if is_match:
                    matches += 1
                    break
            
            similarities.append(best_match_for_frame)
        
        match_percentage = (matches / total_comparisons) * 100 if total_comparisons > 0 else 0
        
        average_similarity = sum(similarities) / len(similarities) if similarities else 0
        best_similarity = max(similarities) if similarities else 0
        worst_similarity = min(similarities) if similarities else 0
        
        confidence_score = average_similarity
        
        is_match = confidence_score >= self.threshold
        
        return {
            'is_match': is_match,
            'confidence_score': confidence_score,
            'matches': matches,
            'total_comparisons': total_comparisons,
            'match_percentage': match_percentage,
            'best_similarity': best_similarity,
            'worst_similarity': worst_similarity,
            'average_similarity': average_similarity
        }
    
    def match_chunked_video(self, suspect_chunks: List[List[str]], 
                           protected_hashes: List[str]) -> List[Dict]:
        """
        Match chunked video (simulates real-time stream processing).
        
        Args:
            suspect_chunks: List of hash lists, one per chunk
            protected_hashes: Reference hashes from protected content
            
        Returns:
            List of match results, one per chunk
            
        Example:
            >>> matcher = VideoMatcher()
            >>> chunks = [chunk1_hashes, chunk2_hashes, chunk3_hashes]
            >>> results = matcher.match_chunked_video(chunks, protected)
            >>> for i, result in enumerate(results):
            ...     if result['is_match']:
            ...         print(f"Chunk {i}: DETECTED at {result['confidence_score']:.1f}%")
        """
        results = []
        
        for chunk_hashes in suspect_chunks:
            result = self.match_video_sequences(chunk_hashes, protected_hashes)
            results.append(result)
        
        return results
    
    def find_best_match(self, suspect_hashes: List[str], 
                       protected_database: List[Dict]) -> Tuple[Dict, Dict]:
        """
        Find the best matching protected content from a database.
        
        Args:
            suspect_hashes: List of pHashes from suspect video
            protected_database: List of protected content dicts with format:
                [
                    {
                        'id': int,
                        'title': str,
                        'video_hashes': List[str],
                        ...
                    },
                    ...
                ]
            
        Returns:
            Tuple of (best_match_content, match_result)
            
        Example:
            >>> matcher = VideoMatcher()
            >>> content, result = matcher.find_best_match(suspect, database)
            >>> if result['is_match']:
            ...     print(f"Matched: {content['title']}")
            ...     print(f"Confidence: {result['confidence_score']:.1f}%")
        """
        best_match = None
        best_result = {
            'is_match': False,
            'confidence_score': 0.0,
            'matches': 0,
            'total_comparisons': 0,
            'match_percentage': 0.0,
            'best_similarity': 0.0,
            'worst_similarity': 0.0,
            'average_similarity': 0.0
        }
        
        for protected_content in protected_database:
            protected_hashes = protected_content.get('video_hashes', [])
            
            if isinstance(protected_hashes, str):
                try:
                    protected_hashes = json.loads(protected_hashes)
                except:
                    continue
            
            result = self.match_video_sequences(suspect_hashes, protected_hashes)
            
            if result['confidence_score'] > best_result['confidence_score']:
                best_result = result
                best_match = protected_content
        
        return best_match, best_result
    
    def calculate_hamming_distance(self, hash1: str, hash2: str) -> int:
        """
        Calculate raw Hamming distance between two hashes.
        
        Args:
            hash1: First pHash as hex string
            hash2: Second pHash as hex string
            
        Returns:
            Number of differing bits
            
        Example:
            >>> matcher = VideoMatcher()
            >>> distance = matcher.calculate_hamming_distance("a3f2", "a3f3")
            >>> print(f"Hamming distance: {distance} bits")
        """
        h1 = imagehash.hex_to_hash(hash1)
        h2 = imagehash.hex_to_hash(hash2)
        
        return h1 - h2
    
    def get_similarity_score(self, hamming_distance: int) -> float:
        """
        Convert Hamming distance to similarity percentage.
        
        Args:
            hamming_distance: Number of differing bits
            
        Returns:
            Similarity percentage (0-100)
        """
        return (1 - (hamming_distance / self.max_distance)) * 100
    
    def set_threshold(self, new_threshold: float):
        """
        Update the matching threshold.
        
        Args:
            new_threshold: New threshold percentage (0-100)
        """
        if 0 <= new_threshold <= 100:
            self.threshold = new_threshold
        else:
            raise ValueError("Threshold must be between 0 and 100")
    
    def sliding_window_match(self, suspect_hashes: List[str], 
                            protected_hashes: List[str]) -> Dict:
        """
        Use sliding window to find where suspect clip matches in protected content.
        Identifies temporal location and provides localized confidence.
        
        Args:
            suspect_hashes: List of pHashes from suspect video (shorter clip)
            protected_hashes: List of pHashes from protected video (full content)
            
        Returns:
            Dictionary with:
            {
                'is_match': bool,
                'confidence_score': float,
                'best_window_start': int,
                'best_window_end': int,
                'temporal_offset_frames': int,
                'window_scores': List[float]
            }
            
        Example:
            >>> matcher = VideoMatcher(window_size=5)
            >>> result = matcher.sliding_window_match(suspect_clip, full_video)
            >>> if result['is_match']:
            ...     print(f"Found at frames {result['best_window_start']}-{result['best_window_end']}")
        """
        if not suspect_hashes or not protected_hashes:
            return {
                'is_match': False,
                'confidence_score': 0.0,
                'best_window_start': -1,
                'best_window_end': -1,
                'temporal_offset_frames': -1,
                'window_scores': []
            }
        
        suspect_len = len(suspect_hashes)
        protected_len = len(protected_hashes)
        
        if suspect_len > protected_len:
            return {
                'is_match': False,
                'confidence_score': 0.0,
                'best_window_start': -1,
                'best_window_end': -1,
                'temporal_offset_frames': -1,
                'window_scores': []
            }
        
        window_scores = []
        best_score = 0.0
        best_start = -1
        
        # Slide window across protected content
        for i in range(protected_len - suspect_len + 1):
            window = protected_hashes[i:i + suspect_len]
            
            # Compare suspect with this window
            similarities = []
            for s_hash, p_hash in zip(suspect_hashes, window):
                _, similarity = self.compare_hashes(s_hash, p_hash)
                similarities.append(similarity)
            
            avg_similarity = sum(similarities) / len(similarities)
            window_scores.append(avg_similarity)
            
            if avg_similarity > best_score:
                best_score = avg_similarity
                best_start = i
        
        is_match = best_score >= self.threshold
        best_end = best_start + suspect_len if best_start >= 0 else -1
        
        return {
            'is_match': is_match,
            'confidence_score': best_score,
            'best_window_start': best_start,
            'best_window_end': best_end,
            'temporal_offset_frames': best_start,
            'window_scores': window_scores
        }
    
    def statistical_confidence_match(self, suspect_hashes: List[str],
                                    protected_hashes: List[str]) -> Dict:
        """
        Calculate confidence based on consistency of matches over time.
        Reduces false positives from transient similarity.
        
        Args:
            suspect_hashes: List of pHashes from suspect video
            protected_hashes: List of pHashes from protected video
            
        Returns:
            Dictionary with statistical confidence metrics
        """
        if not suspect_hashes or not protected_hashes:
            return {
                'is_match': False,
                'confidence_score': 0.0,
                'consistency_ratio': 0.0,
                'temporal_stability': 0.0,
                'match_streak_max': 0,
                'match_streak_avg': 0.0
            }
        
        # Track consecutive matches
        match_streaks = []
        current_streak = 0
        consecutive_matches = 0
        
        similarities = []
        match_flags = []
        
        for suspect_hash in suspect_hashes:
            best_match_sim = 0.0
            found_match = False
            
            for protected_hash in protected_hashes:
                is_match, similarity = self.compare_hashes(suspect_hash, protected_hash)
                if similarity > best_match_sim:
                    best_match_sim = similarity
                if is_match:
                    found_match = True
                    break
            
            similarities.append(best_match_sim)
            match_flags.append(found_match)
            
            if found_match:
                current_streak += 1
                consecutive_matches += 1
            else:
                if current_streak > 0:
                    match_streaks.append(current_streak)
                current_streak = 0
        
        if current_streak > 0:
            match_streaks.append(current_streak)
        
        # Calculate consistency ratio
        consistency_ratio = consecutive_matches / len(suspect_hashes)
        
        # Calculate temporal stability (variance of similarities)
        if len(similarities) > 1:
            mean_sim = sum(similarities) / len(similarities)
            variance = sum((s - mean_sim) ** 2 for s in similarities) / len(similarities)
            std_dev = variance ** 0.5
            temporal_stability = max(0, 100 - std_dev)
        else:
            temporal_stability = 0.0
        
        # Calculate average confidence
        avg_similarity = sum(similarities) / len(similarities) if similarities else 0
        
        # Adjust confidence based on consistency
        adjusted_confidence = avg_similarity * consistency_ratio
        
        # Check if match is consistent enough
        is_match = (adjusted_confidence >= self.threshold and 
                   consistency_ratio >= self.consistency_threshold)
        
        max_streak = max(match_streaks) if match_streaks else 0
        avg_streak = sum(match_streaks) / len(match_streaks) if match_streaks else 0
        
        return {
            'is_match': is_match,
            'confidence_score': adjusted_confidence,
            'raw_confidence': avg_similarity,
            'consistency_ratio': consistency_ratio,
            'temporal_stability': temporal_stability,
            'match_streak_max': max_streak,
            'match_streak_avg': avg_streak,
            'total_frames': len(suspect_hashes),
            'matched_frames': consecutive_matches
        }
    
    def get_match_statistics(self, suspect_hashes: List[str], 
                            protected_hashes: List[str]) -> Dict:
        """
        Get detailed statistics about hash matching.
        
        Args:
            suspect_hashes: List of pHashes from suspect video
            protected_hashes: List of pHashes from protected video
            
        Returns:
            Dictionary with detailed statistics
        """
        if not suspect_hashes or not protected_hashes:
            return {}
        
        all_similarities = []
        hamming_distances = []
        
        for suspect_hash in suspect_hashes:
            for protected_hash in protected_hashes:
                try:
                    if ':' in suspect_hash and ':' in protected_hash:
                        _, similarity = self.compare_hashes(suspect_hash, protected_hash)
                        all_similarities.append(similarity)
                    else:
                        distance = self.calculate_hamming_distance(suspect_hash, protected_hash)
                        similarity = self.get_similarity_score(distance)
                        hamming_distances.append(distance)
                        all_similarities.append(similarity)
                except:
                    continue
        
        if not all_similarities:
            return {}
        
        return {
            'total_comparisons': len(all_similarities),
            'average_similarity': sum(all_similarities) / len(all_similarities),
            'max_similarity': max(all_similarities),
            'min_similarity': min(all_similarities),
            'average_hamming_distance': sum(hamming_distances) / len(hamming_distances) if hamming_distances else 0,
            'min_hamming_distance': min(hamming_distances) if hamming_distances else 0,
            'max_hamming_distance': max(hamming_distances) if hamming_distances else 0,
            'threshold': self.threshold,
            'matches_above_threshold': sum(1 for s in all_similarities if s >= self.threshold)
        }


if __name__ == "__main__":
    matcher = VideoMatcher(threshold=85.0, hash_size=8)
    
    print("Sentinel Video Matcher - Test Mode")
    print("=" * 50)
    print(f"Threshold: {matcher.threshold}%")
    print(f"Hash size: {matcher.hash_size}x{matcher.hash_size}")
    print(f"Max Hamming distance: {matcher.max_distance} bits")
    print("=" * 50)
