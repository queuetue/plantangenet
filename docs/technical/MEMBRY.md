# Membry: Policy-Governed Memory in Plantangenet

---

## Introduction

**Membry** is Plantangenet’s *policy-aware memory management layer*.

It is not a *separate database* or *new storage backend*. Instead, Membry is an **interface** that wraps existing storage systems - like the Omni Store and the Frame Store - to enforce **policy-governed behavior** on all read and write operations.

Membry ensures that *all persistence in Plantangenet is intentional, accountable, and negotiated*.

---

## Purpose

Plantangenet treats memory and storage as **privileged resources**:

* They represent capacity in a shared system.
* They cost real-world value to maintain.
* They must respect boundaries of **privacy**, **policy**, and **accountability**.

**Membry** enforces these principles by:

* Applying *policy rules* to control *what* can be persisted.
* Enforcing *TTL, fading, and degradation* of stored data.
* Filtering *retrieved* data to respect trust levels and privacy.
* Integrating with **Dust** to *charge* for persistence and detail level.

---

## Core Concepts

### 1. Not a Store, but a Policy Layer

Membry doesn’t replace your backing store (like Redis).

Instead, Membry *wraps* existing storage interfaces and:

* Validates incoming data against policy before storing.
* Determines retention, TTL, and degradation rules.
* Filters and transforms data on retrieval to match the requester's permissions.
* Charges **Dust** for persistence and retrieval based on defined policy.

---

### 2. Applies to Multiple Stores

Plantangenet has *at least two distinct storage types*:

* **Omni Store**: Agent state.

  * Field-level structured storage.
  * Supports observation, change-tracking.
  * Typically small, durable.

* **Frame Store**: Semantic Buffer.

  * Time-indexed frames of Axis impulses.
  * High-volume, ephemeral by default.
  * Supports negotiated focus and detail.

**Membry** applies consistently to both:

* Governing what can be persisted.
* Enforcing TTL and retention rules.
* Controlling access detail level.
* Charging Dust for capacity and lifespan.

---

### 3. Policy-Enforced Memory Behavior

Membry is designed to enforce **declared policy** rather than ad-hoc application logic.

Examples of policies Membry can enforce:

* **Redaction**: Mask sensitive fields.
* **Resolution Degradation**: Reduce precision or detail over time or by permission level.
* **Selective Retention**: Enforce TTL per field or per frame.
* **Access Filtering**: Restrict which fields a given Chem can see.
* **Persistence Cost**: Charge Dust for storing or retrieving data at certain resolution or duration.
* **Negotiated Views**: Customize retrieval based on the Chem's trust level or role.

---

## How Membry Works

### A. On Insert

* Receives data to be stored.
* Checks policy:

  * Is the writer allowed to persist this data?
  * Is the requested TTL permitted?
  * Does the actor have sufficient Dust?
  * Are there fields requiring redaction or transformation?
* Transforms data as needed.
* Charges Dust if required.
* Passes approved data to the underlying store.

---

### B. On Retrieval

* Receives request for data (e.g., a frame, an Omni field).
* Identifies requesting Chem and its policy context.
* Filters result:

  * Masks or redacts sensitive fields.
  * Degrades resolution if necessary.
  * Removes expired or policy-restricted elements.
* Charges Dust for detail level or historical depth.
* Returns authorized view of data.

---

### C. On Retention

* Periodically evaluates stored data for policy compliance.
* Enforces fading rules:

  * TTL-based expiration.
  * Resolution degradation over time.
  * Selective redaction.
* Can remove or transform stored data automatically to comply with declared policy.

---

## Example Use Cases

* **Privacy Enforcement**:

  * Membry ensures that sensitive Omni fields or frame regions are masked before leaving local storage or being shared with untrusted Chems.

* **Tiered Access**:

  * High-paying users (Dust) get higher-resolution frames or longer retention.
  * Free-tier users get degraded, partial, or ephemeral access.

* **Ephemeral Memory**:

  * Frames naturally fade after a defined TTL.
  * Memory can be trimmed based on system load, with policy deciding what survives.

* **Focus Negotiation**:

  * Consumers specify what they want to see.
  * Membry + Policy decide what they're *allowed* to see.

---

## Relationship to Dust

Dust is the **currency** of Plantangenet’s cooperative economy.

**Membry enforces Dust-based economics**:

* Storage and retention *cost* Dust.
* Resolution and detail level *cost* Dust.
* Policy defines conversion rates, minimums, and maximums.
* Membry ensures that no actor can store or retrieve more than they can afford.

This supports:

* **Fair, auditable resource allocation**.
* **Non-extractive compensation** for infrastructure providers.
* **Intentional, negotiated access** instead of uncontrolled sharing.

---

## Technical Design Sketch

Membry can be implemented as a *wrapper* over any storage backend:

```python
class Membry:
    def __init__(self, store, policy_engine, dust_account):
        self.store = store
        self.policy_engine = policy_engine
        self.dust_account = dust_account

    def store_data(self, key, value, chem, ttl=None):
        # Apply policy on insert
        permitted, transformed_value, required_dust = self.policy_engine.authorize_store(
            chem, value, ttl
        )
        if not permitted:
            raise PermissionError("Policy denied storage request.")

        # Charge Dust
        self.dust_account.charge(chem, required_dust)

        # Store
        self.store.set(key, transformed_value, ttl=ttl)

    def retrieve_data(self, key, chem):
        # Retrieve raw
        value = self.store.get(key)
        if value is None:
            return None

        # Apply policy on read
        filtered_value, required_dust = self.policy_engine.authorize_retrieve(
            chem, value
        )

        # Charge Dust
        self.dust_account.charge(chem, required_dust)

        return filtered_value
```

---

## Benefits

* **Unified Policy Enforcement** across multiple stores.
* **Flexible Retention Strategies**: Supports ephemeral and durable use cases.
* **Privacy by Design**: Masking, redaction, negotiated detail.
* **Cost Accounting**: Enforced with Dust, preventing unbounded usage.
* **Interoperability**: Works with any backend supporting simple get/set/delete.
* **Transparency**: Auditable, intentional, accountable persistence.

---

## Conclusion

Membry is Plantangenet’s approach to **trustable, negotiated, policy-governed memory**.

It transforms raw storage into:

* A **negotiated space** of shared memory.
* A **controlled, auditable system** of persistence.
* A **fairly priced** resource funded by Dust.

By enforcing policy at every boundary - insert, retention, retrieval - Membry ensures that Plantangenet’s memory isn’t just cheap caching.

It’s **collaborative infrastructure**, built on trust, policy, and intentional economics.

---

**Copyright (c) 1998-2025 Scott Russell**
**SPDX-License-Identifier: MIT**
