"""
TicTacToe tournament application using Plantangenet game abstractions.
Combines the modern GameApplication pattern with multi-referee tournament structure.
"""
import argparse
import asyncio
import time
import ulid
from typing import Dict, Any, Callable, List, Optional
from plantangenet import GLOBAL_LOGGER
from plantangenet.game import GameApplication, GameAppContext

from examples.tictactoe.game import TicTacToeGame
from examples.tictactoe.player import TicTacToePlayer
from examples.tictactoe.referee import TicTacToeReferee
from examples.tictactoe.stats import TicTacToeStats
from examples.tictactoe.tictactoe_types import GameState, PlayerSymbol


class TicTacToeApplication(GameApplication):
    """Main application for running TicTacToe tournaments with multiple referees."""

    def __init__(self):
        super().__init__("TicTacToe")
        self.dashboard_objects = {}  # Registry for dashboard-displayable objects
        self.referees: List[TicTacToeReferee] = []
        self.benchmark_mode = False

    def create_game_factory(self, config: Dict[str, Any]) -> Callable:
        """Create a factory function for creating TicTacToe games."""
        def factory(game_id: str, player_x: Any, player_o: Any) -> TicTacToeGame:
            player_x_id = str(player_x) if player_x is not None else "player_x"
            player_o_id = str(player_o) if player_o is not None else "player_o"
            return TicTacToeGame(game_id, player_x_id, player_o_id)
        return factory

    def create_player_agent(self, player_config: Dict[str, Any]) -> TicTacToePlayer:
        """Create a TicTacToe player agent from configuration."""
        return TicTacToePlayer(
            player_id=player_config["id"],
            strategy=player_config.get("strategy", "random"),
            logger=GLOBAL_LOGGER
        )

    def create_stats_agent(self, config: Dict[str, Any]) -> TicTacToeStats:
        """Create a TicTacToe statistics tracking agent."""
        return TicTacToeStats(logger=GLOBAL_LOGGER)

    def get_dashboard_class(self):
        """Return the dashboard class for TicTacToe."""
        # Widget dashboard not yet implemented for TicTacToe
        return None

    def get_default_config(self) -> Dict[str, Any]:
        """Get default configuration for TicTacToe."""
        config = super().get_default_config()
        config.update({
            "num_referees": 2,
            "num_players": 6,
            "max_runtime": 30.0,
            "benchmark_mode": False,
            # False = batch mode (continuous), True = fixed tournament
            "tournament_mode": False,
            "num_rounds": 10,
            "players": [
                {"id": "alice", "strategy": "random"},
                {"id": "bob", "strategy": "center"},
                {"id": "charlie", "strategy": "minimax"},
                {"id": "diana", "strategy": "corners"},
                {"id": "eve", "strategy": "blocking"},
                {"id": "frank", "strategy": "random"},
            ]
        })
        return config

    async def setup_tournament(self, config: Dict[str, Any]):
        """Set up the tournament with referees and players."""
        # Create referees
        num_refs = config.get("num_referees", 2)
        self.benchmark_mode = config.get("benchmark_mode", False)

        for i in range(num_refs):
            referee = TicTacToeReferee(
                namespace=f"tictactoe_ref{i+1}",
                logger=GLOBAL_LOGGER,
                benchmark_mode=self.benchmark_mode
            )
            self.referees.append(referee)
            if self.session:
                self.session.add_agent(referee)
            # Register referee for dashboard display
            self.dashboard_objects[referee.id] = referee

        # Distribute players among referees
        self._distribute_players_to_referees()

        # Register all players for dashboard display
        for player_id, player in self.players.items():
            self.dashboard_objects[player_id] = player

        print(
            f"Created {len(self.players)} players and {len(self.referees)} referees")
        for i, ref in enumerate(self.referees):
            print(
                f"Referee {i+1}: {len(ref.waiting_players)} players assigned")

    def _distribute_players_to_referees(self):
        """Distribute players among referees using round-robin distribution."""
        if not self.referees or not self.players:
            return

        player_ids = list(self.players.keys())

        # Clear existing distributions
        for ref in self.referees:
            ref.waiting_players.clear()
            ref.player_map.clear()

        # First pass: give each referee at least 2 players (if possible)
        player_index = 0
        for ref in self.referees:
            # Give each ref at least 2 players
            players_for_this_ref = min(2, len(player_ids) - player_index)
            for _ in range(players_for_this_ref):
                if player_index < len(player_ids):
                    player_id = player_ids[player_index]
                    ref.add_player_to_queue(player_id)
                    ref.player_map[player_id] = self.players[player_id]
                    player_index += 1

        # Second pass: distribute remaining players round-robin
        ref_index = 0
        while player_index < len(player_ids):
            player_id = player_ids[player_index]
            ref = self.referees[ref_index % len(self.referees)]
            ref.add_player_to_queue(player_id)
            ref.player_map[player_id] = self.players[player_id]
            player_index += 1
            ref_index += 1

    async def run_tournament(self, config: Dict[str, Any]):
        """Run the TicTacToe tournament."""
        await self.setup_tournament(config)

        max_runtime = config.get("max_runtime", 30.0)
        tournament_mode = config.get("tournament_mode", False)

        if tournament_mode:
            await self._run_fixed_tournament(config)
        else:
            await self._run_batch_mode(config, max_runtime)

        # Print final results
        self._print_tournament_results()

    async def _run_fixed_tournament(self, config: Dict[str, Any]):
        """Run a fixed tournament with set number of rounds."""
        num_rounds = config.get("num_rounds", 10)

        print(f"\n=== Running Fixed Tournament: {num_rounds} rounds ===")

        for round_num in range(num_rounds):
            print(f"\n--- Round {round_num + 1} ---")

            # Run one round of games across all referees
            round_tasks = []
            for ref in self.referees:
                task = asyncio.create_task(ref.update())
                round_tasks.append(task)

            # Wait for all referees to process one round
            await asyncio.gather(*round_tasks)

            # Print round progress
            total_games = sum(ref.completed_games for ref in self.referees)
            print(
                f"Round {round_num + 1} complete. Total games: {total_games}")

    async def _run_batch_mode(self, config: Dict[str, Any], max_runtime: float):
        """Run continuous batch mode until time limit."""
        print(f"\n=== Running Batch Mode: {max_runtime}s runtime ===")

        start_time = time.time()
        frame_count = 0

        while True:
            current_time = time.time()
            if current_time - start_time >= max_runtime:
                break

            # Run one update cycle for all referees
            referee_tasks = []
            for ref in self.referees:
                task = asyncio.create_task(ref.update())
                referee_tasks.append(task)

            await asyncio.gather(*referee_tasks)

            frame_count += 1

            # Progress update every 50 frames
            if frame_count % 50 == 0:
                elapsed = current_time - start_time
                total_games = sum(ref.completed_games for ref in self.referees)
                print(
                    f"Frame {frame_count}: {elapsed:.1f}s elapsed, {total_games} games completed")

            # Dashboard widget updates
            if self.dashboard_compositor:
                self._update_dashboard_widgets()

            # Small delay to prevent busy-waiting
            if not self.benchmark_mode:
                await asyncio.sleep(0.01)

    def _update_dashboard_widgets(self):
        """Update dashboard widgets for active games."""
        if not self.dashboard_compositor:
            return

        # Dashboard widgets not yet fully implemented
        # This would be where we update the visual representation
        # of active games across all referees
        pass

    def _render_game_widget(self, game: TicTacToeGame, x: int, y: int, width: int, height: int):
        """Render a single game as a dashboard widget."""
        # Dashboard widget rendering not yet implemented
        # This would create a visual representation of the game board
        pass

    def _render_summary_widget(self, x: int, y: int, width: int, height: int):
        """Render tournament summary widget."""
        # Dashboard widget rendering not yet implemented
        # This would show tournament statistics
        pass

    def _print_tournament_results(self):
        """Print final tournament results."""
        print("\n🏆 TicTacToe Tournament Results 🏆")
        print("=" * 50)

        # Player stats
        print("\nPlayer Statistics:")
        player_stats = []
        for player_id, player in self.players.items():
            wins = getattr(player, 'total_wins', 0)
            games = getattr(player, 'games_played', 0)
            win_rate = (wins / games * 100) if games > 0 else 0
            player_stats.append({
                'id': player_id,
                'wins': wins,
                'games': games,
                'win_rate': win_rate
            })

        # Sort by wins, then win rate
        player_stats.sort(key=lambda x: (-x['wins'], -x['win_rate']))

        print(f"{'Player':<15} {'Games':<8} {'Wins':<8} {'Win%':<8}")
        print("-" * 40)
        for stats in player_stats:
            print(
                f"{stats['id']:<15} {stats['games']:<8} {stats['wins']:<8} {stats['win_rate']:<7.1f}%")

        # Referee stats
        print("\nReferee Statistics:")
        total_games = 0
        total_moves = 0
        for i, ref in enumerate(self.referees):
            ref_games = getattr(ref, 'completed_games', 0)
            ref_moves = getattr(ref, 'total_moves', 0)
            total_games += ref_games
            total_moves += ref_moves
            print(f"Referee {i+1}: {ref_games} games, {ref_moves} moves")

        print(f"\nTotal: {total_games} games, {total_moves} moves")

        # Stats agent leaderboard
        if self.stats_agent:
            print("\nLeaderboard:")
            try:
                leaderboard = self.stats_agent.get_leaderboard()
                for i, entry in enumerate(leaderboard[:5]):  # Top 5
                    print(
                        f"{i+1}. {entry.get('player', 'Unknown')}: {entry.get('wins', 0)} wins")
            except Exception:
                print("Stats agent leaderboard not available")

    async def initialize(self, config: Dict[str, Any]):
        await super().initialize(config)
        await self.setup_session_dashboard(config)
        # Ensure dashboard has latest session with all agents
        if self.session_dashboard:
            self.session_dashboard.set_session(self.session)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="TicTacToe Multi-Agent Tournament")
    parser.add_argument("--refs", type=int, default=2,
                        help="Number of referees (default: 2)")
    parser.add_argument("--players", type=int, default=6,
                        help="Number of players (default: 6)")
    parser.add_argument("--time", type=float, default=30.0,
                        help="Max runtime in seconds (default: 30.0)")
    parser.add_argument("--benchmark", action="store_true",
                        help="Enable benchmark mode (no delays)")
    parser.add_argument("--dashboard", action="store_true",
                        help="Enable visual dashboard")
    parser.add_argument("--dashboard-size", type=str, default="1200x800",
                        help="Dashboard size in WIDTHxHEIGHT format (default: 1200x800)")
    parser.add_argument("--tournament", action="store_true",
                        help="Use tournament mode (fixed rounds). Default is batch mode")
    parser.add_argument("--rounds", type=int, default=10,
                        help="Number of rounds in tournament mode (default: 10)")
    return parser.parse_args()


async def main():
    """Main entry point for TicTacToe tournament."""
    # Parse arguments and create config
    args = parse_args()

    # Parse dashboard size
    try:
        width, height = map(int, args.dashboard_size.split('x'))
    except:
        width, height = 1200, 800

    # Configure based on arguments
    config = app.get_default_config()
    config.update({
        "num_referees": args.refs,
        "max_runtime": args.time,
        "benchmark_mode": args.benchmark,
        "tournament_mode": args.tournament,
        "num_rounds": args.rounds,
        "dashboard": args.dashboard,
        "dashboard_width": width,
        "dashboard_height": height
    })

    # Adjust players list to match requested number
    if args.players != len(config["players"]):
        strategies = ["random", "center", "minimax", "corners", "blocking"]
        config["players"] = []
        for i in range(args.players):
            config["players"].append({
                "id": f"player_{i+1}",
                "strategy": strategies[i % len(strategies)]
            })

    print(f"\n=== TicTacToe Tournament ===")
    print(f"Referees: {args.refs}")
    print(f"Players: {args.players}")
    print(f"Mode: {'Tournament' if args.tournament else 'Batch'}")
    print(f"Runtime: {args.time}s")
    print(f"Benchmark: {args.benchmark}")
    print(f"Dashboard: {args.dashboard}")

    # Run the application
    await app.run()


app = TicTacToeApplication()

if __name__ == "__main__":
    try:
        asyncio.run(app.run())
    except (KeyboardInterrupt, asyncio.CancelledError):
        print("\nTicTacToe tournament interrupted!")
    except Exception as e:
        print(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
