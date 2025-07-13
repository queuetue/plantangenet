"""
TicTacToe game implementation using Plantangenet activities and tournament system.
"""
from dataclasses import dataclass
from typing import Dict, Tuple, Optional, Any
from plantangenet.game import TurnBasedGameActivity, GameState
from plantangenet import GLOBAL_LOGGER
from plantangenet.session.referee import Judgement

from .tictactoe_types import GameBoard, PlayerSymbol, GameState as TTTGameState
from .referee import TicTacToeReferee
from .helpers import render_tictactoe_game_state


@dataclass
class TicTacToeGame(TurnBasedGameActivity):
    """
    A TicTacToe game activity that supports two players taking turns.
    Inherits from TurnBasedGameActivity for turn management, policy enforcement, and widget support.
    """

    def __init__(self, game_id: str, player_x: str, player_o: str):
        super().__init__(game_id, player_x, player_o, max_players=2)
        self.board = GameBoard(game_id, player_x, player_o)
        self.player_x = player_x
        self.player_o = player_o
        self.referee = TicTacToeReferee()  # Instantiate the referee
        # Ensure current_turn is settable and initialized
        self.current_turn = player_x  # X always goes first

    @property
    def current_turn(self):
        return getattr(self, '_current_turn', None)

    @current_turn.setter
    def current_turn(self, value):
        self._current_turn = value

    def make_game_move(self, player_id: str, row: int, col: int) -> Tuple[bool, str]:
        """
        Make a move in the TicTacToe game.
        """
        return self._make_tictactoe_move(player_id, row, col)

    def _make_tictactoe_move(self, player_id: str, row: int, col: int) -> Tuple[bool, str]:
        """
        Make a move in the TicTacToe game.
        """
        if self.game_state != GameState.IN_PROGRESS:
            return False, "Game is not in progress"
        if player_id not in self.members:
            return False, f"Player {player_id} is not in this game"
        if player_id != self.current_turn:
            return False, f"It's not {player_id}'s turn"
        try:
            self.require_permission(player_id, "move")
        except PermissionError as e:
            return False, f"Permission denied: {str(e)}"
        if row < 0 or row > 2 or col < 0 or col > 2:
            return False, "Invalid position"
        if self.board.board[row][col] != " ":
            return False, "Position already occupied"
        # Determine symbol
        expected_symbol = PlayerSymbol.X.value if player_id == self.player_x else PlayerSymbol.O.value
        # Build proposed state for referee
        proposed_board = [list(r) for r in self.board.board]
        proposed_board[row][col] = expected_symbol
        proposed_state = {
            "board": proposed_board,
            "player": expected_symbol,
            "move": {"row": row, "col": col},
            "current_player": expected_symbol
        }
        result = self.referee.adjudicate([proposed_state])
        if result.judgement != Judgement.WIN:
            return False, f"Move rejected by referee: {result.info.get('reason', 'Unknown')}"
        # Accept the move and update the board
        self.board.board = [list(r) for r in result.state["board"]]
        # Check for win/game over using referee
        winner = self.referee.check_winner()
        if winner:
            self.board.winner = winner
            self._set_game_over()
        elif self.referee.is_board_full():
            self._set_game_over()
            self.board.winner = "DRAW"
        else:
            self.advance_turn()
            self.board.current_player = PlayerSymbol.O.value if expected_symbol == PlayerSymbol.X.value else PlayerSymbol.X.value
        return True, "Move successful"

    def advance_turn(self):
        """Advance the turn to the other player."""
        if self.current_turn == self.player_x:
            self.current_turn = self.player_o
        else:
            self.current_turn = self.player_x

    # Required abstract methods from TurnBasedGameActivity
    def _check_winner(self) -> Optional[str]:
        """Check if there is a winner."""
        board = self.board.board

        # Check rows
        for row in board:
            if row[0] == row[1] == row[2] != " ":
                # Find which player has this symbol
                symbol = row[0]
                return self.player_x if symbol == PlayerSymbol.X.value else self.player_o

        # Check columns
        for col in range(3):
            if board[0][col] == board[1][col] == board[2][col] != " ":
                symbol = board[0][col]
                return self.player_x if symbol == PlayerSymbol.X.value else self.player_o

        # Check diagonals
        if board[0][0] == board[1][1] == board[2][2] != " ":
            symbol = board[0][0]
            return self.player_x if symbol == PlayerSymbol.X.value else self.player_o
        if board[0][2] == board[1][1] == board[2][0] != " ":
            symbol = board[0][2]
            return self.player_x if symbol == PlayerSymbol.X.value else self.player_o

        return None

    def _is_board_full(self) -> bool:
        """Check if the board is full."""
        for row in self.board.board:
            for cell in row:
                if cell == " ":
                    return False
        return True

    def _set_game_over(self):
        """Set the game to finished state."""
        self.game_state = GameState.GAME_OVER
        self.board.state = TTTGameState.FINISHED

    def get_game_state(self) -> Dict:
        """Get the current game state as a dictionary."""
        return {
            "game_id": self.game_id,
            "state": self.game_state.value,
            "current_turn": self.current_turn,
            "board": self.board.to_dict(),
            "frames_elapsed": getattr(self, 'frames_elapsed', 0),
            "winner": self.board.winner
        }

    def get_widget(self, asset: str = "default", **kwargs) -> str:
        """Get a text-based widget representation of the game."""
        status = f"Game {self.game_id}: {self.player_x} vs {self.player_o}"
        if self.game_state == GameState.GAME_OVER:
            if self.board.winner == "DRAW":
                status += " (Draw)"
            else:
                status += f" (Winner: {self.board.winner})"
        else:
            status += f" (Turn: {self.current_turn})"
        return status

    def __render__(self, asset="default", **kwargs) -> Any:
        """Unified render method for dashboard/compositor use."""
        width = kwargs.get('width', 200)
        height = kwargs.get('height', 200)

        from PIL import Image, ImageDraw, ImageFont

        def get_text_size(draw, text, font=None, multiline=False):
            if multiline and hasattr(draw, 'multiline_textbbox'):
                bbox = draw.multiline_textbbox(
                    (0, 0), text, font=font, align="center")
                w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
            elif not multiline and hasattr(draw, 'textbbox'):
                bbox = draw.textbbox((0, 0), text, font=font)
                w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
            else:
                lines = text.split('\n') if multiline else [text]
                w = max([len(line) for line in lines]) * 8
                h = 16 * len(lines)
            return w, h

        if asset == "widget":
            img = Image.new('RGB', (width, height), color=(120, 80, 120))
            draw = ImageDraw.Draw(img)
            text = str(getattr(self, 'name', None) or getattr(
                self, 'game_id', None) or getattr(self, 'id', None) or 'Game')
            try:
                font = ImageFont.truetype("DejaVuSans-Bold.ttf", 22)
            except Exception:
                font = None
            w, h = get_text_size(draw, text, font=font, multiline=False)
            draw.text(((width-w)//2, (height-h)//2), text,
                      fill=(255, 255, 255), font=font)
            return img
        elif asset == "default":
            # Default: show the full game state
            return render_tictactoe_game_state(self.board, width=width, height=height, game=self)
        else:
            raise NotImplementedError(
                f"__render__ asset '{asset}' not implemented for {self.__class__.__name__}")

    def get_default_asset(self, width=200, height=200):
        """For compatibility, just call __render__."""
        return self.__render__(width=width, height=height, asset="default")
