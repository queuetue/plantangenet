# timebase.py
# SPDX-License-Identifier: MIT
import asyncio
import json
from time import monotonic, perf_counter
from typing import Optional, Any
from .accumulator import Accumulator
from plantangenet import OceanMixinBase


class Clock(OceanMixinBase):

    def __init__(self, logger: Any, namespace: str):
        self._stamp = 0.0
        self._interval = 0.0
        self._paused = False
        self._stepping = False
        self._start_time = perf_counter()
        self._accumulators = {}
        self._last_update_time = monotonic()

    async def setup(self, *args, **kwargs) -> None:
        print("Setting up Clock")
        self._stamp = 0.0
        self._paused = False
        self._start_time = perf_counter()
        self._interval = 0.0
        self._last_update_time = monotonic()
        await self.subscribe("clock.step", self.handle_message)
        await self.subscribe("clock.pause", self.handle_message)
        await self.subscribe("clock.resume", self.handle_message)

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

            if self.connected:
                data = await self.to_dict(event_type="pulse")
                try:
                    await asyncio.wait_for(
                        self.publish("clock.pulse", json.dumps(
                            data).encode('utf-8')),
                        timeout=0.01
                    )
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

    async def handle_step(self):
        if not self._paused:
            self.logger.warning("Can only step while paused.")
            return
        self._stepping = True

    async def handle_pause(self):
        self._paused = True
        self.logger.info("Timebase paused.")

    async def handle_resume(self):
        self._paused = False
        self.logger.info("Timebase resumed.")

    async def handle_message(self, message):
        subject = message.subject
        if subject == "clock.step":
            await self.handle_step()
        elif subject == "clock.pause":
            await self.handle_pause()
        elif subject == "clock.resume":
            await self.handle_resume()
        else:
            self.logger.warning(
                f"Unhandled message: {subject} -> {message.data}")

    async def teardown(self):
        await super().teardown()

    def __str__(self):
        status = ">" if not self._paused else "X"
        pulse = f"{self._stamp:.2f}"
        icon = "🌊" if self.connected else "❌"
        return f"{icon}|{status}|stamp={pulse}"

    async def to_dict(self, event_type: str = "pulse") -> dict:
        return {
            "id": self._ocean__id,
            "event_type": event_type,
            "stamp": self._stamp,
            "interval": self._interval,
            "paused": self._paused,
            "stepping": self._stepping,
            "start_time": self._start_time,
            "wall_time": self._last_update_time,
            "disposition": self._ocean__disposition,
            "accumulators": {
                name: acc.to_dict() for name, acc in self._accumulators.items()
            },
        }

    def get_current_tick(self) -> Optional[int]:
        """Return current tick based on timebase."""
        # Convert timestamp to ticks (assuming 96 ticks per second as default)
        current_time = monotonic()
        elapsed = current_time - self._start_time
        return int(elapsed * 96)  # 96 ticks per second
