# Chems: Contextual Identity and Negotiation in Plantangenet

> “Let’s negotiate what you can see, what I will share, at what level of detail and truth, depending on who you are and why you ask.”

## Introduction

In Plantangenet, a *chem* is a structured, negotiable identity used to manage how an agent's private context is shared with the network. Chems enforce clear, auditable boundaries between local sessions and the federated environment. They allow agents to collaborate without losing control over their private data, using explicit policy to manage trust, roles, and permissions.

The system distinguishes *what* data is shared (handled by the Semantic Compositor) from *who* can access it and *how* it's transformed (governed by chems and policy). This separation ensures secure, intentional collaboration in distributed systems.

*Chems* are Plantangenet's negotiable, context-sensitive identities. Letx explore their role in enforcing clear, auditable boundaries between private sessions and federated interactions, showing how chems integrate policy enforcement, roles, focus negotiation, and privacy-preserving sharing:

## Core Concepts

### Contextual Identity

A chem acts as a well-defined role or persona. Agents can manage multiple chems, each with its own policies, trust level, and history. This supports compartmentalization, allowing agents to reveal only what is necessary to different audiences while preserving privacy and narrative control.

### Session vs. Chem

* **Session**: The agent’s private, local state with full internal detail.
* **Chem**: The filtered, policy-governed, network-facing projection of that session. This boundary ensures sensitive data is transformed, masked, or excluded before leaving local control.

> “A first-class citizen in the system for expressing partial, policy-bound, negotiated views of state.”

### Policies and Roles

Chems rely on the Policy Engine to enforce permissions, evaluate roles, conditions, and effects. Policies define *who* can act, *what* they can do, and *under what conditions*. Resources can also behave like chems, enabling symmetric negotiation and consistent trust boundaries.

### Negotiated Perspective

Chems enable asymmetric trust and partial disclosure, supporting negotiated data sharing that adapts to each requester’s trust level. Policies enforce selective access, allowing, for example, aggregated or low-resolution data to be shared while protecting sensitive details.

### Default and Forked Chems

* **Default Chem**: A general-purpose identity with broad, shared policies for typical interactions.
* **Forked Chem**: A specialized, private role with its own isolated policies and history, useful for experimentation or sensitive work.

Forking supports flexible, context-sensitive interactions by allowing agents to adopt specialized identities without affecting default roles.

### Privilege and Trust

All permissions in Plantangenet are explicit and fully auditable. Chems start untrusted by default and gain privileges only through clear, negotiated agreements governed by policy. This model ensures secure, transparent, and accountable interactions in federated systems.

## Integration with the Semantic Compositor

Chems negotiate their view of the shared semantic buffer aggregated by the Semantic Compositor. Policies determine:

* **What** data can be accessed.
* **How** it is transformed or masked.
* **If** access is allowed at all.

Consumers use **focus hints** or **cursors** to specify their interests, while policies mediated through chems ensure that requested data respects privacy boundaries. This approach supports privacy-preserving collaboration, where consumers see only what they’re allowed to see, at the required level of detail.

## Design Patterns

* **Session-to-Chem Boundary**: Enforces privacy and narrative control.
* **Default Chem**: Simplifies typical interactions with shared policies.
* **Forked Chem**: Enables isolated, private contexts for specialized roles.
* **Explicit Privilege**: Requires all permissions to be negotiated and auditable.
* **Policy Integration**: Governs both subjects and resources symmetrically.
* **Negotiated Perspective**: Allows context-sensitive, partial data sharing with masking and transformation.
* **Focus Negotiation**: Consumers declare interests that policies evaluate, enabling tailored data delivery while respecting privacy.

---
Copyright (c) 1998-2025 Scott Russell
SPDX-License-Identifier: MIT 