"""
Breakout game implementation using Plantangenet activities and tournament system.
"""
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
import json

from plantangenet.game import TurnBasedGameActivity, GameState
from plantangenet.session.referee import Judgement
from plantangenet import GLOBAL_LOGGER

from .objects import Ball, Paddle, Block, BreakoutBoard
from .rect import Rect
from .widgets import BreakoutWidget


def render_breakout_game_state(board, width=300, height=200, game=None, info_text=None):
    from PIL import Image, ImageDraw
    # Create image with dark background
    img = Image.new('RGB', (width, height), color=(20, 20, 40))
    draw = ImageDraw.Draw(img)
    # Scale factors to fit board onto image
    scale_x = (width - 20) / board.width
    scale_y = (height - 20) / board.height
    offset_x, offset_y = 10, 10
    # Draw border
    draw.rectangle([5, 5, width-5, height-5], outline=(100, 100, 150), width=2)
    # Draw blocks
    for block in board.blocks:
        if not block.destroyed:
            x1 = int(block.x * scale_x + offset_x)
            y1 = int(block.y * scale_y + offset_y)
            x2 = int((block.x + block.width) * scale_x + offset_x)
            y2 = int((block.y + block.height) * scale_y + offset_y)
            draw.rectangle([x1, y1, x2, y2], fill=(
                255, 80, 80), outline=(200, 60, 60))
    # Draw paddle
    px1 = int(board.paddle.x * scale_x + offset_x)
    py1 = int(board.paddle.y * scale_y + offset_y)
    px2 = int((board.paddle.x + board.paddle.width) * scale_x + offset_x)
    py2 = int((board.paddle.y + board.paddle.height) * scale_y + offset_y)
    draw.rectangle([px1, py1, px2, py2], fill=(80, 180, 255))
    # Draw ball
    bx = int(board.ball.x * scale_x + offset_x)
    by = int(board.ball.y * scale_y + offset_y)
    br = max(2, int(board.ball.radius * min(scale_x, scale_y)))
    draw.ellipse([bx-br, by-br, bx+br, by+br], fill=(220, 220, 40))
    # Draw game info
    if info_text is None:
        score = getattr(board, 'score', 0)
        lives = getattr(board, 'lives', 0)
        turn = getattr(game, 'current_turn', None) if game else None
        info_text = f"Score: {score} | Lives: {lives} | Turn: {turn}"
    draw.text((10, height-20), info_text, fill=(255, 255, 255))
    return img


@dataclass
class BreakoutGame(TurnBasedGameActivity):
    """
    A Breakout game activity that supports single or multiple players taking turns.
    Inherits from TurnBasedGameActivity for turn management, policy enforcement, and widget support.
    """

    def __init__(self, game_id: str, *player_ids: str, player_strategies: Optional[dict] = None):
        super().__init__(game_id, *player_ids, max_players=4)
        self.board = BreakoutBoard()
        self.player_strategies = player_strategies or {}

    def make_game_move(self, player_id: str, row: int, col: int) -> Tuple[bool, str]:
        """
        Make a move in the Breakout game.
        For Breakout, we use row as action type: 0=left, 1=right, 2=wait
        Col parameter is ignored.
        """
        action_map = {0: "left", 1: "right", 2: "wait"}
        action = action_map.get(row, "wait")

        return self._make_breakout_move(player_id, action)

    def _make_breakout_move(self, player_id: str, action: str) -> Tuple[bool, str]:
        """
        Make a move in the Breakout game.
        Actions: 'left', 'right', 'wait'
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

        # Execute the action
        if action == "left":
            self.board.move_paddle_left()
        elif action == "right":
            self.board.move_paddle_right()
        elif action == "wait":
            pass  # No action
        else:
            return False, f"Invalid action: {action}"

        # Update game physics
        self.board.update()
        self.frames_elapsed += 1

        # Check for game end
        if self.board.is_game_over():
            self.game_state = GameState.GAME_OVER

        # Advance turn
        self.advance_turn()

        return True, f"Move executed: {action}"

    # Required abstract methods from MultiMemberTurnbasedActivity
    def _check_winner(self) -> Optional[str]:
        """Check if there is a winner."""
        if self.game_state == GameState.GAME_OVER and self.board.is_win():
            return self.current_turn  # Last player to move wins
        return None

    def get_game_state(self) -> Dict:
        """Get the current game state as a dictionary."""
        return {
            "game_id": self.game_id,
            "state": self.game_state.value,
            "current_turn": self.current_turn,
            "board": self.board.to_dict(),
            "frames_elapsed": self.frames_elapsed,
            "is_win": self.board.is_win() if self.game_state == GameState.GAME_OVER else False
        }

    def get_widget(self, asset: str = "default", **kwargs) -> str:
        """Get a text-based widget representation of the game, including player strategies iconographically."""
        return BreakoutWidget(self).render()

    def __render__(self, width=300, height=80, asset="default", style="default", font=None, color=None, text_color=None, **kwargs) -> Any:
        """
        Unified render method for dashboard/compositor use.
        Returns a flexible type (e.g., PIL.Image.Image, str, ML model output, etc.) depending on the asset and context.
        This endpoint is intentionally polymorphic to support a wide range of renderable outputs.
        """
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
            img = Image.new('RGB', (width, height), color=(60, 180, 80))
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
            # Default: show the full game state as before
            return self.get_default_asset(width=width, height=height)
        else:
            raise NotImplementedError(
                f"__render__ asset '{asset}' not implemented for {self.__class__.__name__}")

    def get_default_asset(self, width=300, height=200):
        return render_breakout_game_state(self.board, width=width, height=height, game=self)
