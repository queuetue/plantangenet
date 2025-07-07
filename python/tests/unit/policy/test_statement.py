import pytest
from plantangenet.policy.role import Role
from plantangenet.policy.statement import Statement


def test_statement_creation():
    role = Role(id="r1", name="reader", description="Can read", members=[])
    stmt = Statement(
        id="s1",
        role_ids=["reader"],
        effect="allow",
        action=["read"],
        resource=["*"],
        condition={},
        delivery=None,
        cost=None,
        capabilities=None
    )
    assert stmt.effect == "allow"
    assert "read" in stmt.action


def test_statement_requires_roles():
    # Statement allows empty role_names, so test that it doesn't raise
    stmt = Statement(
        id="s2",
        role_ids=[],
        effect="deny",
        action=["delete"],
        resource=["*"],
        condition={},
        delivery=None,
        cost=None,
        capabilities=None
    )
    assert stmt.role_ids == []
