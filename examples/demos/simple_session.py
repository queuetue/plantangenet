import asyncio
import os
from typing import Dict
from plantangenet import GLOBAL_LOGGER
from plantangenet.session import Session
from plantangenet.vanilla_banker import create_vanilla_banker_agent
from plantangenet.session_app import SessionApp

# --- Demo Parameters ---
default_axis_name = "popcorn_axis"
namespace = os.getenv("NAMESPACE", "popcorn-demo")
fps = float(os.getenv("FPS", 60.0))  # 60 frames per second for demo
speed = 1.0  # Speed of the popcorn shard movement per tick
reporting_interval = float(os.getenv("REPORTING_INTERVAL", 1.5))


class PopcornShard:
    def __init__(self):
        self._tick = 0
        self._position = 0.0

    async def update(self) -> bool:
        self._tick += 1
        self._position += speed
        return True

    def get_axis_data(self) -> dict:
        return {
            "position": self._position,
            "impulse": {},
            "metadata": {"source": str(self)}
        }

    def get_axis_name(self):
        return default_axis_name

    def __str__(self):
        return f"POP |tick {self._tick}|pos {self._position:.2f}"

    @property
    def logger(self):
        return GLOBAL_LOGGER


async def main():
    # --- Create session and banker ---
    session = Session(session_id="popcorn_demo_session")
    banker = create_vanilla_banker_agent(
        initial_balance=100, namespace=namespace, logger=GLOBAL_LOGGER)
    app = SessionApp(session)
    app.add_banker_agent(banker)

    # --- Register agent(s) ---
    shard = PopcornShard()
    app.add_agent(shard)

    # --- Economic/logging demo ---
    print("\n=== Popcorn Demo: SessionApp Integration ===")
    print(f"Session ID: {session.session_id}")
    print(f"Initial Dust balance: {session.get_dust_balance()}\n")

    estimate = session.get_cost_estimate("popcorn_tick", {"tick": 1})
    print(f"Cost estimate for 'popcorn_tick': {estimate}")
    if estimate and "dust_cost" in estimate:
        result = session.commit_transaction(
            "popcorn_tick", {"tick": 1}, selected_cost=estimate["dust_cost"])
        print(f"Transaction result: {result}")
        print(f"Dust balance after transaction: {session.get_dust_balance()}")
    else:
        print("No cost estimate available; skipping transaction.")

    print("\nRecent transactions:")
    for tx in session.get_transaction_history()[-3:]:
        print(f"  {tx['type']} | {tx['amount']} dust | {tx['reason']}")

    # --- Periodic simulation tick ---
    async def simulation_tick():
        await shard.update()
        print(f"[Tick] {shard}")

    # --- Periodic reporting ---
    async def report():
        print(
            f"[Report] Tick: {shard._tick}, Position: {shard._position:.2f}, Dust: {session.get_dust_balance()}")

    app.add_periodic_task(simulation_tick, interval=1.0 /
                          fps, name="simulation_tick")
    app.add_periodic_task(report, interval=reporting_interval, name="report")

    await app.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Shutting down Popcorn example.")
