from typing import Protocol, Any


class BaseMatchmaker(Protocol):
    def match(self, agents: list) -> list:
        ...
