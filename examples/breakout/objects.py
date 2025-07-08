"""
Breakout game objects: Ball, Paddle, Block, BreakoutBoard.
"""
from typing import List, Optional
import random
import ulid
from dataclasses import dataclass


@dataclass
class Ball:
    x: float
    y: float
    dx: float  # velocity x
    dy: float  # velocity y
    radius: float = 5.0
    id: Optional[str] = None

    def __post_init__(self):
        if self.id is None:
            self.id = str(ulid.ULID())

    def move(self):
        self.x += self.dx
        self.y += self.dy

    def to_dict(self):
        return {"x": self.x, "y": self.y, "dx": self.dx, "dy": self.dy, "radius": self.radius}

    def __render__(self, width=300, height=80, asset="default", style="default", font=None, color=None, text_color=None, **kwargs):
        """Unified render method for dashboard/compositor use."""
        # For now, just call get_default_asset if present, else raise
        if hasattr(self, 'get_default_asset'):
            return self.get_default_asset(width=width, height=height)
        raise NotImplementedError(
            f"__render__ not implemented for {self.__class__.__name__}")

    def get_default_asset(self, width=80, height=80):
        from PIL import Image, ImageDraw
        img = Image.new('RGB', (width, height), color=(30, 30, 30))
        draw = ImageDraw.Draw(img)
        # Draw a circle for the ball
        r = min(width, height) // 4
        cx, cy = width // 2, height // 2
        draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(220, 220, 40))
        draw.text((10, 10), "Ball", fill=(255, 255, 255))
        return img


@dataclass
class Paddle:
    x: float
    y: float
    width: float = 80.0
    height: float = 10.0
    speed: float = 5.0
    id: Optional[str] = None

    def __post_init__(self):
        if self.id is None:
            self.id = str(ulid.ULID())

    def move_left(self, game_width: float):
        self.x = max(0, self.x - self.speed)

    def move_right(self, game_width: float):
        self.x = min(game_width - self.width, self.x + self.speed)

    def to_dict(self):
        return {"x": self.x, "y": self.y, "width": self.width, "height": self.height}

    def __render__(self, width=300, height=80, asset="default", style="default", font=None, color=None, text_color=None, **kwargs):
        """Unified render method for dashboard/compositor use."""
        # For now, just call get_default_asset if present, else raise
        if hasattr(self, 'get_default_asset'):
            return self.get_default_asset(width=width, height=height)
        raise NotImplementedError(
            f"__render__ not implemented for {self.__class__.__name__}")

    def get_default_asset(self, width=120, height=40):
        from PIL import Image, ImageDraw
        img = Image.new('RGB', (width, height), color=(30, 30, 30))
        draw = ImageDraw.Draw(img)
        # Draw a rectangle for the paddle
        pad_h = height // 3
        draw.rectangle([10, height//2 - pad_h//2, width-10,
                       height//2 + pad_h//2], fill=(80, 180, 255))
        draw.text((10, 10), "Paddle", fill=(255, 255, 255))
        return img


@dataclass
class Block:
    x: float
    y: float
    width: float = 40.0
    height: float = 20.0
    hits_remaining: int = 1
    destroyed: bool = False
    id: Optional[str] = None

    def __post_init__(self):
        if self.id is None:
            self.id = str(ulid.ULID())

    def hit(self):
        self.hits_remaining -= 1
        if self.hits_remaining <= 0:
            self.destroyed = True

    def to_dict(self):
        return {"x": self.x, "y": self.y, "width": self.width, "height": self.height,
                "hits_remaining": self.hits_remaining, "destroyed": self.destroyed}

    def __render__(self, width=300, height=80, asset="default", style="default", font=None, color=None, text_color=None, **kwargs):
        """Unified render method for dashboard/compositor use."""
        # For now, just call get_default_asset if present, else raise
        if hasattr(self, 'get_default_asset'):
            return self.get_default_asset(width=width, height=height)
        raise NotImplementedError(
            f"__render__ not implemented for {self.__class__.__name__}")

    def get_default_asset(self, width=60, height=40):
        from PIL import Image, ImageDraw
        img = Image.new('RGB', (width, height), color=(30, 30, 30))
        draw = ImageDraw.Draw(img)
        # Draw a rectangle for the block
        draw.rectangle([10, 10, width-10, height-10], fill=(255, 80, 80))
        draw.text((10, 10), "Block", fill=(255, 255, 255))
        return img


class BreakoutBoard:
    def __init__(self, width: float = 800.0, height: float = 600.0):
        self.width = width
        self.height = height
        self.ball = Ball(width/2, height/2, 3.0, -3.0)
        self.paddle = Paddle(width/2 - 40, height - 50)
        self.blocks = self._create_blocks()
        self.score = 0
        self.lives = 3

    def _create_blocks(self) -> List[Block]:
        blocks = []
        rows = 5
        cols = 15
        block_width = 50.0
        block_height = 20.0
        start_x = 25.0
        start_y = 50.0

        for row in range(rows):
            for col in range(cols):
                x = start_x + col * (block_width + 5)
                y = start_y + row * (block_height + 5)
                blocks.append(Block(x, y, block_width, block_height))

        return blocks

    def update(self):
        self.ball.move()
        if self.ball.x <= self.ball.radius or self.ball.x >= self.width - self.ball.radius:
            self.ball.dx *= -1
        if self.ball.y <= self.ball.radius:
            self.ball.dy *= -1
        if self.ball.y >= self.height - self.ball.radius:
            self.lives -= 1
            if self.lives > 0:
                self._reset_ball()
        if (self.ball.y + self.ball.radius >= self.paddle.y and
            self.ball.x >= self.paddle.x and
                self.ball.x <= self.paddle.x + self.paddle.width):
            self.ball.dy = -abs(self.ball.dy)
        for block in self.blocks:
            if not block.destroyed and self._ball_block_collision(block):
                block.hit()
                if block.destroyed:
                    self.score += 10
                self.ball.dy *= -1
                break

    def _reset_ball(self):
        self.ball.x = self.width / 2
        self.ball.y = self.height / 2
        self.ball.dx = random.choice([-3.0, 3.0])
        self.ball.dy = -3.0

    def _ball_block_collision(self, block: Block) -> bool:
        return (self.ball.x + self.ball.radius >= block.x and
                self.ball.x - self.ball.radius <= block.x + block.width and
                self.ball.y + self.ball.radius >= block.y and
                self.ball.y - self.ball.radius <= block.y + block.height)

    def move_paddle_left(self):
        self.paddle.move_left(self.width)

    def move_paddle_right(self):
        self.paddle.move_right(self.width)

    def is_game_over(self) -> bool:
        return self.lives <= 0 or all(block.destroyed for block in self.blocks)

    def is_win(self) -> bool:
        return all(block.destroyed for block in self.blocks)

    def to_dict(self):
        return {
            "width": self.width,
            "height": self.height,
            "ball": self.ball.to_dict(),
            "paddle": self.paddle.to_dict(),
            "blocks": [block.to_dict() for block in self.blocks if not block.destroyed],
            "score": self.score,
            "lives": self.lives
        }

    def __render__(self, width=300, height=80, asset="default", style="default", font=None, color=None, text_color=None, **kwargs):
        """Unified render method for dashboard/compositor use."""
        # For now, just call get_default_asset if present, else raise
        if hasattr(self, 'get_default_asset'):
            return self.get_default_asset(width=width, height=height)
        raise NotImplementedError(
            f"__render__ not implemented for {self.__class__.__name__}")

    def get_default_asset(self, width=240, height=120):
        from PIL import Image, ImageDraw
        img = Image.new('RGB', (width, height), color=(20, 20, 40))
        draw = ImageDraw.Draw(img)
        # Draw a simple board outline
        draw.rectangle([5, 5, width-5, height-5],
                       outline=(200, 200, 200), width=2)
        draw.text((10, 10), "Board", fill=(255, 255, 255))
        return img
