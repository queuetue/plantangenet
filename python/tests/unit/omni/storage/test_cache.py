import pytest
import time
from plantangenet.omni.storage.cache import LRUCache


def test_lru_cache_init():
    cache = LRUCache(5)
    assert cache.max_items == 5
    assert len(cache.cache) == 0


def test_lru_cache_put_get():
    cache = LRUCache(3)
    
    # Test put and get
    cache.put("key1", "value1")
    assert cache.get("key1") == "value1"
    
    # Test get non-existent key
    assert cache.get("nonexistent") is None


def test_lru_cache_update_existing():
    cache = LRUCache(3)
    
    # Put initial value
    cache.put("key1", "value1")
    assert cache.get("key1") == "value1"
    
    # Update value
    cache.put("key1", "updated_value")
    assert cache.get("key1") == "updated_value"
    assert len(cache.cache) == 1


def test_lru_cache_eviction():
    cache = LRUCache(2)
    
    # Fill cache to capacity
    cache.put("key1", "value1")
    cache.put("key2", "value2")
    
    # Add third item - should evict key1 (least recently used)
    cache.put("key3", "value3")
    
    assert cache.get("key1") is None  # Evicted
    assert cache.get("key2") == "value2"
    assert cache.get("key3") == "value3"
    assert len(cache.cache) == 2


def test_lru_cache_access_order():
    cache = LRUCache(3)
    
    # Add items
    cache.put("key1", "value1")
    cache.put("key2", "value2") 
    cache.put("key3", "value3")
    
    # Access key1 to make it most recently used
    cache.get("key1")
    
    # Add fourth item - key2 should be evicted (least recently used)
    cache.put("key4", "value4")
    
    assert cache.get("key1") == "value1"  # Still there
    assert cache.get("key2") is None     # Evicted
    assert cache.get("key3") == "value3"
    assert cache.get("key4") == "value4"


def test_lru_cache_delete():
    cache = LRUCache(3)
    
    cache.put("key1", "value1")
    cache.put("key2", "value2")
    
    # Delete existing key
    assert cache.delete("key1") is True
    assert cache.get("key1") is None
    assert len(cache.cache) == 1
    
    # Delete non-existent key
    assert cache.delete("nonexistent") is False


def test_lru_cache_clear():
    cache = LRUCache(3)
    
    cache.put("key1", "value1")
    cache.put("key2", "value2")
    
    cache.clear()
    
    assert len(cache.cache) == 0
    assert cache.get("key1") is None
    assert cache.get("key2") is None


def test_lru_cache_keys():
    cache = LRUCache(3)
    
    cache.put("key1", "value1")
    cache.put("key2", "value2")
    cache.put("key3", "value3")
    
    keys = cache.keys()
    assert len(keys) == 3
    assert "key1" in keys
    assert "key2" in keys
    assert "key3" in keys
    
    # Most recent should be first
    assert keys[0] == "key3"


def test_lru_cache_get_stats():
    cache = LRUCache(5)
    
    cache.put("key1", "value1")
    cache.put("key2", "value2")
    
    stats = cache.get_stats()
    
    assert stats["current_items"] == 2
    assert stats["max_items"] == 5
    assert stats["usage_percent"] == 40.0


def test_lru_cache_complex_values():
    cache = LRUCache(3)
    
    # Test with complex data types
    cache.put("dict", {"nested": {"value": 42}})
    cache.put("list", [1, 2, 3, {"key": "value"}])
    cache.put("none", None)
    
    assert cache.get("dict") == {"nested": {"value": 42}}
    assert cache.get("list") == [1, 2, 3, {"key": "value"}]
    assert cache.get("none") is None  # None is a valid value


def test_lru_cache_zero_capacity():
    cache = LRUCache(0)
    
    cache.put("key1", "value1")
    
    # Should not store anything with zero capacity
    assert len(cache.cache) == 0
    assert cache.get("key1") is None
