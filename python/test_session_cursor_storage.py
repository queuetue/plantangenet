import pytest
import asyncio
from plantangenet.session import Session
from plantangenet.policy.identity import Identity
from plantangenet.policy.vanilla import Vanilla
from plantangenet.cursor import Cursor


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
async def test_session_cursor_storage_and_rehydration():
    backend = InMemorySessionStorageBackend()
    Session.storage_backend = backend
    Identity.storage_backend = backend
    Vanilla.storage_backend = backend
    Cursor.storage_backend = backend

    # Create and store identity, policy, and cursors
    identity = Identity(id="id1", nickname="nick")
    policy = Vanilla(logger=None, namespace="testns")
    await identity.store(identity.id, identity.dict())
    await policy.store("policy1", {"namespace": policy._namespace})
    cursor1 = Cursor(axes=["x"], tick_range=(0, 10), owner="id1")
    cursor2 = Cursor(axes=["y"], tick_range=(5, 15), owner="id1")
    await cursor1.store(cursor1.id, cursor1.__dict__)
    await cursor2.store(cursor2.id, cursor2.__dict__)

    # Create session and store
    session = Session(identity=identity, policy=policy,
                      identity_key=identity.id, policy_key="policy1")
    session.cursors = [cursor1, cursor2]
    await session.persist_cursors()
    await session.store(session.session_id, session.persisted_state())

    # Rehydrate session
    rehydrated = await Session.rehydrate(session.session_id, backend=backend, logger=None, namespace="testns")
    assert rehydrated.session_id == session.session_id
    assert rehydrated.identity.nickname == "nick"
    assert rehydrated.policy._namespace == "testns"
    assert len(rehydrated.cursors) == 2
    ids = {c.id for c in rehydrated.cursors}
    assert cursor1.id in ids and cursor2.id in ids
    # Test that runtime fields are not persisted
    assert rehydrated.agents == []
    # Test that persisted_state includes cursor_keys
    state = rehydrated.persisted_state()
    assert set(state.keys()) == {
        "session_id", "metadata", "identity_key", "policy_key", "cursor_keys"}
    assert set(state["cursor_keys"]) == {cursor1.id, cursor2.id}
