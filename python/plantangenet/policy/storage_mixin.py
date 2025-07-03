# Copyright (c) 1998-2025 Scott Russell
# SPDX-License-Identifier: MIT

from typing import Any, Dict, Optional, List
from abc import ABC, abstractmethod


class PolicyStorageMixin(ABC):
    """
    Mixin for policy and policy objects to provide omni-style async storage methods.
    """

    # Should be set to an instance with async store/load/update methods
    storage_backend = None

    async def store(self, object_id: str, data: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None) -> bool:
        if not self.storage_backend:
            raise NotImplementedError(
                "No storage backend configured for PolicyStorageMixin.")
        return await self.storage_backend.store(object_id, data, metadata)

    async def load(self, object_id: str) -> Optional[Dict[str, Any]]:
        if not self.storage_backend:
            raise NotImplementedError(
                "No storage backend configured for PolicyStorageMixin.")
        return await self.storage_backend.load(object_id)

    async def update(self, object_id: str, fields: Dict[str, Any]) -> bool:
        if not self.storage_backend:
            raise NotImplementedError(
                "No storage backend configured for PolicyStorageMixin.")
        return await self.storage_backend.update(object_id, fields)

    async def delete(self, object_id: str) -> bool:
        if not self.storage_backend:
            raise NotImplementedError(
                "No storage backend configured for PolicyStorageMixin.")
        return await self.storage_backend.delete(object_id)
