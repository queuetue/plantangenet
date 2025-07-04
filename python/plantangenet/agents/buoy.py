# Copyright (c) 1998-2025 Scott Russell
# SPDX-License-Identifier: MIT
__version__ = "0.1.0"
from plantangenet.logger import Logger
from plantangenet.mixins.timebase import TimebaseMixin
from plantangenet.mixins.heartbeat import HeartbeatMixin
from plantangenet.mixins.topics import TopicsMixin
from plantangenet.mixins.omni import OmniMixin
from .shard import Shard

__all__ = ["Buoy", "__version__"]


class Buoy(Shard, TimebaseMixin, HeartbeatMixin, OmniMixin, TopicsMixin):

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
