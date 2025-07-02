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

__all__ = [
    "AxisCoordinator",
    "MultiAxisCoordinator",
    "TemporalCoordinator",
    "TemporalMultiAxisCoordinator",
]
