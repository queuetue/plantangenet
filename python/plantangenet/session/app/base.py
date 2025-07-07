import asyncio
import signal
from typing import Callable, List, Optional
from ..schedule.periodic import PeriodicTask


class BaseApp():
    def __init__(self, max_runtime: Optional[float] = None):
        self.periodic_tasks: List[PeriodicTask] = []
        self._shutdown_event = asyncio.Event()
        self.agent_update_interval = 0.1
        self.max_runtime = max_runtime

    def add_periodic_task(self, coro_func: Callable, interval: float, name: Optional[str] = None):
        self.periodic_tasks.append(PeriodicTask(coro_func, interval, name))

    async def setup(self, loop=None):
        loop = loop or asyncio.get_running_loop()
        loop.add_signal_handler(signal.SIGINT, self._handle_signal)
        loop.add_signal_handler(signal.SIGTERM, self._handle_signal)
        await self._start_periodic_tasks()

    async def _start_periodic_tasks(self):
        for task in self.periodic_tasks:
            task._task = asyncio.create_task(task.run())

    def _handle_signal(self):
        print(f" -- SIGNAL RECEIVED in App --", flush=True)
        self._shutdown_event.set()

    async def _max_runtime_task(self):
        if self.max_runtime is not None:
            await asyncio.sleep(self.max_runtime)
            print(
                f"App: max_runtime of {self.max_runtime} seconds reached. Shutting down.")
            self._shutdown_event.set()

    async def run(self):
        """Main run loop for the app."""
        await self.setup()
        max_runtime_task = None
        if self.max_runtime is not None:
            max_runtime_task = asyncio.create_task(self._max_runtime_task())

        try:
            await self._shutdown_event.wait()
        finally:
            await self.shutdown(max_runtime_task)

    async def shutdown(self, *tasks):
        for task in tasks:
            if task:
                task.cancel()
        for task in self.periodic_tasks:
            task.cancel()
        print("App: shutdown complete.")
