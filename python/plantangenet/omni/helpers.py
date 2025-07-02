from .meta import OmniMeta
from .persisted import PersistedBase
from .observable import Observable


def persist(default=None, **meta_kwargs):
    return PersistedBase(OmniMeta(**meta_kwargs), default=default)


def watch(default=None, **meta_kwargs):
    return Observable(OmniMeta(**meta_kwargs), default=default)
