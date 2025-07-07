from typing import Optional, Callable, Any
from ..omni.mixins import CooldownMixin
from .squad import Squad


class CooldownSquad(Squad):
    """Manages cooldown objects with periodic ticking."""

    def __init__(self, name: Optional[str] = None, publish_callback=None):
        super().__init__(name)
        self.publish_callback = publish_callback

    def generate(self, group: str, duration: float, *args, **kwargs):
        """Generate a new cooldown object."""
        cooldown = CooldownMixin(duration)
        self.add(group, cooldown)
        return cooldown

    async def tick_all(self, interval: float):
        """Tick all cooldowns in all groups."""
        for group_name, cooldowns in self._groups.items():
            for cooldown in cooldowns:
                if hasattr(cooldown, 'tick'):
                    cooldown.tick(interval)
                    if hasattr(cooldown, 'ready_to_fire') and cooldown.ready_to_fire and self.publish_callback:
                        await self.publish_callback(f"cooldown.{id(cooldown)}.trigger", cooldown)
