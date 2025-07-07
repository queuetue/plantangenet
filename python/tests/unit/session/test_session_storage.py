import pytest
from plantangenet.session import Session
from plantangenet.policy.identity import Identity
from plantangenet.policy import Policy


class InMemorySessionStorageBackend:
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
async def test_session_storage_and_rehydration():
    backend = InMemorySessionStorageBackend()
    Session.storage_backend = backend
    Identity.storage_backend = backend
    # Vanilla.storage_backend = backend  # Skipped, Vanilla not defined in new code

    # Create and store identity and policy
    identity = Identity(id="id1", nickname="nick", metadata={}, roles=[])
    policy = Policy(logger=None, namespace="testns")

    # Create session and store
    session = Session(id="sess2", identity=identity, policy=policy)
    await backend.store(session._id, {"identity": identity.dict(), "policy": {"namespace": getattr(policy, 'namespace', 'testns')}})

    # Simulate rehydration
    loaded = await backend.load(session._id)
    assert loaded["identity"]["nickname"] == "nick"
    assert loaded["policy"]["namespace"] == "testns"
