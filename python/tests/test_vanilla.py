import pytest
from plantangenet import GLOBAL_LOGGER
from plantangenet.policy.vanilla import Vanilla
from plantangenet.policy.base import Identity, Role


@pytest.fixture
def vanilla():
    v = Vanilla(logger=GLOBAL_LOGGER, namespace="test")
    v.setup()
    yield v
    v.teardown()


def test_role_assignment(vanilla):
    identity = Identity(identity_id="user1", name="U1", metadata={})
    role = Role(role_id="r1", name="admin",
                description="Admin", members=["user1"])

    vanilla.add_identity(identity)
    vanilla.add_role(role)

    assert vanilla.has_role("user1", "admin")


def test_policy_permission_granted(vanilla):
    identity = Identity(identity_id="u2", name="U2", metadata={})
    role = Role(role_id="r2", name="writer",
                description="Writer", members=["u2"])

    vanilla.add_identity(identity)
    vanilla.add_role(role)

    # Add statement for writer role
    vanilla.add_statement(
        roles=["writer"],
        effect="allow",
        action="write",
        resource="/test"
    )

    # Test evaluation
    result = vanilla.evaluate(identity, "write", "/test")
    assert result.passed is True


def test_policy_condition_check(vanilla):
    identity = Identity(identity_id="u3", name="U3", metadata={})
    role = Role(role_id="r3", name="conditional",
                description="Conditional", members=["u3"])

    vanilla.add_identity(identity)
    vanilla.add_role(role)

    # Add conditional statement
    vanilla.add_statement(
        roles=["conditional"],
        effect="allow",
        action="read",
        resource="/data",
        condition={"time": "business_hours"}
    )

    # Test evaluation with context
    result = vanilla.evaluate(
        identity, "read", "/data", {"time": "business_hours"})
    assert result.passed is True


def test_wildcard_policy(vanilla):
    identity = Identity(identity_id="u4", name="U4", metadata={})
    role = Role(role_id="r4", name="wildcard",
                description="Wildcard", members=["u4"])

    vanilla.add_identity(identity)
    vanilla.add_role(role)

    # Add wildcard statement
    vanilla.add_statement(
        roles=["wildcard"],
        effect="allow",
        action="*",
        resource="*"
    )

    # Test wildcard evaluation
    result = vanilla.evaluate(identity, "any_action", "/any/resource")
    assert result.passed is True


def test_policy_flexible_role_types(vanilla):
    """Test that add_statement accepts both Role objects and strings."""
    identity = Identity(identity_id="u5", name="U5", metadata={})
    role = Role(role_id="r5", name="flexible", description="Flexible")

    vanilla.add_identity(identity)
    vanilla.add_role(role)

    # Test with Role objects
    vanilla.add_statement(
        roles=[role],
        effect="allow",
        action="test1",
        resource="/test1"
    )

    # Test with strings
    vanilla.add_statement(
        roles=["flexible"],
        effect="allow",
        action="test2",
        resource="/test2"
    )

    vanilla.add_identity_to_role(identity, role)

    result1 = vanilla.evaluate(identity, "test1", "/test1")
    result2 = vanilla.evaluate(identity, "test2", "/test2")
    assert result1.passed is True
    assert result2.passed is True


def test_policy_invalid_role_type(vanilla):
    """Test that add_statement handles invalid role types gracefully."""
    # This should not raise an exception
    vanilla.add_statement(
        roles=[123, None, "valid_role"],  # Invalid types mixed with valid
        effect="allow",
        action="test",
        resource="/test"
    )
    # If we get here without exception, the test passes
    assert True
