# Copyright (c) 1998-2025 Scott Russell
# SPDX-License-Identifier: MIT

from typing import Optional, Any
from .meta import OmniMeta


class OmniDescriptor:
    """
    Base descriptor for omni fields. Only works within EnhancedOmni classes.
    Policy enforcement is delegated to the omni level for efficiency.
    """

    def __init__(self, meta: Optional[OmniMeta] = None, field_type: Optional[type] = None, default=None):
        self.meta = meta or OmniMeta()
        self.field_type = field_type
        self.default = default
        self.public_name = None
        self.private_name = None

    def __set_name__(self, owner, name):
        # Validate that this is only used in EnhancedOmni subclasses
        from .enhanced_omni import EnhancedOmni
        if not issubclass(owner, EnhancedOmni):
            raise TypeError(
                f"OmniDescriptor fields can only be used in EnhancedOmni subclasses, not {owner}")

        self.public_name = name
        self.private_name = f"_{name}__value"

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self

        # Delegate to omni's centralized access method
        return obj.get_field_value(self.public_name)

    def __set__(self, obj, value):
        # Delegate to omni's centralized access method
        obj.set_field_value(self.public_name, value)


class EfficientObservable(OmniDescriptor):
    """
    Efficient Observable descriptor that delegates policy checks to EnhancedOmni.
    Tracks changes and validation at the omni level, not per-field.
    """

    def __init__(self, meta: Optional[OmniMeta] = None, field_type: Optional[type] = None,
                 default=None, validator=None):
        super().__init__(meta, field_type, default)
        self.validator = validator

    def validate(self, obj, value) -> bool:
        """Validate field value. Called by omni during batch operations."""
        # Type validation
        if self.field_type and value is not None:
            if not isinstance(value, self.field_type):
                try:
                    # Try to convert to the expected type
                    converted_value = self.field_type(value)
                    return True
                except (ValueError, TypeError):
                    return False

        # Custom validator
        if self.validator:
            try:
                return self.validator(obj, self.public_name, value)
            except Exception:
                return False

        return True


class EfficientPersistedBase(OmniDescriptor):
    """
    Efficient PersistedBase descriptor that delegates policy checks to EnhancedOmni.
    Persistence is handled at the omni level, not per-field.
    """

    def __init__(self, meta: Optional[OmniMeta] = None, field_type: Optional[type] = None, default=None):
        super().__init__(meta, field_type, default)


# Backward compatibility aliases
Observable = EfficientObservable
PersistedBase = EfficientPersistedBase
