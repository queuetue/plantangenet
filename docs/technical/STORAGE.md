# Storage in Plantangenet

Plantangenet uses a **key-value-based storage abstraction** designed for speed, flexibility, and low operational overhead.

The storage system is responsible for persisting:

* **Identities**
* **Roles**
* **Policy Statements**
* **Omni Objects (Agents, Controllers, Services, etc.)**

---

## Key Concepts

### `BaseStorage`

An abstract base class that defines:

* `save_policy(...)`
* `save_identity(...)`
* `save_role(...)`
* `list_*()` methods for each type

This interface ensures that any storage backend - memory, Redis, file system - can be dropped in.

---

## `HmapStorage`: Fast Hash Map Abstraction

### Design Goals

* **Simple**: No migrations, schemas, or indices
* **Portable**: Backends must only support basic key-value operations
* **Focused**: Stores only what the policy engine (and agents) need

---

### Namespacing Keys

Keys are prefixed by type for easy listing and filtering:

* `policy:*`
* `identity:*`
* `role:*`
* `omni:*`

---

### Example: Saving a Role

```python
await self.connector.set("role:admin", role.json())
```

Roles are stored as serialized JSON values.

---

## Persisting Omni Objects

Plantangenet’s **Omni system** adds flexible, field-level persistence for agents and services.

An **Omni** object combines:

* **Observed fields** – with validation, dirty tracking, timestamps
* **Persisted fields** – simple stored state

Omni uses the same storage abstraction.

---

### Namespacing Omni Keys

Omni state is typically saved under:

* `omni:<id>:state` → JSON-serialized full object state
* `omni:<id>:field:<name>` → Optional per-field values

---

### Example: Saving an Omni

```python
await connector.set(f"omni:{agent_id}:state", json.dumps(agent.to_dict()))
```

### Example: Hydrating an Omni

```python
raw = await connector.get(f"omni:{agent_id}:state")
if raw:
    agent.from_dict(json.loads(raw))
```

* Omni objects define `.to_dict()` and `.from_dict()` to cleanly serialize *only persisted fields* - including observed and plain persisted values.

---

### Storage Patterns for Omni

* **Full snapshot** – Save/load entire object state.
* **Field-level updates** – Optionally save/load individual fields.
* **TTL support** – Leverage backend timeouts for ephemeral data.

Omni models can choose which fields are:

* Observed (tracked with dirty flags and updated timestamps)
* Persisted-only (simple configuration/state)

---

## `BaseDataConnector`: Pluggable Persistence

This interface abstracts the underlying database:

```python
class BaseDataConnector(ABC):
    async def get(key: str) -> Optional[str]: ...
    async def set(key: str, value: Any) -> bool: ...
    async def keys(pattern: str) -> List[str]: ...
    ...
```

If a backend can `get`, `set`, and `list` keys, it can support **all** of Plantangenet’s core needs - including **Omni** storage.

---

### Required Methods

* `get`, `set`, `incr`, `delete`, `exists`
* `ping`: sanity check connectivity
* `hset`, `hgetall`: optional support for structured objects

---

## Setup & Teardown Lifecycle

### On Startup:

```python
await storage.setup()
```

Typically checks availability (e.g., Redis `PING`).

### On Shutdown:

```python
await storage.teardown()
```

Cleans up the session or logs closure - no actual persistence deletion.

---

## Swapping the Backend

To change persistence layers, implement a new `BaseDataConnector`:

```python
class MyConnector(BaseDataConnector):
    async def get(...): ...
    async def set(...): ...
    # etc.
```

Then inject into `HmapStorage`:

```python
storage = HmapStorage(MyConnector())
```

---

## Future Opportunities

* TTL-based cache keys for ephemeral agents
* Hybrid in-memory/durable store
* Indexed policy and Omni queries
* Versioned object tracking for audit

---

> Plantangenet storage is lightweight by default - but designed for serious extensibility, including **agent state via Omni**.

---

**Copyright (c) 1998-2025 Scott Russell**
**SPDX-License-Identifier: MIT**
