from typing import Any, Callable, List, Optional, Protocol, runtime_checkable
import asyncio


@runtime_checkable
class Runner(Protocol):
    async def run(self, *args, **kwargs):
        ...

    async def step(self, *args, **kwargs):
        ...


class Batch(Runner):
    """
    Generic batch manager for running, stepping, or updating a collection of agents, omnis, or activities.
    Provides a reusable framework for batch processing, simulation, or coordination cycles.
    """

    def __init__(
        self,
        agents: List[Any],
        activity_fn: Optional[Callable[[Any], Any]] = None,
        steps: int = 1,
        async_mode: bool = True,
        pre_step: Optional[Callable[[int, List[Any]], None]] = None,
        post_step: Optional[Callable[[int, List[Any]], None]] = None,
    ):
        self.agents = agents
        self.activity_fn = activity_fn or (
            lambda agent: agent.update() if hasattr(agent, 'update') else None)
        self.steps = steps
        self.async_mode = async_mode
        self.pre_step = pre_step
        self.post_step = post_step

    async def run(self):
        for step in range(self.steps):
            if self.pre_step:
                self.pre_step(step, self.agents)
            coros = []
            for agent in self.agents:
                result = self.activity_fn(agent)
                if asyncio.iscoroutine(result):
                    coros.append(result)
                elif result is not None:
                    # If result is not a coroutine, but not None, wrap in coroutine
                    async def _wrap(val):
                        return val
                    coros.append(_wrap(result))
            if self.async_mode:
                if coros:
                    await asyncio.gather(*coros)
            else:
                for coro in coros:
                    await coro
            if self.post_step:
                self.post_step(step, self.agents)

    async def step(self, *args, **kwargs):
        # Single step for all agents
        coros = []
        for agent in self.agents:
            result = self.activity_fn(agent)
            if asyncio.iscoroutine(result):
                coros.append(result)
            elif result is not None:
                async def _wrap(val):
                    return val
                coros.append(_wrap(result))
        if self.async_mode:
            if coros:
                await asyncio.gather(*coros)
        else:
            for coro in coros:
                await coro
