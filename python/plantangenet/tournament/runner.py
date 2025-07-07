from typing import Protocol, runtime_checkable


@runtime_checkable
class Runner(Protocol):
    async def run(self, *args, **kwargs):
        ...

    async def step(self, *args, **kwargs):
        ...
