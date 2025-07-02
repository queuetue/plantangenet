import pytest
from plantangenet.topics.wrapper import TopicsWrapper


@pytest.mark.asyncio
async def test_once_blocks_after_first():
    called = []

    async def handler(self, msg):
        called.append(msg)

    wrapper = TopicsWrapper("once.topic", once=True)
    wrapped = wrapper(handler)

    d = object()

    await wrapped(d, {"n": 1})
    await wrapped(d, {"n": 2})

    assert called == [{"n": 1}]
