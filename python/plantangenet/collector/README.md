# Plantangenet Collector Module

This package implements the **time-indexed collection system** for multi-dimensional axis data.

It is designed to be:

- **Lightweight and dependency-free** in its core.
- **Optionally extensible** with Pandas and NumPy-based mixins.

---

## Structure

- `core.py` – Defines `TimeSeriesCollector`, the main collection class with no external dependencies.
- `axis_frame.py` – Defines `AxisFrame`, representing one axis's data at a single tick.
- `multi_axis_frame.py` – Defines `MultiAxisFrame`, holding all axes at a single tick.
- `mixins/` – Optional advanced export mixins:
  - `pandas_export.py` – Adds `.to_dataframe()` for Pandas export.
  - `numpy_export.py` – Adds `.to_numpy_tensors()` for NumPy export.
- `advanced.py` – Defines `AdvancedTimeSeriesCollector`, pre-mixed with Pandas/NumPy support.

---

## Usage Examples

### Minimal, dependency-free
```python
from plantangenet.collector.core import TimeSeriesCollector

collector = TimeSeriesCollector()
```

### With advanced export (requires pandas, numpy)

```python
from plantangenet.collector.advanced import AdvancedTimeSeriesCollector

collector = AdvancedTimeSeriesCollector()
df = collector.to_dataframe()
tensors = collector.to_numpy_tensors()
```
---

## When to Use

* **Core only** for small, embedded, or dependency-sensitive environments.
* **Advanced** for data science, ML training pipelines, analysis in notebooks.

