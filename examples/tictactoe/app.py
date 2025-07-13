"""
TicTacToe tournament application using Plantangenet game abstractions.
Combines the modern GameApplication pattern with multi-referee tournament structure.
"""
import asyncio
import time
from typing import Dict, Any, Callable, List
from plantangenet import GLOBAL_LOGGER
from plantangenet.game import GameApplication
from plantangenet.squad.player_manager_squad import PlayerManagerSquad
from examples.tictactoe.game import TicTacToeGame
from examples.tictactoe.player import TicTacToePlayer
from examples.tictactoe.stats import TicTacToeStats
from .referee import TicTacToeReferee


class TicTacToeApplication(GameApplication):
    """Main application for running TicTacToe tournaments with multiple referees."""

    def __init__(self):
        super().__init__("TicTacToe")
        self.dashboard_objects = {}  # Registry for dashboard-displayable objects
        self.referees: List[TicTacToeReferee] = []
        self.benchmark_mode = False
        self.player_manager = PlayerManagerSquad(session=self)
        self.completed_games = 0  # Track completed games at the app level

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
            referee = TicTacToeReferee()
            self.referees.append(referee)
            if self.session:
                self.session.add_agent(referee)
            # Register referee for dashboard display
            self.dashboard_objects[referee.id] = referee

        # Distribute players using the player manager squad
        for player_id in self.players:
            self.player_manager.add_player(player_id)

        # Register all players for dashboard display
        for player_id, player in self.players.items():
            self.dashboard_objects[player_id] = player

        print(
            f"Created {len(self.players)} players and {len(self.referees)} referees")
        print(
            f"PlayerManagerSquad waiting: {self.player_manager.get_waiting_players()}")
        print(
            f"PlayerManagerSquad active games: {self.player_manager.get_active_games()}")

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
            print(
                f"Round {round_num + 1} complete. Total games: {self.completed_games}")

    async def _run_batch_mode(self, config: Dict[str, Any], max_runtime: float):
        """Run continuous batch mode until time limit."""
        print(f"\n=== Running Batch Mode: {max_runtime}s runtime ===")

        start_time = time.time()
        frame_count = 0

        # Set up callback for completed games
        def on_game_completed(game):
            self.completed_games += 1
            # Update player stats
            for pid in [game.player_x, game.player_o]:
                player = self.players.get(pid)
                if player:
                    player.games_played = getattr(
                        player, 'games_played', 0) + 1
            winner = getattr(game, 'winner', None)
            if winner and winner != "DRAW":
                player = self.players.get(winner)
                if player:
                    player.total_wins = getattr(player, 'total_wins', 0) + 1
            elif winner == "DRAW":
                # Track draws for both players
                for pid in [game.player_x, game.player_o]:
                    player = self.players.get(pid)
                    if player:
                        player.draws = getattr(player, 'draws', 0) + 1
            # Optionally, update referee stats if available
            # (Add logic here if you can associate a referee with the game)
        self.player_manager.on_game_completed = on_game_completed

        while True:
            current_time = time.time()
            if current_time - start_time >= max_runtime:
                break

            # Step all active games (simulate moves)
            self.player_manager.step_games()

            if not self.player_manager.get_active_games():
                print("All games completed!")
                break

            frame_count += 1

            # Progress update every 50 frames
            if frame_count % 50 == 0:
                elapsed = current_time - start_time
                print(
                    f"Frame {frame_count}: {elapsed:.1f}s elapsed, {self.completed_games} games completed")

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
            draws = getattr(player, 'draws', 0)
            losses = games - wins - draws
            win_rate = (wins / games * 100) if games > 0 else 0
            player_stats.append({
                'id': player_id,
                'wins': wins,
                'draws': draws,
                'losses': losses,
                'games': games,
                'win_rate': win_rate
            })

        # Sort by wins, then win rate
        player_stats.sort(key=lambda x: (-x['wins'], -x['win_rate']))

        print(
            f"{'Player':<15} {'Games':<8} {'Wins':<8} {'Draws':<8} {'Losses':<8} {'Win%':<8}")
        print("-" * 55)
        for stats in player_stats:
            print(
                f"{stats['id']:<15} {stats['games']:<8} {stats['wins']:<8} {stats['draws']:<8} {stats['losses']:<8} {stats['win_rate']:<7.1f}%")

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
