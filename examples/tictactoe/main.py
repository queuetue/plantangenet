import argparse
import asyncio
import colorsys
import os
import sys
import time
from plantangenet import GLOBAL_LOGGER
from plantangenet.session import Session
from examples.tictactoe.policy import policy, identity
from .widget_dashboard import WidgetDashboard, Widget

from .player import TicTacToePlayer
from .referee import TicTacToeReferee
from .stats import TicTacToeStats
from .tictactoe_types import GameBoard, GameState, PlayerSymbol
from plantangenet.game.tournament import TournamentManager
from plantangenet.game.activity_manager import ActivityManager

# --- Argument Parsing ---


def parse_args():
    parser = argparse.ArgumentParser(
        description="Tic Tac Toe Multi-Agent Tournament (Modernized)")
    parser.add_argument("--refs", type=int, default=1,
                        help="Number of referees (boards)")
    parser.add_argument("--players", type=int, default=6,
                        help="Number of players")
    parser.add_argument("--time", type=float, default=10.0,
                        help="Max runtime in seconds")
    parser.add_argument("--benchmark", action="store_true",
                        help="Enable benchmark mode (no delays, fast as possible)")
    parser.add_argument("--dashboard", action="store_true",
                        help="Enable visual dashboard (WidgetDashboard compositor)")
    parser.add_argument("--dashboard-size", type=str, default="1200x800",
                        help="Dashboard size in WIDTHxHEIGHT format (default: 1200x800)")
    parser.add_argument("--tournament", action="store_true",
                        help="Use tournament mode (fixed games). Default is batch mode (infinite play)")
    return parser.parse_args()


def distribute_players(players, refs):
    # Fill refs first - give each ref at least 2 players before spreading remainder
    if len(players) < 2:
        print(
            f"Warning: Need at least 2 players to start games, but only have {len(players)}")
        return

    if len(refs) > len(players) // 2:
        print(
            f"Warning: Too many refs ({len(refs)}) for players ({len(players)}). Each ref needs at least 2 players.")
        print(
            f"Consider using --refs {len(players) // 2} or --players {len(refs) * 2}")

    # Fill refs first: give each referee at least 2 players
    player_index = 0
    for ref in refs:
        # Give each ref at least 2 players (if available)
        players_for_this_ref = min(2, len(players) - player_index)
        for _ in range(players_for_this_ref):
            if player_index < len(players):
                player = players[player_index]
                ref.add_player_to_queue(player._ocean__id)
                ref.player_map[player._ocean__id] = player
                player_index += 1

    # Distribute remaining players round-robin
    ref_index = 0
    while player_index < len(players):
        player = players[player_index]
        refs[ref_index % len(refs)].add_player_to_queue(player._ocean__id)
        refs[ref_index % len(refs)].player_map[player._ocean__id] = player
        player_index += 1
        ref_index += 1

    # Print distribution for debugging
    for i, ref in enumerate(refs):
        print(f"Ref {i+1}: {len(ref.waiting_players)} players queued")


def distribute_players_by_id(player_ids, refs):
    """
    Distribute a list of player IDs to referees' waiting queues.
    Fill refs first - give each ref at least 2 players before spreading remainder.
    """
    if len(player_ids) < 2:
        print(
            f"Warning: Need at least 2 players to start games, but only have {len(player_ids)}")
        return

    if len(refs) > len(player_ids) // 2:
        print(
            f"Warning: Too many referees ({len(refs)}) for number of players ({len(player_ids)}). Some refs will be idle.")

    # First pass: give each ref 2 players (if possible)
    player_iter = iter(player_ids)
    for ref in refs:
        try:
            ref.add_player_to_queue(next(player_iter))
            ref.add_player_to_queue(next(player_iter))
        except StopIteration:
            break

    # Second pass: distribute remaining players round-robin
    remaining_players = list(player_iter)
    for i, player_id in enumerate(remaining_players):
        ref_index = i % len(refs)
        refs[ref_index].add_player_to_queue(player_id)

    print(
        f"Distributed {len(player_ids)} players. Ref queues: {[len(ref.waiting_players) for ref in refs]}")


async def main(namespace="tictactoe-demo", num_refs=2, num_players=4, max_runtime=30,
               benchmark_mode=False, enable_dashboard=False, dashboard_width=1200, dashboard_height=800,
               use_tournament=False):
    print("\n=== Tic Tac Toe Demo: Multi-Agent Tournament ===")
    session = Session(id="tictactoe_demo_session",
                      policy=policy, identity=identity)

    # Conditionally create and register the WidgetDashboard compositor
    dashboard = None
    if enable_dashboard:
        from plantangenet.comdec import SnapshotterComdec, LoggerComdec, MJPEGComdec

        dashboard = WidgetDashboard(
            width=dashboard_width, height=dashboard_height, dpi=96)
        dashboard.layout_direction = "vertical"
        dashboard.widget_size = (200, 100)
        dashboard.padding = 20

        # Add comdecs to the dashboard
        snapshotter = SnapshotterComdec(
            output_dir="./tictactoe_snapshots",
            interval_seconds=2.0,
            prefix="tournament"
        )
        logger_comdec = LoggerComdec(log_level="INFO")

        # Add MJPEG streaming for live dashboard viewing
        mjpeg_comdec = MJPEGComdec(port=8080)

        dashboard.add_comdec(snapshotter)
        dashboard.add_comdec(logger_comdec)
        dashboard.add_comdec(mjpeg_comdec)

        session.add_compositor("dashboard", dashboard)
        await dashboard.initialize_comdecs()
        # Start periodic MJPEG streaming
        dashboard.start_streaming()

        print(
            f"Dashboard compositor enabled: {dashboard_width}x{dashboard_height}")
        print(f"Snapshotter comdec: saving to ./tictactoe_snapshots every 2 seconds")
        print(f"MJPEG stream available at: http://localhost:8080/")
        print(f"View the live dashboard in your browser or VLC!")

    # Create referees and register as agents
    refs = [TicTacToeReferee(namespace=f"{namespace}_ref{i+1}", logger=GLOBAL_LOGGER,
                             benchmark_mode=benchmark_mode) for i in range(num_refs)]
    for ref in refs:
        session.add_agent(ref)

    # Create players and register as agents
    players = []
    for i in range(num_players):
        player = TicTacToePlayer(namespace=namespace, logger=GLOBAL_LOGGER)
        players.append(player)
        session.add_agent(player)
    distribute_players(players, refs)

    # Create stats agent and register as agent
    stats = TicTacToeStats(namespace=namespace, logger=GLOBAL_LOGGER)
    session.add_agent(stats)

    print(f"Created {len(players)} players and {len(refs)} referees")
    if enable_dashboard and dashboard:
        print(
            f"Dashboard compositor registered with {dashboard.width}x{dashboard.height} resolution")

    # --- Tournament or Batch Loop ---
    start_time = time.time()
    frame_count = 0
    last_reshuffle_time = start_time
    exhaustion_check_interval = 5.0  # Check for exhaustion every 5 seconds

    if use_tournament:
        # Tournament mode: run a fixed set of games, then stop
        tournament = TournamentManager(
            players=players,
            game_factory=game_factory,
            stats_agent=stats,
            num_rounds=10,  # or from args
            games_per_round=10,  # or from args
        )
        await tournament.run()
    else:
        # Batch mode: run refs indefinitely (or until max_runtime)
        batch = ActivityManager(refs, activity_fn=lambda ref: ref.update(),
                                steps=1000, async_mode=True)
        await batch.run()

    # --- Final Tournament Results ---
    print("\n🏆 Final Tournament Standings 🏆\n")
    # Sort by wins, then games played, then nickname
    scoreboard = sorted(
        players, key=lambda p: (-p.games_won, -p.games_played, getattr(p, '_ocean__nickname', '')))
    trophy_emojis = ['🥇', '🥈', '🥉'] + ['🏅'] * (len(scoreboard) - 3)
    print(f"{'Trophy':<3} {'Player':<20} {'Games':>5} {'Wins':>5} {'Win%':>7}")
    print('-' * 45)
    for i, player in enumerate(scoreboard):
        win_rate = (player.games_won / player.games_played *
                    100) if player.games_played > 0 else 0
        trophy = trophy_emojis[i] if i < len(trophy_emojis) else '🏅'
        print(f"{trophy} {getattr(player, '_ocean__nickname', str(i)):<20} {player.games_played:>5} {player.games_won:>5} {win_rate:>6.1f}%")
    # Aggregate referee stats
    print("\nAggregate Referee Benchmarks:")
    total_games = sum(ref.completed_games for ref in refs)
    total_moves = sum(ref.total_moves for ref in refs)
    total_time = time.time() - start_time
    games_per_sec = total_games / total_time if total_time > 0 else 0
    moves_per_sec = total_moves / total_time if total_time > 0 else 0
    print(f"Total Games: {total_games} | Total Moves: {total_moves} | Total Time: {total_time:.2f}s | {games_per_sec:.2f} games/s | {moves_per_sec:.2f} moves/s")
    print("\nPer-Referee Benchmarks:")
    # for i, ref in enumerate(refs):
    #     print(f"[Ref {i+1}] {ref.get_benchmark_report()}")

    # Save final dashboard as PNG
    if enable_dashboard and dashboard:
        print("\nSaving final dashboard...")
        dashboard_output_file = f"tictactoe_dashboard_{int(time.time())}.png"
        if dashboard.save_as_png(dashboard_output_file):
            print(f"Dashboard saved as: {dashboard_output_file}")
        else:
            print("Could not save dashboard (Pillow not available)")

        # Show final dashboard info
        print(
            f"Dashboard: {len(dashboard.widgets)} widgets rendered at {dashboard.width}x{dashboard.height}")

    print("\n✨ Thanks for playing Plantangenet Tic Tac Toe! ✨\n")


class TicTacToeApplication:
    """Programmatic interface for running a TicTacToe tournament (for tests and scripts)."""

    def __init__(self, namespace="tictactoe-test", num_refs=1, num_players=2, max_runtime=5, benchmark_mode=False):
        self.namespace = namespace
        self.num_refs = num_refs
        self.num_players = num_players
        self.max_runtime = max_runtime
        self.benchmark_mode = benchmark_mode
        self.session = None
        self.refs = []
        self.players = []
        self.stats = None
        self.num_rounds = 1
        self.games_per_round = 1
        self.output_dir = None
        self.outputs = None

    async def initialize(self, config=None):
        if config is None:
            config = {}
        self.num_rounds = config.get("num_rounds", 1)
        self.games_per_round = config.get("games_per_round", 1)
        self.output_dir = config.get("output_dir", None)
        self.outputs = config.get("outputs", None)
        self.session = Session(id="tictactoe_test_session",
                               policy=policy, identity=identity)
        self.refs = [TicTacToeReferee(namespace=f"{self.namespace}_ref{i+1}", logger=GLOBAL_LOGGER,
                                      benchmark_mode=self.benchmark_mode) for i in range(self.num_refs)]
        for ref in self.refs:
            self.session.add_agent(ref)
        self.players = [TicTacToePlayer(
            namespace=self.namespace, logger=GLOBAL_LOGGER) for _ in range(self.num_players)]
        for player in self.players:
            self.session.add_agent(player)
        distribute_players(self.players, self.refs)
        self.stats = TicTacToeStats(
            namespace=self.namespace, logger=GLOBAL_LOGGER)
        self.session.add_agent(self.stats)
        # Attach comdecs if outputs and output_dir are specified
        from plantangenet.comdec import SnapshotterComdec, LoggerComdec, StreamingComdec
        if self.outputs and self.output_dir:
            import os
            os.makedirs(self.output_dir, exist_ok=True)
            if self.outputs.get("snapshot"):
                snapshot_file = os.path.join(self.output_dir, "snapshot.json")
                self.stats.add_comdec(
                    SnapshotterComdec(filepath=snapshot_file))
            if self.outputs.get("logger"):
                log_file = os.path.join(self.output_dir, "log.txt")
                from io import StringIO
                # Use a file stream for logger
                log_stream = open(log_file, "w")
                self.stats.add_comdec(LoggerComdec(log_stream=log_stream))
            if self.outputs.get("streaming"):
                # For streaming, use a dummy handler that writes to a file
                stream_file = os.path.join(self.output_dir, "stream.txt")

                def stream_handler(payload):
                    with open(stream_file, "ab") as f:
                        f.write(payload + b"\n")
                self.stats.add_comdec(StreamingComdec(
                    stream_handler=stream_handler))

    async def run_tournament(self):
        # Use the generic Tournament abstraction
        from .game import TicTacToeGame
        from .local_policy import LocalPolicy

        def game_factory(game_id, p1, p2):
            from .game import TicTacToeGame
            game = TicTacToeGame(game_id, p1._ocean__id, p2._ocean__id)
            import random
            while game.board.state == GameState.IN_PROGRESS:
                current_player = game.current_turn
                empty_spots = [(r, c) for r in range(3)
                               for c in range(3) if game.board.board[r][c] == " "]
                if not empty_spots:
                    break
                row, col = random.choice(empty_spots)
                game.make_move(current_player, row, col)
            return game
        tournament = TournamentManager(
            players=self.players,
            game_factory=game_factory,
            stats_agent=self.stats,
            num_rounds=self.num_rounds,
            games_per_round=self.games_per_round
        )
        await tournament.run()
        if self.stats is not None:
            return {
                'total_games': getattr(self.stats, 'total_games', 0),
                'total_moves': getattr(self.stats, 'total_moves', 0)
            }
        else:
            return {'total_games': 0, 'total_moves': 0}
