# Agents, Buoys, Gyres, and Drifts in Plantangenet

## Overview

Plantangenet's distributed simulation and coordination system is built on a flexible hierarchy of autonomous and infrastructural nodes. This document synthesizes and clarifies the roles, relationships, and inheritance patterns of the core agent types: **Agent**, **Buoy**, **Gyre**, and **Drift**.

---

## Ecosystem Features

Plantangenet agents operate within a rich ecosystem of protocols and services. Key features include:

- **Dust (Economics):** The system currency for resource usage, pricing, and rewards. All economic operations are managed by the [Banker agent](BANKER.md), which provides pricing, negotiation, logging, and distribution of Dust.
- **Transport:** Agents communicate via pub-sub messaging (e.g., NATS, topics) using transport mixins. This enables distributed, event-driven coordination.
- **Storage:** Agents persist and retrieve state using pluggable storage backends (e.g., Redis, file, in-memory), often via storage mixins.
- **Sessions:** Sessions provide context boundaries for trust, policy, and economic flows. Agents are grouped and managed within sessions, which delegate all economic operations to their Banker(s).
- **Policy & Access Control:** Fine-grained permissions and economic policies are enforced via pluggable policy modules, ensuring secure and auditable operations.
- **Extensibility:** New agent types, mixins, and features can be added to support custom behaviors, protocols, or domains.

For more details, see: [Dust/Economics](DUST.md), [Banker](BANKER.md), [Transport](TRANSPORT_COSTING.md), [Storage](STORAGE.md), [Sessions](SESSION.md), and [Policy](POLICY.md).

---

## Agent

An **Agent** is the base class for autonomous participants in the Plantangenet system. Agents can represent users, bots, or any entity capable of independent action. They provide:

- Identity and lifecycle management
- Messaging and event handling (via mixins)
- Extensible behaviors through composition

Agents are the foundation for more specialized node types.

---

## Buoy

A **Buoy** is a self-coordinating, persistent node in the Plantangenet ocean. It is the main unit of work and coordination, representing a local peer with:

- Messaging (Topics)
- State Tracking (Status)
- Heartbeat and timebase awareness
- Storage and Transport (via Shard)

**Buoy** is designed for distributed simulation or coordination systems, acting as a smart, floating node that signals, tracks data, and relays information. Buoys manage their own state and behavior, but do not orchestrate other agents.

**Key Features:**
- Inherits from `Shard` and multiple mixins (e.g., `TopicsMixin`, `StatusMixin`)
- Supports pub-sub messaging, status tracking, and storage
- Can subscribe to and handle topics declaratively
- Tracks and reports its own status, including sensitive fields

---

## Gyre

A **Gyre** is a higher-level coordinator node. It extends the capabilities of a Buoy by not only managing itself, but also orchestrating and interpreting the actions of other agents (including Drifts and possibly Buoys).

**Gyre** acts as a hub or controller for groups of agents, providing:
- Collective policy enforcement
- Resource management
- Orchestration and coordination of attached agents

**Key Features:**
- Inherits from `Buoy`
- Manages a collection of agents (with limits on number, etc.)
- Provides methods to add/remove agents and to update all managed agents
- Intended as the main target for orchestration and control in complex scenarios

---

## Drift

A **Drift** is a lightweight, mobile agent that is always attached to a Gyre (or Gyre-like node). Drifts do not coordinate themselves or others; instead, they delegate most operations—including financial and economic decisions—to their parent Gyre.

**Drift** is used for dynamic, possibly short-lived or mobile agents that need to interact with a Gyre for communication, data, coordination, and all Dust-related (economic) operations.

**Key Features:**
- Inherits from `Agent` and multiple mixins (e.g., `TimebaseMixin`, `HeartbeatMixin`, `OmniMixin`, `TopicsMixin`)
- Delegates publish/subscribe/get/set/delete operations to its attached Gyre
- Delegates all financial and economic operations (pricing, payments, Dust usage) to its Gyre, which interacts with the Banker
- Reports its own status, including information about its Gyre attachment
- Not intended as a control/orchestration point

---

## Inheritance and Mixin Chain

| Class  | Inherits From                | Mixins/Composition                |
|--------|------------------------------|-----------------------------------|
| Agent  | (base)                       | (varies by implementation)        |
| Buoy   | Shard                        | TopicsMixin, StatusMixin, etc.    |
| Gyre   | Buoy                         | (adds agent management)           |
| Drift  | Agent                        | TimebaseMixin, HeartbeatMixin, OmniMixin, TopicsMixin |

---

## Coordination Patterns

- **Buoy**: Self-coordinating, persistent node. Manages its own state and messaging.
- **Gyre**: Self-coordinating and orchestrates other agents. Acts as a hub/controller.
- **Drift**: Mobile, agent-like entity. Always attached to a Gyre, delegates operations to it.

---

## Targeting and Control

- **Buoy** and **Gyre** are intended as orchestration/control points.
- **Drift** is a participant, not a controller; always managed by its parent Gyre.
- Target Gyres or Buoys for orchestration, policy, and resource management—not Drifts.

---

## Example Usage

```python
class TemperatureBuoy(Buoy):
    temperature: float = watch(default=20.0, description="Water temperature")

    @on_topic("clock.tick")
    async def handle_tick(self, message):
        self.temperature += 0.1
```

```python
class MyGyre(Gyre):
    def __init__(self, agents, logger):
        super().__init__(agents=agents, logger=logger)
```

```python
class MyDrift(Drift):
    async def update(self):
        # Delegates to gyre for coordination
        await self._gyre.update()
```

---

## Best Practices

- Use Buoys for persistent, self-coordinating nodes.
- Use Gyres for orchestration and management of groups of agents.
- Use Drifts for mobile, dynamic agents that require coordination by a Gyre.
- Document and enforce the intended control points in your system.

---

## Glossary

- **Agent**: Autonomous participant in the system.
- **Buoy**: Self-coordinating, persistent node.
- **Gyre**: Coordinator node that manages itself and other agents.
- **Drift**: Mobile agent, always attached to a Gyre.
- **Shard**: Base class for persistent storage and transport.
- **Mixin**: Composable class providing additional features (e.g., TopicsMixin).

