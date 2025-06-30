# Copyright (c) 1998-2025 Scott Russell
# SPDX-License-Identifier: MIT

from .core import TimeSeriesCollector
from .mixins.numpy_export import NumpyExportMixin


class AdvancedTimeSeriesCollector(NumpyExportMixin, TimeSeriesCollector):
    """Collector with optional Pandas/NumPy export features."""
    pass
