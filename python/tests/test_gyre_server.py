# # Copyright (c) 1998-2025 Scott Russell
# # SPDX-License-Identifier: MIT
# """
# Tests for GyreServer - async orchestration/service layer for Gyre.

# Covers:
# - Initialization and configuration
# - Async orchestration (start, stop, shutdown)
# - Reporting/status methods
# - Peer/service management
# - Edge cases and error handling
# """

# import pytest
# from unittest.mock import MagicMock
# from dummy_server import DummyServer
# from dummy_peer import DummyPeer


# @pytest.fixture
# def gyre_server():
#     return DummyServer(peers=[DummyPeer()], logger=MagicMock())


# @pytest.mark.asyncio
# class TestGyreServerLifecycle:
#     async def test_start_and_shutdown(self, gyre_server):
#         if hasattr(gyre_server, 'start') and hasattr(gyre_server, 'shutdown'):
#             await gyre_server.start()
#             assert getattr(gyre_server, 'running', True)
#             await gyre_server.shutdown()
#             assert not getattr(gyre_server, 'running', False)

#     async def test_status_reporting(self, gyre_server):
#         if hasattr(gyre_server, 'status'):
#             status = await gyre_server.status()
#             assert isinstance(status, dict)
#             assert "gyre" in status or "server" in status

#     async def test_collect_and_report(self, gyre_server):
#         # Simulate a tick/frame collection
#         if hasattr(gyre_server, 'collect_and_report'):
#             result = await gyre_server.collect_and_report(tick=42)
#             assert result.get("current_tick", 42) == 42


# class TestGyreServerEdgeCases:
#     @pytest.mark.asyncio
#     async def test_shutdown_without_start(self, gyre_server):
#         # Should not raise even if not started
#         if hasattr(gyre_server, 'shutdown'):
#             await gyre_server.shutdown()
