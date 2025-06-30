import pytest
import asyncio
from plantangenet.mixins.heartbeat import HeartbeatMixin


class DummyHeartbeat(HeartbeatMixin):
    def __init__(self):
        # No super().__init__ needed unless mixin chain requires it
        self._heartbeat__tick = 0.0
        self._heartbeat__interval = 1.0
        self._heartbeat_healthy_interval = 5.0
        self._on_heartbeat_called = False
        self._on_heartbeat_message = None

    async def on_heartbeat(self, message: dict):
        self._on_heartbeat_called = True
        self._on_heartbeat_message = message


@pytest.mark.asyncio
async def test_handle_heartbeat_updates_tick_and_interval():
    hb = DummyHeartbeat()

    before = hb.last_heartbeat
    await asyncio.sleep(0.01)

    await hb.handle_heartbeat({"foo": "bar"})

    after = hb.last_heartbeat

    assert after > before
    assert hb.heartbeat_interval > 0
    assert hb._on_heartbeat_called is True
    assert hb._on_heartbeat_message == {"foo": "bar"}


@pytest.mark.asyncio
async def test_healthy_property_true_when_recent():
    hb = DummyHeartbeat()

    # Simulate recent heartbeat
    await hb.handle_heartbeat({})
    assert hb.healthy is True


@pytest.mark.asyncio
async def test_healthy_property_false_when_old(monkeypatch):
    hb = DummyHeartbeat()

    # Simulate old heartbeat
    await hb.handle_heartbeat({})
    first_tick = hb.last_heartbeat

    # monkeypatch monotonic to simulate time passage
    monkeypatch.setattr(
        "plantangenet.mixins.heartbeat.monotonic", lambda: first_tick + 10)

    assert hb.healthy is False


def test_status_property_structure():
    hb = DummyHeartbeat()
    status = hb.status

    assert isinstance(status, dict)
    assert "heartbeat" in status
    assert "last_heartbeat" in status["heartbeat"]
    assert "heartbeat_interval" in status["heartbeat"]
