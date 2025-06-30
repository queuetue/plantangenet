# Copyright (c) 1998-2025 Scott Russell
# SPDX-License-Identifier: MIT
__version__ = "0.1.0"
from typing import Any, Callable
from .agent import Agent
from .logger import Logger
from .shard import Shard
from .mixins.timebase import TimebaseMixin
from .mixins.heartbeat import HeartbeatMixin
from .mixins.topics.mixin import TopicsMixin
from .mixins.status.mixin import StatusMixin

__all__ = ["Drift", "__version__"]


class Drift(Agent, TimebaseMixin, HeartbeatMixin, StatusMixin, TopicsMixin):

    async def on_heartbeat(self, message: dict): ...

    def __init__(self, gyre, namespace: str, logger: Logger, **kwargs):
        super().__init__(
            namespace=namespace, logger=logger, **kwargs)
        self._gyre = gyre

    def __str__(self):
        return f"{self.short_id}@@{self._gyre.short_id}|{self.name}"

    async def setup(self, *args, **kwargs) -> None: ...

    async def update(self) -> bool: ...

    async def publish(self, topic: str, data: Any):
        await self._gyre.publish(topic, data)

    async def subscribe(self, topic: str, callback: Callable):
        return await self._gyre.subscribe(topic, callback)

    async def get(self, key: str) -> Any:
        return await self._gyre.get(key)

    async def set(self, key: str, value: Any):
        return await self._gyre.set(key, value)

    async def delete(self, key: str):
        return await self._gyre.delete(key)

    @property
    def status(self) -> dict:
        status = super().status
        status[f'drift.{self.short_id}'] = {
            "attached_to": {
                "name": self._gyre.name,
                "id": self._gyre.id,
                "short_id": self._gyre.short_id,
            },
            "id": self.id,
            "name": self.name,
            "disposition": self.disposition,
            "namespace": self.namespace,
        }
        return status
