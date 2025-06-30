# Copyright (c) 1998-2025 Scott Russell
# SPDX-License-Identifier: MIT

try:
    import pandas as pd
except ImportError as e:
    raise ImportError(
        "PandasExportMixin requires pandas. Install with `pip install pandas`.") from e


class PandasExportMixin:
    def to_dataframe(self, start_tick=None, end_tick=None):
        frames = self.get_time_window(start_tick, end_tick)
        rows = [frame.to_tensor_dict() for frame in frames]
        return pd.DataFrame(rows)
