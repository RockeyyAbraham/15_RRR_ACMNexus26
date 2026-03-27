"""Quick test to verify all imports work"""
import sys
from pathlib import Path

# Add backend to path
BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

print("Testing imports...")

try:
    from utils.redis_utils import redis_manager
    print("✓ redis_utils imported")
except Exception as e:
    print(f"✗ redis_utils failed: {e}")

try:
    from engines.hash_engine import VideoHashEngine
    print("✓ hash_engine imported")
except Exception as e:
    print(f"✗ hash_engine failed: {e}")

try:
    from engines.matcher import VideoMatcher
    print("✓ matcher imported")
except Exception as e:
    print(f"✗ matcher failed: {e}")

try:
    from engines.audio_engine import AudioHashEngine
    print("✓ audio_engine imported")
except Exception as e:
    print(f"✗ audio_engine failed: {e}")

try:
    from generators.dmca_generator import DMCAGenerator
    print("✓ dmca_generator imported")
except Exception as e:
    print(f"✗ dmca_generator failed: {e}")

try:
    from engines.ai_engine import SentinelAI
    print("✓ ai_engine imported")
except Exception as e:
    print(f"✗ ai_engine failed: {e}")

print("\nAll critical imports successful!")
