import pytest
import asyncio
from plantangenet.agent import Agent


class DummyPeer(Agent):

    async def update(self) -> bool:
        """Dummy update method for testing."""
        return True


def test_initialization_defaults():
    peer = DummyPeer(namespace="testspace")
    assert peer.namespace == "testspace"
    assert isinstance(peer.id, str)
    assert peer.disposition in ["GO SLUG BEARS",
                                "GO BEAR SLUGS",
                                "GO PLANTANGENET",
                                "AESTHETICA IN VIVO"]
    assert isinstance(peer.logger, object)
    assert isinstance(peer.short_id, str)
    assert len(peer.short_id) == 6
    assert peer.name is not None


def test_disposition_setter_and_validation():
    peer = DummyPeer()
    peer._ocean__disposition = "HAPPY"
    assert peer.disposition == "HAPPY"


def test_ocean_op_logging():
    peer = DummyPeer()
    peer._ocean__op(True, "set", "foo", value=123, cost=5)
    op = peer._ocean__op_cache[-1]
    assert op["agent_id"] == peer.id
    assert isinstance(op["ulid"], str)
    assert op["key"] == "foo"
    assert op["accepted"] is True
    assert op["operation"] == "set"
    assert op["value"] == "123"
    assert op["cost"] == 5
    assert op["committed"] is False


def test_fresh_id_uniqueness():
    peer = DummyPeer()
    ids = {peer.fresh_id() for _ in range(10)}
    assert len(ids) == 10
    for uid in ids:
        assert isinstance(uid, str)
        assert len(uid) == 26  # ULID length


@pytest.mark.asyncio
async def test_update_and_sync_are_implemented():
    peer = DummyPeer()
    assert await peer.update() is True
