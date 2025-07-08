import pytest
from plantangenet.policy.policy import Policy
from plantangenet.policy.role import Role
from plantangenet.policy.identity import Identity
from plantangenet.session.session import Session


def _make_policy_with_players():
    policy = Policy()
    player_role = Role(id="player", name="player",
                       description="Can play games", members=[])
    policy.add_role(player_role)
    alice = Identity(id="alice", nickname="Alice")
    bob = Identity(id="bob", nickname="Bob")
    policy.add_identity(alice)
    policy.add_identity(bob)
    policy.add_identity_to_role(alice, player_role)
    policy.add_identity_to_role(bob, player_role)
    policy.add_statement(
        roles=[player_role],
        effect="allow",
        action=["move", "join", "view_board"],
        resource=["activity:*"]
    )
    return policy, player_role, alice, bob


@pytest.fixture
def policy_with_players():
    return _make_policy_with_players()


@pytest.fixture
def session_with_policy(policy_with_players):
    policy, _, alice, _ = policy_with_players
    session = Session(id="test_session", policy=policy, identity=alice)
    return session
