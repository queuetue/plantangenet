# Copyright (c) 1998-2025 Scott Russell
# SPDX-License-Identifier: MIT

from abc import abstractmethod
from collections import deque
import random
from typing import Any
from ulid import ULID
from coolname import generate_slug

INITIAL_DISPOSITION = [
    "AESTHETICA IN VIVO",
    "GO SLUG BEARS",
    "GO BEAR SLUGS",
    "GO PLANTANGENET",
]


class Agent():
    """
    This class serves as a base for peers in the Plantangenet Ocean ecosystem,
    providing a unique identifier, namespace management, and basic logging capabilities.

    Initialize the Agent with a unique ID, namespace, and logger.
    :param namespace: The namespace for the peer.
    :param logger: A logger instance for logging messages.

    The Base Peer is expected to be mismanaged by professionals, amateurs and 
    dark actors alike, and it tries to defend it's inputs.

    """

    def __init__(self,
                 namespace: str = "plantangenet",
                 logger: Any = None):
        self._ocean__logger = logger
        self._ocean__id: str = self.fresh_id()
        self._ocean__namespace: str = namespace
        self._ocean__nickname = generate_slug(2)
        self._ocean__disposition = random.choice(INITIAL_DISPOSITION)
        self._ocean__op_cache: deque = deque(maxlen=10000)

    def fresh_id(self) -> str:
        """Generate a new unique ID for this peer."""
        return str(ULID())

    @abstractmethod
    async def update(self) -> bool:
        """Perform periodic update tasks for the peer."""

    @property
    def logger(self) -> Any:
        """Return the logger instance for this peer."""
        return self._ocean__logger

    @property
    def ocean_ready(self):
        """Check if the peer is initialized."""
        return True

    @property
    def namespace(self):
        """Return the namespace of the peer."""
        return self._ocean__namespace

    @property
    def id(self):
        """Return the unique identifier for the peer."""
        return self._ocean__id

    @property
    def short_id(self) -> str:
        """Return a short version of the peer's unique ID."""
        return self._ocean__id[-6:]

    @property
    def name(self) -> str:
        """Return a short version of the peer's unique ID."""
        return self._ocean__nickname

    @property
    def capabilities(self):
        return {
            "message_types": self.message_types,
        }

    @property
    def message_types(self):
        """Return the peer's message types."""
        return set([
            "agent.update",
        ])

    @property
    def disposition(self):
        """Return the peer's disposition."""
        return self._ocean__disposition

    def _ocean__op(self, accepted: bool, operation: str, key: str, value: Any = None, cost: int = 0):
        """
        Log an operation.
        :param accepted: Whether the operation was accepted or rejected.
        :param operation: The type of operation (e.g., "set", "delete").
        :param key: The key involved in the operation.
        :param value: The value involved in the operation, if applicable.
        :param cost: The cost of the operation.
        """

        self._ocean__op_cache.append({
            "agent_id": self._ocean__id,
            "ulid": self.fresh_id(),
            "key": key,
            "accepted": accepted,
            "operation": operation.lower().strip(),
            "value": str(value),
            "cost": cost,
            "committed": False
        })
