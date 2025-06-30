# Copyright (c) 1998-2025 Scott Russell
# SPDX-License-Identifier: MIT

from abc import ABC
from typing import Callable, Coroutine, Optional, Any, Union


class OceanMixinBase(ABC):
    _ocean__namespace: str = "plantangenet"

    async def publish(self, topic: str,
                      data: Union[str, bytes, dict]) -> Optional[list]: ...

    async def on_pulse(self, data: dict) -> None: ...

    async def subscribe(
        self, topic: str, callback: Callable[..., Coroutine[Any, Any, Any]]): ...

    async def setup(self, *args, **kwargs) -> None: ...

    async def teardown(self) -> None: ...

    async def update(self) -> bool: ...

    def get_axis_data(self) -> dict[str, Any]: ...

    @property
    def logger(self) -> Any: ...

    @property
    def name(self) -> str: ...

    @property
    def disposition(self) -> str: ...

    @property
    def ttl(self) -> int: ...

    @property
    def status(self) -> dict:
        return {}
