# Gyre

A **Gyre** is the coordinating manager for a group of **Agents**. It represents a localized, structured swirl of activity, conceptually inspired by the circulating currents of the real-world ocean gyres.

# Purpose

The **Gyre**:

* Hosts and manages many **Agents**.
* Coordinates their lifecycle(add/remove/setup/update).
* Provides them with shared access to:

    * **Message bus / topic system**.
    * **Storage** (e.g., Redis, memory store).
* Acts as a **router** for messages among Agents(planned feature).
* Can collect and track frames / simulation steps.

> In short: The Gyre is the center of gravity for a swarm of Agents.

---

# Design Rationale

* **Agents** do not have their own independent transport or storage connections.
➜ They delegate these to their **Gyre**.
* This models real-world systems where individual agents share infrastructure but maintain local state.
* Encourages modular design: Agents can be lightweight and focused, Gyre handles orchestration.

---

# Analogy

> *A Gyre is an ocean current system
Agents are floating objects caught in its swirl.*

---

# Key Features

* Manages **Agent** instances.
* Enforces limits(max Agents).
* Exposes shared messaging and storage APIs.
* Handles simulation frames(optional).
* Provides unified status reporting.

---

# Example Usage

# Create a Gyre

```python
gyre = Gyre(
    greeblies=[],
    logger=logger,
    namespace="simulation"
)
```

# Add Agents

```python
agent = Agent(
    gyre=gyre,
    namespace="agent-001",
    logger=logger
)

gyre.add_greeblie(agent)
```

# Shared Publish/Subscribe

Agents use Gyre’s transport:

```python
await agent.publish("my.topic", {"data": 123})
await agent.subscribe("my.topic", my_callback)
```

Gyre routes the message.

---

# Class Layout

# `Gyre`

* `__init__`:

    * Sets limits(max Agents, frame history, etc.)
    * Holds a list of Agents.
    * Sets up shared transport and storage(via Buoy).

* Properties:

    * `greeblies`: Current list of Agents.
    * `name`: Gyre’s user-facing name.

* Methods:

    * `add_greeblie`: Add a Agent.
    * `remove_greeblie`: Remove a Agent.
    * `on_frame`: Called each frame(e.g., clock tick).
    * `update`: Can trigger updates across Agents.

---

# Planned Features

* Sophisticated routing of messages to Agents.
* Shared event bus for inter-Agent communication.
* Coordinated state snapshots.
* Frame-by-frame simulation management.

---

# Notes for Developers

* **Storage**: All Agents share the Gyre’s storage prefix and backend.
* **Messaging**: All topic subscriptions/publishes go through Gyre.
* **Status**: Agents include metadata showing attachment to their Gyre.

---

# Example Status Output

When queried, Gyre might report:

```json
{
    "gyre": {
        "name": "Atlantic",
        "agent_count": 3
    },
    "agent.abcd12": {
        "attached_to": {
            "name": "Atlantic",
            "id": "some-gyre-id",
            "short_id": "abcd12"
        },
        "namespace": "simulation",
        ...
    }
}
```

---

# 🌊 Why "Gyre"?

> *Because like an ocean gyre, it traps and circulates Agents within its flow.*

A Gyre in this system is **not a flat manager**. It’s a dynamic, shared environment with shared infrastructure, coordinating many smaller, simpler agents.
