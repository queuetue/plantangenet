# Storage in Plantangenet

Plantangenet uses a **key-value-based storage abstraction** designed for speed, flexibility, and low operational overhead. The storage system is responsible for persisting:

* **Identities**
* **Roles**
* **Policy Statements**

The default implementation - `HmapStorage` - sits atop a `BaseDataConnector`, which defines a uniform API for persistence engines.

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
* **Focused**: Stores only what the policy engine needs

### Namespacing Keys

Keys are prefixed by type for easy listing and filtering:

* `policy:*`

* `identity:*`
* `role:*`

### Example: Saving a Role

```python
await self.connector.set("role:admin", role.json())
```

Roles are stored as serialized JSON values.

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

If a backend can `get`, `set`, and `list` keys, it can support Plantangenet’s core.

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

This typically checks availability (e.g., Redis `PING`).

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

* TTL-based cache keys
* Hybrid in-memory/durable store
* Indexed policy queries
* Versioned object tracking for audit

---

> Plantangenet storage is lightweight by default - but designed for serious extensibility.

---
Copyright (c) 1998-2025 Scott Russell
SPDX-License-Identifier: MIT 