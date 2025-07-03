# Vanilla Policy: Reference Implementation

## Overview

**Vanilla** is the reference implementation of Plantangenet's Policy interface. It is designed for **clarity** and **correctness** rather than performance, favoring **conservative defaults** and **defensive programming**.

Vanilla provides a complete, working policy engine that can run a Plantangenet ocean while serving as a foundation for environment-specific engines.

---

## Design Philosophy

> *"Vanilla is intentionally not the fastest, strictest, or most configurable engine. It is intended as a foundation on which environment-specific engines can be built. But you can run a plantangenet ocean with it."*

**Vanilla prioritizes:**

- **Clarity**: Code is readable and well-documented
- **Correctness**: Conservative defaults with comprehensive error handling  
- **Completeness**: Full implementation of the Policy protocol
- **Defensive programming**: Graceful handling of edge cases and errors

---

## Architecture

### Storage Model

Vanilla uses **in-memory storage** for simplicity:

```python
self._identities: Dict[str, Identity] = {}          # identity_id -> Identity
self._roles: Dict[str, Role] = {}                   # role_name -> Role  
self._policies: List[Statement] = []                # List of policy statements
self.identity_roles: Dict[str, set[str]] = {}       # identity_id -> set of role_names
```

### Synchronous Design

All policy operations are **synchronous** to support:
- Simplicity and ease of integration
- Compatibility with synchronous storage and session systems
- Predictable, blocking behavior for per-field enforcement

### Error Handling Strategy

Every method includes **graceful error handling**:

- **Missing data**: Returns appropriate defaults (False, None, empty collections)
- **Invalid inputs**: Logs warnings and attempts recovery via type coercion
- **Storage failures**: Logs warnings but continues operation where possible
- **Exceptions**: Caught and logged, with fail-safe defaults applied

---

## Core Operations

### Identity Management

```python
# Add an identity
identity_id = policy.add_identity(
    Identity(identity_id="user123", name="Alice"),
    nickname="Admin Alice",
    metadata={"department": "security"}
)

# Retrieve an identity  
identity = policy.get_identity("user123")

# Delete an identity (removes from all roles)
policy.delete_identity(identity)
```

### Role Management

```python
# Create a role
role_name = policy.add_role(
    Role(role_id="role456", name="admin", description="System administrators"),
    members=["user123", "user456"]
)

# Get a role
role = policy.get_role("admin")

# Delete a role (removes from all statements)
policy.delete_role(role)
```

### Role Assignments

```python
# Assign identity to role
policy.add_identity_to_role(identity, role)

# Check role membership
has_admin = policy.has_role("user123", "admin")

# Remove from role
policy.remove_identity_from_role(identity, role)
```

### Policy Statements

```python
# Add a policy statement
statement_id = policy.add_statement(
    roles=["admin", "operator"],
    effect="allow", 
    action=["read", "write"],
    resource="database.*",
    condition={"time_of_day": "business_hours"}
)

# Check if roles exist
includes_roles = policy.includes_any_role(["admin", "guest"])
```

### Policy Evaluation

```python
# Evaluate access
result = policy.evaluate(
    identity="user123",
    action="read", 
    resource="database.users",
    context={"time_of_day": "business_hours"}
)

print(f"Access: {result.passed}, Reason: {result.reason}")
```

---

## Evaluation Logic

Vanilla implements a **conservative evaluation strategy**:

1. **Identity Resolution**: Convert identity string/object to ID and resolve roles
2. **Policy Matching**: Find statements matching identity roles, actions, and resources  
3. **Condition Evaluation**: Check any context conditions in matching statements
4. **Effect Application**: Apply **deny-wins** logic - any deny statement blocks access
5. **Default Deny**: If no allow statements match, access is denied

### Deny Takes Precedence

```python
# Even if an allow statement matches...
policy.add_statement(roles=["admin"], effect="allow", action="read", resource="*")

# ...a deny statement will block access
policy.add_statement(roles=["admin"], effect="deny", action="read", resource="secrets.*")

# Result: admin can read most things, but not secrets.*
```

### Wildcard Support

- **Roles**: `"*"` in roles matches any identity
- **Actions**: `"*"` in actions matches any action  
- **Resources**: `"*"` in resources matches any resource

---

## Lifecycle Management

```python
# Initialize policy engine
policy = Vanilla(logger=logger, namespace="production")

# Setup (optional, for future storage initialization)
policy.setup()

# ... use policy operations ...

# Cleanup resources
policy.teardown()

# Commit changes (no-op in memory implementation)
policy._commit()
```

---

## Configuration

Vanilla accepts minimal configuration:

```python
policy = Vanilla(
    logger=logging.getLogger("policy"),  # Optional logger
    namespace="environment_name"         # Logical namespace for this policy instance
)
```

---

## Error Handling Examples

### Graceful Identity Handling

```python
# Missing identity - creates minimal identity
result = policy.evaluate("unknown_user", "read", "resource")
# Result: denied (no roles = no access)

# Invalid identity type - converts to string
result = policy.evaluate(12345, "read", "resource") 
# Logs warning, treats as "12345"
```

### Role Management Errors

```python
# Adding duplicate role - updates existing
policy.add_role(existing_role)  # Updates rather than errors

# Invalid member ID - logs warning but includes
role.members = ["valid_user", None, "another_user"]
policy.add_role(role)  # Logs warning about None, continues
```

### Storage Failure Simulation

```python
# If storage fails, operations continue gracefully
# (In memory implementation, this means logging warnings)
try:
    policy.add_identity(identity)
except Exception:
    # Never reached - Vanilla handles all exceptions internally
    pass
```

---

## Extension Points

Vanilla serves as a foundation for specialized implementations:

### Storage Backend

Replace in-memory storage with persistent backends:

```python
class DatabaseVanilla(Vanilla):
    def add_identity(self, identity, nickname=None, metadata=None):
        # Store in database instead of memory
        self.db.store_identity(identity)
        return super().add_identity(identity, nickname, metadata)
```

### Custom Evaluation Logic

Override evaluation for specialized rules:

```python
class CustomVanilla(Vanilla):
    def evaluate(self, identity, action, resource, context=None):
        # Add custom pre-processing
        if self._custom_rules_apply(identity, action, resource):
            return self._custom_evaluation(identity, action, resource, context)
        return super().evaluate(identity, action, resource, context)
```

### External Policy Integration

```python
class FederatedVanilla(Vanilla):
    def evaluate(self, identity, action, resource, context=None):
        # Check local policies first
        local_result = super().evaluate(identity, action, resource, context)
        if not local_result.passed:
            return local_result
            
        # Check with federated policy service
        return self.federated_service.evaluate(identity, action, resource, context)
```

---

## Performance Characteristics

Vanilla is optimized for **clarity over performance**:

- **Identity lookup**: O(1) dictionary access
- **Role checking**: O(1) set membership test  
- **Policy evaluation**: O(n) linear scan of statements
- **Memory usage**: All data kept in memory

For high-performance needs, consider specialized implementations with:
- Indexed storage backends
- Compiled policy rules  
- Caching layers
- Distributed evaluation

---

## Testing Vanilla

```python
from plantangenet.policy.vanilla import Vanilla
from plantangenet.policy.base import Identity, Role

def test_vanilla():
    policy = Vanilla(logger=None, namespace="test")
    policy.setup()
    
    # Create test data
    identity = Identity("user1", "Test User")
    role = Role("role1", "tester", "Test role")
    
    # Test operations
    policy.add_identity(identity)
    policy.add_role(role)
    policy.add_identity_to_role(identity, role)
    
    # Test evaluation
    policy.add_statement(["tester"], "allow", "read", "test_data")
    result = policy.evaluate("user1", "read", "test_data")
    
    assert result.passed
    print("✅ Vanilla test passed!")
    
    policy.teardown()

test_vanilla()
```

---

## Persistence and Storage Backends

Vanilla Policy now supports efficient persistence and rehydration of its state using a common storage mixin. While the default storage is in-memory for clarity and simplicity, Vanilla Policy can be configured to use alternative backends (such as Redis) for distributed or persistent operation.

- **Persist/rehydrate pattern:** Vanilla Policy, along with its managed identities, roles, and statements, can persist its state to a storage backend and be rehydrated later.
- **Storage mixin:** The persistable logic is provided by a shared mixin, enabling consistent and extensible storage management across all policy-related objects.
- **Backend flexibility:** You can swap the storage backend for testing, production, or distributed scenarios without changing policy logic.

**Example: Persisting and Rehydrating a Vanilla Policy**

```python
# Persist the policy and all managed objects
data = await vanilla_policy.persist()
# ...store 'data' in your backend...

# Later, rehydrate the policy from persisted data
rehydrated_policy = await VanillaPolicy.rehydrate(data, storage_backend=redis_backend)
```

This approach enables robust testing, easy state recovery, and integration with a variety of storage solutions.

---

## Summary

Vanilla provides a **complete**, **reliable** implementation of Plantangenet's Policy interface. While not optimized for extreme performance, it offers:

- ✅ **Full protocol compliance**
- ✅ **Comprehensive error handling**  
- ✅ **Clear, maintainable code**
- ✅ **Synchronous, integration-friendly architecture**
- ✅ **Extensible design**

Use Vanilla for development, testing, small deployments, or as a foundation for specialized policy engines.

---

**Copyright (c) 1998-2025 Scott Russell**  
**SPDX-License-Identifier: MIT**
