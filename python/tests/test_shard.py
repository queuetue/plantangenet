# Copyright (c) 1998-2025 Scott Russell
# SPDX-License-Identifier: MIT

"""
Tests for Shard - combining Agent with Redis, NATS, and Cluster mixins.

Tests cover:
- Shard initialization and integration
- Status reporting
- Setup, update, and teardown lifecycle
- Storage and transport integration
- Cluster participation
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from plantangenet.logger import Logger
from dummy_shard import DummyShard


@pytest.fixture
def mock_logger():
    """Create a mock logger for testing."""
    return MagicMock(spec=Logger)


@pytest.fixture
def shard(mock_logger):
    """Create a Shard instance for testing."""
    return DummyShard(
        namespace="test-shard",
        logger=mock_logger
    )


class TestShardInitialization:
    """Test Shard initialization and basic properties."""

    def test_default_initialization(self, mock_logger):
        """Test Shard with default parameters."""
        shard = DummyShard(
            namespace="test-shard",
            logger=mock_logger
        )

        assert shard.namespace == "test-shard"
        assert shard.logger == mock_logger


class TestShardStatus:
    """Test Shard status reporting."""

    def test_status_structure(self, shard):
        """Test that status returns proper structure."""
        status = shard.status

        assert "shard" in status
        shard_status = status["shard"]

        assert "id" in shard_status
        assert "namespace" in shard_status

        assert shard_status["id"] == shard.id
        assert shard_status["namespace"] == shard.namespace


@pytest.mark.anyio
class TestShardLifecycle:
    """Test Shard lifecycle methods."""

    @pytest.mark.asyncio
    async def test_setup(self, shard):
        """Test Shard setup process."""
        with patch.object(shard, 'setup_transport', new_callable=AsyncMock) as mock_transport:
            with patch.object(shard, 'setup_storage', new_callable=AsyncMock) as mock_storage:
                await shard.setup()

                mock_transport.assert_called_once()
                mock_storage.assert_called_once()

    @pytest.mark.asyncio
    async def test_teardown(self, shard):
        """Test Shard teardown process."""
        with patch.object(shard, 'teardown_transport', new_callable=AsyncMock) as mock_transport:
            with patch.object(shard, 'teardown_storage', new_callable=AsyncMock) as mock_storage:
                await shard.teardown()

                mock_transport.assert_called_once()
                mock_storage.assert_called_once()


class TestShardIntegration:
    """Test Shard integration with mixins."""

    @pytest.mark.asyncio
    @patch('plantangenet.mixins.nats.NATS')
    @patch('plantangenet.mixins.redis.Redis')
    @pytest.mark.asyncio
    async def test_transport_and_storage_setup(self, mock_redis, mock_nats, shard):
        """Test that both transport and storage are set up."""
        mock_nats_instance = AsyncMock()
        mock_nats.return_value = mock_nats_instance

        mock_redis_instance = MagicMock()
        mock_redis.return_value = mock_redis_instance

        # This should call setup on both transport and storage
        with patch.object(shard, 'setup_transport', new_callable=AsyncMock) as mock_transport_setup:
            with patch.object(shard, 'setup_storage', new_callable=AsyncMock) as mock_storage_setup:
                await shard.setup()

                mock_transport_setup.assert_called_once()
                mock_storage_setup.assert_called_once()


class TestShardErrorHandling:
    """Test Shard error handling and edge cases."""

    @pytest.mark.asyncio
    async def test_setup_transport_failure(self, shard):
        """Test handling of transport setup failure."""
        with patch.object(shard, 'setup_transport', side_effect=Exception("Transport failed")):
            with pytest.raises(Exception, match="Transport failed"):
                await shard.setup()

    @pytest.mark.asyncio
    async def test_setup_storage_failure(self, shard):
        """Test handling of storage setup failure."""
        with patch.object(shard, 'setup_transport', new_callable=AsyncMock):
            with patch.object(shard, 'setup_storage', side_effect=Exception("Storage failed")):
                with pytest.raises(Exception, match="Storage failed"):
                    await shard.setup()

    @pytest.mark.asyncio
    async def test_partial_teardown_failure(self, shard):
        """Test handling of partial teardown failure."""
        with patch.object(shard, 'teardown_transport', side_effect=Exception("Transport teardown failed")):
            with patch.object(shard, 'teardown_storage', new_callable=AsyncMock):
                # Should still attempt storage teardown even if transport fails
                with pytest.raises(Exception, match="Transport teardown failed"):
                    await shard.teardown()


@pytest.mark.anyio
class TestShardAsyncOperations:
    """Test Shard async operations and concurrency."""

    @pytest.mark.asyncio
    async def test_concurrent_operations(self, shard):
        """Test that Shard can handle concurrent operations."""
        import asyncio

        # Mock the underlying operations
        with patch.object(shard, 'update_storage', new_callable=AsyncMock) as mock_storage:
            with patch.object(shard, 'update_transport', new_callable=AsyncMock) as mock_transport:
                # Run multiple updates concurrently
                tasks = [shard.update() for _ in range(5)]
                await asyncio.gather(*tasks)

                # Each update should have been called
                assert mock_storage.call_count == 5
                assert mock_transport.call_count == 5
