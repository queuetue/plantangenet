import asyncio
import os
from typing import Dict

from pyparsing import Any
from plantangenet.gyre.peer import GyrePeer
from plantangenet import GLOBAL_LOGGER
from plantangenet.gyre.server import GyreServer
from plantangenet.compositor.basic import BasicCompositor

default_axis_name = "popcorn_axis"
namespace = os.getenv("NAMESPACE", "popcorn-demo")
fps = float(os.getenv("FPS", 60.0))  # 60 frames per second for demo
speed = 1.0  # Speed of the popcorn shard movement per tick
reporting_interval = float(os.getenv("REPORTING_INTERVAL", 1.5))


class PopcornShard(GyrePeer):
    def __init__(self):
        self._tick = 0
        self._position = 0.0

    def get_current_tick(self):
        return self._tick

    def get_axis_data(self) -> dict[str, Any]:
        return {
            "position": self._position,
            "impulse": {},
            "metadata": {"source": str(self)}
        }

    def get_axis_name(self):
        return default_axis_name

    async def update(self) -> bool:
        self._tick += 1
        self._position += speed
        return True

    def __str__(self):
        return f"POP |tick {self._tick}|pos {self._position:.2f}"

    @property
    def logger(self) -> Any:
        return GLOBAL_LOGGER

    async def handle_leader_update(self, data: Dict[str, Any]) -> None:
        pass

    async def handle_heartbeat(self, data: Dict[str, Any]) -> None:
        pass

    async def on_pulse(self, message: Dict[str, Any]) -> None:
        pass


shard = PopcornShard()

# Create a GyreServer with the PopcornShard peer
gyre_server = GyreServer(
    peers=[shard],
    logger=GLOBAL_LOGGER,
    name="PopcornGyreServer",
    fps=fps,
    reporting_interval=reporting_interval
)

# Attach a BasicCompositor to the GyreServer's frame collector
if gyre_server.frame_collector:
    compositor = BasicCompositor(gyre_server.frame_collector)
else:
    compositor = None


async def main():
    await gyre_server.setup()
    await gyre_server.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Shutting down Popcorn example.")
