# Copyright (c) 1998-2025 Scott Russell
# SPDX-License-Identifier: MIT

"""
Temporal axis coordinator - specialized for time-based progression.

Provides coordinators that understand musical time concepts like tempo,
beats, measures, and time signatures.
"""

from .axis import AxisCoordinator


class TemporalCoordinator(AxisCoordinator):
    """
    A coordinator specialized for temporal (time-based) axis coordination.

    This coordinator understands musical time concepts and can generate
    impulses based on tempo, beats, measures, and time signatures.
    It serves as a foundation for musical conductors.
    """

    def __init__(self, namespace: str, logger, bpm: float = 120.0, time_signature: tuple = (4, 4)):
        """
        Initialize a TemporalCoordinator.

        Args:
            namespace: The namespace for this peer
            logger: Logger instance
            bpm: Beats per minute
            time_signature: Time signature as (numerator, denominator)
        """
        super().__init__(namespace, logger, "temporal", redis_prefix="temporal")

        self._bpm = bpm
        self._time_signature = time_signature
        self._ticks_per_beat = 96  # Standard MIDI resolution
        self._measure_count = 0
        self._beat_count = 0

    @property
    def bpm(self) -> float:
        """Current beats per minute."""
        return self._bpm

    @property
    def time_signature(self) -> tuple:
        """Current time signature."""
        return self._time_signature

    @property
    def ticks_per_beat(self) -> int:
        """Ticks per beat resolution."""
        return self._ticks_per_beat

    def set_bpm(self, bpm: float):
        """Set the tempo in beats per minute."""
        if 20 <= bpm <= 300:  # Reasonable tempo range
            self._bpm = bpm
            self.logger.info(f"Tempo set to {bpm} BPM")
        else:
            self.logger.warning(f"Invalid BPM: {bpm}, must be between 20-300")

    def set_time_signature(self, numerator: int, denominator: int):
        """Set the time signature."""
        self._time_signature = (numerator, denominator)
        self.logger.info(f"Time signature set to {numerator}/{denominator}")

    def tick_to_position(self, tick: int) -> float:
        """Convert tick to temporal position (beats)."""
        return tick / self._ticks_per_beat

    def position_to_measure_and_beat(self, position: float) -> tuple:
        """
        Convert position to measure and beat numbers.

        Args:
            position: Position in beats

        Returns:
            Tuple of (measure, beat) starting from 1
        """
        beats_per_measure = self._time_signature[0]
        total_beats = int(position)

        measure = (total_beats // beats_per_measure) + 1
        beat = (total_beats % beats_per_measure) + 1

        return measure, beat

    def generate_impulse_at_position(self, position: float) -> dict:
        """
        Generate temporal impulse with musical timing information.

        Args:
            position: Position along the temporal axis (in beats)

        Returns:
            Dictionary containing temporal impulse data
        """
        measure, beat = self.position_to_measure_and_beat(position)

        # Calculate fractional beat for sub-beat timing
        fractional_beat = position % 1.0

        # Determine if this is a strong beat (downbeat)
        is_downbeat = beat == 1
        is_strong_beat = beat in [
            1, 3] if self._time_signature[0] == 4 else beat == 1

        return {
            "position_beats": position,
            "measure": measure,
            "beat": beat,
            "fractional_beat": fractional_beat,
            "bpm": self._bpm,
            "time_signature": self._time_signature,
            "is_downbeat": is_downbeat,
            "is_strong_beat": is_strong_beat,
            "ticks_per_beat": self._ticks_per_beat,
            "beats_per_measure": self._time_signature[0]
        }

    def __str__(self):
        status = "🟢" if self._active else "🔴"
        measure, beat = self.position_to_measure_and_beat(
            self._current_position)
        return f"{status} Temporal {self._bpm}BPM {self._time_signature[0]}/{self._time_signature[1]} M{measure}:B{beat}"
