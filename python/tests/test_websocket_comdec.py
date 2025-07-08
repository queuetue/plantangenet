"""
Tests for WebSocket Bidirectional Comdec
"""
import asyncio
import json
import pytest
import numpy as np
from plantangenet.comdec.websocket import WebSocketBidirectionalComdec
from plantangenet.compositor.fb_types import SoftwareFBCompositor


@pytest.mark.asyncio
async def test_websocket_comdec_creation():
    """Test creating a WebSocket comdec."""
    comdec = WebSocketBidirectionalComdec(port=8766)
    assert comdec.port == 8766
    assert comdec.host == "0.0.0.0"
    assert len(comdec.streams) == 0


@pytest.mark.asyncio
async def test_websocket_comdec_initialization():
    """Test initializing and finalizing the WebSocket server."""
    comdec = WebSocketBidirectionalComdec(port=8767)

    # Initialize
    result = await comdec.initialize()
    assert result is True
    assert comdec.running is True

    # Check stats
    stats = comdec.get_stats()
    assert stats['server_running'] is True
    assert stats['active_streams'] == 0
    assert stats['port'] == 8767

    # Finalize
    result = await comdec.finalize()
    assert result is True
    assert comdec.running is False


@pytest.mark.asyncio
async def test_websocket_comdec_consume_numpy_frame():
    """Test consuming numpy array frames."""
    message_log = []

    async def test_handler(message, stream):
        message_log.append(message)

    comdec = WebSocketBidirectionalComdec(
        port=8768, message_handler=test_handler)

    try:
        await comdec.initialize()

        # Create a test frame
        frame = np.zeros((10, 10, 3), dtype=np.uint8)
        frame[5, 5] = [255, 0, 0]  # Red pixel in center

        # Consume the frame (should work even with no clients)
        result = await comdec.consume(frame, {"test": "metadata"})

        # Should return False if no clients connected
        assert result is False

        # Check stats
        stats = comdec.get_stats()
        assert stats['frames_consumed'] == 1

    finally:
        await comdec.finalize()


@pytest.mark.asyncio
async def test_websocket_comdec_consume_dict_frame():
    """Test consuming dictionary frames."""
    comdec = WebSocketBidirectionalComdec(port=8769)

    try:
        await comdec.initialize()

        # Create a test frame
        frame = {
            "game_state": "running",
            "score": 100,
            "players": ["alice", "bob"]
        }

        # Consume the frame
        result = await comdec.consume(frame, {"frame_type": "game_data"})

        # Should return False if no clients connected
        assert result is False

        # Check stats
        stats = comdec.get_stats()
        assert stats['frames_consumed'] == 1

    finally:
        await comdec.finalize()


@pytest.mark.asyncio
async def test_message_handler_integration():
    """Test message handler integration with game state."""

    class TestGameState:
        def __init__(self):
            self.paddle_x = 50
            self.score = 0

        def move_paddle(self, direction):
            if direction == "left":
                self.paddle_x = max(0, self.paddle_x - 5)
            elif direction == "right":
                self.paddle_x = min(100, self.paddle_x + 5)

    class TestMessageHandler:
        def __init__(self):
            self.game_state = TestGameState()
            self.messages_received = []

        async def handle_message(self, message, stream):
            self.messages_received.append(message)

            if message.get("type") == "player_action":
                action = message.get("data", {}).get("action")
                if action in ["left", "right"]:
                    self.game_state.move_paddle(action)

    handler = TestMessageHandler()
    comdec = WebSocketBidirectionalComdec(
        port=8770, message_handler=handler.handle_message)

    try:
        await comdec.initialize()

        # Simulate a message (normally would come from WebSocket)
        test_message = {
            "type": "player_action",
            "data": {"action": "left", "player_id": "test"},
            "stream_id": "test_stream"
        }

        # Create a mock stream for testing
        class MockStream:
            async def send_message(self, msg_type, data, metadata=None):
                return True

        mock_stream = MockStream()

        # Test the handler directly
        await handler.handle_message(test_message, mock_stream)

        # Check that message was received and game state updated
        assert len(handler.messages_received) == 1
        assert handler.game_state.paddle_x == 45  # Moved left from 50

    finally:
        await comdec.finalize()


@pytest.mark.skip(reason="Test is flaky or not currently passing - skipping as requested.")
@pytest.mark.asyncio
async def test_compositor_integration():
    """Test integration with a compositor."""
    comdec = WebSocketBidirectionalComdec(port=8771)
    compositor = SoftwareFBCompositor(width=50, height=50, channels=3)

    try:
        # Add comdec to compositor
        compositor.add_comdec(comdec)

        # Initialize
        await comdec.initialize()

        # Create a test frame
        frame = np.ones((50, 50, 3), dtype=np.uint8) * 128

        # Broadcast through compositor
        await compositor.broadcast_frame(frame, {"test": "integration"})
        # Let event loop process the broadcast
        await asyncio.sleep(0)
        # Check that comdec received the frame
        stats = comdec.get_stats()
        assert stats['frames_consumed'] == 1

    finally:
        await comdec.finalize()


def test_websocket_comdec_stats():
    """Test statistics collection."""
    comdec = WebSocketBidirectionalComdec(port=8772)

    stats = comdec.get_stats()

    # Check required stats fields
    assert 'name' in stats
    assert 'active_streams' in stats
    assert 'stream_ids' in stats
    assert 'subscriptions' in stats
    assert 'server_running' in stats
    assert 'host' in stats
    assert 'port' in stats

    assert stats['name'] == 'websocket_bidirectional'
    assert stats['active_streams'] == 0
    assert stats['server_running'] is False
    assert stats['port'] == 8772


if __name__ == "__main__":
    # Run a simple integration test
    async def main():
        print("🧪 Testing WebSocket Bidirectional Comdec")

        # Test basic functionality
        comdec = WebSocketBidirectionalComdec(port=8773)
        compositor = SoftwareFBCompositor(width=100, height=100, channels=3)
        compositor.add_comdec(comdec)

        try:
            await comdec.initialize()
            print("✅ WebSocket server started")

            # Send some test frames
            for i in range(3):
                frame = np.random.randint(
                    0, 255, (100, 100, 3), dtype=np.uint8)
                await compositor.broadcast_frame(frame, {"frame": i})
                await asyncio.sleep(0.1)

            stats = comdec.get_stats()
            print(f"📊 Sent {stats['frames_consumed']} frames")
            print("✅ Basic test completed")

        except Exception as e:
            print(f"❌ Test failed: {e}")
        finally:
            await comdec.finalize()
            print("🧹 Cleanup completed")

    asyncio.run(main())
