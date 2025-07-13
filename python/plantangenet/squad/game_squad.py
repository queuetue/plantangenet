from typing import Optional
from .squad import Squad


class GameSquad(Squad):
    """Specialized Squad for managing game-specific objects like activities, agents, etc."""

    def __init__(self, session, name: Optional[str] = None):
        super().__init__(name)
        self.session = session

    def generate(self, group: str, object_type: str, *args, **kwargs):
        if object_type == "activity":
            activity = self._create_activity(*args, **kwargs)
        elif object_type == "agent":
            activity = self._create_agent(*args, **kwargs)
        else:
            raise ValueError(f"Unknown game object type: {object_type}")
        self.add(group, activity)
        return activity

    def _create_activity(self, *args, **kwargs):
        raise NotImplementedError(
            "Specific games must implement activity creation")

    def _create_agent(self, *args, **kwargs):
        raise NotImplementedError(
            "Specific games must implement agent creation")
