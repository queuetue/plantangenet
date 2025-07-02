from typing import Optional
from .meta import OmniMeta


class PersistedBase:
    def __init__(self, meta: Optional[OmniMeta] = None, default=None):
        self.meta = meta or OmniMeta()
        self.default = default

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
        return getattr(obj, self.private_name, self.default)

    def __set__(self, obj, value):
        setattr(obj, self.private_name, value)
