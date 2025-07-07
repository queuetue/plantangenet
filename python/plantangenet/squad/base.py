from typing import Callable, Any, List, Optional, Protocol


class BaseSquad:
    """
    Base implementation of Omni Squad that provides common functionality.
    """

    def __init__(self, name: Optional[str] = None):
        self._groups = {}
        self.name = name
        self.is_manager = True  # For duck-typing

    def add(self, group: str, obj: Any):
        if group not in self._groups:
            self._groups[group] = []
        self._groups[group].append(obj)

    def remove(self, group: str, obj: Any):
        if group in self._groups:
            self._groups[group] = [o for o in self._groups[group] if o != obj]

    def get(self, group: str) -> List[Any]:
        return self._groups.get(group, [])

    def all(self) -> dict:
        return self._groups

    def query(self, group: str, predicate: Callable[[Any], bool]) -> List[Any]:
        return [o for o in self._groups.get(group, []) if predicate(o)]

    def difference(self, group_a: str, group_b: str) -> List[Any]:
        """Return items in group_a that are not in group_b (by identity)."""
        set_b = set(self._groups.get(group_b, []))
        return [o for o in self._groups.get(group_a, []) if o not in set_b]

    def transform(self, group: str, data: Any, frame: Any = None) -> Any:
        """Apply all transformers in the group to the data, in order."""
        for transformer in self._groups.get(group, []):
            if callable(transformer):
                data = transformer(data, frame)
        return data

    def generate(self, group: str, *args, **kwargs) -> Any:
        """Base implementation - subclasses should override for domain-specific generation."""
        raise NotImplementedError("Subclasses must implement generate()")

    def __repr__(self):
        return f"<{self.__class__.__name__} name={self.name!r} groups={list(self._groups.keys())}>"
