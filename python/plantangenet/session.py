# Copyright (c) 1998-2025 Scott Russell
# SPDX-License-Identifier: MIT

import uuid
from typing import List, Dict, Any, Optional, Callable, Union
from plantangenet.policy.identity import Identity
from plantangenet.policy.vanilla import Vanilla
from plantangenet.policy.storage_mixin import PolicyStorageMixin

from .cursor import Cursor
from .agents.agent import Agent
from .banker import Banker, NullBanker


class Session(PolicyStorageMixin):
    """
    Represents a policy-bound lifecycle and trust boundary.
    Manages Agents (including Banker agents), Cursors, and interfaces with Compositors.
    Only session_id, metadata, identity_key, and policy_key are persisted.
    """

    def __init__(self,
                 session_id: Optional[str] = None,
                 metadata: Optional[Dict[str, Any]] = None,
                 policy: Optional[Vanilla] = None,
                 identity: Optional[Identity] = None,
                 identity_key: Optional[str] = None,
                 policy_key: Optional[str] = None,
                 storage_backend: Any = None,
                 banker: Optional[Banker] = None):
        self.session_id = session_id or str(uuid.uuid4())
        self.metadata = metadata or {}
        self.identity_key = identity_key
        self.policy_key = policy_key
        self._identity = identity
        self._policy = policy
        self.agents: List[Agent] = []
        self.cursors: List[Cursor] = []
        self.on_change_callbacks: List[Callable[['Session'], None]] = []

        # Financial services - managed through banker agent
        self._banker = banker or NullBanker()

        # Set storage backend for all managed persistable types
        if storage_backend:
            self.set_storage_backend(storage_backend)

    @classmethod
    def set_storage_backend(cls, backend):
        cls.storage_backend = backend
        Identity.storage_backend = backend
        Vanilla.storage_backend = backend
        Cursor.storage_backend = backend

    @property
    def identity(self) -> Optional[Identity]:
        if self._identity:
            return self._identity
        if self.identity_key and Identity.storage_backend:
            # Async load not supported in property, so warn user
            return None
        return None

    @property
    def policy(self) -> Optional[Vanilla]:
        if self._policy:
            return self._policy
        if self.policy_key and Vanilla.storage_backend:
            # Async load not supported in property, so warn user
            return None
        return None

    def persisted_state(self) -> dict:
        return {
            "session_id": self.session_id,
            "metadata": self.metadata,
            "identity_key": self.identity_key,
            "policy_key": self.policy_key,
            "cursor_keys": [c.id for c in self.cursors],
        }

    async def persist_cursors(self):
        if not Cursor.storage_backend:
            raise RuntimeError("No storage backend for Cursor.")
        for cursor in self.cursors:
            await cursor.store(cursor.id, cursor.__dict__)

    @staticmethod
    async def rehydrate_object_list(keys, cls):
        objs = []
        if not cls.storage_backend:
            return objs
        for k in keys:
            data = await cls.storage_backend.load(k)
            if data:
                objs.append(cls(**data))
        return objs

    @classmethod
    async def rehydrate(cls, session_key: str, backend=None, logger=None, namespace=None):
        backend = backend or cls.storage_backend
        if not backend:
            raise RuntimeError(
                "No storage backend configured for Session rehydration.")
        state = await backend.load(session_key)
        if not state:
            raise ValueError(f"No session found for key {session_key}")
        identity = None
        policy = None
        cursors = []
        if state.get("identity_key") and Identity.storage_backend:
            identity_data = await Identity.storage_backend.load(
                state["identity_key"]  # type: ignore[union-attr]
            )
            if identity_data:
                identity = Identity(**identity_data)
        if state.get("policy_key") and Vanilla.storage_backend:
            policy_data = await Vanilla.storage_backend.load(
                state["policy_key"]  # type: ignore[union-attr]
            )
            if policy_data:
                policy = Vanilla(logger=logger, namespace=namespace or policy_data.get(
                    "namespace", "default"))
        if state.get("cursor_keys") and Cursor.storage_backend:
            cursors = await cls.rehydrate_object_list(state["cursor_keys"], Cursor)
        session = cls(
            session_id=state["session_id"],
            metadata=state["metadata"],
            identity=identity,
            policy=policy,
            identity_key=state.get("identity_key"),
            policy_key=state.get("policy_key")
        )
        session.cursors = cursors
        return session

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

    # Banker management methods
    @property
    def banker(self) -> Banker:
        """Get the session's banker."""
        return self._banker

    def set_banker(self, banker: Banker):
        """Set the session's banker."""
        self._banker = banker
        self._notify_change()

    def add_banker_agent(self, banker_agent: Agent):
        """
        Add a banker agent to the session and set it as the primary banker.

        Args:
            banker_agent: An agent that implements the Banker protocol
        """
        if not isinstance(banker_agent, Banker):
            raise ValueError("Agent must implement Banker protocol")

        self.add_agent(banker_agent)
        self.set_banker(banker_agent)

    def get_banker_agents(self) -> List[Agent]:
        """Get all agents that implement the Banker protocol."""
        return [agent for agent in self.agents if isinstance(agent, Banker)]

    # Financial delegation methods (delegate to banker)
    def get_dust_balance(self) -> int:
        """Get current dust balance from banker."""
        return self._banker.get_balance()

    def can_afford(self, amount: int) -> bool:
        """Check if session can afford an amount."""
        return self._banker.can_afford(amount)

    def get_cost_estimate(self, action: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get cost estimate for an action."""
        return self._banker.get_cost_estimate(action, params)

    def negotiate_transaction(self, action: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Negotiate a transaction with cost options."""
        return self._banker.negotiate_transaction(action, params)

    def commit_transaction(self, action: str, params: Dict[str, Any],
                           selected_cost: Optional[int] = None) -> Dict[str, Any]:
        """Commit a transaction through the banker."""
        result = self._banker.commit_transaction(action, params, selected_cost)

        if result.success:
            self._notify_change()

        return {
            "success": result.success,
            "dust_charged": result.dust_charged,
            "message": result.message,
            "transaction_id": result.transaction_id
        }

    def get_transaction_history(self) -> List[Dict[str, Any]]:
        """Get transaction history from banker."""
        return self._banker.get_transaction_history()
