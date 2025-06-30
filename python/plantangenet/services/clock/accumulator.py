# Copyright (c) 1998-2025 Scott Russell
# SPDX-License-Identifier: MIT

class Accumulator:
    def __init__(self, cycle_length: float, running=True, repeating=False):
        """
        Accumulator for managing time-based events in a loop.
        :param cycle_length: The number of frames in one loop cycle.
        :param running: If True, the accumulator is active and will accumulate deltas.
        :param repeating: If True, the accumulator will repeat cycles.
        """
        self._stamp = 0.0
        self._cycles = 0
        self._cycle_length = cycle_length
        self._running = running
        self._repeating = repeating

    def __str__(self):
        return f"Accumulator(stamp={self._stamp}, len={self._cycle_length}, repeat={self._repeating}, , cycles={self._cycles})"

    def accumulate(self, delta: float):
        frame_duration = 1.0 / self._cycle_length
        if self._running:
            self._stamp += delta
            if self._stamp >= frame_duration:
                if self._repeating:
                    while self._stamp >= frame_duration:
                        self._stamp -= frame_duration
                        self._cycles += 1
                else:
                    self._stamp = 0.0

    def to_dict(self):
        return {
            "cycle_length": self._cycle_length,
            "running": self._running,
            "repeating": self._repeating,
            "accumulator": self._stamp,
            "cycles": self._cycles
        }

    def reset(self):
        self._stamp = 0.0
        self._cycles = 0

    @property
    def running(self):
        """Return whether the accumulator is running."""
        return self._running

    @property
    def repeating(self):
        """Return whether the accumulator is repeating."""
        return self._repeating

    @property
    def delta(self):
        """Return the cycle length (delta)."""
        return self._cycle_length

    def get_current_count(self):
        """Return the current count/cycles completed."""
        return self._cycles

    def get_current_stamp(self):
        """Return the current accumulator stamp."""
        return self._stamp
