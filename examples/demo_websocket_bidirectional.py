#!/usr/bin/env python3
"""
Demo of WebSocket Bidirectional Comdec
Shows how to set up a bidirectional stream between a compositor and React-like frontend.
"""
import asyncio
import numpy as np
import time
import json
from typing import Optional, TYPE_CHECKING
from plantangenet.comdec.websocket import WebSocketBidirectionalComdec
from plantangenet.compositor.fb_types import SoftwareFBCompositor

if TYPE_CHECKING:
    from plantangenet.comdec.websocket import WebSocketBidirectionalComdec


class DemoGameState:
    """Simple game state for demo purposes."""

    def __init__(self):
        self.paddle_x = 50
        self.ball_x = 25
        self.ball_y = 25
        self.ball_dx = 2
        self.ball_dy = 1
        self.score = 0
        self.frame_count = 0

    def update(self):
        """Update game state one frame."""
        self.frame_count += 1

        # Move ball
        self.ball_x += self.ball_dx
        self.ball_y += self.ball_dy

        # Bounce ball off walls
        if self.ball_x <= 0 or self.ball_x >= 100:
            self.ball_dx = -self.ball_dx
        if self.ball_y <= 0 or self.ball_y >= 100:
            self.ball_dy = -self.ball_dy

        # Keep ball in bounds
        self.ball_x = max(0, min(100, self.ball_x))
        self.ball_y = max(0, min(100, self.ball_y))

    def move_paddle(self, direction):
        """Move paddle left or right."""
        if direction == "left":
            self.paddle_x = max(0, self.paddle_x - 5)
        elif direction == "right":
            self.paddle_x = min(100, self.paddle_x + 5)
        print(f"Paddle moved {direction} to x={self.paddle_x}")

    def to_dict(self):
        """Convert state to dictionary for JSON serialization."""
        return {
            "paddle_x": self.paddle_x,
            "ball_x": self.ball_x,
            "ball_y": self.ball_y,
            "score": self.score,
            "frame_count": self.frame_count
        }


class DemoMessageHandler:
    """Handles incoming WebSocket messages with access to game state."""

    def __init__(self):
        self.game_state: Optional['DemoGameState'] = None
        self.comdec: Optional['WebSocketBidirectionalComdec'] = None

    async def handle_message(self, message, stream):
        """
        Handle incoming messages from WebSocket clients.
        This is the backchannel - frontend sends events to backend.
        """
        message_type = message.get("type")
        data = message.get("data", {})
        stream_id = message.get("stream_id")

        print(f"📨 Received message from {stream_id}: {message_type}")

        # Route messages based on type
        if message_type == "player_action":
            # Frontend sending game input
            action = data.get("action")
            player_id = data.get("player_id", "unknown")

            print(f"🎮 Player {player_id} action: {action}")

            # Apply action to game state
            if self.game_state and action in ["left", "right"]:
                self.game_state.move_paddle(action)

                # Send immediate feedback
                await stream.send_message("action_confirmed", {
                    "action": action,
                    "player_id": player_id,
                    "new_paddle_x": self.game_state.paddle_x
                })

        elif message_type == "chat":
            # Chat message - broadcast to all clients
            username = data.get("username", "Anonymous")
            text = data.get("text", "")

            print(f"💬 Chat from {username}: {text}")

            # Broadcast to all streams subscribed to "chat" topic
            if self.comdec:
                await self.comdec.broadcast_to_topic("chat", "chat_message", {
                    "username": username,
                    "text": text,
                    "timestamp": time.time()
                })

        elif message_type == "request_state":
            # Frontend requesting current game state
            if self.game_state:
                await stream.send_message("game_state", self.game_state.to_dict())

        else:
            # Unknown message type
            await stream.send_message("error", {
                "message": f"Unknown message type: {message_type}",
                "received_type": message_type
            })


async def main():
    """Main demo function."""
    print("🚀 WebSocket Bidirectional Comdec Demo")
    print("=" * 60)

    # Create game state
    game_state = DemoGameState()

    # Create message handler
    message_handler = DemoMessageHandler()
    message_handler.game_state = game_state

    # Create compositor for rendering frames
    compositor = SoftwareFBCompositor(width=200, height=200, channels=3)

    # Create WebSocket comdec with message handler
    websocket_comdec = WebSocketBidirectionalComdec(
        port=8765,
        host="0.0.0.0",
        message_handler=message_handler.handle_message
    )

    # Complete the circular reference
    message_handler.comdec = websocket_comdec

    # Add comdec to compositor
    compositor.add_comdec(websocket_comdec)

    try:
        # Initialize comdec (starts WebSocket server)
        await websocket_comdec.initialize()

        print("📡 WebSocket server started on ws://localhost:8765")
        print("📋 Try connecting with a WebSocket client and sending:")
        print(
            '   {"type": "player_action", "data": {"action": "left", "player_id": "alice"}}')
        print('   {"type": "chat", "data": {"username": "Bob", "text": "Hello!"}}')
        print('   {"type": "request_state", "data": {}}')
        print(
            '   {"type": "subscribe", "data": {"topics": ["chat", "game_events"]}}')
        print()
        print("🎮 Game loop starting...")

        # Game loop - sends frames out, receives actions in
        frame_count = 0
        while True:
            # Update game state
            game_state.update()

            # Create visual frame (simple colored rectangles)
            frame = np.zeros((200, 200, 3), dtype=np.uint8)

            # Background
            frame[:, :] = [30, 30, 30]

            # Ball (red circle approximated as rectangle)
            ball_x = int(game_state.ball_x * 2)  # Scale to 200px
            ball_y = int(game_state.ball_y * 2)
            frame[ball_y:ball_y+10, ball_x:ball_x+10] = [255, 0, 0]  # Red ball

            # Paddle (blue rectangle)
            paddle_x = int(game_state.paddle_x * 2)
            frame[180:190, paddle_x:paddle_x+30] = [0, 100, 255]  # Blue paddle

            # Send frame through compositor → comdec → WebSocket clients
            await compositor.broadcast_frame(frame, metadata={
                "frame_type": "game_visual",
                "game_state": game_state.to_dict()
            })

            # Also send structured game state updates
            if frame_count % 30 == 0:  # Every second at 30fps
                await websocket_comdec.broadcast_to_topic("game_events", "game_update",
                                                          game_state.to_dict(),
                                                          {"update_type": "periodic"}
                                                          )

            frame_count += 1

            # Print stats every 5 seconds
            if frame_count % 150 == 0:
                stats = websocket_comdec.get_stats()
                print(f"📊 Frame {frame_count}: {stats['active_streams']} active streams, "
                      f"{stats['frames_consumed']} frames sent")
                if stats['active_streams'] > 0:
                    print(f"   Stream IDs: {stats['stream_ids']}")
                    print(f"   Subscriptions: {stats['subscriptions']}")

            await asyncio.sleep(1/30)  # 30 FPS

    except KeyboardInterrupt:
        print("\n⏹️  Demo interrupted")
    except Exception as e:
        print(f"❌ Demo error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Clean up
        print("🧹 Cleaning up...")
        await websocket_comdec.finalize()
        print("✅ Demo finished")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
