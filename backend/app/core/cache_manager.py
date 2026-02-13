# backend/app/core/cache_manager.py

from typing import Optional, Any
import json
from collections import OrderedDict
from app.core.cache import redis_client


class MultiLevelCacheManager:
    """Multi-level cache manager with L1 (local memory) + L2 (Redis)"""

    def __init__(self, redis_client, local_cache_size: int = 1000):
        self.redis = redis_client
        self.local_cache: OrderedDict = OrderedDict()
        self.local_cache_size = local_cache_size

    async def get(self, key: str) -> Optional[Any]:
        """Get cache (L1 local first, then L2 Redis)"""
        # L1: Local memory cache
        if key in self.local_cache:
            # Move to end (LRU)
            self.local_cache.move_to_end(key)
            return self.local_cache[key]

        # L2: Redis cache
        value = self.redis.get(key)
        if value:
            data = json.loads(value)
            # Backfill local cache
            self._set_local(key, data)
            return data

        return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int = 3600,
        local_ttl: int = 60
    ):
        """Set cache (write to both local and Redis)"""
        # Write to Redis
        self.redis.setex(key, ttl, json.dumps(value))

        # Write to local cache
        self._set_local(key, value)

    def _set_local(self, key: str, value: Any):
        """Set local cache with LRU eviction"""
        if len(self.local_cache) >= self.local_cache_size:
            # Remove oldest item (FIFO from OrderedDict)
            self.local_cache.popitem(last=False)

        self.local_cache[key] = value

    async def delete(self, key: str):
        """Delete cache from both levels"""
        # Delete from local cache
        if key in self.local_cache:
            del self.local_cache[key]

        # Delete from Redis
        self.redis.delete(key)

    async def clear_local(self):
        """Clear local cache only"""
        self.local_cache.clear()

    def get_local_stats(self) -> dict:
        """Get local cache statistics"""
        return {
            "size": len(self.local_cache),
            "max_size": self.local_cache_size,
            "usage_pct": round(len(self.local_cache) / self.local_cache_size * 100, 2)
        }


# Global multi-level cache manager instance
multi_level_cache = MultiLevelCacheManager(redis_client)


def get_multi_level_cache():
    """Get multi-level cache manager instance"""
    return multi_level_cache
