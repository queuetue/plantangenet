import pytest
from plantangenet.mixins.topics.wrapper import TopicsWrapper


@pytest.mark.asyncio
async def test_changed_only_on_new_value():
    called = []

    async def handler(self, msg):
        called.append(msg)

    wrapper = TopicsWrapper("change.topic", changed=True)
    wrapped = wrapper(handler)

    d = object()

    await wrapped(d, {"val": 1})
    await wrapped(d, {"val": 1})  # should be blocked
    await wrapped(d, {"val": 2})

    assert len(called) == 2
