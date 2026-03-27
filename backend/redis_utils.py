"""
Redis utility for Sentinel backend.
Provides caching layer for protected content hashes and detection results.
"""

import os
import json
import logging
from typing import Optional, List, Dict, Any
try:
    import redis
except ImportError:
    redis = None

logger = logging.getLogger(__name__)


class RedisManager:
    def __init__(self):
        """Initialize Redis connection."""
        self.redis_host = os.getenv("REDIS_HOST", "localhost")
        self.redis_port = int(os.getenv("REDIS_PORT", 6379))
        self.redis_db = int(os.getenv("REDIS_DB", 0))
        self.redis_password = os.getenv("REDIS_PASSWORD", None)

        if redis is None:
            logger.warning("redis package not installed. Running without Redis cache.")
            self.redis_client = None
            return

        # Try to connect to Redis
        try:
            self.redis_client = redis.Redis(
                host=self.redis_host,
                port=self.redis_port,
                db=self.redis_db,
                password=self.redis_password,
                decode_responses=True,  # Automatically decode responses to strings
                socket_connect_timeout=2,
                socket_timeout=2,
            )
            # Test connection
            self.redis_client.ping()
            logger.info(f"Connected to Redis at {self.redis_host}:{self.redis_port}")
        except Exception as e:
            logger.warning(
                f"Failed to connect to Redis: {e}. Falling back to database-only mode."
            )
            self.redis_client = None

    def is_available(self) -> bool:
        """Check if Redis is available."""
        return self.redis_client is not None

    # Protected Content Hashes Caching
    def cache_protected_hashes(
        self, content_id: int, hashes: List[str], ttl: int = 3600
    ) -> bool:
        """
        Cache protected content hashes in Redis.

        Args:
            content_id: ID of the protected content
            hashes: List of perceptual hashes
            ttl: Time to live in seconds (default: 1 hour)

        Returns:
            bool: Success status
        """
        if not self.is_available():
            return False

        try:
            key = f"protected:{content_id}:hashes"
            self.redis_client.setex(key, ttl, json.dumps(hashes))
            # Also add to the set of all protected content IDs
            self.redis_client.sadd("protected:all", content_id)
            logger.debug(f"Cached hashes for content {content_id} in Redis")
            return True
        except Exception as e:
            logger.error(f"Failed to cache protected hashes: {e}")
            return False

    def get_protected_hashes(self, content_id: int) -> Optional[List[str]]:
        """
        Get protected content hashes from Redis cache.

        Args:
            content_id: ID of the protected content

        Returns:
            List of hashes if found, None otherwise
        """
        if not self.is_available():
            return None

        try:
            key = f"protected:{content_id}:hashes"
            cached = self.redis_client.get(key)
            if cached:
                return json.loads(cached)
            return None
        except Exception as e:
            logger.error(f"Failed to get protected hashes from Redis: {e}")
            return None

    def get_all_protected_content_ids(self) -> List[int]:
        """
        Get all protected content IDs from Redis.

        Returns:
            List of content IDs
        """
        if not self.is_available():
            return []

        try:
            ids = self.redis_client.smembers("protected:all")
            return [int(id_) for id_ in ids]
        except Exception as e:
            logger.error(f"Failed to get protected content IDs from Redis: {e}")
            return []

    # Detection Results Caching
    def cache_detection_result(
        self, detection_id: int, result: Dict[str, Any], ttl: int = 1800
    ) -> bool:
        """
        Cache detection result in Redis.

        Args:
            detection_id: ID of the detection
            result: Detection result dictionary
            ttl: Time to live in seconds (default: 30 minutes)

        Returns:
            bool: Success status
        """
        if not self.is_available():
            return False

        try:
            key = f"detection:{detection_id}:result"
            self.redis_client.setex(key, ttl, json.dumps(result))
            logger.debug(f"Cached detection result for {detection_id} in Redis")
            return True
        except Exception as e:
            logger.error(f"Failed to cache detection result: {e}")
            return False

    def get_detection_result(self, detection_id: int) -> Optional[Dict[str, Any]]:
        """
        Get detection result from Redis cache.

        Args:
            detection_id: ID of the detection

        Returns:
            Detection result dictionary if found, None otherwise
        """
        if not self.is_available():
            return None

        try:
            key = f"detection:{detection_id}:result"
            cached = self.redis_client.get(key)
            if cached:
                return json.loads(cached)
            return None
        except Exception as e:
            logger.error(f"Failed to get detection result from Redis: {e}")
            return None

    # General Cache Methods
    def set_cache(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set a generic cache value."""
        if not self.is_available():
            return False

        try:
            self.redis_client.setex(key, ttl, json.dumps(value))
            return True
        except Exception as e:
            logger.error(f"Failed to set cache: {e}")
            return False

    def get_cache(self, key: str) -> Any:
        """Get a generic cache value."""
        if not self.is_available():
            return None

        try:
            cached = self.redis_client.get(key)
            if cached:
                return json.loads(cached)
            return None
        except Exception as e:
            logger.error(f"Failed to get cache: {e}")
            return None

    def delete_cache(self, key: str) -> bool:
        """Delete a cache key."""
        if not self.is_available():
            return False

        try:
            self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Failed to delete cache: {e}")
            return False


# Global instance
redis_manager = RedisManager()
