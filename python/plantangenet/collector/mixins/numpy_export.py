# Copyright (c) 1998-2025 Scott Russell
# SPDX-License-Identifier: MIT

try:
    import numpy as np
except ImportError as e:
    raise ImportError(
        "NumpyExportMixin requires numpy. Install with `pip install numpy`.") from e

from .pandas_export import PandasExportMixin


class NumpyExportMixin(PandasExportMixin):
    def to_numpy_tensors(self, start_tick=None, end_tick=None):
        df = self.to_dataframe(start_tick, end_tick)
        return {col: df[col].to_numpy() for col in df.columns}
