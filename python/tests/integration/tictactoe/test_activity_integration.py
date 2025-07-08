"""
Integration tests for activity and turn-based logic in TicTacToe.
"""
import pytest
from examples.tictactoe.game import TicTacToeGame
from examples.tictactoe.local_policy import LocalPolicy
from examples.tictactoe.tictactoe_types import GameState, PlayerSymbol


class TestActivityIntegration:
    def test_game_inherits_from_activity(self, policy_with_players):
        game = TicTacToeGame("test_game", "alice", "bob")
        assert hasattr(game, 'members')
        assert hasattr(game, 'current_turn')
        assert hasattr(game, 'turn_order')
        assert hasattr(game, 'board')
        assert hasattr(game, 'game_state')

    def test_activity_member_management(self, policy_with_players):
        game = TicTacToeGame("test_game", "alice", "bob")
        assert len(game.members) == 2
        assert "alice" in game.members
        assert "bob" in game.members

    def test_activity_turn_management(self, policy_with_players):
        game = TicTacToeGame("test_game", "alice", "bob")
        assert len(game.turn_order) == 2
        assert game.current_turn in ["alice", "bob"]
        current_player = game.current_turn
        success, message = game.make_move(current_player, 0, 0)
        assert success is True
        new_current = game.current_turn
        assert new_current != current_player

    def test_activity_policy_integration(self, policy_with_players):
        policy, _, _, _ = policy_with_players
        game = TicTacToeGame("test_game", "alice", "bob")
        local_policy = LocalPolicy(parent_policy=policy)
        game.set_policy(local_policy)
        assert game.policy is not None
        assert isinstance(game.policy, LocalPolicy)
        try:
            game.require_permission("alice", "move")
        except PermissionError:
            pytest.fail("Alice should have move permission")
