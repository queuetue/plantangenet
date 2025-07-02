# Plantangenet Omni System

**Declarative, Observable, Persisted State for Agents**

Plantangenet’s **Omni system** enables agents to *declare*, *validate*, *observe*, *persist*, and *introspect* their internal state in a consistent, serialization-friendly way.

This document explains the design and use of the **Omni components**:

* `watch()`
* `persist()`
* `Observable`
* `Persisted`
* `StatusMeta`
* `OmniMixin`

---

## Overview

The Omni system gives agents:

* **Declarative** field definitions
* **Type enforcement and validation**
* **Optional change tracking (dirty flags, updated timestamps)**
* **Consistent serialization for storage or transport**
* **Structured introspection via `.status`**
* **Hydration from storage with `.from_dict()`**
* **Pydantic model generation** for validation and export

---

## Declarative Fields

Omni supports **two kinds of fields**:

---

### * Observed Fields with `watch()`

Fields with **validation**, **dirty tracking**, and **timestamps**:

```python
health: int = watch(default=100)
```

* Tracks changes (dirty flag).
* Enforces type with optional coercion.
* Records last `updated_at` time.
* Supports validation and hooks.

---

### * Persisted-only Fields with `persist()`

Simpler **stored** fields *without* dirty-tracking:

```python
notes: str = persist(default="")
```

* Included in serialization and hydration.
* No dirty flag or timestamp.
* Great for configuration or auxiliary state.

---

## Why Both?

* Use `watch()` for *state you want to observe and track changes to*.
* Use `persist()` for *state you want to save/load without observation overhead*.

---

## Rich Field Metadata with `StatusMeta`

All fields support:

* `description` – Human-readable explanation.
* `transform` – Callable for customizing export or display.
* `sensitive` – Masks value in `.status` and `.to_dict()`.
* `include_in_dict` – Include/exclude in export.

Example:

```python
health: int = watch(default=100, description="Agent health")
notes: str = persist(default="", sensitive=True)
```

---

## Example Declaration

```python
class Agent(OmniMixin):
    health: int = watch(default=100, description="HP")
    is_active: bool = watch(default=True)
    notes: str = persist(default="", description="Freeform notes")
```

* All fields persisted.
* Only `watch()` fields have dirty-tracking and timestamps.

---

## Automatic Type Inference

`watch()` and `persist()` use **Python type hints**:

```python
health: int = watch(default=100)
notes: str = persist(default="")
```

* Enforces type at runtime.
* Coerces if safe.
* Raises clear errors for conflicts.

---

## Dirty and Updated Tracking

* *Only* `watch()` fields track:

* Dirty flag – True if value changed.
* Updated timestamp – Monotonic time of last change.

Example:

```python
agent.dirty  # True if any watch() field changed
agent.dirty_fields  # Dict of changed fields
agent.clear_dirty()  # Reset flags
```

---

## Structured `.status` Property

OmniMixin provides:

```python
agent.status
```

* Clean, nested dictionary.
* Includes:

* Value (masked if sensitive)
* Dirty flag (if observed)
* Updated timestamp (if observed)

Example:

```python
{
  "agent": {
    "health": {
      "value": 120,
      "dirty": True,
      "updated_at": 1711405725.123
    },
    "notes": {
      "value": "***"
    }
  }
}
```

---

## Flat `.to_dict()` Export

```python
agent.to_dict(include_sensitive=True)
```

* Simple, flat dictionary for storage or transport.
* Honors:

* `include_in_dict`
* `sensitive` masking
* `transform` functions

* All persisted fields included.

---

## Hydration with `.from_dict()`

```python
data = {"health": 80, "notes": "remember this"}
agent.from_dict(data)
```

* Loads all persisted fields from dict.
* Respects field types.

---

## Pydantic Integration

Supports:

* Dynamic Pydantic model generation.
* Type validation.
* JSON serialization.

Example:

```python
model = agent.to_pydantic()
print(model.json())
```

---

## Change Hooks for Observables

Omni supports **event hooks** on `watch()` fields:

* `on_omni_validate(self, field, old, new)`
* `on_omni_before_changed(self, field, old, new)`
* `on_omni_after_changed(self, field, old, new, changed)`

* Use these to implement:

* Logging
* Metrics
* Event-driven integrations

---

## Recommended Idiom

Use `watch()` and `persist()` declaratively:

```python
class MyAgent(OmniMixin):
    hp: int = watch(default=100, description="Hit points")
    is_npc: bool = watch(default=False)
    notes: str = persist(default="", description="Notes", sensitive=True)
```

* Clean, Pythonic.
* Declarative and type-checked.
* Storage- and introspection-friendly.

---

## Benefits

* Declarative agent state
* Type enforcement
* Observability with dirty tracking
* Persistence of all relevant fields
* Metadata-driven introspection
* Unified `.status` view
* Hydration via `.from_dict()`
* Pydantic-ready export
* Minimal boilerplate

---

## Example Usage

```python
class Player(OmniMixin):
    hp: int = watch(default=100)
    name: str = watch(default="Anon", sensitive=True)
    notes: str = persist(default="")

    def on_omni_after_changed(self, field, old, new, changed):
        if changed:
            print(f"{field} changed from {old} to {new}")

player = Player()
player.hp = 80
print(player.status)
```
