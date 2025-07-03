import asyncio
import signal
from typing import Callable, List, Optional, Any
from plantangenet.session import Session


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


class SessionApp:
    def __init__(self, session: Session, max_runtime: Optional[float] = None):
        self.session = session
        self.periodic_tasks: List[PeriodicTask] = []
        self._shutdown_event = asyncio.Event()
        self.agent_update_interval = 0.1  # Update agents every 100ms
        self.max_runtime = max_runtime

    def add_periodic_task(self, coro_func: Callable, interval: float, name: Optional[str] = None):
        self.periodic_tasks.append(PeriodicTask(coro_func, interval, name))

    def add_agent(self, agent: Any):
        self.session.add_agent(agent)

    def add_banker_agent(self, banker: Any):
        self.session.add_banker_agent(banker)

    async def setup(self):
        await self.session.setup()

    def _handle_signal(self):
        print(f" -- SIGNAL RECEIVED in SessionApp --", flush=True)
        self._shutdown_event.set()

    async def _update_agents(self):
        """Periodically update all agents in the session"""
        while not self._shutdown_event.is_set():
            try:
                # Update all agents
                for agent in self.session.agents:
                    if hasattr(agent, 'update'):
                        await agent.update()
                # Update banker if it has an update method
                if self.session.banker and hasattr(self.session.banker, 'update'):
                    await self.session.banker.update()
            except Exception as e:
                print(f"Error updating agents: {e}")

            await asyncio.sleep(self.agent_update_interval)

    async def _max_runtime_task(self):
        if self.max_runtime is not None:
            await asyncio.sleep(self.max_runtime)
            print(
                f"SessionApp: max_runtime of {self.max_runtime} seconds reached. Shutting down.")
            self._shutdown_event.set()

    async def run(self):
        loop = asyncio.get_running_loop()
        loop.add_signal_handler(signal.SIGINT, self._handle_signal)
        loop.add_signal_handler(signal.SIGTERM, self._handle_signal)

        await self.setup()

        # Start agent update task
        agent_update_task = asyncio.create_task(self._update_agents())

        # Start periodic tasks
        for task in self.periodic_tasks:
            task._task = asyncio.create_task(task.run())
        # Start max_runtime timer if set
        max_runtime_task = None
        if self.max_runtime is not None:
            max_runtime_task = asyncio.create_task(self._max_runtime_task())
        try:
            await self._shutdown_event.wait()
        finally:
            agent_update_task.cancel()
            for task in self.periodic_tasks:
                task.cancel()
            await self.session.teardown()
            print("SessionApp: shutdown complete.")
            if max_runtime_task:
                max_runtime_task.cancel()
