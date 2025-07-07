from plantangenet.agents.agent import Agent


class TicTacToeStats(Agent):
    def __init__(self, namespace: str = "tictactoe", logger=None):
        super().__init__(namespace, logger)
        self.total_moves = 0
        self.total_games = 0
        self.comdecs = []
        self.player_wins = {}  # player_id -> win count
        self.ties = 0

    def add_comdec(self, comdec):
        self.comdecs.append(comdec)

    def record_game_result(self, player_x, player_o, winner):
        self.total_games += 1
        if winner == "DRAW" or winner == "tie":
            self.ties += 1
        else:
            self.player_wins[winner] = self.player_wins.get(winner, 0) + 1

    @property
    def logger(self):
        return self._ocean__logger

    async def update(self) -> bool:
        # Collect stats from other agents (in real implementation, would query Redis)
        return True

    async def output_all(self, *args, **kwargs):
        """Call consume on all registered comdecs with stats data."""
        stats_data = {
            "stats": {
                "total_games": self.total_games,
                "player_wins": dict(self.player_wins),
                "ties": self.ties,
                "total_moves": self.total_moves,
            }
        }
        for comdec in self.comdecs:
            if hasattr(comdec, 'consume'):
                await comdec.consume(stats_data, *args, **kwargs)

    @property
    def player_wins(self):
        return self._player_wins

    @player_wins.setter
    def player_wins(self, value):
        self._player_wins = value

    @property
    def ties(self):
        return self._ties

    @ties.setter
    def ties(self, value):
        self._ties = value

    def get_default(self, **kwargs):
        """Default widget rendering (used if asset is unknown)."""
        return self.__render__(asset="default", **kwargs)

    def get_widget(self, asset="status_widget", **kwargs):
        """Return the widget image for the given asset type (default: status_widget)."""
        if asset == "status_widget":
            return self.__render__(asset=asset, **kwargs)
        # Placeholder for future asset types
        return self.get_default(**kwargs)

    def __render__(self, width=300, height=80, asset="default", style="default", font=None, color=None, text_color=None):
        """
        Render a widget representing stats for the dashboard.
        Returns a Pillow Image object.
        """
        if asset == "status_widget":
            # Render the status widget (main stats summary)
            from PIL import Image, ImageDraw, ImageFont
            img = Image.new("RGB", (width, height), color or (80, 80, 80))
            draw = ImageDraw.Draw(img)
            # Use provided font or default
            if font is None:
                try:
                    font = ImageFont.truetype("DejaVuSans-Bold.ttf", 16)
                except Exception:
                    font = ImageFont.load_default()
            # Draw border
            border_color = (180, 180, 0)
            draw.rectangle([0, 0, width-1, height-1],
                           outline=border_color, width=2)
            # Draw stats summary
            text = (
                f"Stats\nGames: {self.total_games}\nTies: {self.ties}\nMoves: {self.total_moves}\n"
                f"Top: {max(self.player_wins, key=self.player_wins.get) if self.player_wins else '-'}"
            )
            # Helper for text size

            def get_text_size(text, font):
                bbox = draw.textbbox((0, 0), text, font=font)
                return bbox[2] - bbox[0], bbox[3] - bbox[1]
            lines = text.split("\n")
            y = 10
            for line in lines:
                w, h = get_text_size(line, font)
                draw.text((10, y), line, font=font,
                          fill=text_color or (255, 255, 255))
                y += h
            return img
        else:
            # Fallback to get_default for unknown asset types
            return self.get_default(width=width, height=height, style=style, font=font, color=color, text_color=text_color)
