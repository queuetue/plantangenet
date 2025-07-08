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

    def _minimax(self, board: list, depth: int, is_maximizing: bool, my_symbol: str, opponent_symbol: str) -> int:
        """Minimax algorithm implementation."""
        winner = self._check_winner(board)
        if winner == my_symbol:
            return 1
        elif winner == opponent_symbol:
            return -1
        elif self._is_board_full(board):
            return 0
            
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
            self.total_wins += 1
        
        # Call parent method for general game tracking
        super().record_game_result(won)
        
        self.current_game_id = None
        self.my_symbol = None
        self.logger.debug(f"Player {self.player_id} finished game. Won: {won}")

    def get_stats(self) -> dict:
        """Get player statistics."""
        stats = self.get_player_stats()
        stats.update({
            "strategy": self.strategy,
            "total_wins": self.total_wins,
            "win_rate": self.total_wins / max(1, self.games_played) if self.games_played > 0 else 0.0
        })
        return stats

    def get_widget(self, asset: str = "default", **kwargs) -> str:
        """Get a text widget representation of the player."""
        win_rate = self.total_wins / max(1, self.games_played) if self.games_played > 0 else 0.0
        return f"Player {self.player_id} ({self.strategy}): {self.games_played} games, {self.total_wins} wins ({win_rate:.1%})"

    def get_render_data(self) -> dict:
        """Get player data for rendering."""
        return self.get_stats()

    def __render__(self, width=300, height=80, asset="default", style="default", font=None, color=None, text_color=None):
        """
        Render a widget representing this player for the dashboard.
        Supports multiple styles: 'default', 'radial', 'compact'.
        Returns a Pillow Image object.
        """
        from PIL import Image, ImageDraw, ImageFont
        img = Image.new("RGB", (width, height), color or (60, 120, 60))
        draw = ImageDraw.Draw(img)
        # Use provided font or default
        if font is None:
            try:
                font = ImageFont.truetype("DejaVuSans-Bold.ttf", 16)
            except Exception:
                font = ImageFont.load_default()
        # Draw border
        border_color = (0, 180, 0)
        draw.rectangle([0, 0, width-1, height-1],
                       outline=border_color, width=2)
        # Helper for text size

        def get_text_size(text, font):
            bbox = draw.textbbox((0, 0), text, font=font)
            return bbox[2] - bbox[0], bbox[3] - bbox[1]
        # Choose style
        if style == "radial":
            # Radial progress: games played (outer), games won (inner)
            import math
            cx, cy = width // 2, height // 2
            r_outer = min(width, height) // 2 - 8
            r_inner = r_outer - 10
            # Draw outer circle (games played)
            total = max(1, self.games_played)
            angle_played = int(360 * self.games_played /
                               (self.games_played + 1))
            draw.arc([cx - r_outer, cy - r_outer, cx + r_outer, cy + r_outer],
                     start=0, end=angle_played, fill=(100, 200, 100), width=6)
            # Draw inner circle (games won)
            angle_won = int(360 * self.games_won / total)
            draw.arc([cx - r_inner, cy - r_inner, cx + r_inner, cy + r_inner],
                     start=0, end=angle_won, fill=(255, 215, 0), width=4)
            # Draw center text
            text = f"{self._ocean__nickname or 'Player'}\n{self.games_won}/{self.games_played}"
            lines = text.split("\n")
            line_heights = [get_text_size(line, font)[1] for line in lines]
            total_height = sum(line_heights)
            y = cy - total_height // 2
            for line, lh in zip(lines, line_heights):
                w, _ = get_text_size(line, font)
                draw.text((cx - w//2, y), line, font=font,
                          fill=text_color or (255, 255, 255), align="center")
                y += lh
        elif style == "compact":
            # Compact: just name and stats
            text = f"{self._ocean__nickname or 'Player'}\nW: {self.games_won} / {self.games_played}"
            lines = text.split("\n")
            y = 10
            for line in lines:
                w, h = get_text_size(line, font)
                draw.text((10, y), line, font=font,
                          fill=text_color or (255, 255, 255))
                y += h
        else:
            # Default: avatar circle + stats
            cx, cy = width // 2, height // 2
            r = min(width, height) // 3
            draw.ellipse([cx - r, cy - r, cx + r, cy + r],
                         fill=(0, 180, 0), outline=(255, 255, 255), width=2)
            text = f"{self._ocean__nickname or 'Player'}"
            w, h = get_text_size(text, font)
            draw.text((cx - w//2, cy - h//2), text, font=font,
                      fill=text_color or (255, 255, 255))
            # Stats at bottom
            stats = f"W: {self.games_won} / {self.games_played}"
            sw, sh = get_text_size(stats, font)
            draw.text((cx - sw//2, height - sh - 6), stats,
                      font=font, fill=(200, 255, 200))
        return img
