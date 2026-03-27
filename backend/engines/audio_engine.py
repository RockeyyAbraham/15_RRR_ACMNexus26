import librosa
import numpy as np
import imagehash
from PIL import Image
import os
import time
from typing import Dict, List, Tuple

class AudioHashEngine:
    """
    Sentinel Audio Fingerprinting Engine.
    Generates perceptual hashes from audio spectrograms for piracy detection.
    Uses mel-spectrogram analysis for robust audio matching.
    """
    
    def __init__(self, sample_rate: int = 22050, n_mels: int = 128, 
                 hop_length: int = 512, hash_size: int = 8, chunk_duration: int = 5):
        """
        Initialize the audio hash engine.
        
        Args:
            sample_rate: Audio sampling rate (default: 22050 Hz)
            n_mels: Number of mel bands (default: 128)
            hop_length: Hop length for STFT (default: 512)
            hash_size: Size of the pHash matrix (default: 8 = 64-bit hash)
            chunk_duration: Duration of each audio chunk in seconds (default: 5)
        """
        self.sample_rate = sample_rate
        self.n_mels = n_mels
        self.hop_length = hop_length
        self.hash_size = hash_size
        self.chunk_duration = chunk_duration

    def extract_audio_hash(self, video_path: str, duration: float = None) -> str:
        """
        Extract audio from video, generate a spectrogram pHash.
        
        Args:
            video_path: Path to the video file
            duration: Max duration to process in seconds
            
        Returns:
            Hex string representation of the audio pHash
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")

        try:
            # Load audio using librosa
            y, sr = librosa.load(video_path, sr=self.sample_rate, duration=duration)
            
            # Generate Mel-spectrogram
            S = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=self.n_mels, 
                                             hop_length=self.hop_length)
            
            # Convert to log scale (dB)
            S_db = librosa.power_to_db(S, ref=np.max)
            
            # Normalize to 0-255 for image conversion
            S_norm = ((S_db - S_db.min()) / (S_db.max() - S_db.min()) * 255).astype(np.uint8)
            
            # Convert spectrogram array to PIL Image
            img = Image.fromarray(S_norm)
            
            # Generate pHash from the spectrogram image
            audio_hash = imagehash.phash(img, hash_size=self.hash_size)
            
            return str(audio_hash)
            
        except Exception as e:
            print(f"❌ Audio extraction failed: {e}")
            return None

    def hash_audio(self, video_path: str) -> Tuple[List[str], Dict]:
        """
        Generate audio fingerprints for entire video.
        Returns list of hashes and metadata.
        
        Args:
            video_path: Path to video file
            
        Returns:
            (hashes, metadata) tuple
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video not found: {video_path}")
        
        start_time = time.time()
        hashes = []
        
        try:
            # Get total duration
            total_duration = librosa.get_duration(path=video_path)
            
            # Process in chunks
            for start in range(0, int(total_duration), self.chunk_duration):
                try:
                    # Load audio chunk
                    y, sr = librosa.load(
                        video_path, 
                        sr=self.sample_rate,
                        offset=start, 
                        duration=self.chunk_duration
                    )
                    
                    # Generate mel-spectrogram
                    S = librosa.feature.melspectrogram(
                        y=y, 
                        sr=sr, 
                        n_mels=self.n_mels,
                        hop_length=self.hop_length
                    )
                    
                    # Convert to dB scale
                    S_db = librosa.power_to_db(S, ref=np.max)
                    
                    # Normalize to 0-255
                    S_norm = ((S_db - S_db.min()) / (S_db.max() - S_db.min()) * 255).astype(np.uint8)
                    
                    # Convert to image and hash
                    img = Image.fromarray(S_norm)
                    audio_hash = str(imagehash.phash(img, hash_size=self.hash_size))
                    
                    hashes.append(audio_hash)
                    
                except Exception as e:
                    print(f"⚠ Chunk at {start}s failed: {e}")
                    continue
            
            processing_time = time.time() - start_time
            
            metadata = {
                'total_duration': total_duration,
                'chunks_processed': len(hashes),
                'chunk_duration': self.chunk_duration,
                'processing_time_seconds': processing_time,
                'sample_rate': self.sample_rate,
                'n_mels': self.n_mels,
                'audio_backend_available': True,
                'error': None
            }
            
            return hashes, metadata
            
        except Exception as e:
            processing_time = time.time() - start_time
            metadata = {
                'total_duration': 0.0,
                'chunks_processed': 0,
                'chunk_duration': self.chunk_duration,
                'processing_time_seconds': processing_time,
                'sample_rate': self.sample_rate,
                'n_mels': self.n_mels,
                'audio_backend_available': False,
                'error': str(e)
            }
            print(f"⚠ Audio processing unavailable for {os.path.basename(video_path)}: {e}")
            return [], metadata

if __name__ == "__main__":
    # Quick Test
    engine = AudioHashEngine()
    test_video = "assets/videos/Race Highlights  2026 Australian Grand Prix - FORMULA 1 (720p, h264, youtube).mp4"
    if os.path.exists(test_video):
        print(f"🔍 Testing Audio Hash Engine on: {os.path.basename(test_video)}")
        h = engine.extract_audio_hash(test_video)
        print(f"✅ Audio Fingerprint: {h}")
    else:
        print("❌ Test video not found.")
