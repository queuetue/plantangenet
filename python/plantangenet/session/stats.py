from typing import Protocol, Any


class Stats(Protocol):
    def record(self, event: Any) -> None:
        ...

    def summary(self) -> dict:
        ...
