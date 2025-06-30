# Copyright (c) 1998-2025 Scott Russell
# SPDX-License-Identifier: MIT

from abc import abstractmethod
from dataclasses import dataclass
from enum import Enum
from random import randint
from plantangenet.mixins.topics import on_topic
from .base import OceanMixinBase

CHOICES = ['🪨 ', '🧻', '✂️ ', '🦎', '🖖']


class WinLoseDraw(Enum):
    UNKNOWN = None
    CONTEST = 100
    WIN = 1
    LOSE = 2
    DRAW = 3
    CHEAT = 110
    ERROR = 120


def a_vs_b(a: str, b: str) -> WinLoseDraw:
    """Determine if choice A beats choice B in Rock-Paper-Scissors-Lizard-Spock."""
    if a == b:
        return WinLoseDraw.DRAW
    if (a == '🪨' and b in ['✂️', '🦎']) or \
       (a == '🧻' and b in ['🪨', '🖖']) or \
       (a == '✂️' and b in ['🧻', '🦎']) or \
       (a == '🦎' and b in ['🧻', '🖖']) or \
       (a == '🖖' and b in ['✂️', '🦎']):
        return WinLoseDraw.WIN
    return WinLoseDraw.LOSE


class RoxMixin(OceanMixinBase):

    def __init__(self):
        OceanMixinBase.__init__(self)
        self._rox__index = randint(0, len(CHOICES) - 1)
        self._rox__choice = CHOICES[self._rox__index]
        self._rox__winning = WinLoseDraw.UNKNOWN
        self._rox__clock_choice = "X"

    @property
    def status(self) -> dict:
        """Get the status of the Rox mixin."""
        status = super().status
        status["rox"] = {
            "choice": self._rox__choice,
            "winning": self._rox__winning.name,
            "clock_choice": self._rox__clock_choice,
            "index": self._rox__index,
        }
        return status

    @property
    def rox_choice(self) -> str:
        """Get the current Rox choice."""
        return self._rox__choice

    @property
    def rox_winning(self) -> WinLoseDraw:
        """Get the current winning state of Rox."""
        return self._rox__winning

    @property
    def rox_clock_choice(self) -> str:
        """Get the current clock choice in Rox."""
        return self._rox__clock_choice

    @property
    def rox_index(self) -> int:
        """Get the current index of the Rox choice."""
        return self._rox__index

    @property
    def rox_choices(self) -> list:
        """Get the list of Rox choices."""
        return CHOICES

    def choose(self) -> None:
        """Randomly choose a Rox choice."""
        self._rox__index = randint(0, len(CHOICES) - 1)
        self._rox__choice = CHOICES[self._rox__index]
        self._rox__winning = WinLoseDraw.UNKNOWN

    @on_topic("rox.go")
    async def handle_rox_go(self, message: dict):
        self.choose()
        self._rox__choice = message.get("choice", "X")
        if self._rox__choice in CHOICES:
            self._rox__winning = WinLoseDraw.UNKNOWN
        else:
            self._rox__winning = WinLoseDraw.ERROR
        await self.on_rox(message)

    @on_topic("clock.pulse")
    async def handle_clock_pulse(self, message: dict):
        clock_choice = message.get("choice", None)
        if clock_choice:
            self._rox__clock_choice = clock_choice
            self._rox__winning = a_vs_b(
                self._rox__choice, self._rox__clock_choice)
        else:
            self._rox__clock_choice = "X"
            self._rox__winning = WinLoseDraw.ERROR
        self._rox__index = randint(0, len(CHOICES) - 1)
        self._rox__choice = CHOICES[self._rox__index]

        if self._rox__winning == WinLoseDraw.WIN:
            await self.on_rox_win(message)
        elif self._rox__winning == WinLoseDraw.LOSE:
            await self.on_rox_loss(message)
        elif self._rox__winning == WinLoseDraw.DRAW:
            await self.on_rox_draw(message)
        else:
            self.logger.error(
                f"Unexpected Rox winning state: {self._rox__winning} for choice {self._rox__choice} vs clock choice {self._rox__clock_choice}")

    @abstractmethod
    async def on_rox(self, message: dict):
        """
        Handle a Rox message.
        This method should be implemented by subclasses to define specific Rox handling logic.
        """

    @abstractmethod
    async def on_rox_draw(self, message: dict):
        """
        Handle a Rox draw message.
        This method should be implemented by subclasses to define specific Rox draw handling logic.
        """

    @abstractmethod
    async def on_rox_win(self, message: dict):
        """
        Handle a Rox win message.
        This method should be implemented by subclasses to define specific Rox win handling logic.
        """

    @abstractmethod
    async def on_rox_loss(self, message: dict):
        """
        Handle a Rox loss message.
        This method should be implemented by subclasses to define specific Rox loss handling logic.
        """
