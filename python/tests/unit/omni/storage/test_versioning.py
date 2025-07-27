import pytest
import time
import asyncio
from datetime import datetime
from plantangenet.omni.storage.versioning import VersionManager


@pytest.mark.asyncio
async def test_version_manager_init():
    manager = VersionManager(max_versions_per_omni=5)
    assert manager.max_versions_per_omni == 5
    assert len(manager._versions) == 0


@pytest.mark.asyncio
async def test_store_version_basic():
    manager = VersionManager()
    
    version_data = {"config": {"param1": 100, "param2": "test"}}
    version_id = await manager.store_version("omni1", version_data)
    
    assert version_id.startswith("v_")
    assert "omni1" in manager._versions
    assert len(manager._versions["omni1"]) == 1
    
    stored_version = manager._versions["omni1"][0]
    assert stored_version["version_id"] == version_id
    assert stored_version["data"] == version_data
    assert "timestamp" in stored_version


@pytest.mark.asyncio
async def test_store_version_with_timestamp():
    manager = VersionManager()
    
    custom_timestamp = time.time() - 3600  # 1 hour ago
    version_data = {"value": 42}
    
    version_id = await manager.store_version("omni1", version_data, custom_timestamp)
    
    stored_version = manager._versions["omni1"][0]
    assert stored_version["timestamp"] == custom_timestamp
    assert version_id == f"v_{int(custom_timestamp * 1000)}"


@pytest.mark.asyncio
async def test_store_multiple_versions():
    manager = VersionManager()
    
    # Store multiple versions with slight delays
    version1 = await manager.store_version("omni1", {"value": 1})
    time.sleep(0.01)
    version2 = await manager.store_version("omni1", {"value": 2})
    time.sleep(0.01)
    version3 = await manager.store_version("omni1", {"value": 3})
    
    assert len(manager._versions["omni1"]) == 3
    
    # Should be sorted by timestamp (earliest first)
    versions = manager._versions["omni1"]
    assert versions[0]["data"]["value"] == 1
    assert versions[1]["data"]["value"] == 2
    assert versions[2]["data"]["value"] == 3


@pytest.mark.asyncio
async def test_store_version_max_limit():
    manager = VersionManager(max_versions_per_omni=3)
    
    # Store more versions than the limit
    for i in range(5):
        await manager.store_version("omni1", {"value": i})
        time.sleep(0.01)  # Ensure different timestamps
    
    # Should only keep the last 3 versions
    assert len(manager._versions["omni1"]) == 3
    
    versions = manager._versions["omni1"]
    assert versions[0]["data"]["value"] == 2  # Oldest kept
    assert versions[1]["data"]["value"] == 3
    assert versions[2]["data"]["value"] == 4  # Newest


@pytest.mark.asyncio
async def test_load_version_latest():
    manager = VersionManager()
    
    # Store multiple versions
    await manager.store_version("omni1", {"value": 1})
    time.sleep(0.01)
    await manager.store_version("omni1", {"value": 2})
    time.sleep(0.01)
    latest_data = {"value": 3}
    await manager.store_version("omni1", latest_data)
    
    # Load latest version (no version_id specified)
    loaded = await manager.load_version("omni1")
    assert loaded == latest_data


@pytest.mark.asyncio
async def test_load_version_specific():
    manager = VersionManager()
    
    # Store versions
    version1_data = {"value": 1}
    version1_id = await manager.store_version("omni1", version1_data)
    time.sleep(0.01)
    version2_data = {"value": 2}
    version2_id = await manager.store_version("omni1", version2_data)
    
    # Load specific version
    loaded = await manager.load_version("omni1", version1_id)
    assert loaded == version1_data
    
    loaded = await manager.load_version("omni1", version2_id)
    assert loaded == version2_data


@pytest.mark.asyncio
async def test_load_version_nonexistent_omni():
    manager = VersionManager()
    
    loaded = await manager.load_version("nonexistent")
    assert loaded is None


@pytest.mark.asyncio
async def test_load_version_nonexistent_version():
    manager = VersionManager()
    
    await manager.store_version("omni1", {"value": 1})
    
    loaded = await manager.load_version("omni1", "nonexistent_version")
    assert loaded is None


@pytest.mark.asyncio
async def test_load_version_empty_versions():
    manager = VersionManager()
    
    # Create empty version list
    manager._versions["omni1"] = []
    
    loaded = await manager.load_version("omni1")
    assert loaded is None


@pytest.mark.asyncio
async def test_list_versions():
    manager = VersionManager()
    
    # Store versions with known timestamps
    timestamps = []
    for i in range(3):
        timestamp = time.time() + i  # Future timestamps for predictability
        await manager.store_version("omni1", {"value": i}, timestamp)
        timestamps.append(timestamp)
    
    # List versions
    versions = await manager.list_versions("omni1")
    
    assert len(versions) == 3
    
    # Should be in reverse order (most recent first)
    assert versions[0]["datetime"] is not None
    assert "version_id" in versions[0]
    assert "timestamp" in versions[0]
    
    # Verify order (most recent first)
    for i in range(2):
        assert versions[i]["timestamp"] > versions[i + 1]["timestamp"]


@pytest.mark.asyncio
async def test_list_versions_with_limit():
    manager = VersionManager()
    
    # Store 5 versions
    for i in range(5):
        await manager.store_version("omni1", {"value": i})
        time.sleep(0.01)
    
    # List with limit
    versions = await manager.list_versions("omni1", limit=3)
    
    assert len(versions) == 3
    # Should get the 3 most recent


@pytest.mark.asyncio
async def test_list_versions_nonexistent():
    manager = VersionManager()
    
    versions = await manager.list_versions("nonexistent")
    assert versions == []


def test_delete_version():
    manager = VersionManager()
    
    # Store versions
    version1_id = asyncio.run(manager.store_version("omni1", {"value": 1}))
    version2_id = asyncio.run(manager.store_version("omni1", {"value": 2}))
    
    assert len(manager._versions["omni1"]) == 2
    
    # Delete one version
    success = manager.delete_version("omni1", version1_id)
    assert success is True
    assert len(manager._versions["omni1"]) == 1
    
    # Verify the right version was deleted
    remaining = manager._versions["omni1"][0]
    assert remaining["version_id"] == version2_id


def test_delete_version_nonexistent():
    manager = VersionManager()
    
    # Try to delete from non-existent omni
    success = manager.delete_version("nonexistent", "version1")
    assert success is False
    
    # Try to delete non-existent version
    asyncio.run(manager.store_version("omni1", {"value": 1}))
    success = manager.delete_version("omni1", "nonexistent_version")
    assert success is False


def test_delete_all_versions():
    manager = VersionManager()
    
    # Store versions for multiple omnis
    asyncio.run(manager.store_version("omni1", {"value": 1}))
    asyncio.run(manager.store_version("omni1", {"value": 2}))
    asyncio.run(manager.store_version("omni2", {"value": 3}))
    
    assert len(manager._versions["omni1"]) == 2
    assert len(manager._versions["omni2"]) == 1
    
    # Delete all versions for omni1
    manager.delete_all_versions("omni1")
    
    assert "omni1" not in manager._versions
    assert "omni2" in manager._versions  # Should remain


def test_get_stats():
    manager = VersionManager()
    
    # Store versions for multiple omnis
    asyncio.run(manager.store_version("omni1", {"value": 1}))
    asyncio.run(manager.store_version("omni1", {"value": 2}))
    asyncio.run(manager.store_version("omni2", {"value": 3}))
    
    stats = manager.get_stats()
    
    assert stats["omnis_with_versions"] == 2
    assert stats["total_versions"] == 3
    assert stats["max_versions_per_omni"] == 10  # Default value


def test_get_stats_empty():
    manager = VersionManager()
    
    stats = manager.get_stats()
    
    assert stats["omnis_with_versions"] == 0
    assert stats["total_versions"] == 0


def test_clear_all_versions():
    manager = VersionManager()
    
    # Store versions
    asyncio.run(manager.store_version("omni1", {"value": 1}))
    asyncio.run(manager.store_version("omni2", {"value": 2}))
    
    assert len(manager._versions) == 2
    
    # Clear all
    manager.clear_all_versions()
    
    assert len(manager._versions) == 0


@pytest.mark.asyncio
async def test_version_data_types():
    manager = VersionManager()
    
    # Test different data types
    test_cases = [
        {"dict": {"nested": {"value": 42}}},
        [1, 2, 3, {"key": "value"}],
        "simple string",
        42,
        True,
        None
    ]
    
    version_ids = []
    for i, data in enumerate(test_cases):
        version_id = await manager.store_version(f"omni{i}", data)
        version_ids.append(version_id)
        loaded = await manager.load_version(f"omni{i}", version_id)
        assert loaded == data


@pytest.mark.asyncio
async def test_concurrent_version_storage():
    manager = VersionManager()
    
    # Simulate concurrent version storage
    async def store_version_task(value):
        return await manager.store_version("omni1", {"value": value})
    
    # Store multiple versions concurrently
    tasks = [store_version_task(i) for i in range(5)]
    version_ids = await asyncio.gather(*tasks)
    
    # All should succeed
    assert len(version_ids) == 5
    assert all(vid.startswith("v_") for vid in version_ids)
    
    # All versions should be stored
    assert len(manager._versions["omni1"]) == 5
