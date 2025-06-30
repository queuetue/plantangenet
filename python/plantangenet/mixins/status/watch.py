from typing import overload
from .meta import StatusMeta
from typing import TypeVar, Any
from .observable import Observable, Observable_bool, Observable_int, Observable_float, Observable_str, Observable_list

T = TypeVar('T')


@overload
def watch(default: T, **meta_kwargs) -> Observable[T]: ...
@overload
def watch(**meta_kwargs) -> Observable[Any]: ...


def watch(default=None, policy_engine=None, **meta_kwargs):
    if isinstance(default, int):
        return Observable_int(StatusMeta(**meta_kwargs), default=default)
    elif isinstance(default, float):
        return Observable_float(StatusMeta(**meta_kwargs), default=default)
    elif isinstance(default, str):
        return Observable_str(StatusMeta(**meta_kwargs), default=default)
    elif isinstance(default, bool):
        return Observable_bool(StatusMeta(**meta_kwargs), default=default)
    elif isinstance(default, list):
        return Observable_list(StatusMeta(**meta_kwargs), default=default)
    else:
        return Observable(StatusMeta(**meta_kwargs), default=default)
