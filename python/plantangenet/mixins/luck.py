# Copyright (c) 1998-2025 Scott Russell
# SPDX-License-Identifier: MIT

from abc import abstractmethod
from random import randint
from typing import Any
from plantangenet.topics import on_topic
from .base import OceanMixinBase

SYMBOLS = ["🌙", "🌝", "⭐", "🌟", "🌀",  "🔥", "💧", "🌊", "🎲"]


def all_same(symbols: str) -> bool:
    """Check if all characters in the symbols are the same."""
    return len(set(symbols)) == 1


def straights(symbols: str) -> bool:
    """Check if the symbols form a straight (all characters are different)."""
    return len(set(symbols)) == len(symbols)


def full_house(symbols: str) -> bool:
    """Check if the symbols form a full house (three of one kind and two of another)."""
    counts = {}
    for char in symbols:
        if char in counts:
            counts[char] += 1
        else:
            counts[char] = 1

    if len(counts) == 2 and sorted(counts.values()) == [2, 3]:
        return True
    return False


def runs(symbols: str, length: int) -> int:
    """Count the number of runs of identical characters in a symbols."""
    count = 0
    current_char = None
    current_run_length = 0

    for char in symbols:
        if char == current_char:
            current_run_length += 1
        else:
            current_char = char
            current_run_length = 1

        if current_run_length == length:
            count += 1

    return count


class LuckMixin(OceanMixinBase):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._lucky_symbols: str = "🦄🦄🦄🦄🦄🦄🦄🦄🦄"
        self._lucky_value = 0
        self._lucky_runs = 3
        self._lucky_iter = 3
        self._unlucky_runs = 5
        self._unlucky_iter = 1

    def _status(self) -> dict:
        status = {}
        return status

    @on_topic("clock.frame")
    async def handle_lucky_symbols(self, message: dict):
        """
        Handle a lucky symbols message.
        This method updates the lucky symbols and calculates the lucky value based on runs of symbols.

        First, we pick a new symbol from the SYMBOLS list.
        Then, we append it to the current lucky symbols, ensuring we keep only the last 9 symbols.
        Finally, we calculate the lucky value based on the number of runs of 3 and 5 identical symbols,
        applying multipliers for each type of run.
        The lucky value is updated and the on_luck method is called to handle the message.
        """
        symbol_index = randint(0, len(SYMBOLS) - 1)
        self._lucky_symbols = (self._lucky_symbols +
                               SYMBOLS[symbol_index])[-9:]

        self._lucky_value = runs(self._lucky_symbols, self._lucky_runs) * self._lucky_iter + \
            runs(self._lucky_symbols, self._unlucky_runs) * self._unlucky_iter

        await self.on_luck(message)

    @abstractmethod
    async def on_luck(self, message: dict):
        """
        Handle a lucky symbols message.
        This method should be implemented by subclasses to define specific lucky symbols handling logic.
        """

    @property
    def lucky_symbols(self) -> str:
        """Get the current lucky symbols."""
        return self._lucky_symbols
