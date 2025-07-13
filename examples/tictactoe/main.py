"""
TicTacToe tournament application using Plantangenet game abstractions.
Combines the modern GameApplication pattern with multi-referee tournament structure.
"""
import asyncio
import argparse
from .app import TicTacToeApplication

app = TicTacToeApplication()


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
        "tournament_mode": tournament_mode,
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
    print(f"Mode: {'Tournament' if tournament_mode else 'Batch'}")
    print(f"Runtime: {args.time}s")
    print(f"Benchmark: {args.benchmark}")
    print(f"Dashboard: {args.dashboard}")

    # Run the application
    await app.run()


if __name__ == "__main__":
    try:
        asyncio.run(app.run())
    except (KeyboardInterrupt, asyncio.CancelledError):
        print("\nTicTacToe tournament interrupted!")
    except Exception as e:
        print(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
