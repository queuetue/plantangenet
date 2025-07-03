# Policies in Plantangenet: Identities, Chems, and Negotiated Enforcement

## Why Policies

Policies establish the rules that define **who** canPlantangenet's **Policy** interface is *## Example Policy Statement

A typical policy statement might look like:

* **Statement ID:** "stmt-001"
* **Roles:** ["analyst", "researcher"]
* **Effect:** "allow"
* **Actions:** ["read", "query"]
* **Resources:** ["ocean.data", "ocean.buffer"]
* **Conditions:** `{ "resolution": "low", "time_of_day": "business_hours" }`
* **Delivery:** `{ "format": "json", "encryption": "standard" }`

This statement allows users with "analyst" or "researcher" roles to read and query ocean data and buffers, but only during business hours and with low resolution, delivered as encrypted JSON.r** and **extensible**.

The current implementation includes:

* **Vanilla Policy**: A reference implementation with in-memory storage, designed for clarity and correctness
* **Synchronous design**: All policy operations are synchronous for simplicity and performance
* **Graceful error handling**: Methods include comprehensive error handling with logging and fallback behaviors
* **Type safety**: Full type annotations and protocol compliance

Future extensions can:

* Integrate with external policy-as-a-service systems
* Support attribute-based access control (ABAC) beyond role-based control
* Include cryptographic verification of roles or identities
* Allow live policy updates without restarting services
* Support persistent storage backends (database, file-based, etc.)what** they can do, and **under what circumstances**.

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

All Policy implementations must implement the synchronous methods defined in the Policy protocol:

```python
def evaluate(
    self, 
    identity: Union[Identity, str], 
    action: str, 
    resource: str, 
    context: Optional[dict] = None
) -> EvaluationResult:
```

The Policy protocol also includes methods for managing identities, roles, and policy statements:

- Identity management: `add_identity()`, `get_identity()`, `delete_identity()`
- Role management: `add_role()`, `get_role()`, `delete_role()`, `has_role()`
- Role assignments: `add_identity_to_role()`, `remove_identity_from_role()`
- Policy statements: `add_statement()`, `delete_statement()`, role-to-statement operations
- System lifecycle: `setup()`, `teardown()`, `_commit()`

---

## Applications in Plantangenet

Plantangenet's policy system is designed for **federated environments** where **privacy** and **negotiation** are key.

**Identities** provide stable references for agents and users, with attributes like `identity_id`, `name`, and optional `metadata`.
**Roles** bundle permissions, making access manageable and consistent. Roles have `role_id`, `name`, optional `description`, and can contain lists of member identity IDs.
**Policy Statements** define the actual access rules, linking roles to allowed/denied actions on resources with optional conditions.
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

**Policy statements** are the core mechanism that link **roles** to **allowed** or **denied** actions on specific resources, optionally under conditions. Each statement contains:

- `statement_id`: Unique identifier
- `roles`: List of role names that the statement applies to
- `effect`: Either "allow" or "deny" 
- `actions`: List of action strings (e.g., "read", "write", "delete")
- `resources`: List of resource identifiers
- `condition`: Optional dictionary of context requirements
- `delivery`: Optional delivery configuration

Identities can hold multiple roles simultaneously, and roles can be assigned statically during identity creation or dynamically through role management operations.

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

1. **Identify** the subject making the request (Identity object or string ID).
2. **Resolve** roles associated with the identity from the policy system's storage.
3. **Match** relevant policy statements based on roles, actions, and resources.
4. **Evaluate** any conditions against the provided context.
5. **Apply** the effect, with **deny** statements taking precedence over **allow** statements.
6. **Return** an `EvaluationResult` with the decision, reason, and any associated messages.

The evaluation is **fail-secure** by default - if no explicit allow policy matches, access is denied.

**Per-field Enforcement:**

Plantangenet supports per-field (per-attribute) access control by invoking policy checks on every field access (read/write) in models using `PersistedBase` and `Observable` descriptors. This enables fine-grained, identity-aware, and context-sensitive enforcement at the data model level.

---

## Pluggable Architecture

Plantangenet’s **Policy** interface is **modular** and **extensible**.

It can:

* Integrate with external policy-as-a-service systems
* Support attribute-based access control (ABAC)
* Include cryptographic verification of roles or identities
* Allow live policy updates without restarting services

---

## Persistence and Storage

All policy-related objects in Plantangenet—including policies, identities, roles, and statements—are now designed to be **persistable** and **rehydratable**. This is achieved via a common storage mixin and the omni/persistable/observable field system, enabling efficient, extensible, and testable state management.

- **Persist/rehydrate pattern:** Each object can persist its state to a storage backend (e.g., Redis) and be rehydrated later, supporting robust recovery and distributed operation.
- **Centralized storage backend management:** The session is responsible for setting the storage backend for all managed persistable types, ensuring consistent configuration and simplifying testing.
- **Extensibility:** The persist/rehydrate pattern is generic and can be extended to other policy-managed objects as needed.

**Example: Persisting and Rehydrating a Policy**

```python
# Persist the policy and all managed objects
data = await policy.persist()
# ...store 'data' in your backend...

# Later, rehydrate the policy from persisted data
rehydrated_policy = await Policy.rehydrate(data, storage_backend=redis_backend)
```

This approach enables:
- Fine-grained, auditable policy management
- Easy integration with different storage backends
- Simplified testing and mocking of policy state

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

* **Policy:** An interface defining rules about who can do what, given context. Implements synchronous methods for evaluation and management.
* **Identity:** A stable representation of a user, agent, or system component with `identity_id`, `name`, and optional `metadata`.
* **Chem (planned):** A negotiable, context-sensitive identity supporting selective disclosure.
* **Role:** A named grouping of permissions with `role_id`, `name`, optional `description`, and member list.
* **Policy Statement:** A rule defining `statement_id`, `roles`, `effect`, `actions`, `resources`, and optional `condition`/`delivery`.
* **Condition:** A context-aware rule refining access decisions based on request details.
* **EvaluationResult:** The result of policy evaluation containing `passed` boolean, `reason` string, and optional `messages`.
* **Federated:** A system where authority and decision-making are distributed among cooperating peers.
* **Vanilla Policy:** The reference implementation of the Policy interface with in-memory, synchronous storage.

---

**Copyright (c) 1998-2025 Scott Russell**
**SPDX-License-Identifier: MIT**
