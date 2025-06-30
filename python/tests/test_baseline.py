# import pytest
# from plantangenet.policy.vanilla import Vanilla
# from plantangenet.policy.identity import Identity
# from plantangenet.policy.role import Role


# @pytest.fixture
# def vanilla():
#     return Vanilla(peer=MockPeer())  # type: ignore


# async def test_role_assignment(anyio_backend, vanilla):
#     identity = Identity(id="user1", nickname="U1", metadata={})
#     role = Role(id="r1", name="admin", description="Admin", members=["user1"])

#     await vanilla.add_identity(identity)
#     await vanilla.add_role(role)

#     assert vanilla.has_role("user1", "admin")


# async def test_policy_permission_granted(anyio_backend, vanilla):
#     identity = Identity(id="u2", nickname="U2", metadata={})
#     role = Role(id="r2", name="writer", description="Writer", members=["u2"])

#     await vanilla.add_identity(identity)
#     await vanilla.add_role(role)
#     await vanilla.add_policy(
#         roles=[role],
#         effect="allow",
#         action="raft.append",
#         resource="*"
#     )

#     assert vanilla.evaluate("u2", "raft.append", "*")
#     assert not vanilla.evaluate("u2", "raft.delete", "*")


# async def test_policy_condition_check(anyio_backend, vanilla):
#     identity = Identity(id="u3", nickname="U3", metadata={})
#     role = Role(id="r3", name="reviewer",
#                 description="Reviewer", members=["u3"])

#     await vanilla.add_identity(identity)
#     await vanilla.add_role(role)
#     await vanilla.add_policy(
#         roles=[role],
#         effect="allow",
#         action="raft.read",
#         resource="*",
#         condition={"secure": True}
#     )

#     assert vanilla.evaluate("u3", "raft.read", "*", context={"secure": True})
#     assert not vanilla.evaluate(
#         "u3", "raft.read", "*", context={"secure": False})


# async def test_wildcard_policy(anyio_backend, vanilla):
#     identity = Identity(id="u4", nickname="U4", metadata={})
#     role = Role(id="r4", name="super", description="Superuser", members=["u4"])

#     await vanilla.add_identity(identity)
#     await vanilla.add_role(role)
#     await vanilla.add_policy(
#         roles=[role],
#         effect="allow",
#         action="*",
#         resource="*"
#     )

#     assert vanilla.evaluate("u4", "anything.go", "whatever")


# async def test_policy_flexible_role_types(anyio_backend, vanilla):
#     """Test that add_policy accepts both Role objects and strings."""
#     identity = Identity(id="u3", nickname="U3", metadata={})
#     role1 = Role(id="r3", name="admin", description="Admin", members=["u3"])
#     role2 = Role(id="r4", name="user", description="User", members=["u3"])

#     await vanilla.add_identity(identity)
#     await vanilla.add_role(role1)
#     await vanilla.add_role(role2)

#     # Should work with mix of Role objects and strings
#     await vanilla.add_policy(
#         roles=[role1, "user"],  # Mix of Role object and string
#         effect="allow",
#         action="test.action",
#         resource="*"
#     )

#     # Verify the policy was added correctly
#     assert vanilla.has_role("u3", "admin")
#     assert vanilla.has_role("u3", "user")


# async def test_policy_invalid_role_type(anyio_backend, vanilla):
#     """Test that add_policy handles invalid role types gracefully."""
#     # Should not raise an exception, but should log warnings and handle gracefully
#     result = await vanilla.add_policy(
#         roles=[123, None, "", "  "],  # Various invalid/edge case types
#         effect="allow",
#         action="test.action",
#         resource="*"
#     )

#     # Should return a key (even if memory-based)
#     assert result is not None
#     assert isinstance(result, str)
