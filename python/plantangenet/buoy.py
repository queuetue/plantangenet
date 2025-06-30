# Copyright (c) 1998-2025 Scott Russell
# SPDX-License-Identifier: MIT
__version__ = "0.1.0"
from .logger import Logger
from .shard import Shard
from .mixins.timebase import TimebaseMixin
from .mixins.heartbeat import HeartbeatMixin
from .mixins.topics.mixin import TopicsMixin
from .mixins.status.mixin import StatusMixin

__all__ = ["Buoy", "__version__"]


class Buoy(Shard, TimebaseMixin, HeartbeatMixin, StatusMixin, TopicsMixin):

    async def on_heartbeat(self, message: dict): ...

    def __init__(self, namespace: str, logger: Logger, redis_prefix: str = "root", **kwargs):
        super().__init__(
            namespace=namespace, logger=logger, storage_prefix=redis_prefix, **kwargs)

    def __str__(self):
        return f"@{self.short_id}|{self.name}"

    async def setup(self, *args, **kwargs) -> None:
        print("Setting up Buoy")
        await super().setup(*args, **kwargs)

    async def update(self) -> bool:
        return await super().update()
