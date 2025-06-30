# Copyright (c) 1998-2025 Scott Russell
# SPDX-License-Identifier: MIT

"""
A complete frame containing data from all axes at a specific time.

This design is ML-ready: 
- Converts seamlessly to flat, tensor-compatible dictionaries.
- Supports semantically-labeled axes and context features.
- Tracks time both as discrete ticks and continuous timestamps.
- Includes coordination data for side-channel or meta-features.

Ideal for time-series analysis, online learning, and federated policy-bound data sharing.
"""

from typing import Dict, Any, Set
from dataclasses import dataclass, field
from .axis_frame import AxisFrame


@dataclass
class MultiAxisFrame:
    """A complete frame containing data from all axes at a specific time."""
    tick: int
    timestamp: float
    axes: Dict[str, AxisFrame] = field(default_factory=dict)
    coordination_data: Dict[str, Any] = field(default_factory=dict)
    dirty_axes: Set[str] = field(default_factory=set)

    def add_axis_frame(self, axis_frame: AxisFrame):
        """Add an axis frame and mark it as dirty."""
        self.axes[axis_frame.axis_name] = axis_frame
        self.dirty_axes.add(axis_frame.axis_name)

    def clear_dirty(self):
        """Clear the dirty flags after processing."""
        self.dirty_axes.clear()

    def to_tensor_dict(self) -> Dict[str, float]:
        """Convert all axes to a flat tensor-compatible dictionary."""
        tensor_data = {
            'tick': float(self.tick),
            'timestamp': self.timestamp
        }

        for axis_frame in self.axes.values():
            axis_tensor_data = axis_frame.to_tensor_data(include_time=False)
            tensor_data.update(axis_tensor_data)

        # Include coordination data
        for key, value in self.coordination_data.items():
            if value is None:
                continue
            if isinstance(value, (int, float)):
                tensor_data[f'coord_{key}'] = float(value)
            elif isinstance(value, bool):
                tensor_data[f'coord_{key}'] = 1.0 if value else 0.0

        return tensor_data
