"""
Test suite for TicTacToe game mechanics and player strategies.

Tests:
1. Game board mechanics
2. Win/lose/tie detection
3. Player implementations
4. Move validation
5. Game flow and turn management
"""

import pytest
import asyncio
from unittest.mock import Mock, patch
import random

from examples.tictactoe.game import TicTacToeGame
from examples.tictactoe.player import TicTacToePlayer
from examples.tictactoe.tictactoe_types import GameState, PlayerSymbol, GameBoard
from plantangenet import GLOBAL_LOGGER


class TestGameMechanics:
    """Test core game mechanics."""

    def test_game_initialization(self):
        """Test game initializes correctly."""
        game = TicTacToeGame("test_game", "alice", "bob")

        assert game.id == "test_game"
        assert game.player_x == "alice"
        assert game.player_o == "bob"
        assert game.board.state == GameState.IN_PROGRESS
        assert len(game.board.board) == 3
        assert all(len(row) == 3 for row in game.board.board)
        assert all(cell == " " for row in game.board.board for cell in row)

    def test_move_validation(self):
        """Test move validation logic."""
        game = TicTacToeGame("test_game", "alice", "bob")

        # Valid move (alice goes first since she's player_x)
        success, message = game.make_move("alice", 0, 0)
        assert success is True
        assert game.board.board[0][0] == PlayerSymbol.X.value

        # Invalid: position already taken
        success, message = game.make_move("bob", 0, 0)
        assert success is False
        assert "occupied" in message.lower()

        # Invalid: out of bounds
        success, message = game.make_move("bob", 3, 3)
        assert success is False
        assert "invalid" in message.lower()

        # Invalid: negative coordinates
        success, message = game.make_move("bob", -1, 0)
        assert success is False

    def test_turn_management(self):
        """Test turn alternation."""
        game = TicTacToeGame("test_game", "alice", "bob")

        # Alice (X) should go first
        current_player = game.members[game.current_turn_index]

        # Make a move
        success, _ = game.make_move(current_player, 0, 0)
        assert success is True

        # Turn should switch
        new_current = game.members[game.current_turn_index]
        assert new_current != current_player

    def test_wrong_turn_prevention(self):
        """Test that players can't move out of turn."""
        game = TicTacToeGame("test_game", "alice", "bob")

        # Determine who goes first
        first_player = game.members[game.current_turn_index]
        second_player = "bob" if first_player == "alice" else "alice"

        # Second player tries to move first
        success, message = game.make_move(second_player, 0, 0)
        assert success is False
        assert "turn" in message.lower()

    def test_win_detection_rows(self):
        """Test win detection for rows."""
        game = TicTacToeGame("test_game", "alice", "bob")

        # Alice wins top row
        game.make_move("alice", 0, 0)  # X
        game.make_move("bob", 1, 0)    # O
        game.make_move("alice", 0, 1)  # X
        game.make_move("bob", 1, 1)    # O
        game.make_move("alice", 0, 2)  # X wins

        assert game.board.state == GameState.FINISHED
        assert game.board.winner == "alice"

    def test_win_detection_columns(self):
        """Test win detection for columns."""
        game = TicTacToeGame("test_game", "alice", "bob")

        # Alice wins left column
        game.make_move("alice", 0, 0)  # X
        game.make_move("bob", 0, 1)    # O
        game.make_move("alice", 1, 0)  # X
        game.make_move("bob", 0, 2)    # O
        game.make_move("alice", 2, 0)  # X wins

        assert game.board.state == GameState.FINISHED
        assert game.board.winner == "alice"

    def test_win_detection_diagonals(self):
        """Test win detection for diagonals."""
        game = TicTacToeGame("test_game", "alice", "bob")

        # Alice wins main diagonal
        game.make_move("alice", 0, 0)  # X
        game.make_move("bob", 0, 1)    # O
        game.make_move("alice", 1, 1)  # X
        game.make_move("bob", 0, 2)    # O
        game.make_move("alice", 2, 2)  # X wins

        assert game.board.state == GameState.FINISHED
        assert game.board.winner == "alice"

    def test_tie_detection(self):
        """Test tie game detection."""
        game = TicTacToeGame("test_game", "alice", "bob")

        # Create a tie game
        moves = [
            ("alice", 0, 0),  # X
            ("bob", 0, 1),    # O
            ("alice", 0, 2),  # X
            ("bob", 1, 0),    # O
            ("alice", 1, 1),  # X
            ("bob", 2, 2),    # O
            ("alice", 1, 2),  # X
            ("bob", 2, 0),    # O
            ("alice", 2, 1),  # X
        ]

        for player, row, col in moves:
            game.make_move(player, row, col)

        assert game.board.state == GameState.FINISHED
        assert game.board.winner == "DRAW"

    def test_game_over_prevents_moves(self):
        """Test that no moves can be made after game ends."""
        game = TicTacToeGame("test_game", "alice", "bob")

        # Alice wins quickly
        game.make_move("alice", 0, 0)  # X
        game.make_move("bob", 1, 0)    # O
        game.make_move("alice", 0, 1)  # X
        game.make_move("bob", 1, 1)    # O
        game.make_move("alice", 0, 2)  # X wins

        assert game.board.state == GameState.FINISHED

        # Try to make another move
        success, message = game.make_move("bob", 2, 0)
        assert success is False
        assert ("progress" in message.lower() or "over" in message.lower() or
                "finished" in message.lower())


"""
Test suite for TicTacToe game mechanics and player functionality.

Tests:
1. Game board mechanics
2. Win/lose/tie detection  
3. Player basic functionality
4. Move validation
5. Game flow and turn management
"""


class TestGameMechanics:
    """Test core game mechanics."""

    def test_game_initialization(self):
        """Test game initializes correctly."""
        game = TicTacToeGame("test_game", "alice", "bob")

        assert game.id == "test_game"
        assert game.player_x == "alice"
        assert game.player_o == "bob"
        assert game.board.state == GameState.IN_PROGRESS
        assert len(game.board.board) == 3
        assert all(len(row) == 3 for row in game.board.board)
        assert all(cell == " " for row in game.board.board for cell in row)

    def test_move_validation(self):
        """Test move validation logic."""
        game = TicTacToeGame("test_game", "alice", "bob")

        # Valid move (alice goes first since she's player_x)
        success, message = game.make_move("alice", 0, 0)
        assert success is True
        assert game.board.board[0][0] == PlayerSymbol.X.value

        # Invalid: position already taken
        success, message = game.make_move("bob", 0, 0)
        assert success is False
        assert "occupied" in message.lower()

        # Invalid: out of bounds
        success, message = game.make_move("bob", 3, 3)
        assert success is False
        assert "invalid" in message.lower()

        # Invalid: negative coordinates
        success, message = game.make_move("bob", -1, 0)
        assert success is False

    def test_turn_management(self):
        """Test turn alternation."""
        game = TicTacToeGame("test_game", "alice", "bob")

        # Alice (X) should go first
        current_player = game.members[game.current_turn_index]

        # Make a move
        success, _ = game.make_move(current_player, 0, 0)
        assert success is True

        # Turn should switch
        new_current = game.members[game.current_turn_index]
        assert new_current != current_player

    def test_wrong_turn_prevention(self):
        """Test that players can't move out of turn."""
        game = TicTacToeGame("test_game", "alice", "bob")

        # Determine who goes first
        first_player = game.members[game.current_turn_index]
        second_player = "bob" if first_player == "alice" else "alice"

        # Second player tries to move first
        success, message = game.make_move(second_player, 0, 0)
        assert success is False
        assert "turn" in message.lower()

    def test_win_detection_rows(self):
        """Test win detection for rows."""
        game = TicTacToeGame("test_game", "alice", "bob")

        # Alice wins top row
        game.make_move("alice", 0, 0)  # X
        game.make_move("bob", 1, 0)    # O
        game.make_move("alice", 0, 1)  # X
        game.make_move("bob", 1, 1)    # O
        game.make_move("alice", 0, 2)  # X wins

        assert game.board.state == GameState.FINISHED
        assert game.board.winner == "alice"

    def test_win_detection_columns(self):
        """Test win detection for columns."""
        game = TicTacToeGame("test_game", "alice", "bob")

        # Alice wins left column
        game.make_move("alice", 0, 0)  # X
        game.make_move("bob", 0, 1)    # O
        game.make_move("alice", 1, 0)  # X
        game.make_move("bob", 0, 2)    # O
        game.make_move("alice", 2, 0)  # X wins

        assert game.board.state == GameState.FINISHED
        assert game.board.winner == "alice"

    def test_win_detection_diagonals(self):
        """Test win detection for diagonals."""
        game = TicTacToeGame("test_game", "alice", "bob")

        # Alice wins main diagonal
        game.make_move("alice", 0, 0)  # X
        game.make_move("bob", 0, 1)    # O
        game.make_move("alice", 1, 1)  # X
        game.make_move("bob", 0, 2)    # O
        game.make_move("alice", 2, 2)  # X wins

        assert game.board.state == GameState.FINISHED
        assert game.board.winner == "alice"

    def test_tie_detection(self):
        """Test tie game detection."""
        game = TicTacToeGame("test_game", "alice", "bob")

        # Create a tie game
        moves = [
            ("alice", 0, 0),  # X
            ("bob", 0, 1),    # O
            ("alice", 0, 2),  # X
            ("bob", 1, 0),    # O
            ("alice", 1, 1),  # X
            ("bob", 2, 2),    # O
            ("alice", 1, 2),  # X
            ("bob", 2, 0),    # O
            ("alice", 2, 1),  # X
        ]

        for player, row, col in moves:
            game.make_move(player, row, col)

        assert game.board.state == GameState.FINISHED
        assert game.board.winner == "DRAW"

    def test_game_over_prevents_moves(self):
        """Test that no moves can be made after game ends."""
        game = TicTacToeGame("test_game", "alice", "bob")

        # Alice wins quickly
        game.make_move("alice", 0, 0)  # X
        game.make_move("bob", 1, 0)    # O
        game.make_move("alice", 0, 1)  # X
        game.make_move("bob", 1, 1)    # O
        game.make_move("alice", 0, 2)  # X wins

        assert game.board.state == GameState.FINISHED

        # Try to make another move
        success, message = game.make_move("bob", 2, 0)
        assert success is False
        assert ("progress" in message.lower() or "over" in message.lower() or
                "finished" in message.lower())


class TestGameBoardClass:
    """Test the GameBoard class functionality."""

    def test_board_initialization(self):
        """Test board initializes correctly."""
        board = GameBoard("test_game", "alice", "bob")

        assert board.game_id == "test_game"
        assert board.player_x == "alice"
        assert board.player_o == "bob"
        assert board.state == GameState.WAITING
        assert len(board.board) == 3
        assert all(len(row) == 3 for row in board.board)
        assert all(cell == " " for row in board.board for cell in row)

    def test_board_serialization(self):
        """Test board can be serialized to/from dict."""
        board = GameBoard("test_game", "alice", "bob")
        board.board[0][0] = PlayerSymbol.X.value
        board.state = GameState.IN_PROGRESS

        # Convert to dict and back
        board_dict = board.to_dict()
        assert isinstance(board_dict, dict)
        assert board_dict["game_id"] == "test_game"
        assert board_dict["board"][0][0] == PlayerSymbol.X.value

        # Create from dict
        restored_board = GameBoard.from_dict(board_dict)
        assert restored_board.game_id == "test_game"
        assert restored_board.board[0][0] == PlayerSymbol.X.value
        assert restored_board.state == GameState.IN_PROGRESS


class TestPlayerFunctionality:
    """Test player basic functionality."""

    def test_player_initialization(self):
        """Test player initializes correctly."""
        player = TicTacToePlayer("tictactoe", logger=GLOBAL_LOGGER)

        assert player.current_game_id is None
        assert player.my_symbol is None
        assert player.games_played == 0
        assert player.games_won == 0
        assert isinstance(player.move_history, list)

    @pytest.mark.asyncio
    async def test_player_update(self):
        """Test player update method."""
        player = TicTacToePlayer("tictactoe", logger=GLOBAL_LOGGER)

        # Should return True when update completes
        result = await player.update()
        assert result is True

    def test_player_game_assignment(self):
        """Test assigning player to a game."""
        player = TicTacToePlayer("tictactoe", logger=GLOBAL_LOGGER)

        # Assign to game
        player.assign_to_game("game123", "X")

        assert player.current_game_id == "game123"
        assert player.my_symbol == "X"

    def test_player_game_finished(self):
        """Test handling game completion."""
        player = TicTacToePlayer("tictactoe", logger=GLOBAL_LOGGER)

        initial_games = player.games_played
        player.game_finished("alice")

        assert player.games_played == initial_games + 1


class TestGameStateTransitions:
    """Test game state transitions and edge cases."""

    def test_game_state_progression(self):
        """Test normal game state progression."""
        game = TicTacToeGame("test_game", "alice", "bob")

        # Should start in progress
        assert game.board.state == GameState.IN_PROGRESS

        # Make moves until someone wins
        game.make_move("alice", 0, 0)  # X
        assert game.board.state == GameState.IN_PROGRESS

        game.make_move("bob", 1, 0)    # O
        assert game.board.state == GameState.IN_PROGRESS

        game.make_move("alice", 0, 1)  # X
        assert game.board.state == GameState.IN_PROGRESS

        game.make_move("bob", 1, 1)    # O
        assert game.board.state == GameState.IN_PROGRESS

        game.make_move("alice", 0, 2)  # X wins
        assert game.board.state == GameState.FINISHED

    def test_immediate_win_detection(self):
        """Test that wins are detected immediately."""
        game = TicTacToeGame("test_game", "alice", "bob")

        # Set up a near-win state
        game.make_move("alice", 0, 0)  # X
        game.make_move("bob", 1, 0)    # O
        game.make_move("alice", 0, 1)  # X
        game.make_move("bob", 1, 1)    # O

        # Winning move
        success, message = game.make_move("alice", 0, 2)  # X wins
        assert success is True
        assert game.board.state == GameState.FINISHED
        assert game.board.winner == "alice"

        # Should mention success in message
        assert "successful" in message.lower()

    def test_game_end_finality(self):
        """Test that game end states are final."""
        game = TicTacToeGame("test_game", "alice", "bob")

        # Force a win
        game.make_move("alice", 0, 0)
        game.make_move("bob", 1, 0)
        game.make_move("alice", 0, 1)
        game.make_move("bob", 1, 1)
        game.make_move("alice", 0, 2)  # Alice wins

        original_state = game.board.state

        # Try to make more moves
        game.make_move("bob", 2, 0)

        # State should not change
        assert game.board.state == original_state

    def test_tie_game_finality(self):
        """Test that tie games are properly final."""
        game = TicTacToeGame("test_game", "alice", "bob")

        # Force a tie
        moves = [
            ("alice", 0, 0),  # X
            ("bob", 0, 1),    # O
            ("alice", 0, 2),  # X
            ("bob", 1, 0),    # O
            ("alice", 1, 1),  # X
            ("bob", 2, 2),    # O
            ("alice", 1, 2),  # X
            ("bob", 2, 0),    # O
            ("alice", 2, 1),  # X
        ]

        for player, row, col in moves:
            game.make_move(player, row, col)

        assert game.board.state == GameState.FINISHED
        assert game.board.winner == "DRAW"

        # Board should be full
        assert all(cell != " " for row in game.board.board for cell in row)


class TestGamePolicyIntegration:
    """Test game integration with policy system."""

    def test_game_with_policy(self):
        """Test that games can have policies set."""
        game = TicTacToeGame("test_game", "alice", "bob")

        # Mock policy
        mock_policy = Mock()
        mock_policy.evaluate = Mock(
            return_value=Mock(passed=True, reason="allowed"))

        game.set_policy(mock_policy)
        assert game.policy is mock_policy

    def test_policy_enforcement_on_moves(self):
        """Test that policy is enforced on moves."""
        game = TicTacToeGame("test_game", "alice", "bob")

        # Mock policy that denies moves
        mock_policy = Mock()
        mock_policy.evaluate = Mock(
            return_value=Mock(passed=False, reason="denied"))

        game.set_policy(mock_policy)

        # Move should be denied
        success, message = game.make_move("alice", 0, 0)
        assert success is False
        assert "denied" in message.lower() or "permission" in message.lower()

    @pytest.mark.asyncio
    async def test_policy_enforcement_on_join(self):
        """Test that policy is enforced when joining games."""
        game = TicTacToeGame("test_game", "alice", "bob")

        # Mock policy that denies joins
        mock_policy = Mock()
        mock_policy.evaluate = Mock(
            return_value=Mock(passed=False, reason="denied"))

        game.set_policy(mock_policy)

        # Join should be denied (though game is already full)
        result = await game.add_member("charlie")
        assert result is False


class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_invalid_move_handling(self):
        """Test handling of invalid moves."""
        game = TicTacToeGame("test_game", "alice", "bob")

        # Invalid position - out of bounds
        success, message = game.make_move("alice", -1, 0)
        assert success is False
        assert "invalid" in message.lower()

        # Invalid position - too large
        success, message = game.make_move("alice", 3, 0)
        assert success is False
        assert "invalid" in message.lower()

        # Position already occupied
        game.make_move("alice", 0, 0)  # Valid move
        success, message = game.make_move("bob", 0, 0)  # Same position
        assert success is False
        assert "occupied" in message.lower()

    def test_game_member_management(self):
        """Test adding and removing members."""
        game = TicTacToeGame("test_game", "alice", "bob")

        # Game should start with 2 members
        assert len(game.members) == 2
        assert "alice" in game.members
        assert "bob" in game.members

    @pytest.mark.asyncio
    async def test_member_removal_ends_game(self):
        """Test that removing a member ends the game."""
        game = TicTacToeGame("test_game", "alice", "bob")

        # Remove a member
        result = await game.remove_member("alice")
        assert result is True
        assert game.board.state == GameState.FINISHED
        assert game.board.winner == "bob"  # Other player wins


if __name__ == "__main__":
    # Run tests if called directly
    pytest.main([__file__, "-v"])


if __name__ == "__main__":
    # Run tests if called directly
    pytest.main([__file__, "-v"])
