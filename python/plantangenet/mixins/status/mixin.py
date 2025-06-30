from typing import Annotated, Any, Dict, get_args, get_origin
from pydantic import BaseModel, create_model

from plantangenet.mixins.status.meta import StatusMeta
from plantangenet.mixins.base import OceanMixinBase


class StatusMixin(OceanMixinBase):

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        annotations = getattr(cls, '__annotations__', {})
        tracked_fields = getattr(cls, '_status_tracked_fields', {})

        for name, hint in annotations.items():
            if name in tracked_fields:
                # If Annotated, extract base type and metadata
                if get_origin(hint) is Annotated:
                    args = get_args(hint)
                    actual_type = args[0]
                    extras = args[1:]

                    for meta in extras:
                        if isinstance(meta, StatusMeta):
                            tracked_fields[name].meta = meta
                else:
                    actual_type = hint

                existing = tracked_fields[name].field_type
                if existing is None:
                    tracked_fields[name].field_type = actual_type
                elif existing != actual_type:
                    raise TypeError(
                        f"Type conflict for field '{name}': "
                        f"annotation={actual_type}, watch field_type={existing}"
                    )

                # Validate default
                default_value = tracked_fields[name].default
                if default_value is not None and not isinstance(default_value, actual_type):
                    raise TypeError(
                        f"Default value {default_value!r} does not match annotated type {actual_type} for field '{name}'"
                    )

    @property
    def tracked_fields(self) -> Dict[str, Any]:
        """Return a dictionary of tracked fields."""
        return getattr(self.__class__, '_status_tracked_fields', {})

    @property
    def dirty_fields(self) -> Dict[str, Any]:
        """Return a dictionary of dirty fields."""
        return {name: getattr(self, tracked._dirty_name, False)
                for name, tracked in self.tracked_fields.items()}

    @property
    def updated_at_fields(self) -> Dict[str, Any]:
        """Return a dictionary of updated_at fields."""
        return {name: getattr(self, tracked._updated_at_name, None)
                for name, tracked in self.tracked_fields.items()}

    @property
    def dirty(self) -> bool:
        """Check if any tracked field is dirty."""
        return any(getattr(self, tracked._dirty_name, False)
                   for tracked in self.tracked_fields.values())

    @property
    def dirty_fields_list(self) -> list[str]:
        """Return a list of names of dirty fields."""
        return [name for name, tracked in self.tracked_fields.items()
                if getattr(self, tracked._dirty_name, False)]

    @property
    def updated_at_fields_list(self) -> list[str]:
        """Return a list of names of updated_at fields."""
        return [name for name, tracked in self.tracked_fields.items()
                if getattr(self, tracked._updated_at_name, None) is not None]

    @property
    def dirty_fields_dict(self) -> Dict[str, Any]:
        """Return a dictionary of dirty fields with their values."""
        return {name: getattr(self, name)
                for name, tracked in self.tracked_fields.items()
                if getattr(self, tracked._dirty_name, False)}

    @property
    def status(self) -> Dict[str, Any]:
        status = super().status
        section_key = type(self).__name__.lower()
        status[section_key] = {}

        for field_name, tracked in getattr(self.__class__, '_status_tracked_fields', {}).items():
            if not tracked.meta.include_in_dict:
                continue
            try:
                value = getattr(self, field_name)
                value = tracked.meta.transform(value)
                dirty = getattr(self, tracked._dirty_name, False)
                updated_at = getattr(self, tracked._updated_at_name, None)

                if tracked.meta.sensitive:
                    display_value = "***"
                else:
                    display_value = value

                status[section_key][field_name] = {
                    "value": display_value,
                    "dirty": dirty,
                    "updated_at": updated_at
                }
            except AttributeError:
                status[section_key][field_name] = None

        return status

    def to_dict(self, include_sensitive: bool = False, include_meta: bool = False) -> Dict[str, Any]:
        """Flat dictionary representation with optional metadata."""
        result = {}

        for field_name, tracked in getattr(self.__class__, '_status_tracked_fields', {}).items():
            if not tracked.meta.include_in_dict:
                continue
            try:
                value = getattr(self, field_name)
                value = tracked.meta.transform(value)

                if tracked.meta.sensitive and not include_sensitive:
                    result[field_name] = "***"
                elif include_meta:
                    result[field_name] = {
                        "value": value,
                        "dirty": getattr(self, tracked._dirty_name, False),
                        "updated_at": getattr(self, tracked._updated_at_name, None)
                    }
                else:
                    result[field_name] = value
            except AttributeError:
                result[field_name] = None

        return result

    def clear_dirty(self):
        """Clear all dirty flags."""
        for tracked in getattr(self.__class__, '_status_tracked_fields', {}).values():
            setattr(self, tracked._dirty_name, False)

    def to_pydantic(self) -> BaseModel:
        """Dynamically generate a Pydantic model instance from the current state."""
        fields = {}
        values = {}
        for field_name, tracked in getattr(self.__class__, '_status_tracked_fields', {}).items():
            fields[field_name] = (tracked.field_type, ...)
            values[field_name] = getattr(self, field_name)

        DynamicModel = create_model(
            f"{self.__class__.__name__}Model", **fields)
        return DynamicModel(**values)
