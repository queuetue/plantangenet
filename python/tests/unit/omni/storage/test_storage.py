import pytest
import asyncio
import time
from plantangenet.omni.storage import ManagedStorage, SimpleStorageAdapter
from plantangenet.omni.storage.backends import StorageBackend, BackendError


class DummyBackend(StorageBackend):
    """In-memory fake backend for testing"""
    def __init__(self):
        self.data_store = {}
        self.versions = {}

    async def store_data(self, key: str, data: dict) -> bool:
        self.data_store[key] = data.copy()
        return True

    async def load_data(self, key: str) -> dict:
        return self.data_store.get(key)

    async def delete_data(self, key: str) -> bool:
        self.data_store.pop(key, None)
        return True

    async def list_keys(self, prefix: str = "") -> list:
        return [k for k in self.data_store.keys() if k.startswith(prefix)]

    async def store_version(self, key: str, version_id: str, data: any) -> bool:
        self.versions.setdefault(key, []).append({"version_id": version_id, "data": data, "timestamp": time.time()})
        return True

    async def load_version(self, key: str, version_id: str = None) -> any:
        versions = self.versions.get(key, [])
        if version_id:
            for v in versions:
                if v["version_id"] == version_id:
                    return v["data"]
            return None
        return versions[-1]["data"] if versions else None

    async def list_versions(self, key: str) -> list:
        return [{"version_id": v["version_id"], "timestamp": v["timestamp"]} for v in self.versions.get(key, [])]

    async def health_check(self) -> bool:
        return True


@pytest.fixture
async def storage():
    from plantangenet.omni.storage.core import SyncStrategy
    managed = ManagedStorage(sync_strategy=SyncStrategy.WRITE_THROUGH, max_memory_items=3)
    managed.add_backend("primary", DummyBackend())
    storage = SimpleStorageAdapter(managed)
    await storage.initialize()
    yield storage
    await storage.cleanup()


@pytest.mark.asyncio
async def test_store_and_load(storage):
    key = 'item1'
    data = {'a': 1, 'b': 'two'}
    assert await storage.store_data(key, data)
    loaded = await storage.load_data(key)
    # Remove metadata fields before comparison
    if isinstance(loaded, dict):
        loaded = {k: v for k, v in loaded.items() if not k.startswith('_')}
    assert loaded == data


@pytest.mark.asyncio
async def test_delete_and_list_keys(storage):
    await storage.store_data('a1', {'x': 1})
    await storage.store_data('a2', {'x': 2})
    keys = storage.list_keys('a')
    assert set(keys) == {'a1', 'a2'}
    assert await storage.delete_data('a1')
    keys2 = storage.list_keys('a')
    assert 'a1' not in keys2 and 'a2' in keys2


@pytest.mark.asyncio
async def test_cache_eviction(storage):
    # cache size is 3
    for i in range(4):
        await storage.store_data(f'k{i}', {'v': i})
    stats = await storage.get_statistics()
    # one item should be evicted
    assert stats['cache']['size'] <= 3


@pytest.mark.asyncio
async def test_versioning(storage):
    key = 'ver1'
    v1 = 'v1'
    v2 = 'v2'
    data1 = {'n': 1}
    data2 = {'n': 2}
    assert await storage.store_version(key, v1, data1)
    assert await storage.store_version(key, v2, data2)
    versions = await storage.list_versions(key)
    assert [v['version_id'] for v in versions] == [v1, v2]
    assert await storage.load_version(key, v1) == data1
    assert await storage.load_version(key) == data2


@pytest.mark.asyncio
async def test_relationships(storage):
    subj = 's'
    obj = 'o'
    await storage.store_relationship(subj, 'rel', obj)
    related = await storage.get_related(subj, 'rel')
    assert related == [obj]
    rev = await storage.get_related(obj, 'rel', reverse=True)
    assert rev == [subj]
    await storage.remove_relationship(subj, 'rel', obj)
    assert await storage.get_related(subj, 'rel') == []


@pytest.mark.asyncio
async def test_policy_cache(storage):
    identity, action, resource = 'id1', 'a', 'r'
    await storage.cache_policy_decision(identity, action, resource, True, 'ok', ttl=1)
    val = await storage.get_cached_policy(identity, action, resource)
    assert val['decision'] is True
    # wait for expiry
    await asyncio.sleep(1.1)
    val2 = await storage.get_cached_policy(identity, action, resource)
    assert val2 is None


@pytest.mark.asyncio
async def test_notifications(storage):
    events = []
    def cb(key, old, new):
        events.append((key, old, new))
    storage.notifications.add_callback('data_changed', cb)
    await storage.store_data('n1', {'v': 0})
    await storage.store_data('n1', {'v': 1})
    assert events[0][0] == 'n1'
    assert events[-1][2]['v'] == 1

# Test health and stats
@pytest.mark.asyncio
async def test_health_and_stats(storage):
    health = await storage.check_health()
    assert health['status'] == 'healthy'
    stats = await storage.get_statistics()
    assert 'cache' in stats and 'backends' in stats
