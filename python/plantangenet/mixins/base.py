# Copyright (c) 1998-2025 Scott Russell
# SPDX-License-Identifier: MIT

from abc import ABC
from typing import Any, TYPE_CHECKING
import logging

if TYPE_CHECKING:
    from plantangenet.logger import Logger


class OceanMixinBase(ABC):
    _ocean__namespace: str = "plantangenet"
    _ocean__id: str = ""
    _ocean__nickname: str = ""

    @property
    def logger(self) -> 'Logger':
        """
        Return a logger instance for this object. Subclasses can override or set _logger.
        Defaults to a standard Python logger named after the class and namespace.
        """
        if hasattr(self, '_logger') and self._logger:
            return self._logger
        from plantangenet.logger import Logger
        logger_name = f"{self._ocean__namespace}.{self.__class__.__name__}"
        self._logger = Logger()
        return self._logger

    @property
    def name(self) -> str: ...

    @property
    def disposition(self) -> str: ...

    @property
    def status(self) -> dict:
        return {
            "id": self._ocean__id,
            "nickname": self._ocean__nickname,
            "message_types": self.message_types,
            "namespace": self._ocean__namespace,
            "name": self.name,
            "disposition": self.disposition,

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
