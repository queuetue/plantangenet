from typing import Optional
from .squad import Squad
from ..omni.mixins import TickMixin


class TickSquad(Squad):
    """Manages tick operations with periodic ticking."""

    def __init__(self, name: Optional[str] = None, publish_callback=None):
        super().__init__(name)
        self.publish_callback = publish_callback

    def generate(self, group: str, interval: float, *args, **kwargs):
        """Generate a new tick object."""
        tick = TickMixin(
            repeating=True,
            running=True,
            *args, **kwargs
        )
        self.add(group, tick)
        return tick

    async def tick_all(self, interval: float):
        """Tick all objects in all groups."""
        for group_name, ticks in self._groups.items():
            for tick in ticks:
                if hasattr(tick, 'tick'):
                    tick.tick(interval)
                    if hasattr(tick, 'ready_to_fire') and tick.ready_to_fire and self.publish_callback:
                        await self.publish_callback(f"tick.{id(tick)}.trigger", tick)
