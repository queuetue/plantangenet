"""
Integration example: Adding WebSocket bidirectional comdec to Breakout
Shows how to extend the existing Breakout game with real-time frontend control.
"""
import asyncio
from plantangenet.comdec.websocket import WebSocketBidirectionalComdec
from examples.breakout.main import BreakoutApplication, BreakoutGame


class WebSocketBreakoutApplication(BreakoutApplication):
    """Breakout application with WebSocket bidirectional communication."""

    def __init__(self):
        super().__init__()
        self.websocket_comdec = None
        self.frontend_player_id = "frontend_player"

    async def setup_websocket_comdec(self, port=8765):
        """Set up WebSocket comdec for frontend communication."""

        async def handle_frontend_message(message, stream):
            """Handle messages from the React/frontend."""
            message_type = message.get("type")
            data = message.get("data", {})
            stream_id = message.get("stream_id")

            print(f"🌐 WebSocket message from {stream_id}: {message_type}")

            if message_type == "player_action":
                # Frontend wants to control a player
                action = data.get("action")
                player_id = data.get("player_id", self.frontend_player_id)

                # Apply action to current game if available
                current_game = getattr(self.session, 'game', None)
                if current_game and hasattr(current_game, 'make_move'):
                    action_map = {"left": 0, "right": 1,
                                  "wait": 2, "launch": 3}
                    row = action_map.get(action, 2)

                    success, message = current_game.make_move(
                        player_id, row, 0)

                    # Send confirmation back to frontend
                    await stream.send_message("action_result", {
                        "action": action,
                        "success": success,
                        "message": message,
                        "player_id": player_id
                    })

                    print(f"🎮 Frontend action {action} → {success}: {message}")
                else:
                    await stream.send_message("error", {
                        "message": "No active game to control"
                    })

            elif message_type == "request_game_state":
                # Frontend wants current game state
                current_game = getattr(self.session, 'game', None)
                if current_game and hasattr(current_game, 'get_game_state'):
                    state = current_game.get_game_state()
                    await stream.send_message("game_state", state)
                else:
                    await stream.send_message("game_state", {
                        "status": "no_active_game"
                    })

            elif message_type == "join_as_player":
                # Frontend wants to join as a controllable player
                requested_id = data.get("player_id", self.frontend_player_id)

                # Add frontend as a player in current game
                current_game = getattr(self.session, 'game', None)
                if current_game:
                    # Update game to include frontend player
                    if hasattr(current_game, 'members') and requested_id not in current_game.members:
                        current_game.members.append(requested_id)

                    await stream.send_message("joined_game", {
                        "player_id": requested_id,
                        "game_id": getattr(current_game, 'game_id', 'unknown'),
                        "can_control": True
                    })

                    print(f"🎮 Frontend joined as player {requested_id}")
                else:
                    await stream.send_message("error", {
                        "message": "No active game to join"
                    })

            elif message_type == "chat":
                # Chat message - broadcast to all clients
                username = data.get("username", "Anonymous")
                text = data.get("text", "")

                await self.websocket_comdec.broadcast_to_topic("chat", "chat_message", {
                    "username": username,
                    "text": text,
                    "timestamp": asyncio.get_event_loop().time()
                })

                print(f"💬 Chat: {username}: {text}")

        # Create WebSocket comdec
        self.websocket_comdec = WebSocketBidirectionalComdec(
            port=port,
            message_handler=handle_frontend_message
        )

        # Add to dashboard compositor if available
        if self.dashboard_compositor:
            self.dashboard_compositor.add_comdec(self.websocket_comdec)

        # Initialize
        await self.websocket_comdec.initialize()
        print(f"🌐 WebSocket server ready on ws://localhost:{port}")
        print("🎮 Frontend can now connect and control the game!")

    async def run_tournament(self, config):
        """Override to set up WebSocket before running tournament."""
        # Set up WebSocket first
        await self.setup_websocket_comdec()

        # Create a frontend-controllable player
        from examples.breakout.player import BreakoutPlayer
        frontend_player = BreakoutPlayer(
            player_id=self.frontend_player_id,
            strategy="manual",  # Will be controlled by frontend
            logger=self.logger
        )
        self.players[self.frontend_player_id] = frontend_player

        # Run the normal tournament but with WebSocket streaming
        try:
            await super().run_tournament(config)
        finally:
            # Clean up WebSocket
            if self.websocket_comdec:
                await self.websocket_comdec.finalize()

    async def broadcast_game_update(self, game, event_type="game_update"):
        """Broadcast game state to all WebSocket clients."""
        if not self.websocket_comdec:
            return

        try:
            game_state = game.get_game_state() if hasattr(game, 'get_game_state') else {}

            # Add visual data for frontend rendering
            if hasattr(game, 'board'):
                board = game.board
                game_state.update({
                    "visual": {
                        "ball": {
                            "x": getattr(board.ball, 'x', 0),
                            "y": getattr(board.ball, 'y', 0),
                            "radius": getattr(board.ball, 'radius', 5)
                        },
                        "paddle": {
                            "x": getattr(board.paddle, 'x', 0),
                            "y": getattr(board.paddle, 'y', 0),
                            "width": getattr(board.paddle, 'width', 20),
                            "height": getattr(board.paddle, 'height', 5)
                        },
                        "blocks": [
                            {
                                "x": block.x,
                                "y": block.y,
                                "width": block.width,
                                "height": block.height,
                                "destroyed": block.destroyed,
                                "hits_remaining": block.hits_remaining
                            }
                            for block in board.blocks
                        ] if hasattr(board, 'blocks') else []
                    }
                })

            # Broadcast to clients subscribed to game events
            await self.websocket_comdec.broadcast_to_topic("game_events", event_type, game_state)

        except Exception as e:
            print(f"Error broadcasting game update: {e}")


async def main():
    """Run WebSocket-enabled Breakout tournament."""
    app = WebSocketBreakoutApplication()

    # Use the game app context
    from plantangenet.game import GameAppContext
    async with GameAppContext(app):
        print("🚀 WebSocket Breakout Demo")
        print("=" * 50)
        print("This demo runs a Breakout tournament with WebSocket control.")
        print("Connect with the HTML client or create a React app to control the game!")
        print()

        config = app.get_default_config()
        await app.run_tournament(config)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 WebSocket Breakout demo stopped")
    except Exception as e:
        print(f"❌ Demo error: {e}")
        import traceback
        traceback.print_exc()
