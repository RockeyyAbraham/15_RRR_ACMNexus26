import librosa
import numpy as np
import imagehash
from PIL import Image
import os

class AudioHashEngine:
    """
    Sentinel Audio Fingerprinting Engine.
    Generates perceptual hashes from audio spectrograms.
    """
    
    def __init__(self, sample_rate: int = 22050, n_mels: int = 128, 
                 hop_length: int = 512, hash_size: int = 16):
        """
        Initialize the audio hash engine.
        
        Args:
            sample_rate: Audio sampling rate (default: 22050 Hz)
            n_mels: Number of mel bands (default: 128)
            hop_length: Hop length for STFT (default: 512)
            hash_size: Size of the pHash matrix (default: 16 = 256-bit hash)
        """
        self.sample_rate = sample_rate
        self.n_mels = n_mels
        self.hop_length = hop_length
        self.hash_size = hash_size

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

    def generate_chunked_audio_hashes(self, video_path: str, chunk_duration: int = 5) -> list:
        """
        Generate audio hashes for fixed-duration chunks.
        Excellent for real-time stream matching.
        """
        hashes = []
        try:
            # Get total duration
            total_duration = librosa.get_duration(path=video_path)
            
            for start in range(0, int(total_duration), chunk_duration):
                h = self.extract_audio_hash(video_path, duration=start + chunk_duration)
                # Note: librosa.load duration is cumulative, we filter locally or use offset
                y, sr = librosa.load(video_path, sr=self.sample_rate, 
                                   offset=start, duration=chunk_duration)
                
                S = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=self.n_mels)
                S_db = librosa.power_to_db(S, ref=np.max)
                S_norm = ((S_db - S_db.min()) / (S_db.max() - S_db.min()) * 255).astype(np.uint8)
                img = Image.fromarray(S_norm)
                audio_hash = str(imagehash.phash(img, hash_size=self.hash_size))
                
                hashes.append({
                    'timestamp': start,
                    'hash': audio_hash
                })
            
            return hashes
        except Exception as e:
            print(f"❌ Chunked audio hashing failed: {e}")
            return []

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
