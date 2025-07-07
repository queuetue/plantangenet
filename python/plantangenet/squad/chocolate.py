import asyncio
from typing import Optional, Any
from .squad import Squad


class ChocolateSquad(Squad):
    """
    A Squad that can be managed by another Squad, or can manage its own groups.
    This allows for hierarchical management of groups.
    It can also manage its own groups and objects.
    """

    def __init__(self, name: Optional[str] = None):
        super().__init__(name)

    async def update(self, *args, **kwargs):
        """
        Default update: update all managed objects in a special 'updatables' group.
        If this Squad is itself managed (has a parent manager), it can optionally
        delegate its update to the parent manager, or handle it locally.
        """
        # If you want to delegate, call: self.parent_manager.update()
        # By default, update all updatables locally
        for obj in self.get('updatables'):
            if hasattr(obj, 'update'):
                if asyncio.iscoroutinefunction(obj.update):
                    await obj.update(*args, **kwargs)
                else:
                    obj.update(*args, **kwargs)

    def __repr__(self):
        return f"<Squad name={self.name!r} groups={list(self._groups.keys())}>"
