# Copyright (c) 1998-2025 Scott Russell
# SPDX-License-Identifier: MIT

from abc import abstractmethod
from .topics import TopicsMixin
from .omni import OmniMixin
from typing import Annotated
from ..topics import on_topic
from ..omni import OmniMeta, watch


class FramesMixin(TopicsMixin, OmniMixin):
    frame_count: Annotated[
        int,
        OmniMeta(description="Frame count")
    ] = watch(default=100)  # type: ignore

    @abstractmethod
    async def on_frame(self):
        """
            Handle a frame update.

            This method is called when a new "accounting" accumulator cycle is detected.
            It can be overridden by subclasses to implement specific frame handling logic.
            For example, it could be used to update the state of the Buoy or trigger other actions
            based on the current frame.
            It is called after the `on_pulse` method has updated the timebase and frame delta.
            Subclasses should implement their own logic in this method to define how they respond
            to frame updates.
        """
        pass

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

        pass
