"""
TicTacToe Multi-Agent Tournament using modernized Plantangenet patterns.
"""
import argparse
import asyncio
from typing import List

from plantangenet import GLOBAL_LOGGER
from plantangenet.game import GameApplication, SessionDashboardServer
from plantangenet.game.tournament import TournamentManager

from .player import TicTacToePlayer
from .referee import TicTacToeReferee  
from .stats import TicTacToeStats
from .game import TicTacToeGame


class TicTacToeApplication(GameApplication):
    """Main application for TicTacToe tournaments."""

    def __init__(self, args):
        super().__init__(args)
        self.args = args
        self.refs: List[TicTacToeReferee] = []
        self.players: List[TicTacToePlayer] = []
        self.stats_agent = None

    async def create_agents(self):
        """Create all agents for the tournament."""
        # Create referees
        for i in range(self.args.refs):
            ref = TicTacToeReferee(
                namespace=f"tictactoe_ref_{i}",
                logger=GLOBAL_LOGGER,
                benchmark_mode=self.args.benchmark
            )
            self.refs.append(ref)
            self.session.add_agent(ref)

        # Create players with different strategies
        strategies = ["random", "defensive", "offensive", "minimax"]
        for i in range(self.args.players):
            strategy = strategies[i % len(strategies)]
            player = TicTacToePlayer(
                player_id=f"player_{i}",
                strategy=strategy,
                logger=GLOBAL_LOGGER
            )
            self.players.append(player)
            self.session.add_agent(player)

        # Create stats agent
        self.stats_agent = TicTacToeStats(logger=GLOBAL_LOGGER)
        self.session.add_agent(self.stats_agent)

        # Distribute players to referees
        self._distribute_players()

        GLOBAL_LOGGER.info(f"Created {len(self.refs)} referees, {len(self.players)} players")

    def _distribute_players(self):
        """Distribute players among referees for matchmaking."""
        if len(self.players) < 2:
            GLOBAL_LOGGER.warning(f"Need at least 2 players, but only have {len(self.players)}")
            return

        if len(self.refs) > len(self.players) // 2:
            GLOBAL_LOGGER.warning(f"Too many refs ({len(self.refs)}) for players ({len(self.players)})")

        # Fill refs: give each referee at least 2 players
        player_index = 0
        for ref in self.refs:
            # Give each ref at least 2 players (if available)
            players_for_this_ref = min(2, len(self.players) - player_index)
            for _ in range(players_for_this_ref):
                if player_index < len(self.players):
                    player = self.players[player_index]
                    ref.add_player_to_queue(player.player_id)
                    ref.player_map[player.player_id] = player
                    player_index += 1

        # Distribute remaining players round-robin
        ref_index = 0
        while player_index < len(self.players):
            player = self.players[player_index]
            self.refs[ref_index % len(self.refs)].add_player_to_queue(player.player_id)
            self.refs[ref_index % len(self.refs)].player_map[player.player_id] = player
            player_index += 1
            ref_index += 1

        # Print distribution for debugging
        for i, ref in enumerate(self.refs):
            GLOBAL_LOGGER.info(f"Ref {i+1}: {len(ref.waiting_players)} players queued")

    async def setup_dashboard(self):
        """Set up the dashboard with TicTacToe-specific objects."""
        if not self.args.dashboard:
            return

        # Register game objects for dashboard display
        if hasattr(self.session, '_component_registry'):
            # Register stats agent
            if self.stats_agent:
                self.session._component_registry.register_component(self.stats_agent)

            # Register first few active games from referees for display
            for ref in self.refs[:2]:  # Show games from first 2 referees
                for game_id, game in list(ref.active_games.items())[:3]:  # Show up to 3 games per ref
                    self.session._component_registry.register_component(game)

        # Start dashboard server
        self.dashboard_server = SessionDashboardServer(port=8081)
        self.dashboard_server.session = self.session

        # Start dashboard in background
        import uvicorn
        config = uvicorn.Config(self.dashboard_server.app, host="0.0.0.0", port=8081, log_level="info")
        self.dashboard_task = asyncio.create_task(uvicorn.Server(config).serve())
        GLOBAL_LOGGER.info("Dashboard available at http://localhost:8081/session")

    async def run_tournament(self):
        """Run the TicTacToe tournament indefinitely."""
        if self.args.tournament:
            # Tournament mode: run for a specific time or number of games
            tournament_manager = TournamentManager(
                session=self.session,
                max_time=self.args.time,
                target_games=1000 if self.args.benchmark else None
            )
            await tournament_manager.run_tournament()
        else:
            # Batch mode: run indefinitely
            start_time = asyncio.get_event_loop().time()
            while True:
                try:
                    # Update dashboard with current games periodically
                    if self.args.dashboard and hasattr(self.session, '_component_registry'):
                        # Re-register current active games
                        for ref in self.refs[:2]:
                            for game_id, game in list(ref.active_games.items())[:3]:
                                if not self.session._component_registry.has_component(game):
                                    self.session._component_registry.register_component(game)

                    # Run one session update cycle
                    await self.session.update()
                    
                    # Check for time limit
                    if self.args.time > 0:
                        elapsed = asyncio.get_event_loop().time() - start_time
                        if elapsed >= self.args.time:
                            GLOBAL_LOGGER.info(f"Time limit reached: {elapsed:.2f}s")
                            break
                    
                    # Small delay to prevent busy loop
                    if not self.args.benchmark:
                        await asyncio.sleep(0.1)
                        
                except KeyboardInterrupt:
                    GLOBAL_LOGGER.info("Tournament interrupted by user")
                    break
                except Exception as e:
                    GLOBAL_LOGGER.error(f"Error in tournament loop: {e}")
                    await asyncio.sleep(1)

    def print_final_stats(self):
        """Print final tournament statistics."""
        if self.stats_agent:
            GLOBAL_LOGGER.info(f"Final Stats - Games: {self.stats_agent.total_games}, Ties: {self.stats_agent.ties}")
            leaderboard = self.stats_agent.get_leaderboard()
            for i, player_stats in enumerate(leaderboard[:5]):
                player = player_stats['player']
                wins = player_stats['wins']
                win_rate = player_stats['win_rate']
                GLOBAL_LOGGER.info(f"{i+1}. {player}: {wins} wins ({win_rate:.1%})")

        # Print benchmark results
        if self.args.benchmark:
            for ref in self.refs:
                report = ref.get_benchmark_report()
                GLOBAL_LOGGER.info(f"Referee benchmark: {report}")


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="TicTacToe Multi-Agent Tournament (Modernized)")
    parser.add_argument("--refs", type=int, default=1, help="Number of referees (game managers)")
    parser.add_argument("--players", type=int, default=6, help="Number of players")
    parser.add_argument("--time", type=float, default=0.0, help="Max runtime in seconds (0 = unlimited)")
    parser.add_argument("--benchmark", action="store_true", help="Enable benchmark mode (fast execution)")
    parser.add_argument("--dashboard", action="store_true", help="Enable web dashboard")
    parser.add_argument("--tournament", action="store_true", help="Use tournament mode (vs infinite batch mode)")
    return parser.parse_args()


async def main():
    """Main entry point."""
    args = parse_args()
    
    app = TicTacToeApplication(args)
    
    try:
        await app.run()
    except KeyboardInterrupt:
        GLOBAL_LOGGER.info("Application interrupted by user")
    except Exception as e:
        GLOBAL_LOGGER.error(f"Application error: {e}")
        raise
    finally:
        await app.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
