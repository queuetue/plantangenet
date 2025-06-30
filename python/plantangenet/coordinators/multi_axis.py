# Copyright (c) 1998-2025 Scott Russell
# SPDX-License-Identifier: MIT

"""
Base classes for axis coordination.

Provides the fundamental abstractions for creating leaders that have
authoritative opinions about impulses along an axis and coordinate
those opinions with subscribers.
"""

from abc import abstractmethod
from collections.abc import Coroutine
import json
from typing import Any, Dict, List, Optional, Callable, Union
from plantangenet.mixins.topics.topic_registry import on_topic
from .axis import AxisCoordinator


class MultiAxisCoordinator():
    """
    Coordinates multiple axis coordinators for complex multidimensional authority.

    This class manages a collection of AxisCoordinator instances and coordinates
    their impulses according to configurable rules. It can:
    - Add/remove axis coordinators dynamically
    - Apply coordination rules across axes
    - Generate unified impulses from multiple axes
    - Handle cross-axis dependencies and interactions
    """

    def __init__(self, ):
        """
        Initialize a MultiAxisCoordinator.

        Args:
            namespace: The namespace for this peer
            logger: Logger instance
            redis_prefix: Redis prefix for storage
        """

        self._axis_coordinators: Dict[str, AxisCoordinator] = {}
        self._coordination_rules: List[Callable] = []
        self._cross_axis_state = {}

    @abstractmethod
    def _stamp(self):
        """
        Generate a timebase stamp for the current time.

        This should be implemented to provide a consistent time reference.
        """
        raise NotImplementedError(
            "Timebase stamp generation must be implemented in the subclass."
        )

    @property
    @abstractmethod
    def logger(self) -> Any:
        """Return the logger instance for this peer."""
        raise NotImplementedError(
            "Logger must be implemented in the subclass."
        )

    def add_axis_coordinator(self, coordinator: AxisCoordinator):
        """
        Add an axis coordinator to the coordination group.

        Args:
            coordinator: The AxisCoordinator instance to add
        """
        self._axis_coordinators[coordinator.axis_name] = coordinator
        self.logger.info(
            f"Added {coordinator.axis_name} coordinator to coordination")

    def remove_axis_coordinator(self, axis_name: str):
        """
        Remove an axis coordinator from the coordination group.

        Args:
            axis_name: Name of the axis to remove
        """
        if axis_name in self._axis_coordinators:
            del self._axis_coordinators[axis_name]
            self.logger.info(
                f"Removed {axis_name} coordinator from coordination")

    def add_coordination_rule(self, rule: Callable):
        """
        Add a coordination rule function.

        Args:
            rule: Function that takes (impulses_dict) and returns modified impulses_dict
        """
        self._coordination_rules.append(rule)

    def get_axis_coordinator(self, axis_name: str) -> Optional[AxisCoordinator]:
        """Get a specific axis coordinator by name."""
        return self._axis_coordinators.get(axis_name)

    def get_all_axis_coordinators(self) -> Dict[str, AxisCoordinator]:
        """Get all axis coordinators."""
        return self._axis_coordinators.copy()

    async def coordinate_impulses(self, stamp=None) -> dict:
        """
        Generate coordinated impulses across all axes.

        Returns:
            Dictionary with coordinated impulse data from all axes
        """
        # Collect impulses from all axis coordinators
        impulses = {}
        for axis_name, coordinator in self._axis_coordinators.items():
            if coordinator.active:
                impulse = coordinator.generate_impulse_at_position(
                    coordinator.current_position)
                impulses[axis_name] = {
                    "impulse": impulse,
                    "position": coordinator.current_position,
                    "axis_type": coordinator.__class__.__name__,
                    "active": coordinator.active
                }

        # Apply coordination rules
        coordinated_impulses = self._apply_coordination_rules(impulses)

        return {
            "coordinated_impulses": coordinated_impulses,
            "timestamp": stamp or self._stamp(),
            "active_axes": list(impulses.keys())
        }

    def _apply_coordination_rules(self, impulses: dict) -> dict:
        """
        Apply coordination rules to impulse collection.

        Args:
            impulses: Dictionary of impulses from each axis

        Returns:
            Modified impulses dictionary
        """
        coordinated = impulses.copy()

        # Apply each coordination rule in sequence
        for rule in self._coordination_rules:
            try:
                coordinated = rule(coordinated)
            except Exception as e:
                self.logger.error(f"Error applying coordination rule: {e}")

        return coordinated

    # async def on_frame(self):
    #     """Default frame handler - coordinates and broadcasts unified impulses."""
    #     # Generate coordinated impulses
    #     coordinated = await self.coordinate_impulses()

    #     # Broadcast unified coordination
    #     topic = "multiaxis.coordination"
    #     await self.publish(topic, json.dumps(coordinated).encode('utf-8'))

    def build_state_for_tick(self, tick: int) -> dict:
        """
        Build coordinated state for a specific tick.

        Generates state from all axis coordinators and applies coordination.
        """
        axis_states = {}

        for axis_name, coordinator in self._axis_coordinators.items():
            axis_states[axis_name] = coordinator.build_state_for_tick(tick)

        return {
            "tick": tick,
            "axis_states": axis_states,
            "coordination": self._apply_coordination_rules(axis_states),
            "active_axes": [name for name, coordinator in self._axis_coordinators.items() if coordinator.active]
        }

    @on_topic("multiaxis.add_coordinator")
    async def handle_add_coordinator(self, message):
        """Handle requests to add axis coordinators."""
        try:
            data = json.loads(message.data.decode())
            # This would need implementation based on how coordinators are serialized/referenced
            self.logger.info("Add coordinator request received")
        except Exception as e:
            self.logger.error(f"Error adding coordinator: {e}")

    @on_topic("multiaxis.set_coordination_rule")
    async def handle_set_coordination_rule(self, message):
        """Handle coordination rule updates."""
        try:
            data = json.loads(message.data.decode())
            # This would need implementation for rule serialization
            self.logger.info("Coordination rule update received")
        except Exception as e:
            self.logger.error(f"Error updating coordination rule: {e}")

    def __str__(self):
        active_count = sum(
            1 for coordinator in self._axis_coordinators.values() if coordinator.active)
        total_count = len(self._axis_coordinators)
        return f"🎭 MultiAxis ({active_count}/{total_count} active) {list(self._axis_coordinators.keys())}"

    @abstractmethod
    async def publish(self, topic: str, data: Union[str, bytes, dict]) -> Optional[list]:
        """Publish a message to the topic with the given data."""

    @abstractmethod
    async def subscribe(self, topic: str, callback: Callable[..., Coroutine[Any, Any, Any]]) -> Any:
        """Subscribe to a topic with the given callback."""
