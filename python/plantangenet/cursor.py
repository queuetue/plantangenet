# Copyright (c) 1998-2025 Scott Russell
# SPDX-License-Identifier: MIT

from typing import List, Tuple, Dict, Any, Optional, Callable
import uuid
from plantangenet.policy.storage_mixin import PolicyStorageMixin


class Cursor(PolicyStorageMixin):
    """
    Represents a region of interest and participates in observation workflows.
    Can be static or dynamically updated by a peer/agent.
    """

    def __init__(
        self,
        axes: List[str],
        tick_range: Tuple[int, int],
        owner: Optional[str] = None,
        dynamic: bool = False,
        metadata: Optional[Dict[str, Any]] = None,
        update_policy: Optional[Callable[['Cursor', Any], bool]] = None,
        id: Optional[str] = None,
        last_observed_state: Optional[Any] = None,  # <-- add this
    ):
        self.id = id or str(uuid.uuid4())
        self.axes = axes
        self.tick_range = tick_range
        self.owner = owner
        self.dynamic = dynamic
        self.metadata = metadata or {}
        self.update_policy = update_policy  # Function to decide if update is needed
        self.last_observed_state = last_observed_state

    def should_update(self, new_state: Any) -> bool:
        """
        Determine if an update/notification is necessary.
        Uses the update_policy if provided, else defaults to 'any change'.
        """
        if self.update_policy:
            return self.update_policy(self, new_state)
        # Default: update if state has changed
        changed = new_state != self.last_observed_state
        return changed

    def observe(self, new_state: Any):
        """
        Observe a new state and update internal record.
        Returns True if an update should be triggered.
        """
        if self.should_update(new_state):
            self.last_observed_state = new_state
            return True
        return False

    def update_region(self, axes: List[str], tick_range: Tuple[int, int]):
        self.axes = axes
        self.tick_range = tick_range

    def __repr__(self):
        return f"<Cursor id={self.id} axes={self.axes} ticks={self.tick_range} owner={self.owner}>"
