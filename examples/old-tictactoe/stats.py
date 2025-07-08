"""
Statistics tracking for TicTacToe tournaments.
"""
from typing import Dict, Any
from collections import defaultdict

from plantangenet.agents.agent import Agent
from plantangenet.game import StatsAgentMixin
from plantangenet import GLOBAL_LOGGER


class TicTacToeStats(Agent, StatsAgentMixin):
    """Agent for tracking TicTacToe tournament statistics."""

    def __init__(self, logger=None):
        Agent.__init__(self, namespace="tictactoe", logger=logger or GLOBAL_LOGGER)
        StatsAgentMixin.__init__(self)
        self.player_wins = defaultdict(int)
        self.ties = 0
        self.total_moves = 0

    async def update(self) -> bool:
        """Periodic update - collect stats from other agents."""
        return True

    def record_game_result(self, player_x: str, player_o: str, winner: str):
        """Record the result of a completed game."""
        # Call parent method
        super().record_game_result()

        if winner == "DRAW" or winner == "tie":
            self.ties += 1
        else:
            self.player_wins[winner] += 1

        # Update stats data
        self.stats_data.update({
            "ties": self.ties,
            "total_moves": self.total_moves
        })

    def get_player_stats(self, player_id: str) -> Dict[str, Any]:
        """Get statistics for a specific player."""
        games_played = sum(1 for x, o in [(x, o) for x in [player_id] for o in self.player_wins.keys() if x != o]) + \
                      sum(1 for x, o in [(x, o) for x in self.player_wins.keys() for o in [player_id] if x != o])
        return {
            "games_played": games_played,
            "wins": self.player_wins[player_id],
            "win_rate": self.player_wins[player_id] / max(1, games_played) if games_played > 0 else 0.0
        }

    def get_leaderboard(self) -> list:
        """Get a leaderboard sorted by wins."""
        players = set(self.player_wins.keys())
        leaderboard = []

        for player in players:
            stats = self.get_player_stats(player)
            leaderboard.append({
                "player": player,
                **stats
            })

        # Sort by wins (descending), then by win rate (descending)
        leaderboard.sort(key=lambda x: (x["wins"], x["win_rate"]), reverse=True)
        return leaderboard

    def get_widget(self, asset: str = "default", **kwargs) -> str:
        """Get a text widget representation of current stats."""
        if self.total_games == 0:
            return "TicTacToe Stats: No games played yet"

        leaderboard = self.get_leaderboard()
        top_player = leaderboard[0] if leaderboard else None

        if top_player:
            return (f"TicTacToe Stats: {self.total_games} games, "
                    f"Leader: {top_player['player']} ({top_player['wins']} wins, "
                    f"rate: {top_player['win_rate']:.1%})")
        else:
            return f"TicTacToe Stats: {self.total_games} games played"

    def get_render_data(self) -> Dict[str, Any]:
        """Get stats data for rendering."""
        return {
            "stats": self.get_stats_summary(),
            "players": {player: self.get_player_stats(player) for player in self.player_wins.keys()},
            "leaderboard": self.get_leaderboard()
        }

    def __render__(self, width=300, height=80, asset="default", style="default", font=None, color=None, text_color=None, **kwargs):
        """Unified render method for dashboard/compositor use."""
        from PIL import Image, ImageDraw, ImageFont

        if asset == "widget":
            img = Image.new('RGB', (width, height), color=(80, 40, 120))
            draw = ImageDraw.Draw(img)
            text = "TicTacToe Stats"
            try:
                font = ImageFont.truetype("DejaVuSans-Bold.ttf", 20)
            except Exception:
                font = None
            if font:
                bbox = draw.textbbox((0, 0), text, font=font)
                w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
                draw.text(((width-w)//2, (height-h)//2), text, fill=(255, 255, 255), font=font)
            else:
                draw.text((10, 10), text, fill=(255, 255, 255))
            return img
        elif asset == "default":
            # Default: detailed stats display
            return self.get_default_asset(width=width, height=height)
        else:
            raise NotImplementedError(f"__render__ asset '{asset}' not implemented for {self.__class__.__name__}")

    def get_default_asset(self, width=300, height=200):
        """Render detailed stats display."""
        from PIL import Image, ImageDraw, ImageFont
        img = Image.new('RGB', (width, height), color=(80, 40, 120))
        draw = ImageDraw.Draw(img)
        
        try:
            title_font = ImageFont.truetype("DejaVuSans-Bold.ttf", 16)
            text_font = ImageFont.truetype("DejaVuSans.ttf", 12)
        except Exception:
            title_font = text_font = None
        
        # Title
        y = 10
        draw.text((10, y), "TicTacToe Tournament Stats", font=title_font, fill=(255, 255, 0))
        y += 25
        
        # Overall stats
        draw.text((10, y), f"Total Games: {self.total_games}", font=text_font, fill=(255, 255, 255))
        y += 15
        draw.text((10, y), f"Ties: {self.ties}", font=text_font, fill=(255, 255, 255))
        y += 15
        draw.text((10, y), f"Total Moves: {self.total_moves}", font=text_font, fill=(255, 255, 255))
        y += 25
        
        # Leaderboard
        draw.text((10, y), "Leaderboard:", font=title_font, fill=(255, 255, 0))
        y += 20
        
        leaderboard = self.get_leaderboard()[:5]  # Top 5
        for i, player_stats in enumerate(leaderboard):
            player = player_stats['player']
            wins = player_stats['wins']
            win_rate = player_stats['win_rate']
            text = f"{i+1}. {player}: {wins} wins ({win_rate:.1%})"
            draw.text((15, y), text, font=text_font, fill=(200, 200, 200))
            y += 15
        
        return img
