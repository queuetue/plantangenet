# Copyright (c) 1998-2025 Scott Russell
# SPDX-License-Identifier: MIT

from typing import Any, Dict, List, Optional, Set, Union
import time
from .meta import OmniMeta


class EnhancedOmni:
    """
    Enhanced Omni base class with centralized policy enforcement and storage integration.

    Key improvements:
    - Policy checks at omni level, not per-field
    - Integrated dirty field tracking
    - Batch operations for efficiency
    - Direct storage integration
    """

    def __init__(self, identity=None, policy=None, storage=None):
        self.identity = identity
        self.policy = policy
        self.storage = storage
        self._omni_id = f"omni_{id(self)}"

        # Centralized state tracking
        self._dirty_fields = set()
        self._original_values = {}
        self._field_cache = {}
        self._policy_cache = {}
        self._last_policy_check = None

        # Initialize field values from defaults
        self._initialize_fields()

    def __init_subclass__(cls):
        """Collect field descriptors and validate they're only used in Omni classes"""
        super().__init_subclass__()

        # Collect field descriptors
        cls._omni_persisted_fields = {}
        cls._omni_observed_fields = {}
        cls._omni_all_fields = {}

        # Look at all attributes, including inherited ones
        for klass in cls.__mro__:
            for name, obj in klass.__dict__.items():
                if hasattr(obj, '__set_name__') and hasattr(obj, 'public_name'):  # It's our descriptor
                    from .efficient_descriptors import EfficientObservable, EfficientPersistedBase

                    if isinstance(obj, EfficientObservable):
                        cls._omni_observed_fields[name] = obj
                        cls._omni_all_fields[name] = obj
                    elif isinstance(obj, EfficientPersistedBase):
                        cls._omni_persisted_fields[name] = obj
                        cls._omni_all_fields[name] = obj

    def _initialize_fields(self):
        """Initialize all fields with their default values"""
        for name, descriptor in self.__class__._omni_all_fields.items():
            if not hasattr(self, descriptor.private_name):
                setattr(self, descriptor.private_name, descriptor.default)

    def _check_omni_access(self, action: str, fields: Optional[List[str]] = None) -> bool:
        """
        Centralized policy check for omni access.

        :param action: Action being performed ('read', 'write', 'create', 'delete')
        :param fields: Optional list of specific fields being accessed
        :return: True if access is allowed
        """
        if not self.policy or not self.identity:
            return True  # No policy enforcement

        # Check cache first (for recent identical requests)
        cache_key = f"{action}:{':'.join(fields or [])}"
        if cache_key in self._policy_cache:
            cache_entry = self._policy_cache[cache_key]
            if time.time() - cache_entry['timestamp'] < 60:  # 1 minute cache
                return cache_entry['allowed']

        # Perform policy check
        try:
            if fields:
                # Check access to specific fields
                for field_name in fields:
                    result = self.policy.evaluate(
                        identity=self.identity,
                        action=action,
                        resource=f"{self._omni_id}.{field_name}"
                    )
                    if not result.passed:
                        self._policy_cache[cache_key] = {
                            'allowed': False,
                            'timestamp': time.time(),
                            'reason': result.reason
                        }
                        return False
            else:
                # Check access to entire omni
                result = self.policy.evaluate(
                    identity=self.identity,
                    action=action,
                    resource=self._omni_id
                )
                if not result.passed:
                    self._policy_cache[cache_key] = {
                        'allowed': False,
                        'timestamp': time.time(),
                        'reason': result.reason
                    }
                    return False

            # Cache positive result
            self._policy_cache[cache_key] = {
                'allowed': True,
                'timestamp': time.time(),
                'reason': 'allowed'
            }
            return True

        except Exception as e:
            # Fail secure - deny access on policy errors
            return False

    def _track_field_change(self, field_name: str, old_value: Any, new_value: Any):
        """Track field changes for dirty tracking and auditing"""
        if old_value != new_value:
            self._dirty_fields.add(field_name)
            if field_name not in self._original_values:
                self._original_values[field_name] = old_value

    def get_field_value(self, field_name: str, check_policy: bool = True) -> Any:
        """
        Get field value with centralized policy checking.

        :param field_name: Name of the field to read
        :param check_policy: Whether to perform policy check
        :return: Field value
        """
        if check_policy and not self._check_omni_access("read", [field_name]):
            raise PermissionError(
                f"Access denied to read field '{field_name}'")

        descriptor = self.__class__._omni_all_fields.get(field_name)
        if descriptor:
            # Use the private name to avoid recursion through descriptor
            return getattr(self, descriptor.private_name, descriptor.default)
        else:
            # For non-descriptor fields, use object.__getattribute__ to avoid recursion
            try:
                return object.__getattribute__(self, field_name)
            except AttributeError:
                return None

    def set_field_value(self, field_name: str, value: Any, check_policy: bool = True):
        """
        Set field value with centralized policy checking and dirty tracking.

        :param field_name: Name of the field to write
        :param value: New value for the field
        :param check_policy: Whether to perform policy check
        """
        if check_policy and not self._check_omni_access("write", [field_name]):
            raise PermissionError(
                f"Access denied to write field '{field_name}'")

        descriptor = self.__class__._omni_all_fields.get(field_name)
        if descriptor:
            # Validate value if descriptor has validation
            if hasattr(descriptor, 'validate') and not descriptor.validate(self, value):
                raise ValueError(
                    f"Validation failed for field '{field_name}' with value: {value}")

            old_value = getattr(
                self, descriptor.private_name, descriptor.default)
            setattr(self, descriptor.private_name, value)
            self._track_field_change(field_name, old_value, value)
        else:
            old_value = object.__getattribute__(
                self, field_name) if hasattr(self, field_name) else None
            setattr(self, field_name, value)
            self._track_field_change(field_name, old_value, value)

    def batch_update_fields(self, updates: Dict[str, Any], check_policy: bool = True) -> bool:
        """
        Update multiple fields in a single operation with one policy check.

        :param updates: Dictionary of field names to new values
        :param check_policy: Whether to perform policy check
        :return: True if successful
        """
        if check_policy and not self._check_omni_access("write", list(updates.keys())):
            raise PermissionError("Access denied to write one or more fields")

        # Apply all updates atomically
        for field_name, value in updates.items():
            # Skip individual checks
            self.set_field_value(field_name, value, check_policy=False)

        return True

    def get_dirty_fields(self) -> Dict[str, Any]:
        """Get all fields that have been modified since last save/clear"""
        return {
            field_name: self.get_field_value(field_name, check_policy=False)
            for field_name in self._dirty_fields
        }

    def clear_dirty_fields(self):
        """Clear dirty field tracking (typically after successful save)"""
        self._dirty_fields.clear()
        self._original_values.clear()

    def has_dirty_fields(self) -> bool:
        """Check if any fields have been modified"""
        return len(self._dirty_fields) > 0

    # Storage integration methods
    async def save_to_storage(self, incremental: bool = True) -> bool:
        """
        Save omni to storage backend.

        :param incremental: If True, only save dirty fields; if False, save all fields
        :return: True if successful
        """
        if not self.storage:
            return False

        if not self._check_omni_access("write"):
            raise PermissionError("Access denied to save omni")

        try:
            if incremental and self.has_dirty_fields():
                # Save only dirty fields
                dirty_fields = self.get_dirty_fields()
                success = await self.storage.update_omni_fields(
                    omni_id=self._omni_id,
                    dirty_fields=dirty_fields,
                    identity_id=self.identity.identity_id if self.identity else None
                )
            else:
                # Save all fields
                all_fields = {}
                for field_name in self.__class__._omni_all_fields:
                    all_fields[field_name] = self.get_field_value(
                        field_name, check_policy=False)

                success = await self.storage.store_omni_structured(
                    omni_id=self._omni_id,
                    fields=all_fields,
                    identity_id=self.identity.identity_id if self.identity else None
                )

            if success:
                self.clear_dirty_fields()

            return success

        except Exception as e:
            # Log error but don't raise to maintain omni functionality
            # Simple print fallback
            print(f"Failed to save omni {self._omni_id}: {e}")
            return False

    async def load_from_storage(self) -> bool:
        """
        Load omni from storage backend.

        :return: True if successful
        """
        if not self.storage:
            return False

        if not self._check_omni_access("read"):
            raise PermissionError("Access denied to load omni")

        try:
            fields = await self.storage.load_omni_structured(self._omni_id)
            if fields:
                # Apply loaded values without policy checks (already checked above)
                for field_name, value in fields.items():
                    if not field_name.startswith('_'):  # Skip metadata fields
                        self.set_field_value(
                            field_name, value, check_policy=False)

                self.clear_dirty_fields()  # Just loaded, so nothing is dirty
                return True

            return False

        except Exception as e:
            print(f"Failed to load omni {self._omni_id}: {e}")
            return False

    async def create_snapshot(self) -> Optional[str]:
        """Create a versioned snapshot of current omni state"""
        if not self.storage:
            return None

        if not self._check_omni_access("read"):
            raise PermissionError("Access denied to create snapshot")

        try:
            # Get all field values
            snapshot_data = {}
            for field_name in self.__class__._omni_all_fields:
                snapshot_data[field_name] = self.get_field_value(
                    field_name, check_policy=False)

            version_id = await self.storage.store_omni_version(
                omni_id=self._omni_id,
                version_data=snapshot_data
            )

            return version_id

        except Exception as e:
            print(f"Failed to create snapshot for omni {self._omni_id}: {e}")
            return None

    async def restore_from_snapshot(self, version_id: Optional[str] = None) -> bool:
        """Restore omni from a versioned snapshot"""
        if not self.storage:
            return False

        if not self._check_omni_access("write"):
            raise PermissionError("Access denied to restore snapshot")

        try:
            snapshot_data = await self.storage.load_omni_version(self._omni_id, version_id)
            if snapshot_data:
                # Apply snapshot values
                for field_name, value in snapshot_data.items():
                    if field_name in self.__class__._omni_all_fields:
                        self.set_field_value(
                            field_name, value, check_policy=False)

                return True

            return False

        except Exception as e:
            print(f"Failed to restore snapshot for omni {self._omni_id}: {e}")
            return False

    def to_dict(self, include_sensitive: bool = False, check_policy: bool = True) -> Dict[str, Any]:
        """Export omni to dictionary format"""
        if check_policy and not self._check_omni_access("read"):
            raise PermissionError("Access denied to export omni")

        result = {}
        for field_name in self.__class__._omni_all_fields:
            descriptor = self.__class__._omni_all_fields[field_name]

            # Check if field should be included
            if hasattr(descriptor, 'meta') and not descriptor.meta.include_in_dict:
                continue

            value = self.get_field_value(field_name, check_policy=False)

            # Handle sensitive fields
            if hasattr(descriptor, 'meta') and descriptor.meta.sensitive and not include_sensitive:
                result[field_name] = "***"
            else:
                result[field_name] = value

        return result

    def from_dict(self, data: Dict[str, Any], check_policy: bool = True):
        """Import omni from dictionary format"""
        if check_policy and not self._check_omni_access("write"):
            raise PermissionError("Access denied to import omni")

        # Apply values
        updates = {}
        for field_name, value in data.items():
            if field_name in self.__class__._omni_all_fields:
                updates[field_name] = value

        if updates:
            self.batch_update_fields(updates, check_policy=False)
