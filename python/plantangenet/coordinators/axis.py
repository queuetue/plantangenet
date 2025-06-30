# Copyright (c) 1998-2025 Scott Russell
# SPDX-License-Identifier: MIT

"""
Base leadership classes for axis coordination.

Provides the fundamental abstractions for creating leaders that have
authoritative opinions about impulses along an axis and coordinate
those opinions with subscribers.
"""

import json
from abc import abstractmethod
from typing import Any, Callable, Coroutine, Optional, Union
from plantangenet.mixins.topics.topic_registry import on_topic


class AxisCoordinator():
    """
    A peer that has authoritative opinions about impulses on an axis for subscribers.

    This base class provides the framework for creating leaders that:
    - Track position along a specific axis (temporal, pitch, intensity, etc.)
    - Generate authoritative impulses about that axis
    - Broadcast opinions to subscribers
    - Handle external control commands

    Subclasses must implement generate_impulse_at_position() to define
    their specific axis behavior.
    """

    def __init__(self, axis_name: str = "default_axis"):
        """
        Initialize an AxisCoordinator.

        Args:
            axis_name: Name of the axis this leader manages (e.g., "temporal", "pitch")
            redis_prefix: Optional Redis prefix, defaults to axis_name
        """
        self._axis_name = axis_name
        self._current_position = 0.0
        self._impulse_rate = 1.0
        self._subscribers = set()
        self._axis_state = {}
        self._active = True

    @property
    @abstractmethod
    def logger(self) -> Any:
        """Return the logger instance for this peer."""
        raise NotImplementedError(
            "Logger must be implemented in the subclass."
        )

    @property
    def axis_name(self) -> str:
        """The name of the axis this coordinator manages."""
        return self._axis_name

    @axis_name.setter
    def axis_name(self, name: str):
        """Set the name of the axis this coordinator manages."""
        self._axis_name = name

    @property
    def current_position(self) -> float:
        """Current position along the axis."""
        return self._current_position

    @property
    def active(self) -> bool:
        """Whether this leader is actively generating impulses."""
        return self._active

    def set_position(self, position: float):
        """Set the current position along the axis."""
        self._current_position = position

    def set_impulse_rate(self, rate: float):
        """Set the rate at which impulses are generated."""
        self._impulse_rate = rate

    def activate(self):
        """Activate impulse generation."""
        self._active = True

    def deactivate(self):
        """Deactivate impulse generation."""
        self._active = False

    @abstractmethod
    def generate_impulse_at_position(self, position: float) -> dict:
        """
        Generate an authoritative opinion about this axis position.

        Args:
            position: Position along the axis to generate impulse for

        Returns:
            Dictionary containing the impulse data

        This is the core method that subclasses must implement to define
        their specific axis behavior.
        """
        raise NotImplementedError(
            "Subclasses must implement generate_impulse_at_position")

    async def broadcast_impulse(self, impulse: dict):
        """
        Share impulse with subscribers.

        Args:
            impulse: The impulse data to broadcast
        """
        topic = f"axis.{self._axis_name}.impulse"
        await self.publish(topic, json.dumps(impulse).encode('utf-8'))

    # async def on_frame(self):
    #     """Default frame handler - generates and broadcasts impulses."""
    #     if self._active:
    #         # Generate impulse for current position
    #         impulse = self.generate_impulse_at_position(self._current_position)
    #         impulse["axis"] = self._axis_name
    #         impulse["position"] = self._current_position
    #         impulse["timestamp"] = self._stamp()

    #         # Broadcast to subscribers
    #         await self.broadcast_impulse(impulse)

    def build_state_for_tick(self, tick: int) -> dict:
        """
        Build state for a specific tick (required by Omni).

        Converts tick to axis position and generates impulse.
        """
        # Convert tick to position - subclasses may override this conversion
        position = self.tick_to_position(tick)
        impulse = self.generate_impulse_at_position(position)

        return {
            "axis": self._axis_name,
            "position": position,
            "tick": tick,
            "impulse": impulse,
            "active": self._active
        }

    def tick_to_position(self, tick: int) -> float:
        """
        Convert a tick to a position along this axis.

        Default implementation treats ticks as direct position values.
        Subclasses can override for axis-specific conversions.
        """
        return float(tick)

    @on_topic("axis.*.set_position")
    async def handle_set_position(self, message):
        """Handle external position set commands."""
        try:
            data = json.loads(message.data.decode())
            axis = data.get("axis")

            # Only respond to our axis
            if axis == self._axis_name:
                position = data.get("position", 0.0)
                self.set_position(position)
                self.logger.info(
                    f"{self._axis_name} position set to {position}")
        except Exception as e:
            self.logger.error(f"Error setting position: {e}")

    @on_topic("axis.*.activate")
    async def handle_activate(self, message):
        """Handle activation commands."""
        try:
            data = json.loads(message.data.decode())
            axis = data.get("axis")

            if axis == self._axis_name:
                self.activate()
                self.logger.info(f"{self._axis_name} activated")
        except Exception as e:
            self.logger.error(f"Error activating: {e}")

    @on_topic("axis.*.deactivate")
    async def handle_deactivate(self, message):
        """Handle deactivation commands."""
        try:
            data = json.loads(message.data.decode())
            axis = data.get("axis")

            if axis == self._axis_name:
                self.deactivate()
                self.logger.info(f"{self._axis_name} deactivated")
        except Exception as e:
            self.logger.error(f"Error deactivating: {e}")

    def __str__(self):
        status = "🟢" if self._active else "🔴"
        return f"{status} {self._axis_name} @ {self._current_position:.2f}"

    @abstractmethod
    async def publish(self, topic: str, data: Union[str, bytes, dict]) -> Optional[list]:
        """Publish a message to the topic with the given data."""

    @abstractmethod
    async def subscribe(self, topic: str, callback: Callable[..., Coroutine[Any, Any, Any]]) -> Any:
        """Subscribe to a topic with the given callback."""

    @abstractmethod
    def _stamp(self):
        """
        Generate a timebase stamp for the current time.

        This should be implemented to provide a consistent time reference.
        """
        raise NotImplementedError(
            "Timebase stamp generation must be implemented in the subclass."
        )
