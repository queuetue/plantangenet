import pytest
from plantangenet.mixins.topics.wrapper import TopicsWrapper


@pytest.mark.asyncio
async def test_mod_filtering():
    called = []

    async def handler(self, msg):
        called.append(msg)

    wrapper = TopicsWrapper("mod.topic", mod=3)
    wrapped = wrapper(handler)

    d = object()

    await wrapped(d, {"n": 1})
    await wrapped(d, {"n": 2})
    await wrapped(d, {"n": 3})  # fires here

    assert len(called) == 1
    assert called[0] == {"n": 3}
