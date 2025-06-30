# Views in Plantangenet

## Introduction

A **view** in Plantangenet is the final, policy-governed, context-aware representation of shared semantic state delivered to a consumer. Views are dynamic and negotiated—they do not exist in advance but are created on demand by resolving multiple interacting layers:

* **Chems**: Define who the requester is, their permissions, and what context they reveal.
* **Policies**: Enforce rules about what data can be accessed, at what resolution, and under which conditions.
* **Cursors**: Declare the consumer’s focus or region of interest in the data.
* **Membry**: Determines what detail is actually available, managing persistence, fading, and degradation.
* **Compositors**: Assemble and transform the final data delivered as a view.

## Properties of Views

* **Context-Sensitive**: Tailored to the identity (Chem) and focus (Cursor) of the consumer.
* **Negotiated**: The result of policy evaluation, trust levels, and explicit requests.
* **Ephemeral**: Often generated per request, not stored indefinitely.
* **Auditable**: Creation and delivery can be logged and validated against policy.

## How Views Are Created

1. **Consumer defines Cursor**: The region or axes they want to access.
2. **Chem mediates identity**: Establishes what trust level, roles, or policies apply.
3. **Policy evaluated**: Determines what data can be shared and at what detail.
4. **Membry consulted**: Supplies stored frames at the allowed resolution, factoring in degradation or TTL policies.
5. **Compositor assembles**: Applies composition rules to produce the final structured response.

## Examples

* A paying customer’s Chem might enable high-resolution views with detailed history.
* An anonymous Chem might only be granted low-resolution or aggregated summaries.
* A regulated dataset might enforce redaction or masking automatically via policy.

## Design Goals

* **Privacy Preservation**: No participant sees more than policy allows.
* **Efficiency**: Only requested regions are fetched and composed.
* **Negotiated Disclosure**: Chems and Policies ensure partial views can be safely shared.
* **Flexible Presentation**: Views can be tailored for dashboards, ML training, simulations, or audits.

## Integration with Other Components

* **Chems**: Provide negotiable identities that determine trust level and scope.
* **Policies**: Define access rules and transformations.
* **Cursors**: Let consumers focus their requests on relevant data regions.
* **Membry**: Enforces retention, degradation, and policy-driven detail control.
* **Compositors**: Transform semantic buffers into consumer-ready representations.
---
Copyright (c) 1998-2025 Scott Russell
SPDX-License-Identifier: MIT 