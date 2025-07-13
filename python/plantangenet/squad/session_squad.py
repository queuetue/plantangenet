from typing import Optional
from .base import BaseSquad


class SessionSquad(BaseSquad):
    """Manages session components like policies, gatekeepers, matchmakers, etc."""

    def __init__(self, session, name: Optional[str] = None):
        super().__init__(name)
        self.session = session

    def generate(self, group: str, component_type: str, *args, **kwargs):
        # TODO: Implement specific component creation
        if component_type == "local_policy":
            component = {"type": "local_policy",
                         "args": args, "kwargs": kwargs}
        elif component_type == "gatekeeper":
            component = {"type": "gatekeeper", "args": args, "kwargs": kwargs}
        elif component_type == "matchmaker":
            component = {"type": "matchmaker", "args": args, "kwargs": kwargs}
        elif component_type == "referee":
            component = {"type": "referee", "args": args, "kwargs": kwargs}
        elif component_type == "stats":
            component = {"type": "stats", "args": args, "kwargs": kwargs}
        else:
            raise ValueError(f"Unknown component type: {component_type}")
        self.add(group, component)
        return component
