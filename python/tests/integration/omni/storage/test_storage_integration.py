import pytest
import asyncio
import time
from plantangenet.omni.storage import ManagedStorage, SimpleStorageAdapter
from plantangenet.omni.storage.backends import StorageBackend, BackendError


class DummyBackend(StorageBackend):
    """In-memory fake backend for integration testing"""
    def __init__(self):
        self.data_store = {}

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
        return True

    async def load_version(self, key: str, version_id: str = None) -> any:
        return None

    async def list_versions(self, key: str) -> list:
        return []

    async def health_check(self) -> bool:
        return True

    async def cleanup(self):
        self.data_store.clear()


class FailingBackend(StorageBackend):
    """Backend that always raises errors"""
    async def store_data(self, key: str, data: dict) -> bool:
        raise BackendError("write failed")

    async def load_data(self, key: str) -> dict:
        raise BackendError("load failed")

    async def delete_data(self, key: str) -> bool:
        raise BackendError("delete failed")

    async def list_keys(self, prefix: str = "") -> list:
        raise BackendError("list failed")

    async def store_version(self, key: str, version_id: str, data: any) -> bool:
        raise BackendError("store_version failed")

    async def load_version(self, key: str, version_id: str = None) -> any:
        raise BackendError("load_version failed")

    async def list_versions(self, key: str) -> list:
        raise BackendError("list_versions failed")

    async def health_check(self) -> bool:
        return False

    async def cleanup(self):
        pass


@pytest.mark.asyncio
async def test_write_back_sync():
    from plantangenet.omni.storage.core import SyncStrategy
    # Setup storage with write-back and short interval
    managed = ManagedStorage(sync_strategy=SyncStrategy.WRITE_BACK, max_memory_items=5, sync_interval=0.1)
    dummy = DummyBackend()
    managed.add_backend('dummy', dummy, is_primary=True)
    storage = SimpleStorageAdapter(managed)
    # Store data (should be in memory only initially)
    key = 'wb_test'
    data = {'val': 123}
    assert await storage.store_data(key, data)
    assert key not in dummy.data_store
    # Wait for sync interval
    await asyncio.sleep(0.2)
    assert key in dummy.data_store
    assert dummy.data_store[key] == data
    await storage.cleanup()


@pytest.mark.asyncio
async def test_write_through_failover():
    from plantangenet.omni.storage.core import SyncStrategy
    # Setup storage with write-through
    managed = ManagedStorage(sync_strategy=SyncStrategy.WRITE_THROUGH, max_memory_items=5)
    fail = FailingBackend()
    good = DummyBackend()
    managed.add_backend('primary', fail, is_primary=True)
    managed.add_backend('backup', good)
    storage = SimpleStorageAdapter(managed)
    # store should succeed via backup
    key = 'wt_test'
    data = {'val': 456}
    assert await storage.store_data(key, data)
    assert key in good.data_store
    await storage.cleanup()


@pytest.mark.asyncio
async def test_health_and_statistics():
    from plantangenet.omni.storage.core import SyncStrategy
    managed = ManagedStorage(sync_strategy=SyncStrategy.WRITE_THROUGH, max_memory_items=5)
    dummy = DummyBackend()
    managed.add_backend('dummy', dummy, is_primary=True)
    storage = SimpleStorageAdapter(managed)
    health = await storage.check_health()
    assert 'status' in health and 'backends' in health
    stats = await storage.get_statistics()
    assert 'cache' in stats and 'backends' in stats
    await storage.cleanup()
