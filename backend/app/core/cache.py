"""Redis cache layer for application caching."""
import json
import logging
from typing import Any, Optional

import redis.asyncio as redis

from app.core.config import settings

logger = logging.getLogger(__name__)


class RedisCache:
    """
    Redis-based cache implementation.

    Provides async get/set/delete operations with JSON serialization.
    """

    _instance: Optional["RedisCache"] = None
    _redis: Optional[redis.Redis] = None

    def __new__(cls) -> "RedisCache":
        """Singleton pattern for cache instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def connect(self) -> None:
        """Connect to Redis."""
        if self._redis is None:
            try:
                self._redis = redis.from_url(
                    settings.REDIS_URL,
                    encoding="utf-8",
                    decode_responses=True,
                )
                # Test connection
                await self._redis.ping()
                logger.info("Connected to Redis cache")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                self._redis = None

    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self._redis:
            await self._redis.close()
            self._redis = None
            logger.info("Disconnected from Redis cache")

    @property
    def is_connected(self) -> bool:
        """Check if Redis is connected."""
        return self._redis is not None

    async def get(self, key: str) -> Optional[Any]:
        """
        Get a value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        if not self._redis:
            return None

        try:
            data = await self._redis.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.warning(f"Cache get error for key {key}: {e}")
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: int = 300,
    ) -> bool:
        """
        Set a value in cache.

        Args:
            key: Cache key
            value: Value to cache (must be JSON serializable)
            ttl_seconds: Time to live in seconds (default: 5 minutes)

        Returns:
            True if successful
        """
        if not self._redis:
            return False

        try:
            serialized = json.dumps(value, default=str)
            await self._redis.setex(key, ttl_seconds, serialized)
            return True
        except Exception as e:
            logger.warning(f"Cache set error for key {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """
        Delete a value from cache.

        Args:
            key: Cache key

        Returns:
            True if key was deleted
        """
        if not self._redis:
            return False

        try:
            result = await self._redis.delete(key)
            return result > 0
        except Exception as e:
            logger.warning(f"Cache delete error for key {key}: {e}")
            return False

    async def delete_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching a pattern.

        Args:
            pattern: Key pattern (e.g., "loan:*")

        Returns:
            Number of keys deleted
        """
        if not self._redis:
            return 0

        try:
            keys = []
            async for key in self._redis.scan_iter(match=pattern):
                keys.append(key)

            if keys:
                return await self._redis.delete(*keys)
            return 0
        except Exception as e:
            logger.warning(f"Cache delete pattern error for {pattern}: {e}")
            return 0

    async def exists(self, key: str) -> bool:
        """
        Check if a key exists in cache.

        Args:
            key: Cache key

        Returns:
            True if key exists
        """
        if not self._redis:
            return False

        try:
            return await self._redis.exists(key) > 0
        except Exception as e:
            logger.warning(f"Cache exists error for key {key}: {e}")
            return False

    async def get_or_set(
        self,
        key: str,
        factory: Any,
        ttl_seconds: int = 300,
    ) -> Any:
        """
        Get value from cache or compute and cache it.

        Args:
            key: Cache key
            factory: Async function to compute value if not cached
            ttl_seconds: TTL in seconds

        Returns:
            Cached or computed value
        """
        # Try to get from cache
        value = await self.get(key)
        if value is not None:
            return value

        # Compute value
        if callable(factory):
            value = await factory() if hasattr(factory, "__await__") else factory()
        else:
            value = factory

        # Cache the result
        await self.set(key, value, ttl_seconds)
        return value

    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """
        Increment a counter.

        Args:
            key: Cache key
            amount: Amount to increment by

        Returns:
            New value or None on error
        """
        if not self._redis:
            return None

        try:
            return await self._redis.incrby(key, amount)
        except Exception as e:
            logger.warning(f"Cache increment error for key {key}: {e}")
            return None

    async def get_stats(self) -> dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache stats
        """
        if not self._redis:
            return {"connected": False}

        try:
            info = await self._redis.info()
            return {
                "connected": True,
                "used_memory": info.get("used_memory_human", "N/A"),
                "connected_clients": info.get("connected_clients", 0),
                "total_keys": await self._redis.dbsize(),
                "hits": info.get("keyspace_hits", 0),
                "misses": info.get("keyspace_misses", 0),
            }
        except Exception as e:
            logger.warning(f"Error getting cache stats: {e}")
            return {"connected": True, "error": str(e)}


# Cache key helpers
class CacheKeys:
    """Helper class for generating cache keys."""

    @staticmethod
    def loan(loan_id: str) -> str:
        """Cache key for a single loan."""
        return f"loan:{loan_id}"

    @staticmethod
    def loan_list(
        country_code: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> str:
        """Cache key for loan list."""
        parts = ["loans"]
        if country_code:
            parts.append(f"country:{country_code}")
        if status:
            parts.append(f"status:{status}")
        parts.append(f"page:{page}")
        parts.append(f"size:{page_size}")
        return ":".join(parts)

    @staticmethod
    def loan_stats(country_code: Optional[str] = None) -> str:
        """Cache key for loan statistics."""
        if country_code:
            return f"stats:loans:{country_code}"
        return "stats:loans:all"

    @staticmethod
    def user(user_id: str) -> str:
        """Cache key for user data."""
        return f"user:{user_id}"


# Global cache instance
cache = RedisCache()


async def get_cache() -> RedisCache:
    """Get cache instance, connecting if necessary."""
    if not cache.is_connected:
        await cache.connect()
    return cache
