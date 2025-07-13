from typing import List, Dict, Optional
from plantangenet.session.referee import BaseReferee, AdjudicationResult, Judgement


class TicTacToeReferee:
    """
    TicTacToe referee: adjudicates proposed board states from players.

    Players all say what they think the board should be:
    - If both players report identical states, accept it ("x did this")
    - If states differ, check which is a valid next move from current state
    - If neither is valid or both are cheating, flag as ERROR or CHEAT
    """

    def __init__(self, current_board: Optional[List[List[str]]] = None):
        self.current_board = current_board or [
            [" ", " ", " "],
            [" ", " ", " "],
            [" ", " ", " "]
        ]
        self.current_player = "X"  # X goes first

    def adjudicate(self, states: List[dict]) -> AdjudicationResult:
        """
        Adjudicate proposed board states from players.

        Expected state format:
        {
            "board": [["X", " ", " "], [" ", "O", " "], [" ", " ", " "]],
            "player": "X" or "O",
            "move": {"row": 0, "col": 1},
            "current_player": "X" or "O"
        }
        """
        if not states:
            return AdjudicationResult(Judgement.UNKNOWN, {}, {'reason': 'No states provided'})

        # Check if all states are identical (consensus)
        if self._all_states_identical(states):
            proposed_state = states[0]
            if self._is_valid_move(proposed_state):
                self._update_current_state(proposed_state)
                return AdjudicationResult(
                    Judgement.WIN,
                    proposed_state,
                    {'reason': 'Consensus on valid move', 'consensus': True}
                )
            else:
                return AdjudicationResult(
                    Judgement.CHEAT,
                    proposed_state,
                    {'reason': 'Consensus on invalid move', 'consensus': True}
                )

        # States differ - check which (if any) are valid
        valid_states = []
        invalid_states = []

        for state in states:
            if self._is_valid_move(state):
                valid_states.append(state)
            else:
                invalid_states.append(state)

        if len(valid_states) == 1:
            # Exactly one valid state - accept it
            valid_state = valid_states[0]
            self._update_current_state(valid_state)
            return AdjudicationResult(
                Judgement.WIN,
                valid_state,
                {
                    'reason': 'One valid move found',
                    'valid_states': len(valid_states),
                    'invalid_states': len(invalid_states)
                }
            )
        elif len(valid_states) > 1:
            # Multiple valid states - this shouldn't happen in TicTacToe
            return AdjudicationResult(
                Judgement.CONTEST,
                {},
                {
                    'reason': 'Multiple valid moves proposed',
                    'valid_states': len(valid_states),
                    'states': valid_states
                }
            )
        else:
            # No valid states - all are errors or cheats
            return AdjudicationResult(
                Judgement.ERROR,
                {},
                {
                    'reason': 'No valid moves proposed',
                    'invalid_states': len(invalid_states),
                    'states': invalid_states
                }
            )

    def _all_states_identical(self, states: List[dict]) -> bool:
        """Check if all proposed states are identical."""
        if len(states) <= 1:
            return True

        first_state = states[0]
        for state in states[1:]:
            if not self._states_equal(first_state, state):
                return False
        return True

    def _states_equal(self, state1: dict, state2: dict) -> bool:
        """Check if two states are equal."""
        return (
            state1.get('board') == state2.get('board') and
            state1.get('player') == state2.get('player') and
            state1.get('move') == state2.get('move')
        )

    def _is_valid_move(self, proposed_state: dict) -> bool:
        """Check if a proposed state represents a valid move."""
        proposed_board = proposed_state.get('board')
        player = proposed_state.get('player')
        move = proposed_state.get('move')

        if not proposed_board or not player or not move:
            return False

        # Check if it's the correct player's turn
        if player != self.current_player:
            return False

        # Check if the move is within bounds
        row, col = move.get('row'), move.get('col')
        if row is None or col is None or row < 0 or row > 2 or col < 0 or col > 2:
            return False

        # Check if the spot was empty in current board
        if self.current_board[row][col] != " ":
            return False

        # Check if the proposed board differs from current board by exactly one move
        differences = 0
        for r in range(3):
            for c in range(3):
                if self.current_board[r][c] != proposed_board[r][c]:
                    differences += 1
                    if differences > 1:
                        return False
                    # Check if the difference is the proposed move
                    if r != row or c != col or proposed_board[r][c] != player:
                        return False

        return differences == 1

    def _update_current_state(self, new_state: dict):
        """Update the referee's current state after accepting a move."""
        self.current_board = new_state['board']
        # Switch players
        self.current_player = "O" if self.current_player == "X" else "X"

    def get_current_board(self) -> List[List[str]]:
        """Get the current board state."""
        return [row[:] for row in self.current_board]  # Deep copy

    def get_current_player(self) -> str:
        """Get the current player."""
        return self.current_player

    def reset_game(self):
        """Reset the game to initial state."""
        self.current_board = [
            [" ", " ", " "],
            [" ", " ", " "],
            [" ", " ", " "]
        ]
        self.current_player = "X"

    def check_winner(self) -> Optional[str]:
        """Check if there's a winner on the current board."""
        board = self.current_board

        # Check rows
        for row in board:
            if row[0] == row[1] == row[2] != " ":
                return row[0]

        # Check columns
        for col in range(3):
            if board[0][col] == board[1][col] == board[2][col] != " ":
                return board[0][col]

        # Check diagonals
        if board[0][0] == board[1][1] == board[2][2] != " ":
            return board[0][0]
        if board[0][2] == board[1][1] == board[2][0] != " ":
            return board[0][2]

        return None

    def is_board_full(self) -> bool:
        """Check if the board is full."""
        for row in self.current_board:
            for cell in row:
                if cell == " ":
                    return False
        return True

    def is_game_over(self) -> bool:
        """Check if the game is over."""
        return self.check_winner() is not None or self.is_board_full()
