# backend/app/core/cache.py
import json
import hashlib
from typing import Optional, Dict, Any
import redis
from app.core.config import settings

redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

def get_cache():
    return redis_client

class CacheManager:
    """Redis cache manager for strategy results"""

    def __init__(self):
        self.redis = redis_client
        self.default_ttl = 1800  # 30 minutes

    def generate_cache_key(self, strategy_type: str, params: Dict[str, Any]) -> str:
        """Generate cache key from strategy type and parameters"""
        params_str = json.dumps(params, sort_keys=True)
        params_hash = hashlib.md5(params_str.encode()).hexdigest()
        return f"strategy:result:{strategy_type}:{params_hash}"

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            value = self.redis.get(key)
            if value:
                self.redis.incr("stats:cache:hits")
                return json.loads(value)
            else:
                self.redis.incr("stats:cache:misses")
                return None
        except Exception as e:
            print(f"Cache get error: {e}")
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with TTL"""
        try:
            ttl = ttl or self.default_ttl
            value_str = json.dumps(value)
            self.redis.setex(key, ttl, value_str)
            return True
        except Exception as e:
            print(f"Cache set error: {e}")
            return False

    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        try:
            self.redis.delete(key)
            return True
        except Exception as e:
            print(f"Cache delete error: {e}")
            return False

    def get_stats(self) -> Dict[str, int]:
        """Get cache statistics"""
        try:
            hits = self.redis.get("stats:cache:hits") or "0"
            misses = self.redis.get("stats:cache:misses") or "0"

            hits_int = int(hits)
            misses_int = int(misses)
            total = hits_int + misses_int

            hit_rate = (hits_int / total * 100) if total > 0 else 0

            return {
                "hits": hits_int,
                "misses": misses_int,
                "total": total,
                "hit_rate": round(hit_rate, 2)
            }
        except Exception as e:
            print(f"Cache stats error: {e}")
            return {"hits": 0, "misses": 0, "total": 0, "hit_rate": 0}

# Global cache manager instance
cache_manager = CacheManager()

def get_redis():
    """Get Redis client for async operations"""
    return redis_client
