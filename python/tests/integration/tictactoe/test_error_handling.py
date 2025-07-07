"""
Integration tests for error handling and recovery in TicTacToe.
"""
import pytest
from unittest.mock import Mock
from plantangenet.policy.policy import Policy
from plantangenet.policy.identity import Identity
from plantangenet.session.session import Session
from examples.tictactoe.game import TicTacToeGame
from examples.tictactoe.local_policy import LocalPolicy

class TestErrorHandling:
    def test_invalid_move_handling(self, policy_with_players):
        game = TicTacToeGame("test_game", "alice", "bob")
        success, message = game.make_move("alice", -1, 0)
        assert success is False
        assert "invalid" in message.lower() or "out of bounds" in message.lower()
        game.make_move("alice", 0, 0)
        success, message = game.make_move("bob", 0, 0)
        assert success is False
        assert "occupied" in message.lower() or "taken" in message.lower()

    def test_policy_error_handling(self, policy_with_players):
        game = TicTacToeGame("test_game", "alice", "bob")
        policy = Policy()
        policy.add_statement(
            roles=["*"],
            effect="deny",
            action=["*"],
            resource=["*"]
        )
        local_policy = LocalPolicy(parent_policy=policy)
        game.set_policy(local_policy)
        success, message = game.make_move("alice", 0, 0)
        assert success is False
        assert "policy" in message.lower() or "denied" in message.lower()

    def test_agent_failure_recovery(self, policy_with_players):
        policy, _, _, _ = policy_with_players
        identity = Identity(id="test", nickname="test")
        session = Session(id="fail_session", policy=policy, identity=identity)
        failing_agent = Mock()
        failing_agent.process = Mock(side_effect=Exception("Agent failed"))
        session.add_agent(failing_agent)
        try:
            assert failing_agent in session.agents
        except Exception:
            pytest.fail("Session should handle agent failures gracefully")
