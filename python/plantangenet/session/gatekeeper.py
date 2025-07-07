from typing import Protocol, Any


class BaseGatekeeper(Protocol):
    def admit(self, agent: Any) -> bool:
        ...
