import pytest
import time
from plantangenet.topics.wrapper import TopicsWrapper


@pytest.mark.asyncio
async def test_cooldown_blocks_second_call(monkeypatch):
    called = []

    async def handler(self, msg):
        called.append(msg)

    wrapper = TopicsWrapper("cool.topic", cooldown=1.0)
    wrapped = wrapper(handler)

    now = time.monotonic()
    monkeypatch.setattr("time.monotonic", lambda: now)
    d = object()

    await wrapped(d, {"n": 1})
    await wrapped(d, {"n": 2})  # should be blocked by cooldown

    assert len(called) == 1
