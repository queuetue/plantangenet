"""
Debug the policy role ID issues.
"""

from plantangenet.policy.policy import Policy
from plantangenet.policy.identity import Identity
from plantangenet.policy.role import Role


def debug_policy_role_tracking():
    """Debug how roles are tracked in the policy system."""

    policy = Policy()

    # Create a role with consistent ID and name
    role = Role(id="test_role", name="test_role",
                description="Test role", members=[])
    identity = Identity(id="alice", nickname="Alice")

    # Add them to the policy
    policy.add_role(role)
    policy.add_identity(identity)
    policy.add_identity_to_role(identity, role)

    print("=== After setup ===")
    print(f"Roles: {list(policy.roles.keys())}")
    print(f"Identities: {list(policy.identities.keys())}")
    print(f"Identity roles: {dict(policy.identity_roles)}")

    # Check what role alice has
    alice_roles = list(policy.identity_roles.get("alice", set()))
    print(f"Alice's roles: {alice_roles}")

    # Add a statement
    policy.add_statement(
        roles=["test_role"],  # Using string role name
        effect="allow",
        action=["test_action"],
        resource=["test_resource"]
    )

    print(f"\nStatements: {len(policy.policies)}")
    for i, stmt in enumerate(policy.policies):
        print(
            f"  Statement {i}: {stmt.effect} {stmt.action} on {stmt.resource} for roles {stmt.role_ids}")

    # Test evaluation
    result = policy.evaluate("alice", "test_action", "test_resource")
    print(f"\nEvaluation result: {result.passed}, reason: {result.reason}")

    # Manual debug of _policy_matches
    stmt = policy.policies[0]
    identity_roles = list(policy.identity_roles.get("alice", set()))
    print(f"\nManual match check:")
    print(f"  Statement role_ids: {stmt.role_ids}")
    print(f"  Alice's roles: {identity_roles}")
    print(
        f"  Role match: {any(role in stmt.role_ids for role in identity_roles)}")
    print(f"  Action match: {'test_action' in stmt.action}")
    print(f"  Resource match: {'test_resource' in stmt.resource}")


if __name__ == "__main__":
    debug_policy_role_tracking()
