"""
Quick CLI runner for TicTacToe tournament/benchmark.
Usage:
    python run_console.py [--games N] [--players M] [--refs R] [--benchmark]

Defaults: 100 games, 4 players, 2 referees, no benchmark mode.
"""
from policy import policy, identity
from plantangenet.session.session import Session
from stats import TicTacToeStats
from player import TicTacToePlayer
from referee import TicTacToeReferee
import asyncio
import argparse
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run TicTacToe tournament in console.")
    parser.add_argument('--games', type=int, default=100,
                        help='Number of games to play')
    parser.add_argument('--players', type=int, default=4,
                        help='Number of players')
    parser.add_argument('--refs', type=int, default=2,
                        help='Number of referees')
    parser.add_argument('--benchmark', action='store_true',
                        help='Enable benchmark mode')
    return parser.parse_args()


async def main():
    args = parse_args()
    session = Session("tictactoe-session", policy=policy, identity=identity)
    stats = TicTacToeStats()
    session.add_agent(stats)
    # Create referees
    referees = [TicTacToeReferee(
        f"ref{i+1}", benchmark_mode=args.benchmark, policy=policy) for i in range(args.refs)]
    for ref in referees:
        session.add_agent(ref)
    # Create players
    players = [TicTacToePlayer(f"player{i+1}") for i in range(args.players)]
    for p in players:
        session.add_agent(p)
        # Register with all refs for stats
        pid = getattr(p, 'namespace', None) or getattr(
            p, '_ocean__id', None) or str(p)
        for ref in referees:
            ref.player_map[pid] = p
    # Distribute players to refs
    for i, p in enumerate(players):
        pid = getattr(p, 'namespace', None) or getattr(
            p, '_ocean__id', None) or str(p)
        referees[i % len(referees)].add_player_to_queue(pid)
    # Run tournament
    print(
        f"Running tournament: {args.games} games, {args.players} players, {args.refs} referees, benchmark={args.benchmark}")
    completed = 0
    while completed < args.games:
        await session.update_agents()
        completed = sum(ref.completed_games for ref in referees)
        if not args.benchmark:
            await asyncio.sleep(0.01)
    # Print stats
    print("\nTournament complete!")
    print(stats.to_dict())
    if args.benchmark:
        for ref in referees:
            print(ref.get_benchmark_report())

if __name__ == "__main__":
    asyncio.run(main())
