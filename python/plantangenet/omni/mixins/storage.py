# Copyright (c) 1998-2025 Scott Russell
# SPDX-License-Identifier: MIT

from abc import abstractmethod
from typing import Any, List, Optional
from .mixin import OmniMixin


class StorageMixin(OmniMixin):
    """
    A mixin for Storage operations, providing basic key-value store functionality.
    This mixin is designed to be used with an async storage client.
    It supports setting, getting, deleting keys, checking existence, and listing keys.
    It also provides a TTL (time-to-live) for keys, which defaults to 10 minutes.
    """
    _ocean__id: str
    _storage__ttl = 600
    _storage_prefix: str = "plantangenet"

    def __init__(self, ttl: Optional[int] = None, prefix: Optional[str] = None):
        if self._ocean__id is None:
            raise ValueError("StorageMixin requires an _ocean__id to be set.")
        if ttl is not None and ttl <= 0:
            self._storage__ttl = ttl
        if prefix is not None:
            self._storage_prefix = prefix

    @property
    def message_types(self):
        """Return the peer's message types."""
        result = super().message_types
        result.update([
            "storage.get",
            "storage.set",
            "storage.delete",
            "storage.keys",
            "storage.exists",
        ])
        return result

    @property
    def storage_prefix(self) -> str:
        """
        Get the storage prefix for the peer.
        :return: The storage prefix.
        """
        return self._storage_prefix

    @property
    def storage_root(self) -> str:
        """
        Get the root key for the storage.
        :return: The root key for the storage.
        """
        return f"{self._storage_prefix}:{self._ocean__namespace}:{self._ocean__id}:storage"

    @abstractmethod
    async def update_storage(self):
        """
        Update the storage for a peer.
        This method should be implemented by subclasses to perform any necessary updates.
        """

    @abstractmethod
    async def setup_storage(self, urls: list[str]) -> None:
        """
        Setup the storage for a peer.
        This method should be implemented by subclasses to perform any necessary initialization.
        """

    @abstractmethod
    async def teardown_storage(self) -> None:
        """
        Teardown the storage for a peer.
        This method should be implemented by subclasses to perform any necessary cleanup.
        """

    @abstractmethod
    async def get(self, key: str, actor=None) -> Optional[Any]:
        """
        Get a value from the store.
        :param key: The key under which the value is stored.
        :param actor: Optional actor identifier for namespacing.
        :return: The value if found, None otherwise.
        """

    @abstractmethod
    async def set(self, key: str, value: Any, nx: bool = False, ttl: Optional[int] = None, actor=None) -> Optional[list]:
        """
        Set a value in the store with a TTL.
        :param key: The key under which to store the value.
        :param value: The value to store.
        :param nx: If True, set the value only if the key does not already exist.
        :param ttl: Time-to-live for the key in seconds. Defaults to 600 seconds (10 minutes).
        :param actor: Optional actor identifier for namespacing.
        :return: A list of log entries for the operation, or None if the key already exists and nx is True.
        """

    @abstractmethod
    async def delete(self, key: str, actor=None) -> Optional[list]:
        """
        Delete a value from the store.
        :param key: The key under which the value is stored.
        :param actor: Optional actor identifier for namespacing.
        :return: A list of log entries for the deleted keys, or None if no keys were deleted.
        """

    @abstractmethod
    async def keys(self, pattern: str = "*", actor=None) -> List[str]:
        """
        List all keys matching a pattern.
        :param pattern: The pattern to match keys against.
        :param actor: Optional actor identifier for namespacing.
        :return: A list of keys matching the pattern.
        """

    @abstractmethod
    async def exists(self, key: str, actor=None) -> bool:
        """
        Check if a key exists in the store.
        :param key: The key to check for existence.
        :param actor: Optional actor identifier for namespacing.
        :return: True if the key exists, False otherwise.
        """
