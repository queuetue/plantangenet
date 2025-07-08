"""
Integration tests for session/omni architecture in TicTacToe.
"""
import pytest
from plantangenet import GLOBAL_LOGGER
from examples.tictactoe.referee import TicTacToeReferee
from examples.tictactoe.player import TicTacToePlayer
from examples.tictactoe.stats import TicTacToeStats
from examples.tictactoe.game import TicTacToeGame
from examples.tictactoe.local_policy import LocalPolicy


class TestSessionArchitecture:
    def test_session_creation(self, policy_with_players, session_with_policy):
        policy, _, _, _ = policy_with_players
        session = session_with_policy
        assert session is not None
        assert session.policy is not None
        assert isinstance(session.policy, type(policy))

    def test_agent_registration(self, policy_with_players, session_with_policy):
        policy, _, _, _ = policy_with_players
        session = session_with_policy
        referee = TicTacToeReferee(policy=policy, logger=GLOBAL_LOGGER)
        player1 = TicTacToePlayer("alice", logger=GLOBAL_LOGGER)
        player2 = TicTacToePlayer("bob", logger=GLOBAL_LOGGER)
        stats = TicTacToeStats(logger=GLOBAL_LOGGER)
        session.add_agent(referee)
        session.add_agent(player1)
        session.add_agent(player2)
        session.add_agent(stats)
        agents = list(session.agents)
        assert referee in agents
        assert player1 in agents
        assert player2 in agents
        assert stats in agents

    def test_session_as_omni_manager(self, policy_with_players, session_with_policy):
        policy, _, _, _ = policy_with_players
        session = session_with_policy
        referee = TicTacToeReferee(policy=policy, logger=GLOBAL_LOGGER)
        stats = TicTacToeStats(logger=GLOBAL_LOGGER)
        session.add_agent(referee)
        session.add_agent(stats)
        agents = list(session.agents)
        assert referee in agents
        assert stats in agents
        assert referee in session.agents
        assert stats in session.agents

    def test_session_policy_delegation(self, policy_with_players, session_with_policy):
        policy, _, _, _ = policy_with_players
        session = session_with_policy
        referee = TicTacToeReferee(policy=session.policy)
        game = TicTacToeGame("test_game", "alice", "bob")
        local_policy = LocalPolicy(parent_policy=session.policy)
        game.set_policy(local_policy)  # type: ignore
        success, message = game.make_move("alice", 0, 0)
        assert success is True
