import pytest
from plantangenet.mixins.topics.mixin import TopicsMixin
from plantangenet.mixins.topics import on_topic
from plantangenet import GLOBAL_LOGGER


class DummyBus(TopicsMixin):
    def __init__(self):
        self._ocean__logger = GLOBAL_LOGGER
        self.subscriptions = []
        super().__init__()

    async def subscribe(self, topic, callback):
        self.subscriptions.append((topic, callback))

    @on_topic("foo.bar")
    async def handle_foo(self, message):
        pass


@pytest.mark.asyncio
async def test_registers_topics():
    d = DummyBus()
    assert ("foo.bar", d.handle_foo) in d._topic_subscriptions

    await d.apply_topic_subscriptions()
    assert ("foo.bar", d.handle_foo) in d.subscriptions


def test_status_includes_topics():
    d = DummyBus()
    status = d.status
    assert "topic_subscriptions" in status
    assert ("foo.bar", d.handle_foo) in status["topic_subscriptions"]
