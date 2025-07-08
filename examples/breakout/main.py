"""
Breakout tournament application using Plantangenet game abstractions.
"""
import asyncio
import ulid
import random
from typing import Dict, Any, Callable
from plantangenet import GLOBAL_LOGGER
from plantangenet.game import GameApplication, GameAppContext
from plantangenet.game.turn_based_tournament import TurnBasedTournament

from .game import BreakoutGame
from .stats import BreakoutStats
from .player import BreakoutPlayer


class BreakoutApplication(GameApplication):
    """Main application for running Breakout tournaments."""

    def __init__(self):
        super().__init__("Breakout")
        self.dashboard_objects = {}  # Registry for dashboard-displayable objects

    def create_game_factory(self, config: Dict[str, Any]) -> Callable:
        """Create a factory function for creating Breakout games."""
        def factory(game_id: str, player1: Any, player2: Any) -> BreakoutGame:
            player1_id = str(player1) if player1 is not None else "player1"
            player2_id = str(player2) if player2 is not None else "player2"
            return BreakoutGame(game_id, player1_id, player2_id)
        return factory

    def create_player_agent(self, player_config: Dict[str, Any]) -> BreakoutPlayer:
        """Create a Breakout player agent from configuration."""
        return BreakoutPlayer(
            player_id=player_config["id"],
            strategy=player_config.get("strategy", "random"),
            logger=GLOBAL_LOGGER
        )

    def create_stats_agent(self, config: Dict[str, Any]) -> BreakoutStats:
        """Create a Breakout statistics tracking agent."""
        return BreakoutStats(logger=GLOBAL_LOGGER)

    def get_dashboard_class(self):
        """Return the dashboard class for Breakout."""
        try:
            from .widget_dashboard import BreakoutWidgetDashboard
            return BreakoutWidgetDashboard
        except ImportError:
            return None

    def get_default_config(self) -> Dict[str, Any]:
        """Get default configuration for Breakout."""
        config = super().get_default_config()
        config.update({
            "players": [
                {"id": "alice", "strategy": "follow_ball"},
                {"id": "bob", "strategy": "center"},
                {"id": "charlie", "strategy": "aggressive"},
                {"id": "diana", "strategy": "random"},
            ]
        })
        return config

    async def run_tournament(self, config: Dict[str, Any]):
        """Run the Breakout tournament using TurnBasedTournament."""
        # Prepare player agents
        players = list(self.players.values())
        max_lives = config.get("max_lives", 3)

        def game_factory(current_player):
            # All agents are present in the game, but only current_player acts
            game_id = f"breakout_{current_player.id}_{ulid.ULID()}"
            all_agent_ids = [p.id for p in players]
            return BreakoutGame(game_id, *all_agent_ids)

        async def run_single_game(game, current_player):
            max_frames = 5000
            frames = 0
            SLOWDOWN = 0.01
            if self.session_dashboard:
                self.session_dashboard.set_current_activity(game)
            if hasattr(self.session, '_component_registry'):
                from plantangenet.core import RegistrableComponent

                class GameWrapper(RegistrableComponent):
                    def __init__(self, game):
                        super().__init__(name=game.game_id)
                        self.game = game
                        self.id = game.game_id

                    def __render__(self, width=300, height=80, asset="default", **kwargs):
                        return self.game.__render__(width=width, height=height, asset=asset, **kwargs)

                    def get_default_asset(self, width=300, height=80):
                        return self.game.get_default_asset(width=width, height=height)
                wrapper = GameWrapper(game)
                wrapper.register_with(self.session)
            setattr(self.session, 'game', game)
            self.dashboard_objects[game.game_id] = game
            self.dashboard_objects[f"{game.game_id}_ball"] = game.board.ball
            self.dashboard_objects[f"{game.game_id}_paddle"] = game.board.paddle
            life_lost = False
            prev_lives = game.board.lives
            # Ensure the game is ready for the current player
            if hasattr(game, "current_turn") and game.current_turn != current_player.id:
                print(
                    f"Syncing game.current_turn ({game.current_turn}) -> {current_player.id}")
                if hasattr(game, "turn_order") and current_player.id in game.turn_order:
                    game.current_turn_index = game.turn_order.index(
                        current_player.id)
            while not game.board.is_game_over() and frames < max_frames:
                game_over = game.board.is_game_over()
                print(
                    f"Frame {frames}: game_over={game_over}, frames={frames}, max_frames={max_frames}")

                # Only act if it's the current player's turn
                if getattr(game, "current_turn", current_player.id) == current_player.id:
                    state = game.get_game_state()
                    # If the ball is parked, always force a launch action
                    if hasattr(game.board, "ball") and getattr(game.board.ball, "parked", False):
                        action = "launch"
                        print(
                            f"Frame {frames}: Ball is parked, forcing launch")
                    else:
                        action = current_player.choose_action(state)
                    action_map = {"left": 0, "right": 1,
                                  "wait": 2, "launch": 3}
                    row = action_map.get(action, 2)
                    print(
                        f"Frame {frames}: current_player={current_player.id}, game.current_turn={getattr(game, 'current_turn', None)}, action={action}, row={row}")
                    success, message = game.make_move(
                        current_player.id, row, 0)
                    print(f"make_move: success={success}, message={message}")
                    if not success:
                        print(f"Move failed: {message}")
                    # Always reset current_turn_index to current_player.id for single-player mode
                    if hasattr(game, "turn_order") and current_player.id in game.turn_order:
                        game.current_turn_index = game.turn_order.index(
                            current_player.id)
                    if game.board.lives < prev_lives:
                        life_lost = True
                        break
                    prev_lives = game.board.lives
                else:
                    # If it's not the current player's turn, just advance the frame without action
                    print(
                        f"Frame {frames}: Not current player's turn, skipping action")

                frames += 1
                if self.dashboard_compositor:
                    self._update_dashboard_widgets(game)
                await asyncio.sleep(SLOWDOWN)
            if self.session_dashboard:
                self.session_dashboard.set_current_activity(None)
            # Clean up dashboard objects
            for key in [game.game_id, f"{game.game_id}_ball", f"{game.game_id}_paddle"]:
                if key in self.dashboard_objects:
                    del self.dashboard_objects[key]
            if hasattr(self.session, '_component_registry'):
                registry = self.session._component_registry
                if hasattr(registry, '_components') and game.game_id in registry._components:
                    del registry._components[game.game_id]
            if hasattr(self.session, 'game') and getattr(self.session, 'game', None) == game:
                setattr(self.session, 'game', None)
            return {
                "score": game.board.score,
                "life_lost": life_lost,
                "frames": frames,
                "lives_remaining": game.board.lives
            }

        tournament = TurnBasedTournament(
            players=players,
            game_factory=game_factory,
            max_lives=max_lives
        )
        tournament.run_single_game = run_single_game
        results = await tournament.run()
        print("\n🏆 Final Tournament Results (Turn-Based) 🏆")
        print("=" * 40)
        for pid, score in results['scores'].items():
            print(
                f"{pid}: {score} points, lives left: {results['lives'][pid]}")
        print(f"Winner: {results['winner']}")

    async def _run_single_game(self, game: BreakoutGame, players: list) -> Dict[str, Any]:
        """Run a single Breakout game to completion."""
        max_frames = 5000  # Prevent infinite games
        frames = 0

        # Set current activity in session dashboard
        if self.session_dashboard:
            self.session_dashboard.set_current_activity(game)

        # Slowdown factor: increase this to slow the game (e.g., 0.03 for ~half speed)
        SLOWDOWN = 0.005

        while not game.board.is_game_over() and frames < max_frames:
            current_player_id = game.current_turn
            if current_player_id and current_player_id in self.players:
                player = self.players[current_player_id]
                action = player.choose_action(game.get_game_state())

                # Convert action to row format for make_move
                action_map = {"left": 0, "right": 1, "wait": 2}
                row = action_map.get(action, 2)

                success, message = game.make_move(current_player_id, row, 0)
                if not success:
                    print(f"Move failed: {message}")

            frames += 1

            # Dashboard widget update
            if self.dashboard_compositor:
                self._update_dashboard_widgets(game)

            # Add small delay for visualization (slowed down for watchability)
            await asyncio.sleep(SLOWDOWN)

        # Determine winner and final score
        winner = "tie"
        if game.board.is_win():
            winner = players[0] if len(
                players) == 1 else "player1"  # Simplified for demo
        elif game.board.lives <= 0:
            winner = "tie"  # Game over due to no lives

        # Clear current activity when done
        if self.session_dashboard:
            self.session_dashboard.set_current_activity(None)

        return {
            "winner": winner,
            "score": game.board.score,
            "frames": frames,
            "lives_remaining": game.board.lives
        }

    def _update_dashboard_widgets(self, game: BreakoutGame):
        """Update dashboard widgets for the current game."""
        if not self.dashboard_compositor:
            return

        try:
            from .widget_dashboard import Widget
            import numpy as np

            self.dashboard_compositor.clear()
            board = game.board

            # Map game coordinates to dashboard pixels
            width = self.dashboard_compositor.width
            height = self.dashboard_compositor.height
            scale_x = width / board.width
            scale_y = height / board.height

            # --- Composite game field widget (for asset view) ---
            # Create an RGB array for the whole field
            field_img = np.zeros((height, width, 3), dtype=np.uint8)
            # Background
            field_img[:, :] = (30, 30, 30)
            # Blocks (for field image)
            for block in board.blocks:
                if not block.destroyed:
                    bx = int(block.x * scale_x)
                    by = int(block.y * scale_y)
                    bw = max(8, int(block.width * scale_x))
                    bh = max(6, int(block.height * scale_x))
                    color = (180, 80 + 30 * (block.hits_remaining % 3), 180)
                    field_img[by:by+bh, bx:bx+bw] = color
            # Paddle
            px = int(board.paddle.x * scale_x)
            py = int(board.paddle.y * scale_y)
            pw = max(10, int(board.paddle.width * scale_x))
            ph = max(6, int(board.paddle.height * scale_x))
            field_img[py:py+ph, px:px+pw] = (100, 200, 255)
            # Ball
            bx = int(board.ball.x * scale_x)
            by = int(board.ball.y * scale_y)
            br = max(6, int(board.ball.radius * scale_x))
            # Draw ball as a filled circle
            for y in range(-br, br):
                for x in range(-br, br):
                    if x*x + y*y <= br*br:
                        iy = by + y
                        ix = bx + x
                        if 0 <= iy < height and 0 <= ix < width:
                            field_img[iy, ix] = (255, 200, 0)
            # Score/lives text (not rendered in asset, but could be added with PIL if desired)
            # Register the composite as a widget for the game object
            self.dashboard_compositor.add_widget(
                game.game_id,
                # color is ignored, image is in .image
                Widget(0, 0, width, height, color=(0, 0, 0))
            )
            # Attach the image to the widget for asset serving
            self.dashboard_compositor.widgets[game.game_id].image = field_img

            # --- Per-element widgets for dashboard visualization ---
            # Ball
            if hasattr(board.ball, 'id'):
                self.dashboard_compositor.add_widget(
                    board.ball.id,
                    Widget(bx, by, br, br, color=(255, 200, 0))
                )
            # Paddle (per-player, use actual agent/player object ID if available)
            for player_id in getattr(game, 'members', []):
                player_obj = self.players.get(player_id)
                widget_id = getattr(player_obj, 'id', player_id)
                self.dashboard_compositor.add_widget(
                    widget_id,
                    Widget(px, py, pw, ph, color=(100, 200, 255))
                )
            # Paddle (main paddle object, if it has an id)
            if hasattr(board.paddle, 'id'):
                self.dashboard_compositor.add_widget(
                    board.paddle.id,
                    Widget(px, py, pw, ph, color=(100, 200, 255))
                )
            # Blocks (for widgets)
            for block in board.blocks:
                if not block.destroyed and hasattr(block, 'id'):
                    bx = int(block.x * scale_x)
                    by = int(block.y * scale_y)
                    bw = max(8, int(block.width * scale_x))
                    bh = max(6, int(block.height * scale_x))
                    color = (180, 80 + 30 * (block.hits_remaining % 3), 180)
                    self.dashboard_compositor.add_widget(
                        block.id,
                        Widget(bx, by, bw, bh, color=color)
                    )
            # Score/lives as a widget (optional, use a fixed id)
            self.dashboard_compositor.add_widget(
                "score",
                Widget(10, 10, 180, 30, color=(40, 40, 40)).set_text(
                    f"Score: {board.score}  Lives: {board.lives}")
            )
        except ImportError:
            pass  # Widget dashboard not available

    def _print_round_results(self, round_num: int, results: list):
        """Print results for a tournament round."""
        print(f"Round {round_num} Results:")
        for i, result in enumerate(results):
            print(
                f"  Game {i+1}: Winner={result['winner']}, Score={result['score']}, Frames={result['frames']}")

    def _print_tournament_results(self):
        """Print final tournament results."""
        print("\n🏆 Final Tournament Results 🏆")
        print("=" * 40)

        # Print player stats
        for player_id, player in self.players.items():
            stats = player.get_stats()
            print(
                f"{player_id}: {stats['games_played']} games, avg score: {stats['average_score']:.1f}")

        # Print leaderboard from stats agent
        if self.stats_agent:
            leaderboard = self.stats_agent.get_leaderboard()
            print("\nLeaderboard:")
            for i, entry in enumerate(leaderboard):
                print(
                    f"{i+1}. {entry['player']}: {entry['wins']} wins, {entry['average_score']:.1f} avg score")


async def main():
    """Main entry point for Breakout tournament."""
    app = BreakoutApplication()
    async with GameAppContext(app):
        await app.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, asyncio.CancelledError):
        print("\nBreakout tournament interrupted or cancelled!")
    except Exception as e:
        # Only print unexpected exceptions
        print(f"Unexpected error: {e}")

# Note: Ensure Ball, Paddle, and Block classes assign a unique id using ulid.new() in their __init__ methods:
# self.id = str(ulid.new())
