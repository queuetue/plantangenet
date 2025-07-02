# Copyright (c) 1998-2025 Scott Russell
# SPDX-License-Identifier: MIT

import asyncio
import functools
import random
import time

from abc import abstractmethod
from collections.abc import Callable
from typing import Optional
from typing import Callable, Coroutine, Any, Optional, Union

WINDOW_SECS_BACK = 5
WINDOW_SECS_FORWARD = 5
WINDOW_SECS_STEP = 0.01
DEFAULT_FPS = 120
STORAGE_TTL = 60 * 10


class TopicsWrapper:
    """
    A wrapper for topic handlers that provides additional functionality such as
    cooldowns, jitter, predicates, debounce, once execution, distinct until changed,
    and rate limiting.

    This wrapper can be used as a decorator for methods that handle specific topics.
    It allows for fine-grained control over how often and under what conditions
    the handler is executed.

    Attributes:
        topic (str): The topic this handler is associated with.
        mod (int): The modulus for message handling frequency. (fire ever `mod` messages)
        cooldown (Optional[float]): Minimum time between calls to the handler.
        jitter (Optional[float]): Random jitter to add to the cooldown.
        predicate (Optional[Callable[[Any], bool]]): A predicate function to filter messages.
        debounce (Optional[float]): Time to wait before executing the handler after the last message.
        once (bool): If True, the handler will only execute once.
        changed (Union[bool, Callable[[Any], Any]]): If True,
            the handler will only execute if the message is distinct from the last one.
        rate_limit (Optional[float]): Minimum time between calls to the handler based on a rate

    """

    def __init__(
        self,
        topic: str,
        mod: int = 1,
        cooldown: Optional[float] = None,
        jitter: Optional[float] = None,
        predicate: Optional[Callable[[Any], bool]] = None,
        debounce: Optional[float] = None,
        once: bool = False,
        changed: Union[bool, Callable[[Any], Any]] = False,
        rate_limit: Optional[float] = None,
    ):
        self.topic = topic
        self.mod = max(1, mod)
        self.cooldown = cooldown
        self.jitter = jitter
        self.predicate = predicate
        self.debounce = debounce
        self.once = once
        self.changed = changed
        self.rate_limit = rate_limit

        self._message_count = 0
        self._last_called = 0.0
        self._call_count = 0
        self._last_value = None

    def __call__(self, fn: Callable[[Any, Any], Coroutine[Any, Any, None]]) -> Callable[[Any, Any], Coroutine[Any, Any, None]]:
        self._original_fn = fn

        @functools.wraps(fn)
        async def wrapped(self_, message: Any):
            now = time.monotonic()
            self._message_count += 1

            if self.once and self._call_count > 0:
                return

            if self._message_count % self.mod != 0:
                return

            if self.cooldown is not None and now - self._last_called < self.cooldown:
                return

            if self.rate_limit is not None:
                min_interval = 1.0 / self.rate_limit
                if now - self._last_called < min_interval:
                    return

            if self.predicate and not self.predicate(message):
                return

            if self.changed:
                key_fn = self.changed if callable(
                    self.changed) else lambda x: x
                current_val = key_fn(message)
                if current_val == self._last_value:
                    return
                self._last_value = current_val

            if self.jitter:
                await asyncio.sleep(self.jitter * random.random())

            if self.debounce:
                await asyncio.sleep(self.debounce)

            self._last_called = time.monotonic()
            self._call_count += 1
            await fn(self_, message)

        # Attach metadata for discovery / documentation
        wrapped.__topic__ = self.topic  # type: ignore
        wrapped.__mod__ = self.mod  # type: ignore
        wrapped.__cooldown__ = self.cooldown  # type: ignore
        wrapped.__predicate__ = self.predicate  # type: ignore
        wrapped.__debounce__ = self.debounce  # type: ignore
        wrapped.__once__ = self.once  # type: ignore
        wrapped.__changed__ = self.changed  # type: ignore
        wrapped.__rate_limit__ = self.rate_limit  # type: ignore
        wrapped.__wrapped_by__ = "TopicsWrapper"  # type: ignore

        return wrapped
