import asyncio
from typing import Callable, Optional


class PeriodicTask:
    def __init__(self, coro_func: Callable, interval: float, name: Optional[str] = None):
        self.coro_func = coro_func
        self.interval = interval
        self.name = name or coro_func.__name__
        self._task: Optional[asyncio.Task] = None
        self._shutdown = False

    async def run(self):
        while not self._shutdown:
            await self.coro_func()
            await asyncio.sleep(self.interval)

    def cancel(self):
        self._shutdown = True
        if self._task:
            self._task.cancel()
