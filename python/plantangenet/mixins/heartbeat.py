# Copyright (c) 1998-2025 Scott Russell
# SPDX-License-Identifier: MIT

from abc import abstractmethod
from time import monotonic
from plantangenet.mixins.topics import on_topic
from .base import OceanMixinBase


class HeartbeatMixin(OceanMixinBase):
    _heartbeat__tick: float = 0.0
    _heartbeat__interval: float = 1.0
    _heartbeat_healthy_interval: float = 5.0

    @property
    def healthy(self) -> bool:
        """
        Check if the heartbeat is healthy.
        A heartbeat is considered healthy if the last heartbeat was received within the healthy interval.
        """
        return (monotonic() - self.last_heartbeat) < self._heartbeat_healthy_interval

    @property
    def status(self) -> dict:
        status = super().status
        status["heartbeat"] = {
            "last_heartbeat": self.last_heartbeat,
            "heartbeat_interval": self.heartbeat_interval,
        }

        return status

    @on_topic("cluster.heartbeat")
    async def handle_heartbeat(self, message: dict):
        now = monotonic()
        self._heartbeat__interval = now - self._heartbeat__tick
        self._heartbeat__tick = now

        await self.on_heartbeat(message)

    @abstractmethod
    async def on_heartbeat(self, message: dict):
        """
        Handle a heartbeat message.
        This method should be implemented by subclasses to define specific heartbeat handling logic.
        """

    @property
    def last_heartbeat(self) -> float:
        """
        Get the timestamp of the last heartbeat.
        """
        return self._heartbeat__tick

    @property
    def heartbeat_interval(self) -> float:
        """
        Get the interval between heartbeats.
        """
        return self._heartbeat__interval
