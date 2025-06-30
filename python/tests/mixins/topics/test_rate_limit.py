import pytest
from plantangenet.mixins.topics.wrapper import TopicsWrapper


@pytest.mark.asyncio
async def test_rate_limit(monkeypatch):
    called = []

    async def handler(self, msg):
        called.append(msg)

    wrapper = TopicsWrapper("rate.topic", rate_limit=2)  # 2 per sec
    wrapped = wrapper(handler)

    now = [100.0]

    def fake_time():
        return now[0]

    monkeypatch.setattr("time.monotonic", fake_time)

    d = object()

    await wrapped(d, {"n": 1})
    now[0] += 0.2
    await wrapped(d, {"n": 2})  # blocked
    now[0] += 0.5
    await wrapped(d, {"n": 3})  # allowed

    assert called == [{"n": 1}, {"n": 3}]
