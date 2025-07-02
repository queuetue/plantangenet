import pytest
import asyncio
import time
from plantangenet.topics.wrapper import TopicsWrapper


@pytest.mark.asyncio
async def test_basic_invocation():
    called = {}

    async def handler(self, msg):
        called['msg'] = msg

    wrapper = TopicsWrapper("my.topic")
    wrapped = wrapper(handler)

    class Dummy:
        pass

    d = Dummy()
    await wrapped(d, {"foo": "bar"})

    assert called['msg'] == {"foo": "bar"}
