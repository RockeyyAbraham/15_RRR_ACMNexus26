import redis
import json
import logging
import os
from dotenv import load_dotenv

load_dotenv()

class RedisManager:
    """
    Manages high-speed caching and real-time hash lookups for Sentinel.
    """
    def __init__(self):
        self.host = os.getenv("REDIS_HOST", "localhost")
        self.port = int(os.getenv("REDIS_PORT", 6379))
        self.db = int(os.getenv("REDIS_DB", 0))
        self.password = os.getenv("REDIS_PASSWORD", None)
        
        try:
            self.client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                decode_responses=True,
                socket_timeout=1
            )
            # Test connection
            self.client.ping()
            logging.info(f"Connected to Redis at {self.host}:{self.port}")
        except Exception as e:
            try:
                import fakeredis
                self.client = fakeredis.FakeRedis(decode_responses=True)
                logging.warning(f"Redis not found. Using Mock Redis (fakeredis) for local testing.")
            except ImportError:
                logging.error("Redis connection failed and fakeredis not installed. Real-time features disabled.")
                self.client = None

    def is_available(self) -> bool:
        """Check if Redis service is reachable."""
        if not self.client:
            return False
        try:
            return self.client.ping()
        except:
            return False

    def cache_protected_hashes(self, content_id: int, hashes: list, ttl: int = 3600):
        """Cache video hashes for a specific content ID."""
        if not self.client:
            return
        
        key = f"protected_hashes:{content_id}"
        try:
            self.client.set(key, json.dumps(hashes), ex=ttl)
            # Also add to a global set of active content IDs
            self.client.sadd("active_protected_content", content_id)
        except Exception as e:
            logging.error(f"Failed to cache hashes in Redis: {e}")

    def get_protected_hashes(self, content_id: int) -> list:
        """Retrieve cached hashes for a specific content ID."""
        if not self.client:
            return None
        
        key = f"protected_hashes:{content_id}"
        try:
            data = self.client.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            logging.error(f"Failed to get hashes from Redis: {e}")
            return None

    def get_all_protected_content_ids(self) -> list:
        """Get IDs of all currently cached protected content."""
        if not self.client:
            return []
        try:
            ids = self.client.smembers("active_protected_content")
            return [int(id) for id in ids]
        except Exception as e:
            logging.error(f"Failed to get content IDs from Redis: {e}")
            return []

    def cache_detection_result(self, detection_id: int, data: dict, ttl: int = 1800):
        """Cache a detection event for real-time dashboard updates."""
        if not self.client:
            return
        
        key = f"detection_cache:{detection_id}"
        try:
            self.client.set(key, json.dumps(data), ex=ttl)
            # Push to a 'latest_detections' list for WS broadcast
            self.client.lpush("latest_detections", json.dumps(data))
            self.client.ltrim("latest_detections", 0, 99) # Keep last 100
        except Exception as e:
            logging.error(f"Failed to cache detection in Redis: {e}")

    def get_latest_detections(self, count: int = 10) -> list:
        """Retrieve recent detection events from cache."""
        if not self.client:
            return []
        try:
            data_list = self.client.lrange("latest_detections", 0, count - 1)
            return [json.loads(d) for d in data_list]
        except Exception as e:
            logging.error(f"Failed to get recent detections from Redis: {e}")
            return []

# Singleton instance
redis_manager = RedisManager()
