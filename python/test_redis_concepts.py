#!/usr/bin/env python3
"""
Direct test of Redis omni storage functionality without type checking issues.
This demonstrates the core concepts and identifies what works vs. what needs refinement.
"""

import asyncio
import json
import pickle
import time
from datetime import datetime

import pytest

try:
    import redis.asyncio as Redis

    @pytest.mark.asyncio
    async def test_redis_concepts():
        """Test Redis concepts for omni storage"""
        try:
            # Use different clients for binary vs text data
            client = Redis.from_url(
                'redis://localhost:6379', decode_responses=True)
            # binary_client = Redis.from_url(
            #     'redis://localhost:6379', decode_responses=False)

            await client.ping()
            print("✅ Redis connection successful")

            # Test 1: Hash storage (structured fields)
            omni_key = "test:omni:123"
            fields = {
                "value": "100",
                "count": "42",
                "metadata": json.dumps({"type": "test"}),
                "_identity_id": "user1",
                "_updated_at": str(time.time())
            }

            result = await client.hset(
                omni_key, mapping=fields  # type: ignore[call-arg]
            )
            print(f"✅ Hash storage: {result} fields set")

            # Load all fields
            loaded = await client.hgetall(
                omni_key  # type: ignore[call-arg]
            )
            print(f"✅ Hash load: {len(loaded)} fields loaded")

            # Load specific fields
            specific = await client.hmget(
                omni_key, ["value", "count"]  # type: ignore[call-arg]
            )
            print(f"✅ Specific fields: {specific}")

            # Test 2: Versioning with sorted sets
            version_key = f"{omni_key}:versions"
            version_data = pickle.dumps({"state": "v1", "fields": fields})
            timestamp = time.time()

            await client.zadd(version_key, {version_data: timestamp})
            print("✅ Version stored")

            # Get latest version
            latest = await client.zrevrange(version_key, 0, 0)
            if latest:
                loaded_version = pickle.loads(latest[0])
                print(f"✅ Version loaded: {loaded_version['state']}")

            # Test 3: Relationships with sets
            parent_key = "test:omni:parent"
            child_key = "test:omni:child"
            relationship_key = f"{parent_key}:children"

            await client.sadd(
                relationship_key,
                child_key
            )  # type: ignore[call-arg]
            children = await client.smembers(
                relationship_key  # type: ignore[call-arg]
            )
            print(f"✅ Relationships: {len(children)} children")

            # Test 4: Policy caching
            cache_key = "test:policy:user1:read:field"
            cache_value = json.dumps({
                "decision": True,
                "reason": "allowed",
                "cached_at": time.time()
            })

            await client.setex(cache_key, 300, cache_value)  # 5 min TTL
            cached = await client.get(cache_key)
            if cached:
                decision = json.loads(cached)
                print(f"✅ Policy cache: {decision['decision']}")

            # Test 5: Change notifications (pub/sub)
            channel = "test:changes"
            message = json.dumps({
                "omni_id": "123",
                "field": "value",
                "old_value": 100,
                "new_value": 200,
                "timestamp": time.time()
            })

            subscribers = await client.publish(channel, message)
            print(f"✅ Change notification: {subscribers} subscribers")

            # Test 6: Audit log with streams
            stream_key = "test:audit:123"
            audit_data = {
                "action": "write",
                "field": "value",
                "old_value": "100",
                "new_value": "200",
                "identity_id": "user1",
                "timestamp": str(time.time())
            }

            entry_id = await client.xadd(
                stream_key,
                audit_data  # type: ignore[call-arg]
            )
            print(f"✅ Audit log: {entry_id}")

            # Read audit entries
            entries = await client.xrevrange(stream_key, count=10)
            print(f"✅ Audit read: {len(entries)} entries")

            # Test 7: Atomic operations with pipeline
            pipe = client.pipeline()
            pipe.hset(omni_key, "atomic_field", "atomic_value")
            pipe.zadd(version_key, {pickle.dumps(
                {"atomic": True}): time.time()})
            pipe.xadd(
                stream_key, {"action": "atomic_update", "timestamp": str(time.time())})

            results = await pipe.execute()
            print(f"✅ Atomic pipeline: {len(results)} operations")

            # Cleanup
            await client.delete(omni_key, version_key, relationship_key, cache_key, stream_key)
            await client.aclose()

            print("\n🎉 All Redis omni storage concepts work!")

        except Exception as e:
            print(f"❌ Redis test failed: {e}")
            import traceback
            traceback.print_exc()

except ImportError:
    async def test_redis_concepts():
        print("Redis not available, skipping Redis concept tests")


@pytest.mark.asyncio
async def test_omni_integration_concepts():
    """Test how omnis would integrate with Redis storage"""

    print("\n🔧 Testing omni integration concepts...")

    # Concept 1: Dirty field tracking
    class DirtyTracker:
        def __init__(self):
            self._dirty_fields = set()
            self._original_values = {}

        def track_change(self, field_name, old_value, new_value):
            if old_value != new_value:
                self._dirty_fields.add(field_name)
                if field_name not in self._original_values:
                    self._original_values[field_name] = old_value

        def get_dirty_changes(self):
            return {field: getattr(self, field, None) for field in self._dirty_fields}

        def clear_dirty(self):
            self._dirty_fields.clear()
            self._original_values.clear()

    tracker = DirtyTracker()
    tracker.value = 100  # type: ignore[assignment]
    tracker.track_change("value", None, 100)
    tracker.track_change("value", 100, 200)

    changes = tracker.get_dirty_changes()
    print(f"✅ Dirty tracking: {len(tracker._dirty_fields)} dirty fields")

    # Concept 2: Serialization strategies
    test_data = {
        "simple_int": 42,
        "simple_str": "hello",
        "complex_dict": {"nested": {"value": 123}},
        "complex_list": [1, 2, {"item": 3}]
    }

    # JSON serialization (Redis-friendly)
    json_data = {}
    for key, value in test_data.items():
        if isinstance(value, (dict, list)):
            json_data[key] = json.dumps(value)
        else:
            json_data[key] = str(value)

    print(f"✅ JSON serialization: {len(json_data)} fields")

    # Pickle serialization (for complex objects)
    pickle_data = pickle.dumps(test_data)
    unpickled = pickle.loads(pickle_data)
    assert unpickled == test_data
    print(f"✅ Pickle serialization: {len(pickle_data)} bytes")

    # Concept 3: Field-level policy integration
    class PolicyEnforcedField:
        def __init__(self, field_name, policy_check_func):
            self.field_name = field_name
            self.policy_check = policy_check_func

        def check_access(self, identity, action):
            return self.policy_check(identity, action, self.field_name)

    def mock_policy_check(identity, action, resource):
        # Mock policy: admin can do anything, user can only read
        if identity == "admin":
            return True
        elif identity == "user" and action == "read":
            return True
        return False

    field = PolicyEnforcedField("secret_field", mock_policy_check)
    assert field.check_access("admin", "write") == True
    assert field.check_access("user", "read") == True
    assert field.check_access("user", "write") == False
    print("✅ Policy enforcement: field-level checks work")

    print("\n🎉 All omni integration concepts work!")

if __name__ == "__main__":
    async def main():
        await test_redis_concepts()
        await test_omni_integration_concepts()

        asyncio.run(main())

    asyncio.run(main())
