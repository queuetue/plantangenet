"""
Breakout player agent with simple AI strategies.
"""
import random
from typing import Optional
from plantangenet.agents.agent import Agent
from plantangenet.game import GamePlayerMixin
from plantangenet import GLOBAL_LOGGER
from plantangenet.omni.base import OmniBase
from plantangenet.omni.observable import Observable
from plantangenet.omni.persisted import PersistedBase


class BreakoutPlayer(OmniBase, Agent, GamePlayerMixin):
    """AI player for Breakout games with configurable strategies (Omni-compatible)."""
    strategy: str = PersistedBase(default="random")
    total_score: int = Observable(default=0)

    def __init__(self, player_id: str, strategy: str = "random", logger=None, **kwargs):
        OmniBase.__init__(self, **kwargs)
        Agent.__init__(self, namespace="breakout",
                       logger=logger or GLOBAL_LOGGER)
        GamePlayerMixin.__init__(self, player_id)
        self.strategy = strategy

    @property
    def session(self):
        return getattr(self, '_omni__session', None)

    @session.setter
    def session(self, value):
        self._omni__session = value

    async def update(self) -> bool:
        """Periodic update - players are reactive, so this is minimal."""
        return True

    def choose_action(self, game_state: dict) -> str:
        """
        Choose an action based on the current game state and strategy.
        Returns: 'left', 'right', or 'wait'
        """
        if self.strategy == "random":
            return random.choice(["left", "right", "wait"])
        elif self.strategy == "follow_ball":
            return self._follow_ball_strategy(game_state)
        elif self.strategy == "center":
            return self._center_strategy(game_state)
        elif self.strategy == "aggressive":
            return self._aggressive_strategy(game_state)
        else:
            return "wait"  # Default to wait if strategy unknown

    def _follow_ball_strategy(self, game_state: dict) -> str:
        """Follow the ball's X position."""
        board = game_state.get("board", {})
        ball = board.get("ball", {})
        paddle = board.get("paddle", {})

        ball_x = ball.get("x", 0)
        paddle_x = paddle.get("x", 0)
        paddle_width = paddle.get("width", 80)
        paddle_center = paddle_x + paddle_width / 2

        # Move toward the ball
        if ball_x < paddle_center - 10:
            return "left"
        elif ball_x > paddle_center + 10:
            return "right"
        else:
            return "wait"

    def _center_strategy(self, game_state: dict) -> str:
        """Always try to center the paddle."""
        board = game_state.get("board", {})
        paddle = board.get("paddle", {})

        board_width = board.get("width", 800)
        paddle_x = paddle.get("x", 0)
        paddle_width = paddle.get("width", 80)
        paddle_center = paddle_x + paddle_width / 2
        board_center = board_width / 2

        # Move toward center
        if paddle_center < board_center - 10:
            return "right"
        elif paddle_center > board_center + 10:
            return "left"
        else:
            return "wait"

    def _aggressive_strategy(self, game_state: dict) -> str:
        """Try to position paddle to hit ball at an angle."""
        board = game_state.get("board", {})
        ball = board.get("ball", {})
        paddle = board.get("paddle", {})

        ball_x = ball.get("x", 0)
        ball_y = ball.get("y", 0)
        ball_dy = ball.get("dy", 0)
        paddle_x = paddle.get("x", 0)
        paddle_width = paddle.get("width", 80)
        paddle_y = paddle.get("y", 0)

        # If ball is moving down and close to paddle
        if ball_dy > 0 and ball_y > paddle_y - 100:
            # Position paddle edge to create angle
            if ball_x < paddle_x + paddle_width * 0.3:
                return "left"
            elif ball_x > paddle_x + paddle_width * 0.7:
                return "right"
            else:
                return "wait"
        else:
            # Otherwise follow ball
            return self._follow_ball_strategy(game_state)

    def record_game_result(self, won: bool, score: int = 0, **kwargs):
        """Record the result of a completed game."""
        # Call parent method
        super().record_game_result(won, **kwargs)
        # Track Breakout-specific data
        self.total_score += score
        self.performance_data["total_score"] = self.total_score
        self.performance_data["average_score"] = self.total_score / \
            max(1, self.games_played)

    def get_stats(self) -> dict:
        """Get player statistics."""
        stats = self.get_player_stats()
        stats.update({
            "strategy": self.strategy,
            "total_score": self.total_score,
            "average_score": self.total_score / max(1, self.games_played)
        })
        return stats

    def get_widget(self, asset: str = "default", **kwargs) -> str:
        """Get a text widget representation of the player."""
        avg_score = self.total_score / max(1, self.games_played)
        return f"Player {self.player_id} ({self.strategy}): {self.games_played} games, avg score: {avg_score:.1f}"

    def get_render_data(self) -> dict:
        """Get player data for rendering."""
        return self.get_stats()

    def __render__(self, width=160, height=80, asset="default", style="default", font=None, color=None, text_color=None, **kwargs):
        """Unified render method for dashboard/compositor use."""
        from PIL import Image, ImageDraw, ImageFont

        def get_text_size(draw, text, font=None, multiline=False):
            # Helper for text size, multiline if needed
            if multiline and hasattr(draw, 'multiline_textbbox'):
                bbox = draw.multiline_textbbox(
                    (0, 0), text, font=font, align="center")
                w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
            elif not multiline and hasattr(draw, 'textbbox'):
                bbox = draw.textbbox((0, 0), text, font=font)
                w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
            else:
                # Fallback: estimate
                lines = text.split('\n') if multiline else [text]
                w = max([len(line) for line in lines]) * 8
                h = 16 * len(lines)
            return w, h
        if asset == "widget":
            img = Image.new('RGB', (width, height), color=(40, 120, 200))
            draw = ImageDraw.Draw(img)
            text = str(getattr(self, 'name', None) or getattr(
                self, 'player_id', None) or getattr(self, 'id', None) or 'Player')
            try:
                font = ImageFont.truetype("DejaVuSans-Bold.ttf", 24)
            except Exception:
                font = None
            w, h = get_text_size(draw, text, font=font, multiline=False)
            draw.text(((width-w)//2, (height-h)//2), text,
                      fill=(255, 255, 255), font=font)
            return img
        elif asset == "default":
            # If player is in a game, render the game state using the shared function
            current_game = kwargs.get('current_game', None)
            if current_game is not None:
                # If current_game is a game object with a board, render it
                if hasattr(current_game, 'board'):
                    from .game import render_breakout_game_state
                    return render_breakout_game_state(current_game.board, width=width, height=height, game=current_game)
            # Otherwise, show waiting/default info
            img = Image.new('RGB', (width, height), color=(40, 80, 180))
            draw = ImageDraw.Draw(img)
            name = str(getattr(self, 'name', None) or getattr(
                self, 'player_id', None) or getattr(self, 'id', None) or 'Player')
            strategy = getattr(self, 'strategy', 'unknown')
            text = f"{name}\n{strategy}\nwaiting"
            try:
                font = ImageFont.truetype("DejaVuSans-Bold.ttf", 14)
            except Exception:
                font = None
            w, h = get_text_size(draw, text, font=font, multiline=True)
            draw.multiline_text(((width-w)//2, (height-h)//2), text,
                                fill=(255, 255, 255), font=font, align="center")
            return img
        else:
            raise NotImplementedError(
                f"__render__ asset '{asset}' not implemented for {self.__class__.__name__}")

    def get_default_asset(self, width=160, height=80):
        # For compatibility, just call __render__
        return self.__render__(width=width, height=height, asset="default")
