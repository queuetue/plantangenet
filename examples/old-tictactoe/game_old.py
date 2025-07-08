"""
TicTacToe game implementation using Plantangenet activities and tournament system.
"""
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import json

from plantangenet.game import TurnBasedGameActivity, GameState
from plantangenet import GLOBAL_LOGGER

from .tictactoe_types import GameBoard, PlayerSymbol


def render_tictactoe_game_state(board, width=200, height=200, game=None, info_text=None):
    """Render a TicTacToe game state as a PIL Image."""
    from PIL import Image, ImageDraw, ImageFont
    
    # Create image with dark background
    img = Image.new('RGB', (width, height), color=(40, 60, 90))
    draw = ImageDraw.Draw(img)
    
    # Draw the TicTacToe board
    board_size = min(width, height) - 40
    board_x = (width - board_size) // 2
    board_y = (height - board_size) // 2 + 10
    
    cell_size = board_size // 3
    
    # Draw grid
    for i in range(4):
        x = board_x + i * cell_size
        y = board_y + i * cell_size
        draw.line([(x, board_y), (x, board_y + board_size)], fill=(200, 200, 200), width=2)
        draw.line([(board_x, y), (board_x + board_size, y)], fill=(200, 200, 200), width=2)
    
    # Draw X's and O's
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", cell_size // 2)
    except Exception:
        font = None
        
    for r in range(3):
        for c in range(3):
            cell_val = board.board[r][c]
            if cell_val != " ":
                x = board_x + c * cell_size + cell_size // 2
                y = board_y + r * cell_size + cell_size // 2
                color = (255, 100, 100) if cell_val == "X" else (100, 100, 255)
                if font:
                    bbox = draw.textbbox((0, 0), cell_val, font=font)
                    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
                    draw.text((x - w//2, y - h//2), cell_val, fill=color, font=font)
                else:
                    draw.text((x - 8, y - 8), cell_val, fill=color)
    
    # Draw game info
    if info_text is None:
        current_player = getattr(board, 'current_player', 'X')
        state = getattr(board, 'state', 'in_progress')
        winner = getattr(board, 'winner', None)
        if winner:
            info_text = f"Winner: {winner}"
        elif state == 'finished':
            info_text = "Draw"
        else:
            info_text = f"Current: {current_player}"
    
    draw.text((10, height-20), info_text, fill=(255, 255, 255))
    return img


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

        # Check permissions
        try:
            self.require_permission(player_id, "move")
        except PermissionError as e:
            return False, f"Permission denied: {str(e)}"

        # Validate move
        if row < 0 or row > 2 or col < 0 or col > 2:
            return False, "Invalid position"

        if self.board.board[row][col] != " ":
            return False, "Position already occupied"

        # Determine symbol
        expected_symbol = PlayerSymbol.X.value if player_id == self.player_x else PlayerSymbol.O.value
        self.board.board[row][col] = expected_symbol

        # Check for win
        winner = self._check_winner()
        if winner:
            self.board.winner = winner
            self._set_game_over()
        elif self._is_board_full():
            self._set_game_over()
            self.board.winner = "DRAW"
        else:
            # Advance turn
            self.advance_turn()
            self.board.current_player = PlayerSymbol.O.value if expected_symbol == PlayerSymbol.X.value else PlayerSymbol.X.value

        return True, "Move successful"

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

    def __render__(self, width=200, height=200, asset="default", style="default", font=None, color=None, text_color=None, **kwargs):
        """Unified render method for dashboard/compositor use."""
        from PIL import Image, ImageDraw, ImageFont

        def get_text_size(draw, text, font=None, multiline=False):
            if multiline and hasattr(draw, 'multiline_textbbox'):
                bbox = draw.multiline_textbbox((0, 0), text, font=font, align="center")
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
            text = str(getattr(self, 'name', None) or getattr(self, 'game_id', None) or getattr(self, 'id', None) or 'Game')
            try:
                font = ImageFont.truetype("DejaVuSans-Bold.ttf", 22)
            except Exception:
                font = None
            w, h = get_text_size(draw, text, font=font, multiline=False)
            draw.text(((width-w)//2, (height-h)//2), text, fill=(255, 255, 255), font=font)
            return img
        elif asset == "default":
            # Default: show the full game state
            return render_tictactoe_game_state(self.board, width=width, height=height, game=self)
        else:
            raise NotImplementedError(f"__render__ asset '{asset}' not implemented for {self.__class__.__name__}")

    def get_default_asset(self, width=200, height=200):
        """For compatibility, just call __render__."""
        return self.__render__(width=width, height=height, asset="default")

    def _check_winner(self) -> Optional[str]:
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

    def _is_activity_full(self) -> bool:
        for row in self.board.board:
            for cell in row:
                if cell == " ":
                    return False
        return True

    def _check_completion(self) -> bool:
        return self.board.state == GameState.FINISHED

    def _available(self) -> bool:
        return self.board.state == GameState.IN_PROGRESS and len(self.members) == 2

    def is_member_turn(self, member_id: str) -> bool:
        """Check if it's the given member's turn."""
        if len(self.members) == 0:
            return False
        current_player = self.members[self.current_turn_index % len(
            self.members)]
        return current_player == member_id

    def next_turn(self) -> None:
        """Advance to the next turn."""
        self.current_turn_index = (
            self.current_turn_index + 1) % len(self.members)
        self.turn_count += 1

    def _is_active_player(self, identity) -> bool:
        """Override from TurnBasedPolicyMixin to check if identity can act on current turn."""
        identity_str = str(identity) if not isinstance(
            identity, str) else identity
        return self.is_member_turn(identity_str)

    async def add_member(self, member_id: str) -> bool:
        """Add a member to the game."""
        # Policy enforcement
        try:
            self.require_permission(member_id, "join")
        except PermissionError:
            return False

        if len(self.members) >= 2:
            return False  # Game is full
        if member_id in self.members:
            return False  # Already a member

        self.members.append(member_id)
        if len(self.members) == 1:
            self.player_x = member_id
        elif len(self.members) == 2:
            self.player_o = member_id

        return True

    async def remove_member(self, member_id: str) -> bool:
        """Remove a member from the game."""
        # Policy enforcement
        try:
            self.require_permission(member_id, "leave")
        except PermissionError:
            return False

        if member_id not in self.members:
            return False

        self.members.remove(member_id)
        # If a player leaves, the game is over
        self.board.state = GameState.FINISHED
        other_player = [m for m in [
            self.player_x, self.player_o] if m != member_id]
        if other_player:
            self.board.winner = other_player[0]

        return True

    @property
    def turn_order(self):
        # Return the order of player IDs
        return [self.player_x, self.player_o]

    @property
    def current_turn(self):
        # Return the player whose turn it is
        return self.members[self.current_turn_index]

    @property
    def game_state(self):
        """Expose the current game state for test compatibility."""
        return self.board.state

    def get_activity_specific_permissions(self) -> Dict[str, str]:
        """Get TicTacToe-specific permissions."""
        return {
            'move': 'Make a move on the board',
            'pass_turn': 'Pass the current turn (not applicable to TicTacToe)',
            'forfeit': 'Forfeit the game',
            'view_board': 'View the current board state',
        }
