import pytest
import asyncio
import time
from plantangenet.omni.storage.notifications import ChangeNotifier, ChangeBuffer


@pytest.mark.asyncio
async def test_change_notifier_init():
    notifier = ChangeNotifier()
    assert len(notifier._callbacks) == 0


def test_add_callback():
    notifier = ChangeNotifier()
    
    def dummy_callback(change_data):
        pass
    
    notifier.add_callback(dummy_callback)
    assert len(notifier._callbacks) == 1
    assert dummy_callback in notifier._callbacks


def test_add_multiple_callbacks():
    notifier = ChangeNotifier()
    
    def callback1(change_data):
        pass
    
    def callback2(change_data):
        pass
    
    notifier.add_callback(callback1)
    notifier.add_callback(callback2)
    
    assert len(notifier._callbacks) == 2
    assert callback1 in notifier._callbacks
    assert callback2 in notifier._callbacks


def test_remove_callback():
    notifier = ChangeNotifier()
    
    def dummy_callback(change_data):
        pass
    
    notifier.add_callback(dummy_callback)
    assert len(notifier._callbacks) == 1
    
    success = notifier.remove_callback(dummy_callback)
    assert success is True
    assert len(notifier._callbacks) == 0


def test_remove_nonexistent_callback():
    notifier = ChangeNotifier()
    
    def dummy_callback(change_data):
        pass
    
    success = notifier.remove_callback(dummy_callback)
    assert success is False


@pytest.mark.asyncio
async def test_notify_change_sync_callback():
    notifier = ChangeNotifier()
    received_changes = []
    
    def sync_callback(change_data):
        received_changes.append(change_data)
    
    notifier.add_callback(sync_callback)
    
    await notifier.notify_change(
        omni_id="test1",
        field_name="status",
        old_value="inactive",
        new_value="active",
        identity_id="user1"
    )
    
    assert len(received_changes) == 1
    change = received_changes[0]
    assert change["omni_id"] == "test1"
    assert change["field"] == "status"
    assert change["old_value"] == "inactive"
    assert change["new_value"] == "active"
    assert change["identity_id"] == "user1"
    assert "timestamp" in change


@pytest.mark.asyncio
async def test_notify_change_async_callback():
    notifier = ChangeNotifier()
    received_changes = []
    
    async def async_callback(change_data):
        received_changes.append(change_data)
    
    notifier.add_callback(async_callback)
    
    await notifier.notify_change(
        omni_id="test1",
        field_name="value",
        old_value=10,
        new_value=20
    )
    
    assert len(received_changes) == 1
    change = received_changes[0]
    assert change["omni_id"] == "test1"
    assert change["field"] == "value"
    assert change["old_value"] == 10
    assert change["new_value"] == 20
    assert change["identity_id"] is None


@pytest.mark.asyncio
async def test_notify_change_multiple_callbacks():
    notifier = ChangeNotifier()
    sync_received = []
    async_received = []
    
    def sync_callback(change_data):
        sync_received.append(change_data)
    
    async def async_callback(change_data):
        async_received.append(change_data)
    
    notifier.add_callback(sync_callback)
    notifier.add_callback(async_callback)
    
    await notifier.notify_change("test1", "field", "old", "new")
    
    assert len(sync_received) == 1
    assert len(async_received) == 1
    assert sync_received[0]["omni_id"] == "test1"
    assert async_received[0]["omni_id"] == "test1"


@pytest.mark.asyncio
async def test_notify_change_no_callbacks():
    notifier = ChangeNotifier()
    
    # Should not raise error with no callbacks
    await notifier.notify_change("test1", "field", "old", "new")


@pytest.mark.asyncio
async def test_notify_change_callback_exception():
    notifier = ChangeNotifier()
    working_received = []
    
    def failing_callback(change_data):
        raise ValueError("Callback error")
    
    def working_callback(change_data):
        working_received.append(change_data)
    
    notifier.add_callback(failing_callback)
    notifier.add_callback(working_callback)
    
    # Should not raise error, and working callback should still be called
    await notifier.notify_change("test1", "field", "old", "new")
    
    assert len(working_received) == 1


def test_clear_callbacks():
    notifier = ChangeNotifier()
    
    def callback1(change_data):
        pass
    
    def callback2(change_data):
        pass
    
    notifier.add_callback(callback1)
    notifier.add_callback(callback2)
    assert len(notifier._callbacks) == 2
    
    notifier.clear_callbacks()
    assert len(notifier._callbacks) == 0


def test_get_callback_count():
    notifier = ChangeNotifier()
    
    assert notifier.get_callback_count() == 0
    
    def dummy_callback(change_data):
        pass
    
    notifier.add_callback(dummy_callback)
    assert notifier.get_callback_count() == 1


@pytest.mark.asyncio
async def test_cleanup():
    notifier = ChangeNotifier()
    
    def dummy_callback(change_data):
        pass
    
    notifier.add_callback(dummy_callback)
    assert len(notifier._callbacks) == 1
    
    await notifier.cleanup()
    assert len(notifier._callbacks) == 0


# ChangeBuffer tests

@pytest.mark.asyncio
async def test_change_buffer_init():
    notifier = ChangeNotifier()
    buffer = ChangeBuffer(notifier, buffer_time=0.1)
    
    assert buffer.notifier == notifier
    assert buffer.buffer_time == 0.1
    assert len(buffer._buffer) == 0


@pytest.mark.asyncio
async def test_change_buffer_add_change():
    notifier = ChangeNotifier()
    buffer = ChangeBuffer(notifier, buffer_time=0.05)
    
    await buffer.add_change("test1", "field", "old", "new", "user1")
    
    assert len(buffer._buffer) == 1
    change = buffer._buffer[0]
    assert change["omni_id"] == "test1"
    assert change["field"] == "field"
    assert change["old_value"] == "old"
    assert change["new_value"] == "new"
    assert change["identity_id"] == "user1"


@pytest.mark.asyncio
async def test_change_buffer_flush():
    notifier = ChangeNotifier()
    received_batches = []
    
    async def batch_callback(changes):
        received_batches.append(changes)
    
    buffer = ChangeBuffer(notifier, buffer_time=0.05)
    buffer.add_batch_callback(batch_callback)
    
    # Add changes
    await buffer.add_change("test1", "field1", "old1", "new1")
    await buffer.add_change("test2", "field2", "old2", "new2")
    
    # Manually flush
    await buffer.flush()
    
    assert len(received_batches) == 1
    batch = received_batches[0]
    assert len(batch) == 2
    assert batch[0]["omni_id"] == "test1"
    assert batch[1]["omni_id"] == "test2"
    
    # Buffer should be empty after flush
    assert len(buffer._buffer) == 0


@pytest.mark.asyncio
async def test_change_buffer_auto_flush():
    notifier = ChangeNotifier()
    received_batches = []
    
    async def batch_callback(changes):
        received_batches.append(changes)
    
    buffer = ChangeBuffer(notifier, buffer_time=0.02)  # Very short buffer time
    buffer.add_batch_callback(batch_callback)
    
    # Add change
    await buffer.add_change("test1", "field1", "old1", "new1")
    
    # Wait for auto-flush
    await asyncio.sleep(0.05)
    
    # Should have auto-flushed
    assert len(received_batches) == 1
    assert len(received_batches[0]) == 1


@pytest.mark.asyncio
async def test_change_buffer_multiple_batches():
    notifier = ChangeNotifier()
    received_batches = []
    
    async def batch_callback(changes):
        received_batches.append(changes)
    
    buffer = ChangeBuffer(notifier, buffer_time=0.05)
    buffer.add_batch_callback(batch_callback)
    
    # Add first batch
    await buffer.add_change("test1", "field1", "old1", "new1")
    await buffer.flush()
    
    # Add second batch
    await buffer.add_change("test2", "field2", "old2", "new2")
    await buffer.add_change("test3", "field3", "old3", "new3")
    await buffer.flush()
    
    assert len(received_batches) == 2
    assert len(received_batches[0]) == 1
    assert len(received_batches[1]) == 2


def test_change_buffer_clear():
    notifier = ChangeNotifier()
    buffer = ChangeBuffer(notifier)
    
    # Add changes
    asyncio.run(buffer.add_change("test1", "field1", "old1", "new1"))
    asyncio.run(buffer.add_change("test2", "field2", "old2", "new2"))
    
    assert len(buffer._buffer) == 2
    
    buffer.clear()
    assert len(buffer._buffer) == 0


@pytest.mark.asyncio
async def test_change_buffer_get_stats():
    notifier = ChangeNotifier()
    buffer = ChangeBuffer(notifier)
    
    # Add changes
    await buffer.add_change("test1", "field1", "old1", "new1")
    await buffer.add_change("test2", "field2", "old2", "new2")
    
    stats = buffer.get_stats()
    
    assert stats["buffered_changes"] == 2
    assert stats["buffer_time"] == 0.1  # Default
    assert "oldest_change_age" in stats


@pytest.mark.asyncio
async def test_change_buffer_cleanup():
    notifier = ChangeNotifier()
    buffer = ChangeBuffer(notifier)
    
    # Add changes
    await buffer.add_change("test1", "field1", "old1", "new1")
    
    await buffer.cleanup()
    
    # Should cancel flush task and clear buffer
    assert len(buffer._buffer) == 0
    if buffer._flush_task:
        # Wait a bit for task to actually be cancelled
        await asyncio.sleep(0.01)
        assert buffer._flush_task.cancelled() or buffer._flush_task.done()


@pytest.mark.asyncio
async def test_timestamp_consistency():
    notifier = ChangeNotifier()
    received_changes = []
    
    def callback(change_data):
        received_changes.append(change_data["timestamp"])
    
    notifier.add_callback(callback)
    
    # Notify multiple changes quickly
    start_time = time.time()
    for i in range(3):
        await notifier.notify_change(f"test{i}", "field", "old", "new")
    end_time = time.time()
    
    # All timestamps should be within the test duration
    assert len(received_changes) == 3
    for timestamp in received_changes:
        assert start_time <= timestamp <= end_time
    
    # Timestamps should be in order (or very close)
    for i in range(1, len(received_changes)):
        assert received_changes[i] >= received_changes[i-1]
