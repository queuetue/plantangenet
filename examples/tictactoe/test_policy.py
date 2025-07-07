"""
Simple test to understand how the policy system works.
"""

from plantangenet.policy.policy import Policy
from plantangenet.policy.identity import Identity
from plantangenet.policy.role import Role


def test_policy_basics():
    """Test basic policy functionality."""

    policy = Policy()

    # Create a simple role and identity
    role = Role(id="test_role", name="test",
                description="Test role", members=[])
    identity = Identity(id="alice", nickname="Alice")

    # Add them to the policy
    policy.add_role(role)
    policy.add_identity(identity)
    policy.add_identity_to_role(identity, role)

    # Add a simple statement
    policy.add_statement(
        roles=[role],
        effect="allow",
        action=["test_action"],
        resource=["test_resource"]
    )

    # Test evaluation
    result = policy.evaluate(identity, "test_action", "test_resource")
    print(f"Basic test: {result.passed}, reason: {result.reason}")

    # Test with string identity
    result2 = policy.evaluate("alice", "test_action", "test_resource")
    print(f"String identity test: {result2.passed}, reason: {result2.reason}")

    # Test denied action
    result3 = policy.evaluate("alice", "denied_action", "test_resource")
    print(f"Denied action test: {result3.passed}, reason: {result3.reason}")


if __name__ == "__main__":
    test_policy_basics()
