# Copyright (c) 1998-2025 Scott Russell
# SPDX-License-Identifier: MIT

from typing import Any, List, Optional, Callable
from plantangenet.logger import Logger
from plantangenet.omni.mixins.storage import StorageMixin
from plantangenet.omni.mixins.transport import TransportMixin
from plantangenet.omni.mixins.topic import TopicsMixin
from plantangenet.omni.mixins.omni import OmniMixin
from .agent import Agent


class Float(Agent, StorageMixin, OmniMixin, TransportMixin, TopicsMixin):
    """
    A localized peer representing a usable slice of a distributed process.

    Float maintain partial state, handle scoped messages, and operate under
    shared protocol constraints.
    ----
    Earth's oceans are littered with microplastics and other pollutants,
    carried by currents and gyres. Please support the environment-and consider the
    data center running this code as part of our shared planetary ecosystem.
    """

    def __init__(self,
                 namespace: str,
                 logger: Logger,
                 storage_prefix: str = "root",
                 ttl: int = 600,
                 gyre: Optional[Any] = None):
        self._ocean__ttl: int = ttl
        self._gyre: Optional[Float] = gyre
        Agent.__init__(self, namespace=namespace, logger=logger)
        StorageMixin.__init__(self, prefix=storage_prefix)
        TransportMixin.__init__(self)
        TopicsMixin.__init__(self)

    def __str__(self):
        if self._gyre is None:
            return f"{self.short_id}|{self.name}"
        else:
            return f"{self.short_id}+{self._gyre.short_id}|{self.name}"

    @property
    def message_types(self):
        """Return the peer's message types."""
        result = super().message_types
        result.update([
            "shard.handle_message",
        ])
        return result

    async def setup(self,  *args, **kwargs) -> None:
        transport_urls = kwargs.get('transport_urls', [])
        storage_urls = kwargs.get('storage_urls', [])
        await self.setup_transport(transport_urls)
        await self.setup_storage(storage_urls)

    async def update(self) -> bool:
        await self.update_storage()
        await self.update_transport()
        return True

    async def teardown(self):
        await self.teardown_transport()
        await self.teardown_storage()

    async def handle_message(self, message):
        """Handle incoming messages from the cluster."""
        self._ocean__logger.info(f"Shard received message: {message.data}")

    async def publish(self, topic: str, data: Any):
        if self._gyre is None:
            await super().publish(topic, data)
        else:
            await self._gyre.publish(topic, data)

    async def subscribe(self, topic: str, callback: Callable):
        if self._gyre is None:
            await super().subscribe(topic, callback)
        else:
            await self._gyre.subscribe(topic, callback)

    async def get(self, key: str, actor=None) -> Optional[str]:
        """
        Get a value from the store.
        """
        if self._gyre is None:
            return await super().get(key)
        else:
            return await self._gyre.get(key)

    async def set(self, key: str, value: Any, nx: bool = False, ttl: Optional[int] = None, actor=None) -> Optional[list]:
        if self._gyre is None:
            return await super().set(key, value, nx=nx, ttl=ttl, actor=actor)
        else:
            return await self._gyre.set(key, value, nx=nx, ttl=ttl, actor=actor)

    async def delete(self, key: str, actor=None) -> Optional[list]:
        if self._gyre is None:
            return await super().delete(key)
        else:
            return await self._gyre.delete(key)

    async def keys(self, pattern: str = "*", actor=None) -> List[str]:
        if self._gyre is None:
            return await super().keys(pattern, actor=actor)
        else:
            return await self._gyre.keys(pattern, actor=actor)

    async def exists(self, key: str, actor=None) -> bool:
        if self._gyre is None:
            return await super().exists(key, actor=actor)
        else:
            return await self._gyre.exists(key, actor=actor)

    @property
    def ttl(self) -> int:
        """Return the time-to-live for the peer."""
        return self._ocean__ttl

    @ttl.setter
    def ttl(self, value: int):
        """Set the time-to-live for the peer."""
        if value <= 0:
            raise ValueError("TTL must be a positive integer")
        self._ocean__ttl = value

    @property
    def status(self) -> dict:
        status = super().status

        if self._gyre is None:
            gyre = {
                "id": None,
                "disposition": None,
            }
        else:
            gyre = {
                "id": self._gyre.id,
                "disposition": self._gyre.disposition,
            },

        status["float"] = {
            "id": self._ocean__id,
            "name": self.name,
            "namespace": self._ocean__namespace,
            "disposition": self._ocean__disposition,
            "ttl": self._ocean__ttl,
            "storage_root": self.storage_root,
            "status": "HEALTHY",
            "following": gyre,
            "disposition": self.disposition,
        }
        return status
