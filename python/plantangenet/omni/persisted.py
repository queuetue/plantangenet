from typing import Optional, Callable
from .meta import OmniMeta


class PersistedBase:
    def __init__(self, meta: Optional[OmniMeta] = None, default=None, field_type: Optional[type] = None, validator: Optional[Callable] = None):
        self.meta = meta or OmniMeta()
        self.default = default
        self.field_type = field_type
        self.validator = validator

    def __set_name__(self, owner, name):
        self.public_name = name
        self.private_name = f"_{name}__persisted"

        # Register in _omni_persisted_fields
        if not hasattr(owner, '_omni_persisted_fields'):
            owner._omni_persisted_fields = {}
        owner._omni_persisted_fields[name] = self

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self.default

        # Per-field policy check for read access
        self._check_field_access(obj, "read")

        return getattr(obj, self.private_name, self.default)

    def __set__(self, obj, value):
        # Per-field policy check for write access
        self._check_field_access(obj, "write", value)

        # Type enforcement/coercion
        if self.field_type and value is not None and not isinstance(value, self.field_type):
            try:
                value = self.field_type(value)
            except Exception as e:
                raise TypeError(
                    f"Failed to coerce {self.public_name} to {self.field_type}: {e}")

        # Custom validator
        if self.validator:
            try:
                valid = self.validator(obj, self.public_name, value)
                if not valid:
                    raise ValueError(
                        f"Validation failed for {self.public_name} with value {value}")
            except Exception as e:
                raise ValueError(
                    f"Validation error for {self.public_name}: {e}")

        setattr(obj, self.private_name, value)

    def _check_field_access(self, obj, action: str, value=None):
        """
        Check policy access for this field on the given object.

        :param obj: The object instance
        :param action: The action being performed ('read' or 'write')
        :param value: The value being set (for write operations)
        :raises PermissionError: If access is denied
        """
        # Get policy from object instance
        policy = getattr(obj, 'policy', None)
        if not policy:
            return  # No policy enforcement if policy not available

        # Get session/identity from object instance
        session = getattr(obj, 'session', None)
        identity = getattr(session, 'identity', None) if session else None
        if not identity:
            return  # No policy enforcement if identity not available

        # Build context for policy evaluation
        context = {
            "instance": obj,
            "field_name": self.public_name,
            "private_name": self.private_name
        }
        if value is not None:
            context["value"] = value

        try:
            # Build resource identifier: omni_private_key::field_name::action
            omni_key = getattr(obj, 'private_key', obj.__class__.__name__)
            resource_id = f"{omni_key}::{self.public_name}::{action}"
            # Evaluate policy using the constructed resource identifier
            result = policy.evaluate(
                identity=identity,
                action=action,
                resource=resource_id,
                context=context
            )

            # Check if access is allowed
            if not result.passed:
                raise PermissionError(
                    f"Access denied: {action} operation on field '{self.public_name}' "
                    f"for identity '{identity}': {result.reason}"
                )

        except Exception as e:
            # Policy evaluation failure should be treated as access denied
            # This is a circuit breaker - when policy system fails, deny access
            if isinstance(e, PermissionError):
                raise
            raise PermissionError(
                f"Policy evaluation failed for field '{self.public_name}': {str(e)}"
            )
