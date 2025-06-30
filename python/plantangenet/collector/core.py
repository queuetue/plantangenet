# Copyright (c) 1998-2025 Scott Russell
# SPDX-License-Identifier: MIT

"""
Lightweight multi-dimensional data collection system.

Provides time-indexed collection of axis data with efficient change tracking
without requiring external dependencies like pandas/numpy.
"""

from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field
import time
from .axis_frame import AxisFrame
from .multi_axis_frame import MultiAxisFrame


class TimeSeriesCollector:
    """
    Collects multi-axis data over time for efficient composition and analysis.

    This is the "stuff at t collector" that aggregates impulses from all axes
    and provides efficient access patterns for downstream composition.
    """

    def __init__(self, max_history: int = 10000):
        self._frames: Dict[int, MultiAxisFrame] = {}
        self._max_history = max_history
        self._current_tick = 0
        self._axis_names: Set[str] = set()
        self._sorted_ticks: List[int] = []
        self._dirty_ticks: Set[int] = set()

    def collect_axis_data(
        self,
        tick: int,
        axis_name: str,
        position: float,
        impulse_data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[float] = None
    ):
        """
        Collect data from a single axis at a specific tick.

        Args:
            tick: The time tick
            axis_name: Name of the axis
            position: Position along the axis
            impulse_data: The impulse data from the axis leader
            metadata: Optional metadata
            timestamp: Optional externally-provided timestamp
        """
        ts = timestamp if timestamp is not None else time.time()

        axis_frame = AxisFrame(
            tick=tick,
            timestamp=ts,
            axis_name=axis_name,
            position=position,
            impulse_data=impulse_data,
            metadata=metadata or {}
        )

        if tick not in self._frames:
            self._frames[tick] = MultiAxisFrame(tick=tick, timestamp=ts)
            self._sorted_ticks.append(tick)
            self._sorted_ticks.sort()

        self._frames[tick].add_axis_frame(axis_frame)
        self._dirty_ticks.add(tick)
        self._axis_names.add(axis_name)
        self._current_tick = max(self._current_tick, tick)

        self._trim_history()

    def get_frame(self, tick: int) -> Optional[MultiAxisFrame]:
        return self._frames.get(tick)

    def get_dirty_frames(self) -> List[MultiAxisFrame]:
        return [self._frames[tick] for tick in self._dirty_ticks if tick in self._frames]

    def clear_dirty(self):
        for tick in self._dirty_ticks:
            if tick in self._frames:
                self._frames[tick].clear_dirty()
        self._dirty_ticks.clear()

    def get_time_window(self, start_tick: int, end_tick: int) -> List[MultiAxisFrame]:
        return [
            self._frames[tick]
            for tick in self._sorted_ticks
            if start_tick <= tick <= end_tick and tick in self._frames
        ]

    def to_tensor_list(self, start_tick: Optional[int] = None, end_tick: Optional[int] = None) -> List[Dict[str, float]]:
        if start_tick is None:
            start_tick = min(self._sorted_ticks) if self._sorted_ticks else 0
        if end_tick is None:
            end_tick = max(self._sorted_ticks) if self._sorted_ticks else 0

        frames = self.get_time_window(start_tick, end_tick)
        return [frame.to_tensor_dict() for frame in frames]

    def get_axis_history(self, axis_name: str, num_frames: int = 100) -> List[AxisFrame]:
        recent_ticks = self._sorted_ticks[-num_frames:] if len(
            self._sorted_ticks) > num_frames else self._sorted_ticks

        axis_frames = []
        for tick in recent_ticks:
            if tick in self._frames and axis_name in self._frames[tick].axes:
                axis_frames.append(self._frames[tick].axes[axis_name])

        return axis_frames

    def _trim_history(self):
        if len(self._frames) <= self._max_history:
            return

        excess = len(self._frames) - self._max_history
        old_ticks = self._sorted_ticks[:excess]

        for tick in old_ticks:
            if tick in self._frames:
                del self._frames[tick]
            if tick in self._dirty_ticks:
                self._dirty_ticks.remove(tick)

        self._sorted_ticks = self._sorted_ticks[excess:]

    def get_stats(self) -> Dict[str, Any]:
        return {
            'total_frames': len(self._frames),
            'current_tick': self._current_tick,
            'axis_count': len(self._axis_names),
            'axes': list(self._axis_names),
            'dirty_frames': len(self._dirty_ticks),
            'tick_range': (min(self._sorted_ticks), max(self._sorted_ticks)) if self._sorted_ticks else (0, 0)
        }
