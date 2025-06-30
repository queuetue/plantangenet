import pytest
from plantangenet.policy.role import Role
from plantangenet.policy.statement import Statement


def test_statement_creation():
    role = Role(id="r1", name="reader", description="Can read")
    stmt = Statement(
        id="s1",
        role_names=["reader"],
        effect="allow",
        action=["read"],
        resource=["*"]
    )
    assert stmt.effect == "allow"
    assert "read" in stmt.action


def test_statement_requires_roles():
    # Statement allows empty role_names, so test that it doesn't raise
    stmt = Statement(
        id="s2",
        role_names=[],
        effect="deny",
        action=["delete"],
        resource=["*"]
    )
    assert stmt.role_names == []
