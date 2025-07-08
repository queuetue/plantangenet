"""
TicTacToe player agent with AI strategies.
"""
import asyncio
import random
from typing import Optional
from plantangenet.agents.agent import Agent
from plantangenet.game import GamePlayerMixin
from plantangenet import GLOBAL_LOGGER
from plantangenet.omni.base import OmniBase
from plantangenet.omni.observable import Observable
from plantangenet.omni.persisted import PersistedBase


class TicTacToePlayer(OmniBase, Agent, GamePlayerMixin):
    """AI player for TicTacToe games with configurable strategies (Omni-compatible)."""
    strategy = PersistedBase(default="random")
    total_wins = Observable(default=0)
    
    def __init__(self, player_id: str, strategy: str = "random", logger=None, **kwargs):
        OmniBase.__init__(self, **kwargs)
        Agent.__init__(self, namespace="tictactoe", logger=logger or GLOBAL_LOGGER)
        GamePlayerMixin.__init__(self, player_id)
        self.strategy = strategy
        self.current_game_id: Optional[str] = None
        self.my_symbol: Optional[str] = None
        self.move_history = []

    @property
    def session(self):
        return getattr(self, '_omni__session', None)

    @session.setter
    def session(self, value):
        self._omni__session = value

    async def update(self) -> bool:
        """Periodic update - players are reactive, so this is minimal."""
        # Check for new game assignments or game state updates
        if self.current_game_id:
            # Make a move if it's our turn
            await self._try_make_move()
        return True

    def choose_action(self, board_state: list, my_symbol: str) -> tuple:
        """
        Choose an action based on the current board state and strategy.
        Returns: (row, col) tuple for the move
        """
        if self.strategy == "random":
            return self._random_strategy(board_state)
        elif self.strategy == "defensive":
            return self._defensive_strategy(board_state, my_symbol)
        elif self.strategy == "offensive":
            return self._offensive_strategy(board_state, my_symbol)
        elif self.strategy == "minimax":
            return self._minimax_strategy(board_state, my_symbol)
        else:
            return self._random_strategy(board_state)

    def _random_strategy(self, board_state: list) -> tuple:
        """Make a random valid move."""
        empty_spots = [(r, c) for r in range(3) for c in range(3) if board_state[r][c] == " "]
        return random.choice(empty_spots) if empty_spots else (0, 0)

    def _defensive_strategy(self, board_state: list, my_symbol: str) -> tuple:
        """Block opponent wins, otherwise random."""
        opponent_symbol = "O" if my_symbol == "X" else "X"
        # Check if opponent can win next turn
        for r in range(3):
            for c in range(3):
                if board_state[r][c] == " ":
                    board_state[r][c] = opponent_symbol
                    if self._check_winner(board_state) == opponent_symbol:
                        board_state[r][c] = " "  # Reset
                        return (r, c)
                    board_state[r][c] = " "  # Reset
        return self._random_strategy(board_state)

    def _offensive_strategy(self, board_state: list, my_symbol: str) -> tuple:
        """Win if possible, otherwise block opponent."""
        # Check if we can win
        for r in range(3):
            for c in range(3):
                if board_state[r][c] == " ":
                    board_state[r][c] = my_symbol
                    if self._check_winner(board_state) == my_symbol:
                        board_state[r][c] = " "  # Reset
                        return (r, c)
                    board_state[r][c] = " "  # Reset
        # Otherwise be defensive
        return self._defensive_strategy(board_state, my_symbol)

    def _minimax_strategy(self, board_state: list, my_symbol: str) -> tuple:
        """Simple minimax implementation."""
        best_score = float('-inf')
        best_move = (0, 0)
        opponent_symbol = "O" if my_symbol == "X" else "X"
        
        for r in range(3):
            for c in range(3):
                if board_state[r][c] == " ":
                    board_state[r][c] = my_symbol
                    score = self._minimax(board_state, 0, False, my_symbol, opponent_symbol)
                    board_state[r][c] = " "
                    if score > best_score:
                        best_score = score
                        best_move = (r, c)
        return best_move

    def _minimax(self, board: list, depth: int, is_maximizing: bool, my_symbol: str, opponent_symbol: str) -> float:
        """Minimax algorithm implementation."""
        winner = self._check_winner(board)
        if winner == my_symbol:
            return 1.0
        elif winner == opponent_symbol:
            return -1.0
        elif self._is_board_full(board):
            return 0.0
            
        if is_maximizing:
            best_score = float('-inf')
            for r in range(3):
                for c in range(3):
                    if board[r][c] == " ":
                        board[r][c] = my_symbol
                        score = self._minimax(board, depth + 1, False, my_symbol, opponent_symbol)
                        board[r][c] = " "
                        best_score = max(score, best_score)
            return best_score
        else:
            best_score = float('inf')
            for r in range(3):
                for c in range(3):
                    if board[r][c] == " ":
                        board[r][c] = opponent_symbol
                        score = self._minimax(board, depth + 1, True, my_symbol, opponent_symbol)
                        board[r][c] = " "
                        best_score = min(score, best_score)
            return best_score

    def _check_winner(self, board: list) -> Optional[str]:
        """Check if there's a winner on the board."""
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

    def _is_board_full(self, board: list) -> bool:
        """Check if the board is full."""
        for row in board:
            for cell in row:
                if cell == " ":
                    return False
        return True

    async def _try_make_move(self):
        if not self.current_game_id:
            return

        # Simulate thinking time
        await asyncio.sleep(random.uniform(0.1, 0.5))

        # In a real implementation, this would get the actual board state
        # For now, we'll just log the intent
        self.logger.info(f"Player {self.player_id} thinking about move in game {self.current_game_id}")

    def assign_to_game(self, game_id: str, symbol: str):
        """Assign this player to a game."""
        self.current_game_id = game_id
        self.my_symbol = symbol
        self.logger.debug(f"Player {self.player_id} assigned to game {game_id} as {symbol}")

    def game_finished(self, winner: str):
        """Handle game completion."""
        won = winner == self.id
        if won:
            self.total_wins = (self.total_wins or 0) + 1
        
        # Call parent method for general game tracking
        super().record_game_result(won)
        
        self.current_game_id = None
        self.my_symbol = None
        self.logger.debug(f"Player {self.player_id} finished game. Won: {won}")

    def get_stats(self) -> dict:
        """Get player statistics."""
        stats = self.get_player_stats()
        total_wins = self.total_wins or 0
        games_played = self.games_played or 0
        stats.update({
            "strategy": self.strategy,
            "total_wins": total_wins,
            "win_rate": total_wins / max(1, games_played) if games_played > 0 else 0.0
        })
        return stats

    def get_widget(self, asset: str = "default", **kwargs) -> str:
        """Get a text widget representation of the player."""
        total_wins = self.total_wins or 0
        games_played = self.games_played or 0
        win_rate = total_wins / max(1, games_played) if games_played > 0 else 0.0
        return f"Player {self.player_id} ({self.strategy}): {games_played} games, {total_wins} wins ({win_rate:.1%})"

    def get_render_data(self) -> dict:
        """Get player data for rendering."""
        return self.get_stats()

    def __render__(self, width=160, height=80, asset="default", style="default", font=None, color=None, text_color=None, **kwargs):
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
            img = Image.new('RGB', (width, height), color=(60, 120, 60))
            draw = ImageDraw.Draw(img)
            text = str(getattr(self, 'name', None) or getattr(self, 'player_id', None) or getattr(self, 'id', None) or 'Player')
            try:
                font = ImageFont.truetype("DejaVuSans-Bold.ttf", 24)
            except Exception:
                font = None
            w, h = get_text_size(draw, text, font=font, multiline=False)
            draw.text(((width-w)//2, (height-h)//2), text, fill=(255, 255, 255), font=font)
            return img
        elif asset == "default":
            # If player is in a game, render the game state
            current_game = kwargs.get('current_game', None)
            if current_game is not None and hasattr(current_game, 'board'):
                return self._render_game_state(current_game, width, height)
            # Otherwise, show waiting/default info
            img = Image.new('RGB', (width, height), color=(60, 80, 120))
            draw = ImageDraw.Draw(img)
            name = str(getattr(self, 'name', None) or getattr(self, 'player_id', None) or getattr(self, 'id', None) or 'Player')
            strategy = getattr(self, 'strategy', 'unknown')
            status = "in game" if self.current_game_id else "waiting"
            text = f"{name}\n{strategy}\n{status}"
            try:
                font = ImageFont.truetype("DejaVuSans-Bold.ttf", 14)
            except Exception:
                font = None
            w, h = get_text_size(draw, text, font=font, multiline=True)
            draw.multiline_text(((width-w)//2, (height-h)//2), text, fill=(255, 255, 255), font=font, align="center")
            return img
        else:
            raise NotImplementedError(f"__render__ asset '{asset}' not implemented for {self.__class__.__name__}")

    def _render_game_state(self, game, width, height):
        """Render the current game state."""
        from PIL import Image, ImageDraw, ImageFont
        img = Image.new('RGB', (width, height), color=(40, 60, 90))
        draw = ImageDraw.Draw(img)
        
        # Draw the TicTacToe board
        board_size = min(width, height) - 20
        board_x = (width - board_size) // 2
        board_y = (height - board_size) // 2
        
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
                cell_val = game.board.board[r][c]
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
        
        return img

    def get_default_asset(self, width=160, height=80):
        """For compatibility, just call __render__."""
        return self.__render__(width=width, height=height, asset="default")
