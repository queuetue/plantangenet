# Copyright (c) 1998-2025 Scott Russell
# SPDX-License-Identifier: MIT

"""
Lightweight multi-dimensional data collection system.

Provides time-indexed collection of axis data with efficient change tracking
without requiring external dependencies like pandas/numpy.
"""

from typing import Dict, Any
from dataclasses import dataclass, field
import time


@dataclass
class AxisFrame:
    """A single frame of data for one axis at a specific time."""
    tick: int
    timestamp: float
    axis_name: str
    position: float
    impulse_data: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_tensor_data(self, include_time: bool = True) -> Dict[str, float]:
        """Convert to tensor-compatible numeric data."""
        numeric_data = {}

        if include_time:
            numeric_data['tick'] = float(self.tick)
            numeric_data['timestamp'] = self.timestamp

        numeric_data['position'] = self.position

        # Extract numeric values from impulse data
        for key, value in self.impulse_data.items():
            if value is None:
                continue
            if isinstance(value, (int, float)):
                numeric_data[f'{self.axis_name}_{key}'] = float(value)
            elif isinstance(value, bool):
                numeric_data[f'{self.axis_name}_{key}'] = 1.0 if value else 0.0
        return numeric_data
