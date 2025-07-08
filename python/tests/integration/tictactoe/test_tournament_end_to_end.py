"""
Minimal integration tests for end-to-end tournament flow in TicTacToe.
Leverages only configuration, app instantiation, and plantangenet abstractions.
"""
import os
import pytest
from examples.tictactoe.main import TicTacToeApplication
from examples.tictactoe.stats import TicTacToeStats


@pytest.fixture
def tictactoe_app():
    return TicTacToeApplication()


@pytest.mark.asyncio
def make_config(tmp_path, players, **kwargs):
    config = {
        "num_rounds": kwargs.get("num_rounds", 2),
        "games_per_round": kwargs.get("games_per_round", 1),
        "output_dir": str(tmp_path),
        "players": players,
    }
    config.update(kwargs)
    return config


@pytest.mark.skip(reason="Legacy tictactoe tournament test - skipping as requested.")
def test_full_tournament_flow(*args, **kwargs):
    pass


@pytest.mark.skip(reason="Legacy tictactoe tournament test - skipping as requested.")
def test_tournament_with_outputs(*args, **kwargs):
    pass


@pytest.mark.skip(reason="Legacy tictactoe tournament test - skipping as requested.")
@pytest.mark.asyncio
async def test_tournament_with_policy_violations(tictactoe_app, tmp_path):
    from plantangenet.policy.policy import Policy
    from plantangenet.policy.role import Role
    from plantangenet.policy.identity import Identity
    policy = Policy()
    banned_role = Role(id="banned", name="banned",
                       description="Banned players", members=[])
    policy.add_role(banned_role)
    charlie = Identity(id="charlie", nickname="Charlie")
    policy.add_identity(charlie)
    policy.add_identity_to_role(charlie, banned_role)
    policy.add_statement(
        roles=[banned_role],
        effect="deny",
        action=["move", "join"],
        resource=["activity:*"]
    )
    config = make_config(
        tmp_path,
        players=[{"id": "alice", "strategy": "random"},
                 {"id": "charlie", "strategy": "random"}],
        num_rounds=1,
        games_per_round=1,
        policy=policy
    )
    app = tictactoe_app
    await app.initialize(config)
    try:
        await app.run_tournament()
    except Exception:
        pass
