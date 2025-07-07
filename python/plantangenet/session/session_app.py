import asyncio
import signal
from typing import Callable, List, Optional, Any
from .session import Session
from .schedule import PeriodicTask
from ..core.group_manager import BaseGroupManager, Squad


class App:
    def __init__(self, max_runtime: Optional[float] = None):
        self.periodic_tasks: List[PeriodicTask] = []
        self._shutdown_event = asyncio.Event()
        self.agent_update_interval = 0.1
        self.max_runtime = max_runtime

    def add_periodic_task(self, coro_func: Callable, interval: float, name: Optional[str] = None):
        self.periodic_tasks.append(PeriodicTask(coro_func, interval, name))

    def setup_signal_handlers(self):
        loop = asyncio.get_running_loop()
        loop.add_signal_handler(signal.SIGINT, self._handle_signal)
        loop.add_signal_handler(signal.SIGTERM, self._handle_signal)

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

    async def shutdown(self, *tasks):
        for task in tasks:
            if task:
                task.cancel()
        for task in self.periodic_tasks:
            task.cancel()
        print("App: shutdown complete.")


class SessionApp(App):
    def __init__(self, session: Session, max_runtime: Optional[float] = None, sport: Optional[Squad] = None):
        super().__init__(max_runtime)
        self.session = session
        self._manager = sport or BaseGroupManager(name="session_manager")

    @property
    def manager(self):
        # Read-only access for introspection/testing, not for mutation
        return self._manager

    def add(self, obj: Any, group: Optional[str] = None):
        # Duck-typed: if obj has a 'banker' attribute, treat as banker, else agent, else use group
        if group:
            self._manager.add(group, obj)
        elif hasattr(obj, 'is_banker') and getattr(obj, 'is_banker'):
            self._manager.add('bankers', obj)
        else:
            self._manager.add('agents', obj)
        # Forward to session if it supports add()
        if hasattr(self.session, 'add'):
            self.session.add(obj, group=group)

    async def setup(self):
        await self.session.setup()

    async def _update_all_agents(self):
        # Process periodic_agents first, then the rest
        periodic_agents = self._manager.get('periodic_agents')
        for agent in periodic_agents:
            if hasattr(agent, 'update'):
                await agent.update()
        # Now process agents not in periodic_agents
        other_agents = self._manager.difference('agents', 'periodic_agents')
        for agent in other_agents:
            if hasattr(agent, 'update'):
                await agent.update()

    async def _update_agents(self):
        while not self._shutdown_event.is_set():
            try:
                await self._update_all_agents()
            except Exception as e:
                print(f"Error updating agents: {e}")
            await asyncio.sleep(self.agent_update_interval)

    async def run(self):
        self.setup_signal_handlers()
        await self.setup()
        agent_update_task = asyncio.create_task(self._update_agents())
        await self._start_periodic_tasks()
        max_runtime_task = None
        if self.max_runtime is not None:
            max_runtime_task = asyncio.create_task(self._max_runtime_task())
        try:
            await self._shutdown_event.wait()
        finally:
            await self.shutdown(agent_update_task, max_runtime_task)


class BankingSessionApp(SessionApp):
    def add_banker_agent(self, banker: Any):
        self.session.add_banker_agent(banker)
        self._manager.add('bankers', banker)
        # Also add to the session's own group if it exists
        if hasattr(self.session, 'manager'):
            self.session.manager.add('bankers', banker)

    def add(self, obj: Any, group: Optional[str] = None):
        # Prefer explicit group, else banker/agent detection
        if group:
            self._manager.add(group, obj)
        elif hasattr(obj, 'is_banker') and getattr(obj, 'is_banker'):
            self._manager.add('bankers', obj)
        else:
            self._manager.add('agents', obj)
        if hasattr(self.session, 'add'):
            self.session.add(obj, group=group)

    async def _update_banker(self):
        for banker in self._manager.get('bankers'):
            if hasattr(banker, 'update'):
                await banker.update()  # type: ignore

    async def _update_agents(self):
        while not self._shutdown_event.is_set():
            try:
                await self._update_all_agents()
                await self._update_banker()
            except Exception as e:
                print(f"Error updating agents: {e}")
            await asyncio.sleep(self.agent_update_interval)
