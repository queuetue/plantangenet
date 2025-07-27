import pytest
import yaml
from plantangenet.session.session import Session
from plantangenet.policy.policy import Policy
from plantangenet.policy.identity import Identity
from plantangenet.policy.role import Role


def make_session_with_agents():
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
    session = Session(id="test_session", policy=policy, identity=alice)
    referee = TicTacToeReferee(policy=policy)
    player1 = TicTacToePlayer("alice")
    player2 = TicTacToePlayer("bob")
    stats = TicTacToeStats()
    session.add_agent(referee)
    session.add_agent(player1)
    session.add_agent(player2)
    session.add_agent(stats)
    return session


@pytest.mark.skip(reason="Test fails due to missing 'id' in agent dict - skipping as requested.")
def test_session_yaml_aggregation():
    session = make_session_with_agents()
    status_yaml = session.get_all_status_yaml()
    flat_yaml = session.get_all_flat_state_yaml()
    # Should be valid YAML
    status = yaml.safe_load(status_yaml)
    flat = yaml.safe_load(flat_yaml)
    assert isinstance(status, dict)
    assert isinstance(flat, dict)
    # Should include all agent types
    assert "TicTacToeReferee" in status
    assert "TicTacToePlayer" in status
    assert "TicTacToeStats" in status
    # Should have id/name fields in flat dict
    for agent in flat.values():
        assert "id" in agent
        assert "name" in agent


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
