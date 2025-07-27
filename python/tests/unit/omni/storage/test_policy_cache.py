import pytest
import time
import asyncio
from plantangenet.omni.storage.policy_cache import PolicyCache


@pytest.mark.asyncio
async def test_policy_cache_init():
    cache = PolicyCache()
    assert len(cache._cache) == 0
    assert len(cache._ttl) == 0


@pytest.mark.asyncio
async def test_cache_decision_basic():
    cache = PolicyCache()
    
    success = await cache.cache_decision(
        identity_id="user1",
        action="read",
        resource="/docs/file.txt",
        decision=True,
        reason="User has read permission",
        ttl=300
    )
    
    assert success is True
    assert len(cache._cache) == 1
    
    # Check cache key format
    cache_key = "user1:read:/docs/file.txt"
    assert cache_key in cache._cache
    assert cache_key in cache._ttl


@pytest.mark.asyncio
async def test_cache_decision_values():
    cache = PolicyCache()
    
    await cache.cache_decision(
        identity_id="user1",
        action="write",
        resource="/admin/config",
        decision=False,
        reason="Insufficient permissions",
        ttl=600
    )
    
    cache_key = "user1:write:/admin/config"
    cached_data = cache._cache[cache_key]
    
    assert cached_data["decision"] is False
    assert cached_data["reason"] == "Insufficient permissions"
    assert cached_data["identity_id"] == "user1"
    assert cached_data["action"] == "write"
    assert cached_data["resource"] == "/admin/config"
    assert "cached_at" in cached_data


@pytest.mark.asyncio
async def test_get_decision_valid():
    cache = PolicyCache()
    
    # Cache a decision
    await cache.cache_decision("user1", "read", "/file.txt", True, "Allowed", 300)
    
    # Retrieve it
    decision = await cache.get_decision("user1", "read", "/file.txt")
    
    assert decision is not None
    assert decision["decision"] is True
    assert decision["reason"] == "Allowed"
    assert decision["identity_id"] == "user1"


@pytest.mark.asyncio
async def test_get_decision_nonexistent():
    cache = PolicyCache()
    
    # Try to get non-existent decision
    decision = await cache.get_decision("user1", "read", "/file.txt")
    assert decision is None


@pytest.mark.asyncio
async def test_get_decision_expired():
    cache = PolicyCache()
    
    # Cache with very short TTL
    await cache.cache_decision("user1", "read", "/file.txt", True, "Allowed", ttl=1)
    
    # Wait for expiration
    time.sleep(1.1)
    
    # Should return None and clean up expired entry
    decision = await cache.get_decision("user1", "read", "/file.txt")
    assert decision is None
    
    # Entry should be removed from cache
    cache_key = "user1:read:/file.txt"
    assert cache_key not in cache._cache
    assert cache_key not in cache._ttl


@pytest.mark.asyncio
async def test_cache_decision_overwrite():
    cache = PolicyCache()
    
    # Cache initial decision
    await cache.cache_decision("user1", "read", "/file.txt", True, "Initial", 300)
    
    # Overwrite with new decision
    await cache.cache_decision("user1", "read", "/file.txt", False, "Updated", 600)
    
    # Should have updated values
    decision = await cache.get_decision("user1", "read", "/file.txt")
    assert decision["decision"] is False
    assert decision["reason"] == "Updated"
    
    # Should still be only one entry
    assert len(cache._cache) == 1


def test_cleanup_expired():
    cache = PolicyCache()
    
    # Add entries with different TTLs
    current_time = time.time()
    
    # Add expired entry
    cache._cache["expired"] = {"decision": True}
    cache._ttl["expired"] = current_time - 100  # Expired
    
    # Add valid entry
    cache._cache["valid"] = {"decision": False}
    cache._ttl["valid"] = current_time + 300  # Valid
    
    # Cleanup
    cache.cleanup_expired()
    
    assert "expired" not in cache._cache
    assert "expired" not in cache._ttl
    assert "valid" in cache._cache
    assert "valid" in cache._ttl


def test_clear_cache():
    cache = PolicyCache()
    
    # Add some entries
    asyncio.run(cache.cache_decision("user1", "read", "/file1", True, "OK", 300))
    asyncio.run(cache.cache_decision("user2", "write", "/file2", False, "No", 300))
    
    assert len(cache._cache) == 2
    assert len(cache._ttl) == 2
    
    # Clear all
    cache.clear_cache()
    
    assert len(cache._cache) == 0
    assert len(cache._ttl) == 0


def test_clear_for_identity():
    cache = PolicyCache()
    
    # Add entries for different identities
    asyncio.run(cache.cache_decision("user1", "read", "/file1", True, "OK", 300))
    asyncio.run(cache.cache_decision("user1", "write", "/file2", False, "No", 300))
    asyncio.run(cache.cache_decision("user2", "read", "/file3", True, "OK", 300))
    
    assert len(cache._cache) == 3
    
    # Clear for user1
    cache.clear_for_identity("user1")
    
    assert len(cache._cache) == 1
    
    # Only user2's entry should remain
    remaining_key = list(cache._cache.keys())[0]
    assert remaining_key.startswith("user2:")


def test_clear_for_resource():
    cache = PolicyCache()
    
    # Add entries for different resources
    asyncio.run(cache.cache_decision("user1", "read", "/secret.txt", True, "OK", 300))
    asyncio.run(cache.cache_decision("user2", "write", "/secret.txt", False, "No", 300))
    asyncio.run(cache.cache_decision("user1", "read", "/public.txt", True, "OK", 300))
    
    assert len(cache._cache) == 3
    
    # Clear for /secret.txt
    cache.clear_for_resource("/secret.txt")
    
    assert len(cache._cache) == 1
    
    # Only /public.txt entry should remain
    remaining_key = list(cache._cache.keys())[0]
    assert remaining_key.endswith(":/public.txt")


def test_get_stats():
    cache = PolicyCache()
    
    # Add mixed allow/deny decisions
    asyncio.run(cache.cache_decision("user1", "read", "/file1", True, "OK", 300))
    asyncio.run(cache.cache_decision("user2", "write", "/file2", False, "No", 300))
    asyncio.run(cache.cache_decision("user3", "read", "/file3", True, "OK", 300))
    
    # Add an expired entry
    current_time = time.time()
    cache._cache["expired"] = {"decision": False}
    cache._ttl["expired"] = current_time - 100
    
    stats = cache.get_stats()
    
    # Should clean up expired entries first
    assert stats["total_entries"] == 3  # Expired entry removed
    assert stats["decisions_by_result"]["allow"] == 2
    assert stats["decisions_by_result"]["deny"] == 1
    assert "avg_ttl_remaining" in stats


def test_get_stats_empty():
    cache = PolicyCache()
    
    stats = cache.get_stats()
    
    assert stats["total_entries"] == 0
    assert stats["decisions_by_result"]["allow"] == 0
    assert stats["decisions_by_result"]["deny"] == 0
    assert stats["avg_ttl_remaining"] == 0


@pytest.mark.asyncio
async def test_multiple_users_same_resource():
    cache = PolicyCache()
    
    # Different users, same resource, different decisions
    await cache.cache_decision("admin", "delete", "/file.txt", True, "Admin access", 300)
    await cache.cache_decision("user", "delete", "/file.txt", False, "No permission", 300)
    
    # Should be separate cache entries
    admin_decision = await cache.get_decision("admin", "delete", "/file.txt")
    user_decision = await cache.get_decision("user", "delete", "/file.txt")
    
    assert admin_decision["decision"] is True
    assert user_decision["decision"] is False
    assert len(cache._cache) == 2


@pytest.mark.asyncio
async def test_same_user_different_actions():
    cache = PolicyCache()
    
    # Same user, same resource, different actions
    await cache.cache_decision("user1", "read", "/file.txt", True, "Read OK", 300)
    await cache.cache_decision("user1", "write", "/file.txt", False, "Write denied", 300)
    
    # Should be separate cache entries
    read_decision = await cache.get_decision("user1", "read", "/file.txt")
    write_decision = await cache.get_decision("user1", "write", "/file.txt")
    
    assert read_decision["decision"] is True
    assert write_decision["decision"] is False
    assert len(cache._cache) == 2


@pytest.mark.asyncio
async def test_cache_key_special_characters():
    cache = PolicyCache()
    
    # Test with special characters in identifiers
    await cache.cache_decision(
        identity_id="user@domain.com",
        action="read:metadata",
        resource="/path/with spaces/file.txt",
        decision=True,
        reason="Special chars OK",
        ttl=300
    )
    
    decision = await cache.get_decision(
        "user@domain.com",
        "read:metadata", 
        "/path/with spaces/file.txt"
    )
    
    assert decision is not None
    assert decision["decision"] is True
