# Plantangenet Status System

**Declarative, Observable, Validated State for Agents**

Plantangenet’s **Status system** enables agents to *declare*, *validate*, *track*, and *introspect* their internal state in a consistent, observable, serialization-friendly way.

This document explains the design and use of the **Status** components:

* `watch()`
* `Observable`
* `ObservableStatusField`
* `StatusMeta`
* `StatusMixin`

---

## Overview

The Status system gives agents:

* **Declarative** field definitions
* **Type enforcement and validation**
* **Automatic change tracking (dirty flags)**
* **Timestamps** for last updates
* **Structured `.status` introspection**
* **Pydantic model generation** for validation and export

---

## Declarative Fields with `watch()`

The **preferred** modern style is to use the `watch()` factory:

```python
health: Observable[int] = watch(default=100)
```

* Automatically picks the right observable type (int, float, bool, str, list).
* Sets up dirty tracking, timestamps, and metadata.
* Clean, Pythonic, type-annotated interface.

---

### Alternative: `watch()`

For **untyped** or advanced use:

```python
mystery: Any = watch(default=None)
```

* `watch()` is the **generic fallback**.
* It can explicitly specify a field type if needed.

---

## StatusMeta

Rich metadata for fields:

* `description` – Human-readable explanation
* `transform` – Callable for customizing display
* `sensitive` – Masks value in `.status` output
* `include_in_dict` – Include/exclude in export

Example:

```python
health: Observable[int] = watch(default=100, description="Agent health")
```

---

## ObservableStatusField

The **descriptor** that powers the system:

* Stores the actual value
* Validates type on set
* Tracks "dirty" flag
* Records last `updated_at` time
* Supports change hooks for event-driven designs

---

## Automatic Type Inference

`watch()` uses **Python type hints**:

```python
health: Observable[int] = watch(default=100)
```

* Enforces type at runtime
* Rejects wrong types or tries safe coercion
* Raises clear errors if conflicting types

---

## Dirty and Updated Tracking

Every field:

* Dirty flag – True if changed
* Updated timestamp – Monotonic time of last change

Example `.status` output:

```python
{
  "agent": {
    "health": {
      "value": 120,
      "dirty": True,
      "updated_at": 1711405725.123
    }
  }
}
```

---

## Structured `.status` Property

`StatusMixin` provides:

```python
agent.status
```

* Clean, nested dictionary
* Includes value (masked if sensitive)
* Dirty flag
* Updated timestamp

---

## Flat `.to_dict()` Export

```python
agent.to_dict(include_sensitive=True)
```

* Simple, flat dictionary for storage or transport
* Optional metadata (dirty flags, timestamps)

---

## Pydantic Integration

Supports:

* Dynamic Pydantic model generation
* Type validation
* JSON serialization

Example:

```python
model = agent.to_pydantic()
print(model.json())
```

---

## Change Hooks

Built-in support for lifecycle events:

* `on_status_attempted_change(self, field, old, new)`
* `on_status_changed(self, field, old, new)`
* `on_status_after_changed(self, field, old, new, changed)`

Enables:

* Logging
* Metrics
* Event-driven design
* Integration with bus systems

---

## Recommended Idiom

Use `watch()` with type hints:

```python
class MyAgent(StatusMixin):
    health: Observable[int] = watch(default=100, description="HP")
    name: Observable[str] = watch(default="Anonymous", sensitive=True)
```

* Clean and modern
* Type-checked
* Declarative

---

## Benefits

✨ Declarative agent state
✨ Type enforcement
✨ Dirty tracking and timestamps
✨ Hooks for observability
✨ Unified `.status` view
✨ Pydantic-ready export
✨ Minimal boilerplate, maximum clarity

---

## Example Usage

```python
class Player(StatusMixin):
    hp: Observable[int] = watch(default=100)
    name: Observable[str] = watch(default="Anon", sensitive=True)

    def on_status_changed(self, field, old, new):
        self.logger.info(f"{field} changed: {old} → {new}")

player = Player()
player.hp = 80
print(player.status)
```

---

## Summary

The Plantangenet **Status System** enables:

* Declarative, typed agent state
* Automatic introspection
* Lifecycle event hooks
* Validation and serialization

*Build observable, maintainable, introspectable agents with ease.*

---

**Copyright (c) 1998-2025 Scott Russell**
**SPDX-License-Identifier: MIT**
