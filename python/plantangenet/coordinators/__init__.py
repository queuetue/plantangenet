# Copyright (c) 1998-2025 Scott Russell
# SPDX-License-Identifier: MIT

"""
Coordinatorship abstractions for coordinating impulses along axes.

This module provides base classes for creating authoritative coordinators
that generate opinions about progression along various axes (temporal,
pitch, intensity, mood, etc.) and broadcast those opinions to subscribers.
"""

from .axis import AxisCoordinator
from .multi_axis import MultiAxisCoordinator
from .temporal import TemporalCoordinator
from .temporal_multiaxis import TemporalMultiAxisCoordinator


from ..collector.core import TimeSeriesCollector
from ..collector.axis_frame import AxisFrame
from ..collector.multi_axis_frame import MultiAxisFrame
from ..compositor.basic import BasicCompositor
# from ..compositor.advanced import AdvancedCompositor

__all__ = ["AxisCoordinator", "MultiAxisCoordinator",
           "TemporalCoordinator", "TemporalMultiAxisCoordinator",
           "TimeSeriesCollector", "BasicCompositor",
           #    "AdvancedCompositor",
           "AxisFrame", "MultiAxisFrame"]
