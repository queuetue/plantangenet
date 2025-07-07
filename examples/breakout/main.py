import argparse
import asyncio
import os
import time
from plantangenet import GLOBAL_LOGGER
from plantangenet.vanilla_banker import create_vanilla_banker_agent
from plantangenet.session.app import ChocolateApp

from .game import Game
from .stats import Stats


def parse_args():
    parser = argparse.ArgumentParser(
        description="Activity Multi-Agent Turn")
    return parser.parse_args()


args = parse_args()

namespace = os.getenv("NAMESPACE", "activities-demo")
reporting_interval = float(os.getenv("REPORTING_INTERVAL", 2.0))


async def main():
    print("\n=== Multi-Agent Turn ===")
    app = ChocolateApp(session_id="activities_demo_session")

    # Create banker agent
    banker = create_vanilla_banker_agent(
        initial_balance=1000,
        namespace=namespace,
        logger=GLOBAL_LOGGER
    )
    app.add(banker)

    # Create game instance
    game = Game(namespace=namespace, logger=GLOBAL_LOGGER)
    app.add(game)

    # Create stats agent
    stats = Stats()
    app.add(stats)

    print(f"Initial Dust balance: {app.dust}")

    async def turn():
        print("--", end="", flush=True)

    app.add_periodic_task(
        turn, interval=reporting_interval, name="turn")

    print("\nStarting ...")
    print("Press Ctrl+C to stop the tournament\n")

    wall_start = time.time()
    await app.run()
    wall_end = time.time()
    wall_elapsed = wall_end - wall_start

    # --- Final Turn Results ---
    print("\n🏆 Final Turn Standings 🏆\n")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nTurn finished!")
