# Plantangenet

## Introduction

Plantangenet is a framework and event-driven runtime for **building small, bounded, policy-enforced worlds**. It is designed for developers who need **negotiated sharing**, **explicit trust boundaries**, **enforceable policies**, and **ephemeral, attention-shaped memory**.

Plantangenet lets you model **privacy**, **trust**, **negotiation**, and **economic memory** as first-class system features. It is not just an API - it's a system design approach for building "tiny universes" where participants negotiate *what* they reveal, *to whom*, *at what level of detail*, and *for how long*.

---

## Core Concepts

* **Sessions**: Bounded contexts managing identity, policy, lifecycles, and local state.
* **Agents**: Policy-enforced actors that embody roles, preferences, and trust boundaries.
* **Chems**: *Planned*: Negotiable, context-aware identity interfaces controlling disclosure.
* **Cursors**: Focus declarations defining regions of interest, shaping memory and data access.
* **Compositors**: Transformations that generate partial, policy-filtered views.
* **Membry**: Attention-shaped, degraded, fading memory with TTL and Dust accounting.
* **Policies**: Machine-enforced rules governing who can do what, when, and how.
* **Dust**: Internal accounting system for contributions, value exchange, and attention prioritization.

---

## Why Plantangenet?

* **Negotiated Disclosure**

> Define exactly what data you share, with whom, at what resolution.

* **Enforceable Policy Boundaries**

> Machine-enforced, auditable rules for all interactions.

* **Ephemeral Memory**

> Memory that fades over time, shaped by attention and cost.

* **Economic Incentives**

> Contributions and retention paid with Dust.

* **Privacy by Design**

> Participant-controlled, role-based, asymmetric sharing.

*Example:* A collaborative writing app where users negotiate section visibility and sharing duration, with partial views for guest readers and full access for trusted collaborators.

---

## Features Overview

* **Bounded Sessions**: Explicit lifecycle boundaries with enforced policy contexts.
* **Multi-Axis Coordination**: Compositors generate views over multiple semantic axes. [compositing](docs/technical/COMPOSITORS_AND_AXES.md)
* **Pluggable Policy Engine**: Supports custom evaluators. [vanilla](python/plantangenet/policy/vanilla.py)
* **Integrated Storage & Transport**: Extensible backends for persistence and messaging. [storage](python/plantangenet/ocean/mixins/storage.py) [transport](python/plantangenet/ocean/mixins/transport.py)
* **Attention-Shaped Memory**: Membry stores degraded, ephemeral data based on Dust budgeting.
* **Identity & Policy Sync**: Ensures consistent, distributed permission enforcement.

---

## Use Cases

* Multiplayer games with negotiated secrecy and role-based views.
* Privacy-conscious simulations with partial disclosure.
* Federated services needing auditable, policy-driven data sharing.
* Collaborative art projects with granular credit tracking and ephemeral sharing.
* Data marketplaces with attention-priced memory and negotiated resolution.

---

## Technical Architecture

### Sessions

* Trust boundary and lifecycle manager.
* Manages agents, cursors, and metadata.
* Enforces policies for attached participants.

### Agents

* Actors embodying roles and preferences.
* Enforce policy context during interactions.
* Track cursors and agents.

### Chems *(Planned)*

* Negotiable, partial-disclosure interfaces for agents.
* Control what is revealed, to whom, and under what conditions.
* Integrate with policy evaluation and Membry.

### Cursors

* Declare regions of interest in time/axis space.
* Shape attention and memory allocation.
* Used to prioritize storage and degrade detail selectively.

### Compositors

* Generate **Views** of data tailored to policy.
* Apply degradation rules for partial disclosure.
* Support multiple consumer perspectives from shared semantic buffers.

### Membry

* Durable, lossy memory store with TTL.
* Supports degraded, attention-priced storage.
* Integrates Dust accounting to prioritize high-value regions.

### Policy Engine

* Evaluates permissions using roles and context.
* Supports static and negotiated policies.
* Enforces access for all operations.

### Dust

* Internal currency for contribution and value exchange.
* Used to allocate attention and control retention.

---

## Example: Musical Conductor

> *“What if time was a beat that drove system state?”*

A tick-based engine that can:

* Synchronize multiplayer music sessions.
* Drive timed art installations.
* Control pacing in games.
* Coordinate distributed systems.

*(See [popcorn.py](examples/popcorn.py) for full code.)*

---

## Example: Sessions and Banker Agent Integration

Here's how you create a session and add a Banker agent to manage all economic operations:

```python
from plantangenet.session import Session
from plantangenet.vanilla_banker import create_vanilla_banker_agent

# Create a session
session = Session(session_id="demo_session")

# Add a Banker agent with an initial Dust balance and cost base
banker = create_vanilla_banker_agent(initial_balance=100, cost_base_paths=["./effects.zip"])
session.add_banker_agent(banker)

# Get a quote for an action
quote = session.get_cost_estimate("save_object", {"fields": ["name", "email"]})

# Negotiate a transaction (get options, preview)
negotiation = session.negotiate_transaction("save_object", {"fields": ["name", "email"]})

# Commit a transaction (spend Dust)
result = session.commit_transaction("save_object", {"fields": ["name", "email"]}, selected_cost=quote["dust_cost"])

# Check balance and history
balance = session.get_dust_balance()
history = session.get_transaction_history()
```

All economic logic (pricing, negotiation, payment, refund) is now handled by the Banker agent. For more, see [Banker Agent Integration](docs/BANKER_AGENT_INTEGRATION.md).

---

## The `on_topic` Decorator

Registers message handlers with features like:

* `mod`, `cooldown`, `jitter`, `predicate`
* `debounce`, `once`, `distinct_until_changed`, `rate_limit`

*(Detailed examples in /examples/.)*

---

## Principles

* **Boundaries are explicit**: Sessions define clear scopes.
* **Trust is negotiated**: Chems and policies mediate disclosure.
* **Memory is shaped by attention**: Membry fades unused regions.
* **Privacy is by design**: Policy-enforced, participant-controlled sharing.
* **Fairness is accounted**: Dust tracks contributions and costs.
* **Transparency is enforced**: Auditable policies and logs.

---

## Status

Active development. Functional, evolving, and welcoming contributions.

---

## License

© 1998–2025 Scott Russell
SPDX-License-Identifier: MIT
