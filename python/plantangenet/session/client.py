from typing import Protocol, Any


class BaseClient(Protocol):
    def send(self, message: Any) -> None:
        ...

    def receive(self) -> Any:
        ...
