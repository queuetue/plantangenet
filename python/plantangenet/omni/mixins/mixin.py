# Copyright (c) 1998-2025 Scott Russell
# SPDX-License-Identifier: MIT

from abc import ABC
from plantangenet.logger import Logger


class OmniMixin(ABC):
    _ocean_logger: Logger
    _ocean__namespace: str
    _ocean__id: str
    _ocean__nickname: str

    @property
    def logger(self) -> Logger:
        """Return the logger for this mixin."""
        if not hasattr(self, "_ocean__logger"):
            self._ocean__logger = Logger()
        return self._ocean__logger

    @property
    def status(self) -> dict:
        return {
            "mixin": {
                "id": self._ocean__id,
                "nickname": self._ocean__nickname,
                "message_types": self.message_types,
                "namespace": self._ocean__namespace,
            }
        }

    @property
    def message_types(self):
        """Return the peer's message types."""
        message_types = set([
            "ocean.setup",
            "ocean.teardown",
            "ocean.update",
        ])
        return message_types
