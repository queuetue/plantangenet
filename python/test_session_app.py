import asyncio
import pytest
from unittest.mock import MagicMock
from plantangenet.session import Session
from plantangenet.session_app import SessionApp
from plantangenet.agent import Agent


class DummyAgent(Agent):
    async def update(self) -> bool:
        self.updated = True
        return True

    def __init__(self):
        super().__init__(namespace="test", logger=MagicMock())
        self.updated = False


@pytest.mark.asyncio
async def test_session_app_lifecycle():
    session = Session(session_id="test_session")
    app = SessionApp(session)
    agent = DummyAgent()
    app.add_agent(agent)

    # Check that agent was registered before running
    assert agent in session.agents

    # Add a periodic task that sets a flag
    flag = {"ran": False}

    async def periodic():
        flag["ran"] = True
    app.add_periodic_task(periodic, interval=0.1)

    # Run the app for a short time
    async def run_and_shutdown():
        shutdown_task = asyncio.create_task(app.run())
        await asyncio.sleep(0.3)
        app._shutdown_event.set()
        await shutdown_task

    await run_and_shutdown()

    # Check that periodic task ran (after shutdown)
    assert flag["ran"]
