# Copyright (c) 2025 Scott Russell
# SPDX-License-Identifier: MIT

"""
Temporal multi-axis coordination module.

Provides a coordinator that coordinates temporal progression with other axes.
The specific axes are composed by the caller, making this more flexible
and reusable for different musical applications.
"""

from .axis import AxisCoordinator
from .multi_axis import MultiAxisCoordinator
from .temporal import TemporalCoordinator
from typing import Optional, Dict, Any, Callable


class TemporalMultiAxisCoordinator(MultiAxisCoordinator):
    """
    A multi-axis coordinator that coordinates temporal progression with other axes.

    This class provides a temporal coordinator as the primary axis and allows
    other axes to be added and coordinated. The specific coordination rules
    can be customized based on the application needs.
    """

    def __init__(self, namespace: str, logger, bpm: float = 120.0,
                 time_signature: tuple = (4, 4)):
        """
        Initialize a TemporalMultiAxisCoordinator.

        Args:
            namespace: The namespace for this peer
            logger: Logger instance
            bpm: Initial beats per minute
            time_signature: Initial time signature
        """
        super().__init__(namespace, logger, redis_prefix="temporal_multiaxis")

        # Create and add the temporal coordinator as the primary axis
        self._temporal_coordinator = TemporalCoordinator(
            namespace, logger, bpm, time_signature)
        self.add_axis_coordinator(self._temporal_coordinator)

    @property
    def temporal_coordinator(self) -> TemporalCoordinator:
        """Access to the temporal coordinator."""
        return self._temporal_coordinator

    def get_axis_coordinator(self, axis_name: str) -> Optional[AxisCoordinator]:
        """Get a specific axis coordinator by name."""
        return self._axis_coordinators.get(axis_name)

    def set_tempo(self, bpm: float):
        """Set the tempo of the temporal coordinator."""
        self._temporal_coordinator.set_bpm(bpm)
        self.logger.info(f"Tempo set to {bpm} BPM")

    def set_time_signature(self, numerator: int, denominator: int):
        """Set the time signature of the temporal coordinator."""
        self._temporal_coordinator.set_time_signature(numerator, denominator)
        self.logger.info(f"Time signature set to {numerator}/{denominator}")

    def add_temporal_coordination_rule(self, rule: Callable[[Dict[str, Any]], Dict[str, Any]]):
        """
        Add a coordination rule that specifically works with temporal data.

        The rule function receives the impulses dict and should return the modified dict.
        It can assume that 'temporal' will be present in the impulses.
        """
        def temporal_wrapper(impulses: Dict[str, Any]) -> Dict[str, Any]:
            if "temporal" in impulses:
                return rule(impulses)
            return impulses

        self.add_coordination_rule(temporal_wrapper)

    def build_conductor_state_for_tick(self, tick: int) -> dict:
        """
        Build comprehensive conductor state for a specific tick.

        Combines temporal and other axis information into conductor-friendly format.
        """
        base_state = self.build_state_for_tick(tick)

        # Extract temporal state for easy access
        temporal_state = base_state["axis_states"].get("temporal", {})

        # Build conductor-ready state with temporal information
        conductor_ready = {
            "bpm": self._temporal_coordinator.bpm,
            "time_signature": self._temporal_coordinator.time_signature,
            "measure": temporal_state.get("impulse", {}).get("measure", 1),
            "beat": temporal_state.get("impulse", {}).get("beat", 1),
        }

        # Add any other axis states to conductor_ready
        for axis_name, axis_state in base_state["axis_states"].items():
            if axis_name != "temporal":
                conductor_ready[f"{axis_name}_state"] = axis_state

        return {
            "tick": tick,
            "temporal": temporal_state,
            "axis_states": base_state["axis_states"],
            "coordination": base_state["coordination"],
            "conductor_ready": conductor_ready
        }

    def __str__(self):
        temporal_str = str(self._temporal_coordinator)
        other_axes = [
            str(coordinator) for name, coordinator in self._axis_coordinators.items() if name != "temporal"]
        if other_axes:
            return f"🎭 MultiAxis: {temporal_str} | {' | '.join(other_axes)}"
        return f"🎭 Temporal: {temporal_str}"
