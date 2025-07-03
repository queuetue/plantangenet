from examples.tictactoe.tictactoe_types import GameBoard, GameState, PlayerSymbol
from typing import Tuple


class TicTacToeGame:
    def __init__(self, game_id: str, player_x: str, player_o: str):
        self.board = GameBoard(game_id, player_x, player_o)
        self.board.state = GameState.IN_PROGRESS

    def make_move(self, player_id: str, row: int, col: int) -> Tuple[bool, str]:
        # Validate move
        if self.board.state != GameState.IN_PROGRESS:
            return False, "Game not in progress"

        if row < 0 or row > 2 or col < 0 or col > 2:
            return False, "Invalid position"

        if self.board.board[row][col] != " ":
            return False, "Position already occupied"

        # Check if it's the player's turn
        expected_symbol = None
        if player_id == self.board.player_x and self.board.current_player == PlayerSymbol.X.value:
            expected_symbol = PlayerSymbol.X.value
        elif player_id == self.board.player_o and self.board.current_player == PlayerSymbol.O.value:
            expected_symbol = PlayerSymbol.O.value
        else:
            return False, "Not your turn"

        # Make the move
        self.board.board[row][col] = expected_symbol

        # Check for win
        if self._check_winner():
            self.board.winner = player_id
            self.board.state = GameState.FINISHED
        elif self._is_board_full():
            self.board.state = GameState.FINISHED
            self.board.winner = "DRAW"
        else:
            # Switch turns
            self.board.current_player = PlayerSymbol.O.value if self.board.current_player == PlayerSymbol.X.value else PlayerSymbol.X.value

        return True, "Move successful"

    def _check_winner(self) -> bool:
        board = self.board.board

        # Check rows
        for row in board:
            if row[0] == row[1] == row[2] != " ":
                return True

        # Check columns
        for col in range(3):
            if board[0][col] == board[1][col] == board[2][col] != " ":
                return True

        # Check diagonals
        if board[0][0] == board[1][1] == board[2][2] != " ":
            return True
        if board[0][2] == board[1][1] == board[2][0] != " ":
            return True

        return False

    def _is_board_full(self) -> bool:
        for row in self.board.board:
            for cell in row:
                if cell == " ":
                    return False
        return True
