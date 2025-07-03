import argparse
import asyncio
import os
import sys
import time
from plantangenet import GLOBAL_LOGGER
from plantangenet.session import Session
from plantangenet.vanilla_banker import create_vanilla_banker_agent
from plantangenet.session_app import SessionApp

from player import TicTacToePlayer
from referee import TicTacToeReferee
from stats import TicTacToeStats
from examples.tictactoe.tictactoe_types import GameBoard, GameState, PlayerSymbol

# --- Argument Parsing ---


def parse_args():
    parser = argparse.ArgumentParser(
        description="Tic Tac Toe Multi-Agent Tournament")
    parser.add_argument("--refs", type=int, default=1,
                        help="Number of referees (boards)")
    parser.add_argument("--players", type=int, default=6,
                        help="Number of players")
    parser.add_argument("--time", type=float, default=10.0,
                        help="Max runtime in seconds")
    parser.add_argument("--benchmark", action="store_true",
                        help="Enable benchmark mode (no delays, fast as possible)")
    return parser.parse_args()


args = parse_args()

namespace = os.getenv("NAMESPACE", "tictactoe-demo")
num_refs = args.refs
num_players = args.players
max_runtime = args.time
benchmark_mode = args.benchmark
reporting_interval = float(os.getenv("REPORTING_INTERVAL", 2.0))


def distribute_players(players, refs):
    # Evenly distribute players among refs
    for i, player in enumerate(players):
        refs[i % len(refs)].add_player_to_queue(player._ocean__id)
        refs[i % len(refs)].player_map[player._ocean__id] = player


async def main():
    print("\n=== Tic Tac Toe Demo: Multi-Agent Tournament ===")
    session = Session(session_id="tictactoe_demo_session")
    banker = create_vanilla_banker_agent(
        initial_balance=1000, namespace=namespace, logger=GLOBAL_LOGGER)
    app = SessionApp(session, max_runtime=max_runtime)
    app.add_banker_agent(banker)

    # Create referees
    refs = [TicTacToeReferee(namespace=f"{namespace}_ref{i+1}", logger=GLOBAL_LOGGER,
                             benchmark_mode=benchmark_mode) for i in range(num_refs)]
    for ref in refs:
        app.add_agent(ref)

    # Create players
    players = []
    for i in range(num_players):
        player = TicTacToePlayer(namespace=namespace, logger=GLOBAL_LOGGER)
        players.append(player)
        app.add_agent(player)
    distribute_players(players, refs)

    # Create stats agent
    stats = TicTacToeStats(namespace=namespace, logger=GLOBAL_LOGGER)
    app.add_agent(stats)

    print(f"Created {len(players)} players and {len(refs)} referees")
    print(f"Initial Dust balance: {session.get_dust_balance()}")

    # Periodic tournament status report
    async def tournament_report():
        # Only show a compact aggregate summary during the run
        total_games = sum(ref.completed_games for ref in refs)
        total_moves = sum(ref.total_moves for ref in refs)
        print(
            f"\r[Aggregate] Games: {total_games} | Moves: {total_moves} | Refs: {len(refs)} | Players: {len(players)}", end="", flush=True)

    app.add_periodic_task(
        tournament_report, interval=reporting_interval, name="tournament_report")

    print(
        f"\nStarting tournament with {num_players} players, {num_refs} referees...")
    print("Press Ctrl+C to stop the tournament\n")

    wall_start = time.time()
    await app.run()
    wall_end = time.time()
    wall_elapsed = wall_end - wall_start

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
    total_time = wall_elapsed
    games_per_sec = total_games / total_time if total_time > 0 else 0
    moves_per_sec = total_moves / total_time if total_time > 0 else 0
    print(f"Total Games: {total_games} | Total Moves: {total_moves} | Total Time: {total_time:.2f}s | {games_per_sec:.2f} games/s | {moves_per_sec:.2f} moves/s")
    print("\nPer-Referee Benchmarks:")
    # for i, ref in enumerate(refs):
    #     print(f"[Ref {i+1}] {ref.get_benchmark_report()}")
    print("\n✨ Thanks for playing Plantangenet Tic Tac Toe! ✨\n")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nTournament finished!")
