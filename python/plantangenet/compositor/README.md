# Plantangenet Compositor Module

This package implements the **transformation and analysis system** for time-indexed axis data.

It provides tools for:

- **Composing** collected frames into enriched feature sets.
- **Applying transformation rules**.
- **Analyzing** axis patterns over time.

---

## Structure

- `basic.py` – Defines `BasicCompositor`, with dependency-free analysis and transformation.
- `rule.py` – Defines the `CompositionRule` protocol for user-defined feature functions.
- *(Planned)* `advanced_compositor.py` – Extends with NumPy-based advanced analysis.

---

## Usage Examples

### Importing the basic compositor
```python
from plantangenet.compositor.basic import BasicCompositor
```

### Creating and using

```python
compositor = BasicCompositor(collector)

def my_rule(data, frame):
    data['normalized_position'] = data['position'] / 100.0
    return data

compositor.add_composition_rule(my_rule)

result = compositor.compose_frame(tick=42)
```

---

## When to Use

* Use **BasicCompositor** for dependency-free transformation and feature engineering.
* Add **AdvancedCompositor** (planned) for NumPy-powered advanced analysis (e.g. gradients, FFT).

