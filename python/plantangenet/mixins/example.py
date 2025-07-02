# Copyright (c) 1998-2025 Scott Russell
# SPDX-License-Identifier: MIT

from abc import abstractmethod
from plantangenet.topics import on_topic
from .base import OceanMixinBase


class ExampleMixin(OceanMixinBase):

    @property
    def status(self) -> dict:
        return {}

    @on_topic("message")
    async def handle_message(self, message: dict):
        await self.on_message(message)

    @abstractmethod
    async def on_message(self, message: dict):
        """
        Override this method to handle your message.
        """
