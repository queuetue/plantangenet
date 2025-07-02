# Copyright (c) 1998-2025 Scott Russell
# SPDX-License-Identifier: MIT

from abc import ABC
from typing import Any


class OceanMixinBase(ABC):
    _ocean__namespace: str = "plantangenet"
    _ocean__id: str = ""
    _ocean__nickname: str = ""

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
