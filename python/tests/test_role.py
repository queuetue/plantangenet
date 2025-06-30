from plantangenet.policy.role import Role


def test_role_basics():
    role = Role(id="r1", name="admin", description="Administrator")
    assert role.members == []
    assert role.name == "admin"
