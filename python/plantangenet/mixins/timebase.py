# Copyright (c) 1998-2025 Scott Russell
# SPDX-License-Identifier: MIT

from abc import abstractmethod
from time import monotonic, perf_counter
from plantangenet.mixins.topics import on_topic
from .base import OceanMixinBase


class TimebaseMixin(OceanMixinBase):
    now = monotonic()
    _ocean__clock_frame = 0
    _ocean__origin_start_time = perf_counter()
    _last_frame_wall_time = now
    _ocean__timebase_wall_time = _last_frame_wall_time
    _ocean__origin_wall_time = _last_frame_wall_time
    _ocean__frame_delta = 0
    _ocean__origin_pulse: dict = {
        "id": None,
        "stamp": 0.0,
        "interval": 0.0,
        "paused": False,
        "stepping": False,
        "start_time": 0.0,
        "wall_time": monotonic(),
        "accumulators": {},
        "current_tick": 0,
    }

    _ocean__pulse: dict

    _ocean__timebase_stamp = 0.0
    _ocean__timebase_interval = 0.0
    _ocean__timebase_paused = False
    _ocean__timebase_stepping = False
    _ocean__timebase_accumulators = {}
    _ocean__clock_choice = None
    _ocean__origin_tick = 0

    @property
    def status(self) -> dict:
        status = super().status

        status["origin"] = {
            "id": self._ocean__origin_pulse["id"],
            "stamp": self._ocean__origin_pulse["stamp"],
            "start_time": self._ocean__origin_pulse["start_time"],
            "wall_time": self._ocean__origin_pulse["wall_time"],
        }

        status["timebase"] = {
            "clock_frame": self._ocean__clock_frame,
            "frame_delta": self._ocean__frame_delta,
            "stamp": self._ocean__timebase_stamp,
            "interval": self._ocean__timebase_interval,
            "paused": self._ocean__timebase_paused,
            "step": self._ocean__timebase_stepping,
            "start_time": self._ocean__origin_start_time,
            "wall_time": self._ocean__timebase_wall_time,
            "accumulators": self._ocean__timebase_accumulators,
            "current_choice": self._ocean__clock_choice,
        }

        return status

    @on_topic("clock.pulse")
    async def handle_pulse(self, message: dict):
        """
            Gets called when a clock pulse message is received.

            message fields:
            = "id": The ID of the clock originating the pulse.
            - "stamp": The current time stamp.
            - "interval": The time interval since the last pulse.
            = "paused": Whether the clock is paused.
            - "stepping": Whether the clock is stepping while paused.
            - "start_time": The start time of the clock.
            - "namespace": The namespace of the clock.
            - "wall_time": The wall time of the clock.
            - "current_choice": The current choice of the clock.
            - "accumulators": A dictionary of accumulators
        """

        if not self._ocean__origin_pulse:
            await self.set_origin(message)

        self._ocean__pulse = message
        self._ocean__timebase_stamp = message.get("stamp", 0.0)
        self._ocean__timebase_interval = message.get("interval", 0.0)
        self._ocean__timebase_paused = message.get("paused", False)
        self._ocean__timebase_stepping = message.get("stepping", False)
        self._ocean__origin_start_time = message.get("start_time", 0.0)
        self._ocean__clock_choice = message.get("current_choice", None)
        self._last_frame_wall_time = monotonic()
        self._ocean__timebase_wall_time = self._last_frame_wall_time
        self._ocean__timebase_accumulators = message.get("accumulators", {})

    async def set_origin(self, message: dict):
        """
            Sets the initial pulse message and initializes the timebase.
        """
        self._last_frame_wall_time = monotonic()
        self._ocean__origin_wall_time = self._last_frame_wall_time
        self._ocean__origin_start_time = perf_counter()
        self._ocean__origin_pulse = message
        self._ocean__origin_tick = message["current_tick"]
