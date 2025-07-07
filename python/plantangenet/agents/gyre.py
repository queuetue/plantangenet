# Copyright (c) 1998-2025 Scott Russell
# SPDX-License-Identifier: MIT

from typing import List
from .agent import Agent
from .float import Float


class Gyre(Float):

    def __init__(
        self,
        agents: List[Agent],
        logger,
        name: str = "Gyre",
        namespace: str = "plantangenet",
        collect_frames: bool = True,
        maximum_agents: int = 100,
        maximum_records: int = 204800,
        maximum_axes: int = 12,
    ):
        self._agents = []
        self._name = name
        self._maximum_agents = maximum_agents
        self._maximum_records = maximum_records
        self._maximum_axes = maximum_axes
        if len(agents) > self._maximum_agents:
            raise ValueError(
                f"Too many agents: {len(agents)} exceeds maximum of {self._maximum_agents}")
        self._agents = agents
        self.collect_frames = collect_frames

        super().__init__(logger=logger, namespace=namespace)

    @property
    def agents(self) -> List[Agent]:
        return self._agents


    async def update(self) -> bool:
        return await super().update()

    def add_agent(self, agent: Agent):
        if len(self._agents) >= self._maximum_agents:
            raise ValueError(
                f"Cannot add agent: maximum {self._maximum_agents} reached.")
        self._agents.append(agent)
        self.logger.info(f"{self.name}: added new agent: {agent}")

    def remove_agent(self, agent: Agent):
        self._agents.remove(agent)
        self.logger.info(f"{self.name}: removed agent: {agent}")
