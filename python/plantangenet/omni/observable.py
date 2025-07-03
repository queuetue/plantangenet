from collections import deque
from typing import Optional
from .persisted import PersistedBase
from .meta import OmniMeta
from time import monotonic


class Observable(PersistedBase):
    def __init__(self, meta: Optional[OmniMeta] = None, field_type: Optional[type] = None,
                 default=None, namespace="", validator=None):
        super().__init__(meta=meta, default=default)
        self.field_type = field_type
        self.namespace = namespace
        self.validator = validator
        self.__observable_errors__ = deque(maxlen=100)

    def __set_name__(self, owner, name):
        super().__set_name__(owner, name)

        self._dirty_name = f"_{name}__dirty"
        self._updated_at_name = f"_{name}__updated_at"

        # Also register in _omni_observed_fields
        if not hasattr(owner, '_omni_observed_fields'):
            owner._omni_observed_fields = {}
        owner._omni_observed_fields[name] = self

    def validate(self, value):
        if self.validator:
            result, result_dict = self.validator.validate(
                self.public_name, value)
            if result_dict.get("errors"):
                self.__observable_errors__.extend(result_dict["errors"])
            return result is True
        return True

    def __set__(self, obj, value):
        # Per-field policy check for write access (sync version)
        self._check_field_access(obj, "write", value)

        self.__observable_errors__.clear()
        old_value = getattr(obj, self.private_name, self.default)

        # Handle before/after hooks
        before_change = getattr(obj, 'on_omni_before_changed', None)
        after_change = getattr(obj, 'on_omni_after_changed', None)
        on_validate = getattr(obj, 'on_omni_validate', None)

        if self.field_type and not isinstance(value, self.field_type):
            try:
                value = self.field_type(value)
            except Exception as e:
                self.__observable_errors__.append(
                    f"Failed to coerce {self.public_name}: {e}")
                return

        if value == old_value:
            return

        if not self.validate(value):
            self.__observable_errors__.append(
                f"Validation failed for {self.public_name} with value {value}")
            return

        if on_validate and not on_validate(obj, self.public_name, old_value, value):
            self.__observable_errors__.append(
                f"on_validate rejected value for {self.public_name}")
            return

        if before_change:
            before_change(obj, self.public_name, old_value, value)

        # Save
        setattr(obj, self.private_name, value)
        setattr(obj, self._dirty_name, True)
        setattr(obj, self._updated_at_name, monotonic())

        if after_change:
            after_change(obj, self.public_name, old_value, value, True)
