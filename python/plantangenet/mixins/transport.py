# Copyright (c) 1998-2025 Scott Russell
# SPDX-License-Identifier: MIT

from typing import Any, Callable, Coroutine
from typing import Union, Optional
from abc import abstractmethod

from plantangenet.mixins.base import OceanMixinBase


class TransportMixin(OceanMixinBase):
    """
    A mixin for Transport operations, providing basic publish/subscribe functionality.
    This mixin is designed to be used with an async transport client.
    It supports publishing messages to topics, subscribing to topics with callbacks,
    and unsubscribing from topics.
    """

    @abstractmethod
    async def update_transport(self):
        """
        Update the transport peer.
        This method should be implemented by subclasses to perform any necessary updates.
        """

    @abstractmethod
    async def setup_transport(self, urls: list[str]) -> None:
        """
        Setup the transport peer.
        This method should be implemented by subclasses to perform any necessary initialization.
        """

    @abstractmethod
    async def teardown_transport(self):
        """
        Teardown the transport peer.
        This method should be implemented by subclasses to perform any necessary cleanup.
        """

    @abstractmethod
    async def publish(self, topic: str, data: Union[str, bytes, dict]) -> Optional[list]:
        """Publish a message to the topic with the given data."""

    @abstractmethod
    async def subscribe(self, topic: str, callback: Callable[..., Coroutine[Any, Any, Any]]) -> Any:
        """Subscribe to a topic with the given callback."""

    @property
    @abstractmethod
    def connected(self) -> bool:
        """
        Check if the storage backend is connected.
        This property should be implemented by subclasses to indicate connection status.
        """
