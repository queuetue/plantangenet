from typing import Annotated
from plantangenet import on_topic, TopicsMixin, StatusMixin
from plantangenet.mixins.status import Observable, watch
import time


# class Cooldown(TopicsMixin, StatusMixin):
#     cycles: Observable[int] = watch(default=0)

#     def __init__(self, gyre, namespace: str, logger, cooldown: float = 0.1, running: bool = True, repeating: bool = True, **kwargs):
#         super().__init__(namespace=namespace, logger=logger, **kwargs)
#         self._gyre = gyre
#         self.cooldown = cooldown
#         self.running = running
#         self.repeating = repeating
#         self._stamp = 0.0

#     def accumulate(self, interval: float):
#         if self.running:
#             self._stamp += interval
#             if self._stamp >= self.cooldown:
#                 self._stamp -= self.cooldown
#                 self.cycles += 1
#                 if not self.repeating:
#                     self.running = False

#     @on_topic("clock.pulse")
#     async def handle_clock_pulse(self, message):
#         interval = message.get("interval", 0.0)
#         self.accumulate(interval)
#         if self.ready_to_fire:
#             await self.publish(f"drift.{self.short_id}.trigger", self.status)

#     @property
#     def ready_to_fire(self) -> bool:
#         return self.running and self._stamp >= self.cooldown

#     @property
#     def time_till_next_trigger(self) -> float:
#         if self.running:
#             return max(0.0, self.cooldown - self._stamp)
#         return float('inf')

#     @property
#     def status(self) -> dict:
#         status = super().status
#         status[f'drift.{self.short_id}'] = {
#             "attached_to": {
#                 "name": self._gyre.name,
#                 "id": self._gyre.id,
#                 "short_id": self._gyre.short_id,
#             },
#             "id": self.id,
#             "name": self.name,
#             "disposition": self.disposition,
#             "namespace": self.namespace,
#             "cooldown": self.cooldown,
#             "running": self.running,
#             "repeating": self.repeating,
#             "stamp": self._stamp,
#             "cycles": self.cycles,
#         }
#         return status
