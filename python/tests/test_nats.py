# Copyright (c) 1998-2025 Scott Russell
# SPDX-License-Identifier: MIT

"""
Tests for NATS transport mixin.

Tests cover:
- Connection establishment and management
- Publishing and subscribing to topics
- Error handling and reconnection logic
- Message encoding and decoding
- Connection lifecycle
"""

from typing import Any
import pytest
import logging
from unittest.mock import AsyncMock, MagicMock, patch
from plantangenet.mixins.nats import NatsMixin
from plantangenet import GLOBAL_LOGGER
from nats.aio.errors import ErrNoServers

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class ConcreteNatsClient(NatsMixin):
    """Concrete implementation for testing NatsMixin."""

    def __init__(self, namespace="test", disposition="test-disposition"):
        self._namespace = namespace
        self._disposition = disposition
        super().__init__()

    @property
    def namespace(self) -> str:
        return self._namespace

    @property
    def disposition(self) -> str:
        return self._disposition

    @property
    def logger(self) -> Any:
        """Return the logger instance for this peer."""
        return GLOBAL_LOGGER


@pytest.fixture
def nats_client():
    """Create a concrete NATS client for testing."""
    return ConcreteNatsClient()


@pytest.fixture
def mock_nats():
    """Create a mock NATS client."""
    mock = AsyncMock()
    mock.connect = AsyncMock()
    mock.publish = AsyncMock()
    mock.subscribe = AsyncMock()
    mock.close = AsyncMock()
    return mock


class TestNatsMixinProperties:
    """Test NatsMixin properties and initialization."""

    def test_initial_state(self, nats_client):
        """Test initial state of NatsMixin."""
        assert not nats_client.connected
        assert nats_client._ocean_nats__client is None
        assert nats_client._ocean_nats__subscriptions == {}
        assert not nats_client._ocean_nats__connected

    def test_namespace_property(self, nats_client):
        """Test namespace property."""
        assert nats_client.namespace == "test"

    def test_disposition_property(self, nats_client):
        """Test disposition property."""
        assert nats_client.disposition == "test-disposition"


@pytest.mark.anyio
class TestNatsMixinConnection:
    """Test NATS connection establishment and management."""

    @patch('plantangenet.mixins.nats.NATS')
    async def test_setup_transport_success(self, mock_nats_class, nats_client):
        """Test successful transport setup."""
        mock_nats = AsyncMock()
        mock_nats_class.return_value = mock_nats
        mock_nats.connect = AsyncMock()
        mock_nats.publish = AsyncMock()

        await nats_client.setup_transport(urls=["nats://localhost:4222"])

        assert nats_client.connected
        assert nats_client._ocean_nats__client == mock_nats
        mock_nats.connect.assert_called_once()
        mock_nats.publish.assert_called_once()

    @patch('plantangenet.mixins.nats.NATS')
    async def test_setup_transport_no_servers(self, mock_nats_class, nats_client):
        """Test setup when no NATS servers are available."""
        mock_nats = AsyncMock()
        mock_nats_class.return_value = mock_nats
        mock_nats.connect.side_effect = ErrNoServers("No servers available")

        # Setup should try to connect, fail, and continue in offline mode
        with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
            # Short-circuit the retry loop for testing
            mock_sleep.side_effect = [None] * 10  # Allow some retries

            await nats_client.setup_transport(urls=["nats://localhost:4222"])

        # Should be marked as disconnected but not raise exception
        assert not nats_client.connected
        # Logger should have been called to log the connection failure

    @patch('plantangenet.mixins.nats.NATS')
    async def test_setup_transport_unexpected_error(self, mock_nats_class, nats_client):
        """Test setup with unexpected connection error."""
        mock_nats = AsyncMock()
        mock_nats_class.return_value = mock_nats
        mock_nats.connect.side_effect = Exception("Unexpected error")

        # Setup should handle the error gracefully and continue in offline mode
        with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
            mock_sleep.side_effect = [None] * 10  # Allow retries

            await nats_client.setup_transport(urls=["nats://localhost:4222"])

        # Should be marked as disconnected but not raise exception
        assert not nats_client.connected

    async def test_teardown_transport(self, nats_client):
        """Test transport teardown."""
        # Setup a mock client
        mock_nats = AsyncMock()
        nats_client._ocean_nats__client = mock_nats
        nats_client._ocean_nats__connected = True
        nats_client._ocean_nats__subscriptions = {"test.topic": MagicMock()}

        await nats_client.teardown_transport()

        mock_nats.close.assert_called_once()
        assert nats_client._ocean_nats__client is None
        assert not nats_client._ocean_nats__connected
        assert nats_client._ocean_nats__subscriptions == {}


@pytest.mark.anyio
class TestNatsMixinPublishing:
    """Test message publishing functionality."""

    async def test_publish_dict(self, nats_client):
        """Test publishing dictionary data."""
        mock_nats = AsyncMock()
        nats_client._ocean_nats__client = mock_nats
        nats_client._ocean_nats__connected = True  # Mark as connected

        data = {"key": "value", "number": 42}
        await nats_client.publish("test.topic", data)

        mock_nats.publish.assert_called_once()
        call_args = mock_nats.publish.call_args
        assert call_args[0][0] == "test.topic"
        # Should be JSON encoded bytes
        assert isinstance(call_args[0][1], bytes)

    async def test_publish_string(self, nats_client):
        """Test publishing string data."""
        mock_nats = AsyncMock()
        nats_client._ocean_nats__client = mock_nats
        nats_client._ocean_nats__connected = True  # Mark as connected

        data = "test message"
        await nats_client.publish("test.topic", data)

        mock_nats.publish.assert_called_once_with(
            "test.topic", b"test message")

    async def test_publish_bytes(self, nats_client):
        """Test publishing raw bytes data."""
        mock_nats = AsyncMock()
        nats_client._ocean_nats__client = mock_nats
        nats_client._ocean_nats__connected = True  # Mark as connected

        data = b"raw bytes"
        await nats_client.publish("test.topic", data)

        mock_nats.publish.assert_called_once_with("test.topic", b"raw bytes")

    async def test_publish_invalid_type(self, nats_client):
        """Test publishing invalid data type."""
        mock_nats = AsyncMock()
        nats_client._ocean_nats__client = mock_nats
        nats_client._ocean_nats__connected = True  # Mark as connected

        # Type validation still happens even with resilient handling
        with pytest.raises(TypeError, match="Data must be bytes, str, or dict"):
            await nats_client.publish("test.topic", 123)

    async def test_publish_no_client(self, nats_client):
        """Test publishing when no client is available."""
        # With resilient handling, this should not raise an exception
        # Instead, it should log a debug message and return early
        await nats_client.publish("test.topic", "data")

    async def test_publish_connection_error(self, nats_client):
        """Test publishing when connection fails."""
        mock_nats = AsyncMock()
        mock_nats.publish.side_effect = ErrNoServers("Connection lost")
        nats_client._ocean_nats__client = mock_nats
        nats_client._ocean_nats__connected = True

        await nats_client.publish("test.topic", "data")

        # Should mark as disconnected and log warning
        assert not nats_client._ocean_nats__connected


@pytest.mark.anyio
class TestNatsMixinSubscribing:
    """Test message subscription functionality."""

    async def test_subscribe_success(self, nats_client):
        """Test successful subscription."""
        mock_nats = AsyncMock()
        mock_sub = MagicMock()
        mock_nats.subscribe.return_value = mock_sub
        nats_client._ocean_nats__client = mock_nats
        nats_client._ocean_nats__connected = True  # Mark as connected

        callback = AsyncMock()
        result = await nats_client.subscribe("test.topic", callback)

        mock_nats.subscribe.assert_called_once_with(
            subject="test.topic", cb=callback)
        assert result == mock_sub
        assert nats_client._ocean_nats__subscriptions["test.topic"] == mock_sub

    async def test_subscribe_no_client(self, nats_client):
        """Test subscription when no client is available."""
        callback = AsyncMock()

        # With resilient handling, this should return None and log a warning
        result = await nats_client.subscribe("test.topic", callback)

        assert result is None

    async def test_subscribe_error(self, nats_client):
        """Test subscription error handling."""
        mock_nats = AsyncMock()
        mock_nats.subscribe.side_effect = Exception("Subscription failed")
        nats_client._ocean_nats__client = mock_nats
        nats_client._ocean_nats__connected = True  # Mark as connected

        callback = AsyncMock()

        # With resilient handling, this should return None and log the exception
        result = await nats_client.subscribe("test.topic", callback)

        assert result is None


@pytest.mark.anyio
class TestNatsMixinLifecycle:
    """Test full lifecycle operations."""

    async def test_disconnect(self, nats_client):
        """Test disconnect functionality."""
        mock_nats = AsyncMock()
        nats_client._ocean_nats__client = mock_nats
        nats_client._ocean_nats__connected = True

        await nats_client.disconnect()

        mock_nats.close.assert_called_once()
        assert not nats_client._ocean_nats__connected

    async def test_disconnect_no_client(self, nats_client):
        """Test disconnect when no client exists."""
        # Should not raise any exception
        await nats_client.disconnect()
        assert not nats_client._ocean_nats__connected

    async def test_update_transport_no_client(self, nats_client):
        """Test update_transport when no client is initialized."""
        await nats_client.update_transport()

        # Should log info message


class TestNatsMixinConfiguration:
    """Test configuration and environment variables."""

    def test_nats_urls_default(self):
        """Test default NATS URLs configuration."""
        from plantangenet.mixins.nats import NATS_URLS
        assert NATS_URLS == ["nats://localhost:4222"]

    @patch.dict('os.environ', {'NATS_URLS': 'nats://server1:4222,nats://server2:4222'})
    def test_nats_urls_from_env(self):
        """Test NATS URLs from environment variable."""
        # Need to reimport to get updated env var
        import importlib
        import plantangenet.mixins.nats
        importlib.reload(plantangenet.mixins.nats)

        from plantangenet.mixins.nats import NATS_URLS
        assert "nats://server1:4222" in NATS_URLS
        assert "nats://server2:4222" in NATS_URLS
