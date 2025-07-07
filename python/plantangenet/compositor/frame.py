# Copyright (c) 1998-2025 Scott Russell
# SPDX-License-Identifier: MIT

"""
FrameCompositor: Specializes BaseCompositor for time-indexed frame composition.
"""

from typing import Any, Optional, List, Dict
from .base import BaseCompositor
from plantangenet.collector.core import TimeSeriesCollector


class FrameCompositor(BaseCompositor):
    """
    Composes time-indexed frames using a pipeline of transformation rules.
    This is the base for all frame-based (time series) compositors.
    """

    def __init__(self, collector: TimeSeriesCollector):
        super().__init__()
        self.collector = collector

    def compose(self, tick: int) -> Optional[Dict[str, Any]]:
        frame = self.collector.get_frame(tick)
        if not frame:
            return None
        composed = frame.to_tensor_dict()
        for rule in self.composition_rules:
            composed = rule(composed, frame)
        return composed

    def compose_window(self, start_tick: int, end_tick: int) -> List[Dict[str, Any]]:
        frames = self.collector.get_time_window(start_tick, end_tick)
        composed_frames = []
        for frame in frames:
            tensor_dict = frame.to_tensor_dict()
            for rule in self.composition_rules:
                tensor_dict = rule(tensor_dict, frame)
            composed_frames.append(tensor_dict)
        return composed_frames
