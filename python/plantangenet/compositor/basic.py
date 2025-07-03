# Copyright (c) 1998-2025 Scott Russell
# SPDX-License-Identifier: MIT

"""
Lightweight multi-dimensional data collection system.

Provides time-indexed collection of axis data with efficient change tracking
without requiring external dependencies like pandas/numpy.
"""

from typing import Dict, List, Any, Optional
from .rule import CompositionRule
from plantangenet.collector.core import TimeSeriesCollector

# Core opcodes:

# MOV src, dst – Copy data

# LD addr, dst – Load from buffer

# ST src, addr – Store to buffer

# ADD/SUB/MUL/DIV – Math

# AND/OR/XOR/NOT – Bitwise

# CMP/SET – Comparison

# BRA/RET – Control flow

# BARRIER – Synchronization (for compositing parallel transforms)

# MASK – Enforce policy filtering

# Specialized semantic ops:

# FOCUS_CHECK – Evaluate consumer cursor focus

# POLICY_CHECK – Apply chem/policy rules

# MERGE – Composite two semantic regions

# REDUCE – Aggregate data across regions

# MAP – Remap coordinates


class BasicCompositor:
    """
    A basic compositor for multi-dimensional musical data.

    This provides the foundation for blending, transformation,
    and analysis operations on collected multi-axis time series data.
    """

    def __init__(self, collector: TimeSeriesCollector):
        self.collector = collector
        self._composition_rules: List[CompositionRule] = []

    def add_composition_rule(self, rule: CompositionRule):
        self._composition_rules.append(rule)

    def compose_frame(self, tick: int) -> Optional[Dict[str, Any]]:
        frame = self.collector.get_frame(tick)
        if not frame:
            return None

        composed = frame.to_tensor_dict()
        for rule in self._composition_rules:
            composed = rule(composed, frame)

        return composed

    def compose_window(self, start_tick: int, end_tick: int) -> List[Dict[str, Any]]:
        frames = self.collector.get_time_window(start_tick, end_tick)
        composed_frames = []

        for frame in frames:
            tensor_dict = frame.to_tensor_dict()
            for rule in self._composition_rules:
                tensor_dict = rule(tensor_dict, frame)
            composed_frames.append(tensor_dict)

        return composed_frames

    def analyze_patterns(self, axis_name: str, window_size: int = 100) -> Dict[str, Any]:
        history = self.collector.get_axis_history(axis_name, window_size)
        if not history:
            return {}

        positions = [
            frame.position for frame in history if frame.position is not None]
        ticks = [frame.tick for frame in history]

        if not positions:
            return {}

        mean_pos = sum(positions) / len(positions)
        variance = sum((p - mean_pos) ** 2 for p in positions) / len(positions)
        std_pos = variance ** 0.5
        min_pos = min(positions)
        max_pos = max(positions)

        velocity = 0.0
        if len(positions) > 1 and ticks[-1] != ticks[0]:
            velocity = (positions[-1] - positions[0]) / (ticks[-1] - ticks[0])

        analysis = {
            'mean_position': mean_pos,
            'std_position': std_pos,
            'velocity': velocity,
            'range': (min_pos, max_pos),
            'sample_count': len(positions)
        }

        return analysis
