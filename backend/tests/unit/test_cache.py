# backend/tests/unit/test_cache.py
import pytest
from app.core.cache import CacheManager

@pytest.fixture
def cache_manager():
    manager = CacheManager()
    # Clear test keys before each test
    manager.redis.delete("test:key")
    manager.redis.delete("stats:cache:hits")
    manager.redis.delete("stats:cache:misses")
    return manager

def test_generate_cache_key(cache_manager):
    """Test cache key generation"""
    key1 = cache_manager.generate_cache_key("graham", {"limit": 10})
    key2 = cache_manager.generate_cache_key("graham", {"limit": 10})
    key3 = cache_manager.generate_cache_key("graham", {"limit": 20})

    # Same params should generate same key
    assert key1 == key2

    # Different params should generate different key
    assert key1 != key3

    # Key should follow format
    assert key1.startswith("strategy:result:graham:")

def test_cache_set_and_get(cache_manager):
    """Test setting and getting cache values"""
    test_data = {"stock_code": "600000", "stock_name": "浦发银行"}

    # Set value
    result = cache_manager.set("test:key", test_data, ttl=60)
    assert result is True

    # Get value
    cached = cache_manager.get("test:key")
    assert cached == test_data

def test_cache_miss(cache_manager):
    """Test cache miss returns None"""
    result = cache_manager.get("nonexistent:key")
    assert result is None

def test_cache_delete(cache_manager):
    """Test deleting cache keys"""
    test_data = {"test": "data"}

    # Set and verify
    cache_manager.set("test:key", test_data)
    assert cache_manager.get("test:key") == test_data

    # Delete and verify
    result = cache_manager.delete("test:key")
    assert result is True
    assert cache_manager.get("test:key") is None

def test_cache_stats(cache_manager):
    """Test cache statistics tracking"""
    # Initial stats
    stats = cache_manager.get_stats()
    initial_hits = stats["hits"]
    initial_misses = stats["misses"]

    # Cache miss
    cache_manager.get("nonexistent:key")

    # Cache hit
    cache_manager.set("test:key", {"data": "value"})
    cache_manager.get("test:key")

    # Check stats
    stats = cache_manager.get_stats()
    assert stats["hits"] == initial_hits + 1
    assert stats["misses"] == initial_misses + 1
    assert stats["total"] == stats["hits"] + stats["misses"]

def test_cache_ttl(cache_manager):
    """Test cache TTL expiration"""
    import time

    test_data = {"test": "data"}

    # Set with 1 second TTL
    cache_manager.set("test:key", test_data, ttl=1)

    # Should exist immediately
    assert cache_manager.get("test:key") == test_data

    # Wait for expiration
    time.sleep(2)

    # Should be expired
    assert cache_manager.get("test:key") is None
