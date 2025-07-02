class Omni:
    def __init_subclass__(cls):
        # Collect field descriptors
        super().__init_subclass__()
        cls._omni_persisted_fields = getattr(cls, '_omni_persisted_fields', {})
        cls._omni_observed_fields = getattr(cls, '_omni_observed_fields', {})

    @property
    def persisted_fields(self):
        return self.__class__._omni_persisted_fields

    @property
    def observed_fields(self):
        return self.__class__._omni_observed_fields

    @property
    def dirty_fields(self):
        return {
            name: getattr(self, name)
            for name, desc in self.observed_fields.items()
            if getattr(self, desc._dirty_name, False)
        }

    def clear_dirty(self):
        for desc in self.observed_fields.values():
            setattr(self, desc._dirty_name, False)

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
