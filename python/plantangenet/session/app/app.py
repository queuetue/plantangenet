from plantangenet.squad.chocolate import ChocolateSquad
import asyncio
from typing import Optional, Any
from .base import BaseApp
from ..session import Session
from ...policy.identity import Identity
from ...policy.policy import Policy


class App(BaseApp):
    def __init__(self, session_id, max_runtime: Optional[float] = None):
        super().__init__(max_runtime)
        dummy_identity = Identity(
            id="dummy", nickname="dummy", metadata={}, roles=[])
        dummy_policy = Policy(logger=None, namespace="dummy")
        self._session = Session(
            id=session_id, policy=dummy_policy, identity=dummy_identity)
        self._manager = ChocolateSquad()

    @property
    def manager(self):
        return self._manager

    @property
    def session(self):
        return self._session

    @property
    def dust(self) -> float:
        """Get the current dust balance from the session."""
        return self._session.get_dust_balance() or 0.0

    def add(self, obj: Any, group: Optional[str] = None):
        # Duck-typed: if obj has a 'banker' attribute, treat as banker, else agent, else use group
        if group:
            self._manager.add(group, obj)
        elif hasattr(obj, 'is_banker') and getattr(obj, 'is_banker'):
            self._manager.add('bankers', obj)
        else:
            self._manager.add('agents', obj)
        # Forward to session if it supports add()
        if hasattr(self._session, 'add'):
            self._session.add(obj, group=group)  # type: ignore

    async def setup(self, loop=None):
        await self._session.setup()
        await super().setup(loop=loop)

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
        """Main run loop for the chocolate app."""
        await self.setup()
        agent_update_task = asyncio.create_task(self._update_agents())
        max_runtime_task = None
        if self.max_runtime is not None:
            max_runtime_task = asyncio.create_task(self._max_runtime_task())

        try:
            await self._shutdown_event.wait()
        finally:
            await self.shutdown(agent_update_task, max_runtime_task)
