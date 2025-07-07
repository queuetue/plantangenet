import pytest
import asyncio
from plantangenet.tournament.batch import Batch


class DummyAgent:
    def __init__(self):
        self.updated = False

    async def update(self):
        self.updated = True
        return 'updated'


@pytest.mark.asyncio
async def test_batch_run_and_step():
    agent1 = DummyAgent()
    agent2 = DummyAgent()
    batch = Batch([agent1, agent2], activity_fn=lambda a: a.update(), steps=2)
    await batch.run()
    assert agent1.updated
    assert agent2.updated
    # Reset and test step
    agent1.updated = False
    agent2.updated = False
    await batch.step()
    assert agent1.updated
    assert agent2.updated


def test_batch_is_runner_protocol():
    from typing import runtime_checkable
    from plantangenet.tournament.batch import Runner
    batch = Batch([])
    assert isinstance(batch, Runner)
