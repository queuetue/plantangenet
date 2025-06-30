# Copyright (c) 1998-2025 Scott Russell
# SPDX-License-Identifier: MIT

from abc import abstractmethod
import asyncio
from time import monotonic, perf_counter
from typing import Optional
from plantangenet import on_topic, OceanMixinBase
from .accumulator import Accumulator


class ClockMixin(OceanMixinBase):

    def __init__(self):
        self._stamp = 0.0
        self._interval = 0.0
        self._paused = False
        self._stepping = False
        self._start_time = perf_counter()
        self._accumulators = {}
        self._last_update_time = monotonic()

    @property
    def status(self) -> dict:
        status = super().status
        status["clock"] = {
            "stamp": self._stamp,
            "interval": self._interval,
            "paused": self._paused,
            "stepping": self._stepping,
            "start_time": self._start_time,
            "last_update_time": self._last_update_time,
            "accumulators": {
                name: acc.to_dict() for name, acc in self._accumulators.items()
            },
        }

        return status

    async def add_accumulator(self, name: str, delta: int):
        if name in self._accumulators:
            raise ValueError(f"Accumulator '{name}' already exists.")
        self._accumulators[name] = Accumulator(
            delta, running=True, repeating=True)

    async def remove_accumulator(self, name: str):
        if name not in self._accumulators:
            raise ValueError(f"Accumulator '{name}' does not exist.")
        del self._accumulators[name]

    async def get_accumulator(self, name: str) -> Optional[Accumulator]:
        return self._accumulators.get(name)

    async def list_accumulators(self) -> dict[str, Accumulator]:
        return self._accumulators.copy()

    async def reset_accumulators(self):
        for accum in self._accumulators.values():
            accum.reset()

    @on_topic("clock.pause")
    async def handle_clock_pause(self, message: dict):
        self._paused = True

    @on_topic("clock.resume")
    async def handle_clock_resume(self, message: dict):
        self._paused = False

    @on_topic("clock.step")
    async def handle_clock_step(self, message: dict):
        self._stepping = True
        await self.update()
        self._stepping = False

    async def update(self) -> bool:
        if await super().update():
            now = monotonic()
            interval = now - self._last_update_time
            self._last_update_time = now
            self._interval = interval

            if not self._paused or self._stepping:
                self._stamp += interval
                for accum in self._accumulators.values():
                    accum.accumulate(interval)
                try:
                    await self.publish("clock.pulse", self.status)
                except asyncio.TimeoutError:
                    self.logger.warning("Publish timed out")
                except asyncio.CancelledError:
                    self.logger.warning("Publish cancelled")
                    raise
                except Exception as e:
                    self.logger.warning(f"Publish failed: {e}")
            else:
                self.logger.warning("Cannot publish pulse: not connected")
            self._stepping = False
            return True
        return False
