import pytest
import asyncio
from plantangenet.policy.vanilla import Vanilla
from plantangenet.policy.identity import Identity
from plantangenet.policy.role import Role
from plantangenet.policy.statement import Statement


class InMemoryPolicyStorageBackend:
    def __init__(self):
        self._store = {}

    async def store(self, object_id, data, metadata=None):
        self._store[object_id] = (data, metadata)
        return True

    async def load(self, object_id):
        return self._store.get(object_id, (None, None))[0]

    async def update(self, object_id, fields):
        if object_id in self._store:
            self._store[object_id][0].update(fields)
            return True
        return False

    async def delete(self, object_id):
        return self._store.pop(object_id, None) is not None


@pytest.mark.asyncio
async def test_policy_storage_roundtrip():
    backend = InMemoryPolicyStorageBackend()
    Vanilla.storage_backend = backend
    Identity.storage_backend = backend
    Role.storage_backend = backend
    Statement.storage_backend = backend

    policy = Vanilla(logger=None, namespace="test")
    identity = Identity(id="id1", nickname="nick")
    role = Role(id="role1", name="admin", description="desc")
    statement = Statement(id="stmt1", role_names=[
                          "admin"], effect="allow", action=["read"], resource=["db"])

    # Store
    assert await policy.store("policy1", {"namespace": policy._namespace})
    assert await identity.store(identity.id, identity.dict())
    assert await role.store(role.id, role.dict())
    assert await statement.store(statement.id, statement.dict())

    # Load
    loaded_policy = await policy.load("policy1")
    loaded_identity = await identity.load(identity.id)
    loaded_role = await role.load(role.id)
    loaded_statement = await statement.load(statement.id)
    assert loaded_policy["namespace"] == "test"
    assert loaded_identity["nickname"] == "nick"
    assert loaded_role["name"] == "admin"
    assert loaded_statement["effect"] == "allow"

    # Update
    await identity.update(identity.id, {"nickname": "newnick"})
    loaded_identity2 = await identity.load(identity.id)
    assert loaded_identity2["nickname"] == "newnick"

    # Delete
    assert await identity.delete(identity.id)
    assert await identity.load(identity.id) is None
