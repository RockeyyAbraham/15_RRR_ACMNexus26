import imagehash
from typing import List, Tuple, Dict
import json


class VideoMatcher:
    """
    Matching engine for comparing video fingerprints.
    Uses Hamming distance to calculate similarity between pHashes.
    """
    
    def __init__(self, threshold: float = 85.0, hash_size: int = 8):
        """
        Initialize the matcher.
        
        Args:
            threshold: Minimum similarity percentage to consider a match (default: 85%)
            hash_size: Size of the pHash matrix (default: 8 = 64-bit hash)
        """
        self.threshold = threshold
        self.hash_size = hash_size
        self.max_distance = hash_size ** 2
    
    def compare_hashes(self, hash1: str, hash2: str) -> Tuple[bool, float]:
        """
        Compare two pHashes using Hamming distance.
        
        Args:
            hash1: First pHash as hex string (e.g., "a3f2c1b4...")
            hash2: Second pHash as hex string
            
        Returns:
            Tuple of (is_match, similarity_percentage)
            
        Example:
            >>> matcher = VideoMatcher(threshold=85.0)
            >>> is_match, score = matcher.compare_hashes("a3f2c1b4", "a3f2c1b5")
            >>> print(f"Match: {is_match}, Similarity: {score:.2f}%")
        """
        try:
            h1 = imagehash.hex_to_hash(hash1)
            h2 = imagehash.hex_to_hash(hash2)
            
            distance = h1 - h2
            
            similarity = (1 - (distance / self.max_distance)) * 100
            
            is_match = similarity >= self.threshold
            
            return is_match, similarity
            
        except Exception as e:
            raise ValueError(f"Error comparing hashes: {e}")
    
    def match_video_sequences(self, suspect_hashes: List[str], protected_hashes: List[str]) -> Dict:
        """
        Match a suspect video sequence against a protected video sequence.
        
        Args:
            suspect_hashes: List of pHashes from suspect video
            protected_hashes: List of pHashes from protected video
            
        Returns:
            Dictionary with match results:
            {
                'is_match': bool,
                'confidence_score': float,
                'matches': int,
                'total_comparisons': int,
                'match_percentage': float,
                'best_similarity': float,
                'worst_similarity': float,
                'average_similarity': float
            }
            
        Example:
            >>> matcher = VideoMatcher()
            >>> result = matcher.match_video_sequences(suspect, protected)
            >>> if result['is_match']:
            ...     print(f"PIRACY DETECTED! Confidence: {result['confidence_score']:.1f}%")
        """
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
                distance = self.calculate_hamming_distance(suspect_hash, protected_hash)
                similarity = self.get_similarity_score(distance)
                
                hamming_distances.append(distance)
                all_similarities.append(similarity)
        
        return {
            'total_comparisons': len(all_similarities),
            'average_similarity': sum(all_similarities) / len(all_similarities),
            'max_similarity': max(all_similarities),
            'min_similarity': min(all_similarities),
            'average_hamming_distance': sum(hamming_distances) / len(hamming_distances),
            'min_hamming_distance': min(hamming_distances),
            'max_hamming_distance': max(hamming_distances),
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
