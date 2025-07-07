import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock

from plantangenet.policy.identity import Identity
from plantangenet.policy.policy import Policy
from plantangenet.transport_operations import TransportOperationsManager
from plantangenet.session import Session


class MockTransportClient:
    """Mock transport client for testing."""

    def __init__(self):
        self.published_messages = []
        self.subscriptions = {}

    async def publish(self, topic: str, data):
        self.published_messages.append({"topic": topic, "data": data})

    async def subscribe(self, topic: str, callback):
        subscription_id = f"sub_{len(self.subscriptions)}"
        self.subscriptions[topic] = {
            "callback": callback, "id": subscription_id}
        return subscription_id


def test_transport_operations_manager_creation():
    session = Session(id="test_session", policy=Policy(logger=None, namespace="test_policy"),
                      identity=Identity(id="test_identity", nickname="Test User", metadata={}, roles=[]))
    manager = TransportOperationsManager(session)
    assert manager.session == session


def test_data_size_calculation():
    session = Session(id="test_session", policy=Policy(logger=None, namespace="test_policy"),
                      identity=Identity(id="test_identity", nickname="Test User", metadata={}, roles=[]))
    manager = TransportOperationsManager(session)
    string_size = manager._calculate_data_size("hello world")
    assert string_size == len("hello world".encode('utf-8'))
    dict_data = {"key": "value", "number": 42}
    dict_size = manager._calculate_data_size(dict_data)
    assert dict_size > 0
    bytes_data = b"hello bytes"
    bytes_size = manager._calculate_data_size(bytes_data)
    assert bytes_size == len(bytes_data)
