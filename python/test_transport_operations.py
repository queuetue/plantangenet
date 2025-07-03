"""
Test suite for Transport Operations with Banker Agent Integration.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock

from plantangenet.transport_operations import TransportOperationsManager
from plantangenet.session import Session
from plantangenet.vanilla_banker import create_vanilla_banker_agent


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
    """Test creating a transport operations manager."""
    session = Session(session_id="test_session")
    manager = TransportOperationsManager(session)

    assert manager.session == session


def test_data_size_calculation():
    """Test data size calculation for different data types."""
    session = Session(session_id="test_session")
    manager = TransportOperationsManager(session)

    # Test string data
    string_size = manager._calculate_data_size("hello world")
    assert string_size == len("hello world".encode('utf-8'))

    # Test dict data
    dict_data = {"key": "value", "number": 42}
    dict_size = manager._calculate_data_size(dict_data)
    assert dict_size > 0

    # Test bytes data
    bytes_data = b"hello bytes"
    bytes_size = manager._calculate_data_size(bytes_data)
    assert bytes_size == len(bytes_data)


def test_topic_complexity_calculation():
    """Test topic complexity calculation."""
    session = Session(session_id="test_session")
    manager = TransportOperationsManager(session)

    # Simple topic
    simple_complexity = manager._calculate_topic_complexity("topic")
    assert simple_complexity == 1

    # Complex topic with segments
    complex_complexity = manager._calculate_topic_complexity(
        "domain.service.action.specific")
    assert complex_complexity == 4

    # Topic with wildcard
    wildcard_complexity = manager._calculate_topic_complexity(
        "domain.*.action")
    assert wildcard_complexity == 5  # 3 segments + 2 for wildcard

    # Topic with multi-level wildcard
    multi_wildcard_complexity = manager._calculate_topic_complexity("domain.>")
    assert multi_wildcard_complexity == 5  # 2 segments + 3 for multi-level wildcard


def test_preview_without_banker():
    """Test getting previews when default NullBanker is used."""
    session = Session(session_id="test_session")
    manager = TransportOperationsManager(session)

    # Should return basic quote from NullBanker
    publish_preview = manager.get_publish_preview("test.topic", "test data")
    assert publish_preview is not None
    assert publish_preview["dust_cost"] == 0

    subscribe_preview = manager.get_subscribe_preview("test.topic")
    assert subscribe_preview is not None
    assert subscribe_preview["dust_cost"] == 0


@pytest.mark.asyncio
async def test_publish_without_banker():
    """Test publishing with default NullBanker (backward compatibility)."""
    session = Session(session_id="test_session")
    manager = TransportOperationsManager(session)
    mock_client = MockTransportClient()

    result = await manager.publish_with_cost("test.topic", "test data", mock_client)

    assert result["success"] is True
    assert result["cost_paid"] == 0
    assert "Published to test.topic, cost: 0 Dust" in result["message"]
    assert len(mock_client.published_messages) == 1
    assert mock_client.published_messages[0]["topic"] == "test.topic"


@pytest.mark.asyncio
async def test_subscribe_without_banker():
    """Test subscribing with default NullBanker (backward compatibility)."""
    session = Session(session_id="test_session")
    manager = TransportOperationsManager(session)
    mock_client = MockTransportClient()

    async def test_callback(message):
        pass

    result = await manager.subscribe_with_cost("test.topic", test_callback, mock_client)

    assert result["success"] is True
    assert result["cost_paid"] == 0
    assert "Subscribed to test.topic, cost: 0 Dust" in result["message"]
    assert "subscription" in result
    assert "test.topic" in mock_client.subscriptions


@pytest.mark.asyncio
async def test_transport_operations_with_banker():
    """Test transport operations with banker integration."""
    # Create session with banker
    session = Session(session_id="test_session")
    # Higher balance for realistic costs
    banker = create_vanilla_banker_agent(initial_balance=1000)
    session.add_banker_agent(banker)

    # Add some transport costs to the banker's negotiators
    test_cost_base = {
        "api_costs": {
            "transport.publish": 5,
            "transport.subscribe": 3
        }
    }
    banker.add_cost_base_data("test", test_cost_base)

    manager = TransportOperationsManager(session)
    mock_client = MockTransportClient()

    # Test publish with banker
    publish_result = await manager.publish_with_cost("test.topic", "test data", mock_client)

    assert publish_result["success"] is True
    assert publish_result["cost_paid"] > 0  # Should have charged some dust
    assert len(mock_client.published_messages) == 1

    # Test subscribe with banker
    async def test_callback(message):
        pass

    subscribe_result = await manager.subscribe_with_cost("test.topic", test_callback, mock_client)

    assert subscribe_result["success"] is True
    assert subscribe_result["cost_paid"] > 0  # Should have charged some dust
    assert "subscription" in subscribe_result


@pytest.mark.asyncio
async def test_insufficient_dust():
    """Test operations when insufficient dust is available."""
    # Create session with banker with very low balance
    session = Session(session_id="test_session")
    banker = create_vanilla_banker_agent(initial_balance=1)  # Very low balance
    session.add_banker_agent(banker)

    # Add expensive transport costs
    test_cost_base = {
        "api_costs": {
            "transport.publish": 100,  # More than available balance
            "transport.subscribe": 100
        }
    }
    banker.add_cost_base_data("test", test_cost_base)

    manager = TransportOperationsManager(session)
    mock_client = MockTransportClient()

    # Test publish should fail due to insufficient funds
    publish_result = await manager.publish_with_cost("test.topic", "test data", mock_client)

    assert publish_result["success"] is False
    assert publish_result["cost_paid"] == 0
    assert "error" in publish_result
    # Should not have published
    assert len(mock_client.published_messages) == 0


def test_get_previews_with_banker():
    """Test getting cost previews with banker configured."""
    # Create session with banker
    session = Session(session_id="test_session")
    # Higher balance for realistic costs
    banker = create_vanilla_banker_agent(initial_balance=1000)
    session.add_banker_agent(banker)

    # Add transport costs
    test_cost_base = {
        "api_costs": {
            "transport.publish": 5,
            "transport.subscribe": 3
        }
    }
    banker.add_cost_base_data("test", test_cost_base)

    manager = TransportOperationsManager(session)

    # Test publish preview
    publish_preview = manager.get_publish_preview("test.topic", "test data")
    assert publish_preview is not None
    # Check the structure - it returns the quote in the negotiation result
    assert "quote" in publish_preview
    assert "dust_cost" in publish_preview["quote"]

    # Test subscribe preview
    subscribe_preview = manager.get_subscribe_preview("test.topic")
    assert subscribe_preview is not None
    assert "quote" in subscribe_preview
    assert "dust_cost" in subscribe_preview["quote"]


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__])
