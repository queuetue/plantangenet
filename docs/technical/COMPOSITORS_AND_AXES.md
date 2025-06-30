# Frames and Axes in Plantangenet

## Introduction

In Plantangenet, the **semantic compositor** coordinates data from independent, domain-specific axes into a shared semantic buffer. Frames are the ephemeral snapshots of this coordinated state, while axes are the independent generators of impulses along specific semantic dimensions. Together, they enable modular, distributed, and negotiated data sharing across diverse consumers and producers.

---

## Axes

An **axis** is a peer responsible for producing domain-specific impulses, such as time progression, gravity effects, mass distribution, color hue, or sound harmony. Each axis operates independently, focusing on its specialized domain without assuming how its data will be consumed or rendered. Axes can also adjust output detail in response to consumer-provided **focus** cues, prioritizing the most relevant data.

---

## Frames and Ephemerality

A **frame** is a snapshot of coordinated data from all participating axes at a given moment. Frames are designed to be ephemeral: they can be skipped if resources are constrained or if only the latest state is needed. This intentional skipping ensures responsive, efficient operation even in high-latency or distributed environments, avoiding bottlenecks while supporting asynchronous updates.

---

## Dirty Regions and Efficient Updates

The compositor tracks **dirty regions**, which represent changes since the last frame. Only these regions are recomputed and broadcast, significantly reducing computation and network usage in large-scale systems. This mechanism supports variable update rates from different axes and ensures consumers only process what's new.

---

## Cursors and Focus Negotiation

Consumers express their interests via **cursors**, metadata structures indicating the specific regions or semantic dimensions they care about. The compositor uses these focus hints to prioritize detail and routing for different consumers. Axes respond to these negotiated focuses by adjusting impulse generation to deliver relevant detail while respecting privacy policies.

Focus negotiation is mediated through chems and policy engines: a consumer's chem negotiates what it can request, while the producing axes' chems negotiate what they are willing to reveal. Policies ensure that these negotiations are explicitly governed and auditable.

---

## Integration with Chems and Policies

Chems provide the context-sensitive identities for both consumers and producers. Policies define the rules for what data can be shared, at what detail level, and under what conditions. This integration allows:

* Asymmetric sharing: Consumers may see different versions of the same semantic buffer.
* Privacy-aware negotiation: Sensitive properties (like mass) can be masked while still enabling shared computations (like velocity updates).
* Federated cooperation: Axes and consumers can be distributed, negotiating detail and focus across trust boundaries.

---

## Rendering and Interpretation

The compositor deliberately avoids enforcing any specific rendering or interpretation. It maintains the semantic buffer in an abstract form, leaving consumers to interpret it according to their needs—whether that's a user interface, scientific simulation, control system, or artistic visualization. This separation ensures a single coordinated model can support many use cases without architectural changes.

---

## Benefits

* **Separation of Concerns:** Decouples semantic generation from rendering.
* **Modularity:** Supports independent evolution of axes.
* **Efficiency:** Skipped frames and dirty tracking avoid unnecessary work.
* **Focus Awareness:** Consumers get the detail they need without enforcing global synchronization.
* **Privacy and Negotiation:** Chems and policies mediate controlled, negotiated sharing.
* **Scalability:** Enables asynchronous, distributed production.
* **Interoperability:** Provides a shared semantic buffer usable by diverse consumers.
---
Copyright (c) 1998-2025 Scott Russell
SPDX-License-Identifier: MIT 