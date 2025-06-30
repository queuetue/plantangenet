# Policies in Plantangenet: Identities, Chems, and Negotiated Enforcement

## Why Policies

Policies establish the rules that define **who** can act, **what** they can do, and **under what circumstances**.

In federated systems with multiple independent participants, clear policies prevent accidental or malicious misuse by enforcing **trust boundaries**. They create a shared understanding of acceptable actions, supporting **secure**, **privacy-conscious collaboration**.

Policies themselves are abstract. To make them meaningful in Plantangenet, **roles**, **identities**, and (planned) **chems** provide the context in which these rules apply.

---

## What is a Role (RBAC Theory)

Role-Based Access Control (RBAC) groups permissions into named **roles**. Instead of assigning permissions to each user or agent individually, you grant them roles that specify what they can do.

This simplifies management and ensures consistency even in complex systems with many participants.

Plantangenet extends this model by supporting **dynamic, context-sensitive roles** (via identities and chems), enabling **negotiated access** that adapts to trust and context.

---

## What is a Policy in Plantangenet?

A **Policy** is any object that knows how to evaluate whether an **identity** is allowed to perform an **action** on a **resource**, optionally using **context**.

It is a pluggable interface for enforcing trust boundaries.

It must implement:

```python
def evaluate(
    self, 
    identity: Union[Identity, str], 
    action: str, 
    resource: str, 
    context: Optional[dict] = None
) -> EvaluationResult:
```

---

## Applications in Plantangenet

Plantangenet's policy system is designed for **federated environments** where **privacy** and **negotiation** are key.

**Identities** provide stable references for agents and users.
**Roles** bundle permissions, making access manageable and consistent.
**Chems** (planned) are *dynamic*, *context-sensitive* identities that enable **negotiated**, **selective disclosure**.

Policies govern these interactions, ensuring that **all data sharing** follows agreed-upon rules and respects **local autonomy**.

---

## Subjects and Resources

**Subjects** are entities making requests:

* Users with persistent identities
* Agents acting on behalf of users or systems
* (Planned) **Chems** that negotiate context-sensitive identities per interaction

**Resources** are the targets of actions:

* Data stores
* APIs
* Logs
* Even other chems (planned), supporting partial, negotiated views

Policies manage both *who* can act and *how* resources respond to different requesters.

---

## Roles and Permissions

Roles **bundle permissions** to simplify access control.

Policy statements link **roles** to **allowed** or **denied** actions on specific resources, optionally under conditions.

Subjects can hold multiple roles at once, assigned statically or negotiated dynamically (via chems or identity services).

---

## Negotiated Perspective and Chems

**Chems** are central to Plantangenet’s **privacy-preserving vision**.

They are planned as **dynamic**, **negotiated identities** that support **partial disclosure**.

For example, a chem might share only **aggregated** or **low-resolution** data to protect sensitive details while still enabling collaboration.

> *Example:* A chem representing a research dataset might allow sharing summary statistics but block access to raw data.

While chems are not yet fully implemented, the policy design anticipates them by supporting context-aware, partial disclosure in evaluation.

---

## Conditions and Context-Aware Controls

Policies can include **conditions** that evaluate **request context**:

* Origin of the request
* Session attributes
* Trust level
* Requested data resolution

This enables **fine-grained control** for use cases like multi-tenancy, selective disclosure, and federated sharing.

---

## Enforcement Model

Requests in Plantangenet follow a consistent evaluation process:

1. **Identify** the subject making the request.
2. **Resolve** roles from identity services or chem metadata (planned).
3. **Match** relevant policy statements.
4. **Evaluate** conditions and context.
5. **Apply** the effect, with **deny** taking precedence over **allow**.

---

## Pluggable Architecture

Plantangenet’s **Policy** interface is **modular** and **extensible**.

It can:

* Integrate with external policy-as-a-service systems
* Support attribute-based access control (ABAC)
* Include cryptographic verification of roles or identities
* Allow live policy updates without restarting services

---

## Summary

Plantangenet’s policy system provides a **flexible**, **auditable** framework for access control in federated environments.

By treating **roles**, **identities**, and (planned) **chems** as first-class inputs to policy evaluation, it enables **secure**, **privacy-conscious**, **negotiated collaboration**.

---

## Audience

This document is intended for **developers**, **security architects**, and **students** interested in understanding Plantangenet’s policy system and its role in supporting **federated**, **privacy-conscious collaboration**.

---

## Example Policy Statement

* **Roles:** “analyst”
* **Effect:** “allow”
* **Actions:** “read.buffer”
* **Resources:** “ocean.data”
* **Conditions:** `{ resolution: 'low' }`

---

## Glossary

* **Policy:** An interface defining rules about who can do what, given context.
* **Identity:** A stable representation of a user, agent, or system component.
* **Chem (planned):** A negotiable, context-sensitive identity supporting selective disclosure.
* **Role:** A named grouping of permissions assigned to users, agents, or chems.
* **Condition:** A context-aware rule refining access decisions based on request details.
* **Policy Statement:** A rule defining roles, effects, actions, resources, and conditions.
* **Federated:** A system where authority and decision-making are distributed among cooperating peers.

---

**Copyright (c) 1998-2025 Scott Russell**
**SPDX-License-Identifier: MIT**
