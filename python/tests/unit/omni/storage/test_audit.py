import pytest
import asyncio
import time
from datetime import datetime, timedelta
from plantangenet.omni.storage.audit import AuditLogger


@pytest.mark.asyncio
async def test_audit_logger_init():
    logger = AuditLogger(enabled=True, max_entries_per_omni=500)
    assert logger.enabled is True
    assert logger.max_entries_per_omni == 500
    assert len(logger._audit_log) == 0


@pytest.mark.asyncio
async def test_audit_logger_disabled():
    logger = AuditLogger(enabled=False)
    
    entry_id = await logger.log(
        omni_id="test1",
        action="write",
        field_name="status",
        old_value="old",
        new_value="new",
        identity_id="user1"
    )
    
    assert entry_id == ""
    assert len(logger._audit_log) == 0


@pytest.mark.asyncio
async def test_audit_logger_log_basic():
    logger = AuditLogger()
    
    entry_id = await logger.log(
        omni_id="test1",
        action="write",
        field_name="status",
        old_value="inactive",
        new_value="active",
        identity_id="user1"
    )
    
    assert entry_id.startswith("audit_")
    assert "test1" in logger._audit_log
    assert len(logger._audit_log["test1"]) == 1
    
    entry = logger._audit_log["test1"][0]
    assert entry["action"] == "write"
    assert entry["field"] == "status"
    assert entry["old_value"] == "inactive"
    assert entry["new_value"] == "active"
    assert entry["identity_id"] == "user1"
    assert "timestamp" in entry


@pytest.mark.asyncio
async def test_audit_logger_log_minimal():
    logger = AuditLogger()
    
    entry_id = await logger.log(
        omni_id="test1",
        action="delete"
    )
    
    assert entry_id.startswith("audit_")
    entry = logger._audit_log["test1"][0]
    assert entry["action"] == "delete"
    assert "field" not in entry
    assert "old_value" not in entry
    assert "new_value" not in entry
    assert entry["identity_id"] is None


@pytest.mark.asyncio
async def test_audit_logger_log_with_context():
    logger = AuditLogger()
    
    context = {"reason": "automated cleanup", "batch_id": "batch_123"}
    
    await logger.log(
        omni_id="test1",
        action="cleanup",
        context=context
    )
    
    entry = logger._audit_log["test1"][0]
    assert entry["action"] == "cleanup"
    assert entry["context"] == context


@pytest.mark.asyncio
async def test_audit_logger_multiple_entries():
    logger = AuditLogger()
    
    # Add multiple entries
    await logger.log("test1", "create", identity_id="user1")
    await logger.log("test1", "update", field_name="name", old_value="old", new_value="new")
    await logger.log("test1", "delete", identity_id="user2")
    
    assert len(logger._audit_log["test1"]) == 3
    
    # Check chronological order
    entries = logger._audit_log["test1"]
    assert entries[0]["action"] == "create"
    assert entries[1]["action"] == "update"
    assert entries[2]["action"] == "delete"


@pytest.mark.asyncio
async def test_audit_logger_max_entries_trimming():
    logger = AuditLogger(max_entries_per_omni=3)
    
    # Add more entries than the limit
    for i in range(5):
        await logger.log("test1", f"action_{i}")
    
    # Should only keep the last 3 entries
    assert len(logger._audit_log["test1"]) == 3
    
    entries = logger._audit_log["test1"]
    assert entries[0]["action"] == "action_2"
    assert entries[1]["action"] == "action_3"
    assert entries[2]["action"] == "action_4"


@pytest.mark.asyncio
async def test_audit_logger_get_log():
    logger = AuditLogger()
    
    # Add entries with slight time delays to test ordering
    await logger.log("test1", "action_1")
    time.sleep(0.01)
    await logger.log("test1", "action_2")
    time.sleep(0.01)
    await logger.log("test1", "action_3")
    
    # Get all entries
    entries = await logger.get_log("test1")
    assert len(entries) == 3
    assert entries[0]["action"] == "action_1"  # Earliest first
    assert entries[2]["action"] == "action_3"  # Latest last


@pytest.mark.asyncio
async def test_audit_logger_get_log_with_limit():
    logger = AuditLogger()
    
    # Add 5 entries
    for i in range(5):
        await logger.log("test1", f"action_{i}")
    
    # Get with limit
    entries = await logger.get_log("test1", limit=3)
    assert len(entries) == 3
    
    # Should get the most recent 3
    assert entries[0]["action"] == "action_2"
    assert entries[1]["action"] == "action_3"
    assert entries[2]["action"] == "action_4"


@pytest.mark.asyncio
async def test_audit_logger_get_log_with_since():
    logger = AuditLogger()
    
    # Add entry, wait, add more entries
    await logger.log("test1", "old_action")
    time.sleep(0.1)
    
    cutoff_time = datetime.now()
    time.sleep(0.1)
    
    await logger.log("test1", "new_action_1")
    await logger.log("test1", "new_action_2")
    
    # Get entries since cutoff
    entries = await logger.get_log("test1", since=cutoff_time)
    assert len(entries) == 2
    assert entries[0]["action"] == "new_action_1"
    assert entries[1]["action"] == "new_action_2"


@pytest.mark.asyncio
async def test_audit_logger_get_log_nonexistent():
    logger = AuditLogger()
    
    entries = await logger.get_log("nonexistent")
    assert entries == []


@pytest.mark.asyncio
async def test_audit_logger_get_log_disabled():
    logger = AuditLogger(enabled=False)
    
    entries = await logger.get_log("test1")
    assert entries == []


def test_audit_logger_get_stats():
    logger = AuditLogger()
    
    stats = logger.get_stats()
    assert stats["enabled"] is True
    assert stats["omnis_with_audit"] == 0
    assert stats["total_entries"] == 0


@pytest.mark.asyncio
async def test_audit_logger_get_stats_with_data():
    logger = AuditLogger()
    
    await logger.log("test1", "action1")
    await logger.log("test1", "action2")
    await logger.log("test2", "action3")
    
    stats = logger.get_stats()
    assert stats["omnis_with_audit"] == 2
    assert stats["total_entries"] == 3


def test_audit_logger_clear_log():
    logger = AuditLogger()
    
    # Add entries to multiple omnis
    asyncio.run(logger.log("test1", "action1"))
    asyncio.run(logger.log("test2", "action2"))
    
    # Clear one omni's log
    logger.clear_log("test1")
    
    assert "test1" not in logger._audit_log
    assert "test2" in logger._audit_log


def test_audit_logger_clear_all_logs():
    logger = AuditLogger()
    
    # Add entries
    asyncio.run(logger.log("test1", "action1"))
    asyncio.run(logger.log("test2", "action2"))
    
    # Clear all
    logger.clear_all_logs()
    
    assert len(logger._audit_log) == 0


@pytest.mark.asyncio
async def test_audit_logger_cleanup():
    logger = AuditLogger()
    
    # Should complete without error
    await logger.cleanup()
