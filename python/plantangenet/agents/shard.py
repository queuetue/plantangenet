# Copyright (c) 1998-2025 Scott Russell
# SPDX-License-Identifier: MIT

__version__ = "0.1.0"
from plantangenet.logger import Logger
from plantangenet.mixins.storage import StorageMixin
from plantangenet.mixins.transport import TransportMixin
from plantangenet.mixins.topics import TopicsMixin
from .agent import Agent

__all__ = ["Shard", "__version__"]


class Shard(Agent, StorageMixin, TransportMixin, TopicsMixin):
    """
    A localized peer representing a usable slice of a distributed process.

    Shards maintain partial state, handle scoped messages, and operate under
    shared protocol constraints. They serve as active participants in the larger
    Ocean or Gyre ecosystem-discrete work units with routing and storage capability.

    ----

    Earth's oceans are littered with microplastics and other pollutants,
    carried by currents and gyres. Please support the environment-and consider the
    data center running this code as part of our shared planetary ecosystem.
    """

    def __init__(
            self,
            namespace: str,
            logger: Logger,
            storage_prefix: str = "root",
            ttl: int = 600
    ):
        self._ocean__ttl: int = ttl
        Agent.__init__(self, namespace=namespace, logger=logger)
        StorageMixin.__init__(self, prefix=storage_prefix)
        TransportMixin.__init__(self)
        TopicsMixin.__init__(self)

    async def teardown_transport(self): ...

    async def teardown_storage(self): ...

    @property
    def status(self) -> dict:
        status = super().status
        status["shard"] = {
            "id": self._ocean__id,
            "namespace": self._ocean__namespace,
            "disposition": self._ocean__disposition,
            "ttl": self._ocean__ttl,
            "storage_root": self.storage_root,
            "status": "HEALTHY",
        }
        return status

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

    async def handle_message(self, message):
        """Handle incoming messages from the cluster."""
        self._ocean__logger.info(f"Shard received message: {message.data}")

    async def teardown(self):
        await self.teardown_transport()
        await self.teardown_storage()

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
