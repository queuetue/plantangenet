from typing import Annotated, get_args, get_origin
from plantangenet.omni.meta import OmniMeta
from plantangenet.omni.observable import Observable
from plantangenet.omni.persisted import PersistedBase


class OmniMixin:
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        annotations = getattr(cls, '__annotations__', {})
        persisted = getattr(cls, '_omni_persisted_fields', {})
        observed = getattr(cls, '_omni_observed_fields', {})

        for name, hint in annotations.items():
            field = getattr(cls, name, None)
            if isinstance(field, PersistedBase):
                # Type inference
                if get_origin(hint) is Annotated:
                    args = get_args(hint)
                    actual_type = args[0]
                    for meta in args[1:]:
                        if isinstance(meta, OmniMeta):
                            field.meta = meta
                else:
                    actual_type = hint
                if field.field_type is None and hasattr(field, "field_type"):
                    field.field_type = actual_type

                # Type check default
                if field.default is not None and not isinstance(field.default, actual_type):
                    raise TypeError(
                        f"Default value {field.default!r} does not match annotated type {actual_type} for field '{name}'"
                    )

                persisted[name] = field
                if isinstance(field, Observable):
                    observed[name] = field

        cls._omni_persisted_fields = persisted
        cls._omni_observed_fields = observed

    @property
    def persisted_fields(self):
        return self.__class__._omni_persisted_fields

    @property
    def observed_fields(self):
        return self.__class__._omni_observed_fields

    @property
    def dirty(self):
        return any(
            getattr(self, desc._dirty_name, False)
            for desc in self.observed_fields.values()
        )

    def to_dict(self, include_sensitive=False):
        data = {}
        for name, desc in self.persisted_fields.items():
            if not desc.meta.include_in_dict:
                continue
            value = getattr(self, name)
            if desc.meta.sensitive and not include_sensitive:
                data[name] = "***"
            else:
                data[name] = desc.meta.transform(value)
        return data

    def from_dict(self, data: dict):
        for name, desc in self.persisted_fields.items():
            if name in data:
                setattr(self, name, data[name])

    def clear_dirty(self):
        for desc in self.observed_fields.values():
            setattr(self, desc._dirty_name, False)

    @property
    def status(self):
        out = {}
        section = type(self).__name__.lower()
        out[section] = {}
        for name, desc in self.persisted_fields.items():
            if not desc.meta.include_in_dict:
                continue
            val = getattr(self, name)
            dirty = getattr(self, getattr(desc, "_dirty_name", ""), False)
            updated = getattr(self, getattr(
                desc, "_updated_at_name", ""), None)

            if desc.meta.sensitive:
                display = "***"
            else:
                display = desc.meta.transform(val)

            out[section][name] = {
                "value": display,
                "dirty": dirty,
                "updated_at": updated
            }
        return out

# async def test_redis_roundtrip(redis_client):
#     omni = Dummy()
#     omni.count = 5
#     omni.notes = "memo"

#     await redis_client.set("test:omni", json.dumps(omni.to_dict()))
#     raw = await redis_client.get("test:omni")
#     data = json.loads(raw)

#     restored = Dummy()
#     restored.from_dict(data)
#     assert restored.count == 5
#     assert restored.notes == "memo"
