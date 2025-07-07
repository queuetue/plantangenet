# Copyright (c) 1998-2025 Scott Russell
# SPDX-License-Identifier: MIT

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Set, Union
import json
import time
from datetime import datetime


class OmniStorageMixin(ABC):
    """
    Enhanced storage mixin for omni objects with advanced capabilities:
    - Structured field storage (Redis hashes)
    - Dirty field tracking for incremental updates
    - Versioning and history
    - Cross-reference tracking
    - Policy-aware caching
    - Change notifications
    """

    @abstractmethod
    async def store_omni_structured(
        self,
        omni_id: str,
        fields: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        identity_id: Optional[str] = None
    ) -> bool:
        """
        Store omni fields in a structured way (e.g., Redis hash)

        :param omni_id: Unique identifier for the omni
        :param fields: Dictionary of field names to values
        :param metadata: Optional metadata (version, timestamps, etc.)
        :param identity_id: Identity associated with this omni
        :return: True if successful
        """
        pass

    @abstractmethod
    async def load_omni_structured(
        self,
        omni_id: str,
        field_names: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Load omni fields from structured storage

        :param omni_id: Unique identifier for the omni
        :param field_names: Optional list of specific fields to load
        :return: Dictionary of field names to values, or None if not found
        """
        pass

    @abstractmethod
    async def update_omni_fields(
        self,
        omni_id: str,
        dirty_fields: Dict[str, Any],
        identity_id: Optional[str] = None
    ) -> bool:
        """
        Update only the dirty/changed fields of an omni

        :param omni_id: Unique identifier for the omni
        :param dirty_fields: Dictionary of changed field names to new values
        :param identity_id: Identity associated with this omni
        :return: True if successful
        """
        pass

    @abstractmethod
    async def store_omni_version(
        self,
        omni_id: str,
        version_data: Any,
        timestamp: Optional[float] = None
    ) -> str:
        """
        Store a versioned snapshot of an omni

        :param omni_id: Unique identifier for the omni
        :param version_data: Serialized omni state
        :param timestamp: Optional timestamp, defaults to current time
        :return: Version identifier
        """
        pass

    @abstractmethod
    async def load_omni_version(
        self,
        omni_id: str,
        version_id: Optional[str] = None
    ) -> Optional[Any]:
        """
        Load a specific version of an omni, or latest if version_id is None

        :param omni_id: Unique identifier for the omni
        :param version_id: Specific version to load, or None for latest
        :return: Deserialized omni state, or None if not found
        """
        pass

    @abstractmethod
    async def list_omni_versions(
        self,
        omni_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        List available versions for an omni

        :param omni_id: Unique identifier for the omni
        :param limit: Maximum number of versions to return
        :return: List of version info (id, timestamp, etc.)
        """
        pass

    @abstractmethod
    async def add_omni_relationship(
        self,
        parent_id: str,
        child_id: str,
        relationship_type: str = "child"
    ) -> bool:
        """
        Add a relationship between two omnis

        :param parent_id: Parent omni identifier
        :param child_id: Child omni identifier  
        :param relationship_type: Type of relationship
        :return: True if successful
        """
        pass

    @abstractmethod
    async def remove_omni_relationship(
        self,
        parent_id: str,
        child_id: str,
        relationship_type: str = "child"
    ) -> bool:
        """
        Remove a relationship between two omnis

        :param parent_id: Parent omni identifier
        :param child_id: Child omni identifier
        :param relationship_type: Type of relationship
        :return: True if successful
        """
        pass

    @abstractmethod
    async def get_omni_relationships(
        self,
        omni_id: str,
        relationship_type: str = "child",
        reverse: bool = False
    ) -> List[str]:
        """
        Get related omni IDs

        :param omni_id: Omni identifier to find relationships for
        :param relationship_type: Type of relationship to find
        :param reverse: If True, find omnis that have this omni as a relationship
        :return: List of related omni IDs
        """
        pass

    @abstractmethod
    async def cache_policy_decision(
        self,
        identity_id: str,
        action: str,
        resource: str,
        decision: bool,
        reason: str,
        ttl: int = 300
    ) -> bool:
        """
        Cache a policy decision

        :param identity_id: Identity making the request
        :param action: Action being performed
        :param resource: Resource being accessed
        :param decision: True if allowed, False if denied
        :param reason: Reason for the decision
        :param ttl: Time to live in seconds
        :return: True if cached successfully
        """
        pass

    @abstractmethod
    async def get_cached_policy_decision(
        self,
        identity_id: str,
        action: str,
        resource: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get a cached policy decision

        :param identity_id: Identity making the request
        :param action: Action being performed
        :param resource: Resource being accessed
        :return: Cached decision dict with 'decision', 'reason', or None if not cached
        """
        pass

    @abstractmethod
    async def publish_omni_change(
        self,
        omni_id: str,
        field_name: str,
        old_value: Any,
        new_value: Any,
        identity_id: Optional[str] = None
    ) -> bool:
        """
        Publish a change notification

        :param omni_id: Omni that changed
        :param field_name: Field that changed
        :param old_value: Previous value
        :param new_value: New value
        :param identity_id: Identity that made the change
        :return: True if published successfully
        """
        pass

    @abstractmethod
    async def log_omni_audit(
        self,
        omni_id: str,
        action: str,
        field_name: Optional[str] = None,
        old_value: Any = None,
        new_value: Any = None,
        identity_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Log an audit entry for omni operations

        :param omni_id: Omni identifier
        :param action: Action performed (read, write, create, delete)
        :param field_name: Field that was accessed/modified
        :param old_value: Previous value (for write operations)
        :param new_value: New value (for write operations)
        :param identity_id: Identity performing the action
        :param context: Additional context
        :return: Audit entry ID
        """
        pass

    @abstractmethod
    async def get_omni_audit_log(
        self,
        omni_id: str,
        limit: int = 100,
        since: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Get audit log entries for an omni

        :param omni_id: Omni identifier
        :param limit: Maximum number of entries to return
        :param since: Only return entries after this timestamp
        :return: List of audit entries
        """
        pass

    @abstractmethod
    async def atomic_omni_update(
        self,
        omni_id: str,
        updates: Dict[str, Any],
        conditions: Optional[Dict[str, Any]] = None,
        identity_id: Optional[str] = None
    ) -> bool:
        """
        Perform an atomic update of omni fields with optional conditions

        :param omni_id: Omni identifier
        :param updates: Fields to update
        :param conditions: Optional conditions that must be met (e.g., field values)
        :param identity_id: Identity performing the update
        :return: True if update was successful
        """
        pass
