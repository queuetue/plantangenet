# Plantangenet Session

**Managing Boundaries, Identity, Policy, and Lifecycle for Connected Agents**

A **Session** is the *boundary* around multiple connected **Agents** and their **Cursors** in Plantangenet. It acts as a **coordination context** for lifecycle management, preference tracking, and *policy enforcement*, providing the foundation for negotiated, privacy-aware, and economically-shaped data exchange.

---

## Overview

A **Session** is the local **owner** of many independent **Agents** (clients, bots, bridges) and their **Cursors** (regions of interest). It acts as:

* A **lifecycle manager** for attached agents
* A **trust and policy boundary** for enforcing access controls
* An **introspection and configuration hub** for state and metadata
* A **container** for connections, cursors, subscriptions, and economic signals

Sessions are the **natural place** to:

* Track *who* and *what* is attached
* Enforce *policy* for attachments and actions
* Handle *authentication* and *authorization*
* Coordinate *identity* and *roles*
* Interface with *Compositors* for data generation
* Observe *state* and *status* of participants

---

## Why a Session?

Real systems don't have just **one** participant per connection. Instead:

* Agents may maintain multiple *cursors* or *subscriptions*.
* Agents may spawn *transient* tasks or drifts.
* Agents may hold *persistent* identities and roles.
* Multiple Agents might share a *negotiated context*.

A **Session** gives you a single object to manage this complexity with strong policy boundaries.

---

## Key Features

* **ID and Metadata**
  Each session has a stable `session_id` and customizable metadata, supporting auditability and personalization.

* **Agent Management**
  Sessions own the lifecycles of connected Agents, adding, removing, and coordinating them.

* **Cursor Management**
  Sessions track **Cursor** objects on behalf of Agents, defining regions of interest in time/axis space.

* **Policy Enforcement**
  Sessions enforce a **Policy** interface that evaluates permissions for actions on resources.

* **Compositor Integration**
  Sessions interface with **Compositors** to retrieve or generate data views matching Cursors, enforcing policy for disclosure.

* **Lifecycle Hooks**
  Sessions support setup and teardown for all contained Agents, ensuring clean resource management.

* **Reactive Hooks**
  Sessions support on-change callbacks for integration into higher-level event systems.

---

## Example Use Cases

* A WebSocket connection is represented as a Session.
* An authenticated user's workspace in the UI is backed by a Session.
* A background worker spawns a Session for task batches.
* A Session negotiates data disclosure policy for a guest user.
* A Session tracks paid-for attention (Dust) by managing Cursors.

---

## Example (Conceptual)

```python
session = Session(policy=my_policy)

# Add user metadata
session.metadata["user_id"] = "alice"

# Add an Agent
session.add_agent(AliceAgent())

# Add a Cursor on behalf of the agent
session.add_cursor(AliceAgent(), Cursor(axes=["temperature"], tick_range=(100, 200)))
```

---

## Lifecycle Management

Sessions manage:

* Adding and removing Agents and Cursors
* Tracking the active set of resources
* Cleaning up attached Agents on disconnect or teardown
* Supporting reactive hooks for event integration

---

## Trust and Policy Boundary

In Plantangenet’s model:

* Sessions hold **identity** and **metadata** for *this* connection.
* Sessions negotiate **roles** and **policies** for attached Agents.
* All attached Agents share this **trust context**.
* The **Policy** interface evaluates and enforces *what is allowed* and *what gets disclosed*.

Example Policy call:

```python
allowed = policy.evaluate(agent, action="read", resource="axis.temperature")
```

---

## Compositor Coordination

Sessions **interface with** Compositors (external data producers):

* Querying Buffers using Cursors
* Enforcing policy-based masking or degradation
* Supporting negotiated, partial disclosure

Sessions don't own Compositors but *coordinate* with them securely.

---

## Federation and Chems

Sessions are the **place where identity negotiation happens**:

* Sessions may carry a **Chem** - a policy-aware, partial disclosure interface.
* Chems act as *bidirectional compositors*, enforcing asymmetric, negotiated sharing.
* Agents inherit the Session’s **trust context**, roles, and negotiated permissions.

> *Note: Chem is the advanced abstraction for future development, where policy becomes fully negotiated and ML-ready.*

---

## Recommended Pattern

* **Create** a Session per connection, user, or context.
* **Attach** Agents that belong to it.
* **Negotiate** policy once at the Session level.
* **Use** the Session’s metadata and roles for all evaluations.
* **Teardown** the Session to clean up all resources on disconnect.

---

## Conceptual Analogs

* JACK or Wayland sessions → manage user connection boundaries
* Database sessions → scoped, authenticated query sets
* Web sessions → cookies, auth contexts, state
* Kafka consumer groups → shared cursor state

---

## Example Session Responsibilities

* Who are the Agents?
* What roles and policies do they have?
* What Cursors are they tracking?
* What Compositors are they querying?
* What data can they see?
* How are Dust budgets accounted?
* How is privacy enforced?

---

## Benefits

* Clean separation of **identity** and **agent logic**
* Supports **negotiated privacy** and **selective disclosure**
* Manages **transient** and **persistent** state with lifecycle hooks
* Enables **per-user policy enforcement** via a **Policy** interface
* Supports **economically-shaped attention** (via Dust and Cursors)
* Encourages **modular, testable** agent designs

---

## Summary

**Plantangenet Sessions** are designed to be:

* The *boundary of trust*
* The *scope of lifecycle management*
* The *context of negotiated policy*
* The *manager of attached Agents and their Cursors*
* The *coordinator for secure access to Compositors*

Sessions are the *interface* between a user (or peer) and the agents working on their behalf, enforcing policy-bound, auditable, and economic participation in the Plantangenet system.

---

**Copyright (c) 1998-2025 Scott Russell**
**SPDX-License-Identifier: MIT**

