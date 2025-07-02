# Copyright (c) 1998-2025 Scott Russell
# SPDX-License-Identifier: MIT

from typing import List, Dict, Any, Optional, Callable, Union
import uuid
from .cursor import Cursor
from .agent import Agent
from .policy.base import Policy


class Session:
    """
    Represents a policy-bound lifecycle and trust boundary.
    Manages Agents and Cursors, and interfaces with Compositors.
    """

    def __init__(self,
                 session_id: Optional[str] = None,
                 metadata: Optional[Dict[str, Any]] = None,
                 policy: Optional[Policy] = None):
        self.session_id = session_id or str(uuid.uuid4())
        self.metadata = metadata or {}

        self.agents: List[Agent] = []
        self.cursors: List[Cursor] = []
        self.policy = policy

        self.on_change_callbacks: List[Callable[['Session'], None]] = []

    # Agent management
    def add_agent(self, agent: Agent):
        self.agents.append(agent)
        self._notify_change()

    def remove_agent(self, agent: Agent):
        if agent in self.agents:
            self.agents.remove(agent)
            self._notify_change()

    def list_agents(self) -> List[Agent]:
        return list(self.agents)

    async def update_agents(self):
        for agent in self.agents:
            await agent.update()

    # Cursor management
    def add_cursor(self, agent: Agent, cursor: Cursor):
        if self.evaluate_policy(agent, "add_cursor", resource=cursor.axes):
            cursor.owner = agent.id
            self.cursors.append(cursor)
            self._notify_change()
        else:
            raise PermissionError("Policy denied adding cursor.")

    def remove_cursor(self, cursor: Cursor):
        if cursor in self.cursors:
            self.cursors.remove(cursor)
            self._notify_change()

    def list_cursors(self) -> List[Cursor]:
        return list(self.cursors)

    def get_relevant_frames(self, buffer, axis_filter: Optional[List[str]] = None) -> List[Any]:
        frames = []
        for cursor in self.cursors:
            for tick in range(cursor.tick_range[0], cursor.tick_range[1] + 1):
                frame = buffer.get_frame(tick)
                if frame:
                    if axis_filter:
                        filtered_axes = {
                            a: f for a, f in frame.axes.items() if a in axis_filter}
                        if filtered_axes:
                            frames.append((tick, filtered_axes))
                    else:
                        frames.append(frame)
        return frames

    # # Policy evaluation
    def evaluate_policy(self, identity: Union[Agent, str], action: str, resource: Any, context: Optional[dict] = None) -> bool:
        # if self.policy:
        #     return self.policy.evaluate(identity, action, resource, context).allowed
        return True

    # Lifecycle management
    async def setup(self):
        pass

    async def teardown(self):
        self.agents.clear()
        self.cursors.clear()

    # Reactive hooks
    def add_on_change_callback(self, callback: Callable[['Session'], None]):
        self.on_change_callbacks.append(callback)

    def _notify_change(self):
        for callback in self.on_change_callbacks:
            callback(self)
