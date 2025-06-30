from collections import deque
import inspect
import asyncio
from collections import deque
from time import monotonic
from typing import Any, Generic, Optional
from .meta import StatusMeta

from typing import TypeVar, Optional
T = TypeVar('T')


class Observable(Generic[T]):
    def __init__(self, meta: StatusMeta, field_type: Optional[type] = None, default: Optional[T] = None, namespace="", validator=None):
        self.field_type = field_type
        self.default = default
        self.meta = meta
        self.namespace = namespace
        self.private_name = f"_unset_{self.namespace}_{id(self)}"
        self.__observable_errors__ = deque(maxlen=100)
        self.validator = validator

    def validate(self, value: T) -> bool:
        """
        Validate the value before setting it.
        Override this method in subclasses to provide custom validation logic.
        """
        if self.validator:
            result, result_dict = self.validator.validate(
                self.public_name, value)
            if result_dict.get("errors"):
                self.__observable_errors__.extend(result_dict["errors"])
            return result == True
        return True

    def __set_name__(self, owner, name):
        self.public_name = name
        self.private_name = f"_{name}__{self.namespace}_{id(self)}"

        self._dirty_name = f"_{name}__dirty"
        self._updated_at_name = f"_{name}__updated_at"

        if not hasattr(owner, '_status_tracked_fields'):
            owner._status_tracked_fields = {}
        owner._status_tracked_fields[name] = self

    def __get__(self, obj, objtype=None) -> Optional[T]:
        if obj is None:
            return self.default
        return getattr(obj, self.private_name, self.default)

    def __set__(self, obj, value: T):
        self.__observable_errors__.clear()  # Clear previous errors
        old_value = getattr(obj, self.private_name, self.default)

        before_change = getattr(obj, 'on_status_before_changed', None)
        after_change = getattr(obj, 'on_status_after_changed', None)
        on_validate = getattr(obj, 'on_status_validate', None)

        if self.field_type and not isinstance(value, self.field_type):
            try:
                value = self.field_type(value)
            except Exception as e:
                self.errors.append(
                    f"Failed to convert {self.public_name} to {self.field_type.__name__}: {e}")
                return

        if value == old_value:
            return

        if not self.validate(value):
            self.__observable_errors__.append(
                f"Validation failed for {self.public_name} with value {value}")
            return

        # Call on_validate if it exists
        if on_validate:
            if inspect.iscoroutinefunction(on_validate):
                self.__observable_errors__.append(
                    f"on_validate cannot be an async function.")
            else:
                result = on_validate(obj, self.public_name, old_value, value)
                if not result:
                    self.__observable_errors__.append(
                        f"Validation failed for {self.public_name} with value {value}")
                    return

        # Call before_change if it exists
        if before_change:
            if inspect.iscoroutinefunction(before_change):
                self.__observable_errors__.append(
                    f"before_change cannot be an async function."
                )
            else:
                before_change(obj, self.public_name, old_value, value)

        setattr(obj, self._updated_at_name, monotonic())
        changed = False

        if old_value != value:
            changed = True
            setattr(obj, self.private_name, value)
            setattr(obj, self._dirty_name, True)

        if after_change:
            if inspect.iscoroutinefunction(after_change):
                asyncio.create_task(after_change(
                    obj, self.public_name, old_value, value))
            else:
                after_change(obj, self.public_name, old_value, value, changed)

    @property
    def errors(self) -> list[str]:
        return list(self.__observable_errors__)

    @property
    def error(self) -> Optional[str]:
        if self.__observable_errors__:
            return self.__observable_errors__[0]


class Observable_int(Observable[int]):
    def __init__(self, meta: StatusMeta, default: Optional[int] = None, namespace=""):
        super().__init__(meta, field_type=int, default=default, namespace=namespace)


class Observable_float(Observable[float]):
    def __init__(self, meta: StatusMeta, default: Optional[float] = None, namespace=""):
        super().__init__(meta, field_type=float, default=default, namespace=namespace)


class Observable_str(Observable[str]):
    def __init__(self, meta: StatusMeta, default: Optional[str] = None, namespace=""):
        super().__init__(meta, field_type=str, default=default, namespace=namespace)


class Observable_bool(Observable[bool]):
    def __init__(self, meta: StatusMeta, default: Optional[bool] = None, namespace=""):
        super().__init__(meta, field_type=bool, default=default, namespace=namespace)


class Observable_list(Observable[list]):
    MAXIMUM_LENGTH = 1000

    def __init__(self, meta: StatusMeta, default: Optional[list] = None, namespace="", item_type=str):
        super().__init__(meta, field_type=list, default=default, namespace=namespace)
        self.item_type = item_type

    def validate(self, value: list) -> bool:
        if not isinstance(value, list):
            self.__observable_errors__.append(
                f"Expected a list for {self.public_name}, got {type(value).__name__}")
            return False
        return True

    def __set__(self, obj, value: list):
        for item in value:
            if not isinstance(item, self.item_type):
                self.__observable_errors__.append(
                    f"Expected items of type {self.item_type.__name__} in {self.public_name}, got {type(item).__name__}")
                continue

        super().__set__(obj, value)

        if len(value) > self.MAXIMUM_LENGTH:
            self.__observable_errors__.append(
                f"List for {self.public_name} exceeds maximum length of {self.MAXIMUM_LENGTH} and will be truncated.")
            value = value[:self.MAXIMUM_LENGTH]

    def __get__(self, obj, objtype=None) -> Optional[list]:
        if obj is None:
            return self.default
        value = getattr(obj, self.private_name, self.default)
        if not isinstance(value, list):
            return []
        return value

    def append(self, obj, item: T):
        if not isinstance(item, self.item_type):
            raise TypeError(
                f"Expected item of type {self.item_type.__name__}, got {type(item).__name__}")
        current_list = self.__get__(obj) or []
        current_list.append(item)
        self.__set__(obj, current_list)

    def remove(self, obj, item: T):
        current_list = self.__get__(obj) or []
        if item in current_list:
            current_list.remove(item)
            self.__set__(obj, current_list)
        else:
            raise ValueError(f"{item} not found in {self.public_name}")

    def clear(self, obj):
        self.__set__(obj, [])
