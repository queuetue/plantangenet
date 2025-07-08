"""
Visually distinctive widgets for the Breakout game objects.
"""
from typing import List, Dict
from .objects import Ball, Paddle, Block, BreakoutBoard


class BallWidget:
    """Renders the ball."""

    def __init__(self, ball: Ball):
        self.ball = ball

    def render(self) -> str:
        return "●"


class PaddleWidget:
    """Renders the paddle."""

    def __init__(self, paddle: Paddle):
        self.paddle = paddle

    def render(self) -> str:
        # Scale width for display
        return "▀" * int(self.paddle.width / 10)


class BlockWidget:
    """Renders a block."""

    def __init__(self, block: Block):
        self.block = block

    def render(self) -> str:
        if self.block.destroyed:
            return "  "
        return "[▓▓]"


class GameBoardWidget:
    """Renders the entire game board as a grid."""

    def __init__(self, board: BreakoutBoard, width: int = 80, height: int = 24):
        self.board = board
        self.width = width
        self.height = height
        self.grid = [[' ' for _ in range(width)] for _ in range(height)]

    def _place_object(self, x: int, y: int, representation: str):
        """Places a string representation of an object on the grid."""
        if 0 <= y < self.height:
            for i, char in enumerate(representation):
                if 0 <= x + i < self.width:
                    self.grid[y][x + i] = char

    def render(self) -> str:
        """Renders the grid with all game objects."""
        # Clear grid
        self.grid = [[' ' for _ in range(self.width)]
                     for _ in range(self.height)]

        # Scale game coordinates to grid coordinates
        scale_x = self.width / self.board.width
        scale_y = self.height / self.board.height

        # Draw paddle
        paddle_x = int(self.board.paddle.x * scale_x)
        paddle_y = int(self.board.paddle.y * scale_y)
        paddle_repr = PaddleWidget(self.board.paddle).render()
        self._place_object(paddle_x, paddle_y, paddle_repr)

        # Draw ball
        ball_x = int(self.board.ball.x * scale_x)
        ball_y = int(self.board.ball.y * scale_y)
        ball_repr = BallWidget(self.board.ball).render()
        self._place_object(ball_x, ball_y, ball_repr)

        # Draw blocks
        for block in self.board.blocks:
            if not block.destroyed:
                block_x = int(block.x * scale_x)
                block_y = int(block.y * scale_y)
                block_repr = BlockWidget(block).render()
                self._place_object(block_x, block_y, block_repr)

        # Draw border
        rendered_grid = [list(row) for row in self.grid]
        for y in range(self.height):
            rendered_grid[y][0] = '|'
            rendered_grid[y][self.width - 1] = '|'
        for x in range(self.width):
            rendered_grid[0][x] = '-'
            rendered_grid[self.height - 1][x] = '-'
        rendered_grid[0][0] = '+'
        rendered_grid[0][self.width - 1] = '+'
        rendered_grid[self.height - 1][0] = '+'
        rendered_grid[self.height - 1][self.width - 1] = '+'

        return "\n".join("".join(row) for row in rendered_grid)


class BreakoutWidget:
    """A composite widget for the entire Breakout game."""

    def __init__(self, game):  # game is BreakoutGame
        self.game = game

    def render(self) -> str:
        """Renders the complete game view with header and board."""
        board = self.game.board
        board_widget = GameBoardWidget(board)
        board_str = board_widget.render()

        # Player info
        strategy_icons = {
            "random": "●",
            "follow_ball": "▲",
            "center": "■",
            "aggressive": "★"
        }
        player_lines = []
        for pid in self.game.turn_order:
            strat = self.game.player_strategies.get(pid, "?")
            icon = strategy_icons.get(strat, "?")
            player_lines.append(f"  {pid}: {icon} ({strat})")
        players_str = "\n".join(
            player_lines) if player_lines else "  (no players)"

        header = f"Breakout Game {self.game.game_id}: Score={board.score}, Lives={board.lives}, Turn={self.game.current_turn}"

        return f"{header}\nPlayers:\n{players_str}\n{board_str}"
