import pytest
from plantangenet.policy import Policy
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

    identity = Identity(id="id1", nickname="nick", metadata={}, roles=[])
    role = Role(id="role1", name="admin", description="desc", members=[])
    statement = Statement(id="stmt1", role_ids=["admin"], effect="allow", action=[
                          "read"], resource=["db"], condition={}, delivery=None, cost=None, capabilities=None)

    # Store
    assert await backend.store("policy1", {"namespace": "test"})
    assert await backend.store(identity.id, identity.dict())
    assert await backend.store(role.id, role.dict())
    assert await backend.store(statement.id, statement.dict())

    # Load
    loaded_policy = await backend.load("policy1")
    loaded_identity = await backend.load(identity.id)
    loaded_role = await backend.load(role.id)
    loaded_statement = await backend.load(statement.id)
    assert loaded_policy["namespace"] == "test"
    assert loaded_identity["nickname"] == "nick"
    assert loaded_role["name"] == "admin"
    assert loaded_statement["effect"] == "allow"

    # Update
    await backend.update(identity.id, {"nickname": "newnick"})
    loaded_identity2 = await backend.load(identity.id)
    assert loaded_identity2["nickname"] == "newnick"

    # Delete
    assert await backend.delete(identity.id)
    assert await backend.load(identity.id) is None
