# Copyright (c) 1998-2025 Scott Russell
# SPDX-License-Identifier: MIT

import pytest
from plantangenet.omni.mixins.rox import RoxMixin, WinLoseDraw, a_vs_b, CHOICES
from ulid import ULID
from coolname import generate_slug
from plantangenet.omni.mixins.topic import TopicsMixin
from plantangenet.topics import on_topic


class DummyBus(TopicsMixin):
    def __init__(self):
        # Initialize required ocean attributes for mixin compatibility
        self._ocean__id = str(ULID())
        self._ocean__namespace = "test"
        self._ocean__nickname = generate_slug(2)
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
