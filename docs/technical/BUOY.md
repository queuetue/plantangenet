## Buoy

A **Buoy** is the main unit of work and coordination in the Plantangenet ocean simulation system.

It represents a **local peer** with:

* Messaging (Topics)
* State Tracking (Status)
* Heartbeat and timebase awareness
* Storage and Transport (via Shard)

Think of it as the standard *active node* in your networked simulation.

---

### Conceptual Model

> A **Buoy** is a floating, signaling node in the ocean, with a *name*, *ID*, and *behavior*.

It can **publish** messages, **subscribe** to topics, **track** its status, and maintain connections to **storage** backends.

---

### Topics System

**Purpose**: Provide pub-sub style message bus for communication.

* Buoy *inherits* TopicsMixin.
* Supports `publish()` and `subscribe()`.
* Subscriptions are managed by topic name.
* Topics can represent event types, data channels, or command queues.

* Usage:

```python
await buoy.publish("temperature.update", {"value": 22.5})

await buoy.subscribe("temperature.update", my_callback)
```

**Use case**: A Buoy subscribes to clock ticks or heartbeat messages, and can relay data to other Buoys or external systems.

---

### Topics Handlers

Buoy supports declarative handler registration via `@on_topic()`:

```python
@on_topic("clock.tick")
async def handle_tick(self, message):
    ...
```

When a message is published to `"clock.tick"`, `handle_tick` is called automatically.

---

### Status System

**Purpose**: Structured, introspectable self-reporting of node state.

* Buoy *inherits* StatusMixin.
* Exposes a `status` property returning a dictionary.
* Tracks *registered* fields and their metadata.

* Automatic dirty-tracking:

```python
self.temperature = 22.5
assert self.dirty is True
```

* Supports sensitive fields:

```python
secret_key: str = watch(default="topsecret", sensitive=True)
```

When exported:

```python
{
    "secret_key": "***"
}
```

* Supports inclusion/exclusion in dict output.

---

### Example Buoy Status

```json
{
  "buoy": {
    "temperature": {
      "value": 22.5,
      "dirty": true,
      "updated_at": "2025-06-29T14:00:00Z"
    },
    "pressure": {
      "value": 1013,
      "dirty": false,
      "updated_at": null
    }
  }
}
```

---

### Declaring Status Fields

Use `watch` to define trackable properties:

```python
temperature: float = watch(default=20.0, description="Water temperature")
```

* Supports:

* Default values
* Metadata like descriptions
* Sensitivity
* Custom transforms

---

### Summary

* Buoy is a **Shard** with full messaging and storage capabilities.
* Tracks its **status** automatically.
* Supports **Topics** for decoupled message-based design.
* Designed for **distributed** simulation or coordination systems.

---

### Why "Buoy"?

> Like a real ocean buoy, it's a smart, floating node that signals, tracks data, and relays information in the current.

---

## Example Usage

```python
class TemperatureBuoy(Buoy):
    temperature: float = watch(default=20.0, description="Water temperature")

    @on_topic("clock.tick")
    async def handle_tick(self, message):
        self.temperature += 0.1
```
