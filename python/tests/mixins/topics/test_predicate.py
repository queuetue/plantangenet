import pytest
from plantangenet.mixins.topics.wrapper import TopicsWrapper


@pytest.mark.asyncio
async def test_predicate_blocks():
    called = []

    async def handler(self, msg):
        called.append(msg)

    wrapper = TopicsWrapper(
        "pred.topic", predicate=lambda m: m.get("pass", False))
    wrapped = wrapper(handler)

    d = object()

    await wrapped(d, {"pass": False})
    await wrapped(d, {"pass": True})

    assert len(called) == 1
    assert called[0] == {"pass": True}
