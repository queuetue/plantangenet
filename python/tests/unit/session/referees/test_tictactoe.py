import pytest
from plantangenet.session.referees.tictactoe import TicTacToeReferee
from plantangenet.session.referee import Judgement


def test_tictactoe_referee_creation():
    """Test creating a TicTacToe referee."""
    referee = TicTacToeReferee()
    assert referee.current_player == "X"
    assert referee.current_board == [
        [" ", " ", " "],
        [" ", " ", " "],
        [" ", " ", " "]
    ]


def test_consensus_valid_move():
    """Test when both players agree on a valid move."""
    referee = TicTacToeReferee()

    # Both players propose the same valid move
    states = [
        {
            "board": [["X", " ", " "], [" ", " ", " "], [" ", " ", " "]],
            "player": "X",
            "move": {"row": 0, "col": 0}
        },
        {
            "board": [["X", " ", " "], [" ", " ", " "], [" ", " ", " "]],
            "player": "X",
            "move": {"row": 0, "col": 0}
        }
    ]

    result = referee.adjudicate(states)
    assert result.judgement == Judgement.WIN
    assert result.info["consensus"] is True
    assert referee.current_player == "O"  # Should switch to O


def test_consensus_invalid_move():
    """Test when both players agree on an invalid move."""
    referee = TicTacToeReferee()

    # Both players propose an invalid move (wrong player)
    states = [
        {
            "board": [["O", " ", " "], [" ", " ", " "], [" ", " ", " "]],
            "player": "O",  # Wrong player (should be X)
            "move": {"row": 0, "col": 0}
        },
        {
            "board": [["O", " ", " "], [" ", " ", " "], [" ", " ", " "]],
            "player": "O",
            "move": {"row": 0, "col": 0}
        }
    ]

    result = referee.adjudicate(states)
    assert result.judgement == Judgement.CHEAT
    assert result.info["consensus"] is True


def test_one_valid_move():
    """Test when one player proposes a valid move and another proposes invalid."""
    referee = TicTacToeReferee()

    states = [
        {
            "board": [["X", " ", " "], [" ", " ", " "], [" ", " ", " "]],
            "player": "X",
            "move": {"row": 0, "col": 0}
        },
        {
            "board": [["O", " ", " "], [" ", " ", " "], [" ", " ", " "]],
            "player": "O",  # Wrong player
            "move": {"row": 0, "col": 0}
        }
    ]

    result = referee.adjudicate(states)
    assert result.judgement == Judgement.WIN
    assert result.info["valid_states"] == 1
    assert result.info["invalid_states"] == 1


def test_no_valid_moves():
    """Test when no players propose valid moves."""
    referee = TicTacToeReferee()

    states = [
        {
            "board": [["O", " ", " "], [" ", " ", " "], [" ", " ", " "]],
            "player": "O",  # Wrong player
            "move": {"row": 0, "col": 0}
        },
        {
            "board": [["X", "X", " "], [" ", " ", " "], [" ", " ", " "]],
            "player": "X",  # Too many changes
            "move": {"row": 0, "col": 1}
        }
    ]

    result = referee.adjudicate(states)
    assert result.judgement == Judgement.ERROR
    assert result.info["invalid_states"] == 2


def test_move_validation():
    """Test various move validation scenarios."""
    referee = TicTacToeReferee()

    # Valid move
    valid_state = {
        "board": [["X", " ", " "], [" ", " ", " "], [" ", " ", " "]],
        "player": "X",
        "move": {"row": 0, "col": 0}
    }
    assert referee._is_valid_move(valid_state) is True

    # Wrong player
    wrong_player = {
        "board": [["O", " ", " "], [" ", " ", " "], [" ", " ", " "]],
        "player": "O",
        "move": {"row": 0, "col": 0}
    }
    assert referee._is_valid_move(wrong_player) is False

    # Out of bounds
    out_of_bounds = {
        "board": [["X", " ", " "], [" ", " ", " "], [" ", " ", " "]],
        "player": "X",
        "move": {"row": 3, "col": 0}
    }
    assert referee._is_valid_move(out_of_bounds) is False


def test_occupied_cell():
    """Test that moves to occupied cells are invalid."""
    referee = TicTacToeReferee()
    # Set up a board with X in position (0,0)
    referee.current_board[0][0] = "X"

    # Try to move to the same position
    invalid_state = {
        "board": [["O", " ", " "], [" ", " ", " "], [" ", " ", " "]],
        "player": "O",
        "move": {"row": 0, "col": 0}
    }
    assert referee._is_valid_move(invalid_state) is False


def test_game_over_detection():
    """Test winner and game over detection."""
    referee = TicTacToeReferee()

    # Set up a winning board for X
    referee.current_board = [
        ["X", "X", "X"],
        ["O", "O", " "],
        [" ", " ", " "]
    ]

    assert referee.check_winner() == "X"
    assert referee.is_game_over() is True

    # Test draw
    referee.current_board = [
        ["X", "O", "X"],
        ["O", "X", "O"],
        ["O", "X", "O"]
    ]

    assert referee.check_winner() is None
    assert referee.is_board_full() is True
    assert referee.is_game_over() is True


def test_referee_state_updates():
    """Test that referee properly updates its state after moves."""
    referee = TicTacToeReferee()

    # Make a move
    valid_state = {
        "board": [["X", " ", " "], [" ", " ", " "], [" ", " ", " "]],
        "player": "X",
        "move": {"row": 0, "col": 0}
    }

    result = referee.adjudicate([valid_state])
    assert result.judgement == Judgement.WIN
    assert referee.current_player == "O"  # Should switch to O
    assert referee.current_board[0][0] == "X"


def test_reset_game():
    """Test game reset functionality."""
    referee = TicTacToeReferee()

    # Make some moves
    referee.current_board[0][0] = "X"
    referee.current_player = "O"

    # Reset
    referee.reset_game()

    assert referee.current_player == "X"
    assert referee.current_board == [
        [" ", " ", " "],
        [" ", " ", " "],
        [" ", " ", " "]
    ]


def test_empty_states():
    """Test adjudication with no states."""
    referee = TicTacToeReferee()

    result = referee.adjudicate([])
    assert result.judgement == Judgement.UNKNOWN
    assert result.info["reason"] == "No states provided"
