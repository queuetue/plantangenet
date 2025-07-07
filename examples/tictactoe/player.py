import asyncio
import random
from plantangenet.agents.agent import Agent
from typing import Optional


class TicTacToePlayer(Agent):
    def __init__(self, namespace: str = "tictactoe", logger=None):
        super().__init__(namespace, logger)
        self.current_game_id: Optional[str] = None
        self.my_symbol: Optional[str] = None
        self.games_played = 0
        self.games_won = 0
        self.move_history = []

    @property
    def logger(self):
        return self._ocean__logger

    async def update(self) -> bool:
        # Check for new game assignments or game state updates
        if self.current_game_id:
            # Make a move if it's our turn
            await self._try_make_move()
        return True

    async def _try_make_move(self):
        if not self.current_game_id:
            return

        # Simulate thinking time
        await asyncio.sleep(random.uniform(0.1, 0.5))

        # Make a random valid move (simple AI)
        row, col = random.randint(0, 2), random.randint(0, 2)

        # In a real implementation, this would send a message to the referee
        # For now, we'll just log the intent
        self.logger.info(
            f"Player {self._ocean__nickname} attempting move at ({row}, {col}) in game {self.current_game_id}")
        self.move_history.append((self.current_game_id, row, col))

    def assign_to_game(self, game_id: str, symbol: str):
        self.current_game_id = game_id
        self.my_symbol = symbol
        self.logger.debug(
            f"Player {self._ocean__nickname} assigned to game {game_id} as {symbol}")

    def game_finished(self, winner: str):
        self.games_played += 1
        if winner == self._ocean__id:
            self.games_won += 1
        self.current_game_id = None
        self.my_symbol = None
        self.logger.debug(
            f"Player {self._ocean__nickname} finished game. Won: {winner == self._ocean__id}")

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
