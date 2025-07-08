"""
Statistics tracking for Breakout tournaments.
"""
from typing import Dict, Any
from collections import defaultdict

from plantangenet.agents.agent import Agent
from plantangenet.game import StatsAgentMixin
from plantangenet import GLOBAL_LOGGER


class BreakoutStats(Agent, StatsAgentMixin):
    """Agent for tracking Breakout tournament statistics."""

    def __init__(self, logger=None):
        Agent.__init__(self, namespace="breakout",
                       logger=logger or GLOBAL_LOGGER)
        StatsAgentMixin.__init__(self)
        self.player_wins = defaultdict(int)
        # List of scores for each player
        self.player_scores = defaultdict(list)
        self.ties = 0
        self.average_game_length = 0.0
        self.total_frames = 0

    def record_game_result(self, player1: str, player2: str, winner: str,
                           player1_score: int = 0, player2_score: int = 0,
                           frames: int = 0):
        """Record the result of a completed game."""
        # Call parent method
        super().record_game_result()

        self.total_frames += frames

        if winner == "tie":
            self.ties += 1
        else:
            self.player_wins[winner] += 1

        self.player_scores[player1].append(player1_score)
        self.player_scores[player2].append(player2_score)

        if self.total_games > 0:
            self.average_game_length = self.total_frames / self.total_games

        # Update stats data
        self.stats_data.update({
            "ties": self.ties,
            "average_game_length_frames": self.average_game_length,
            "total_frames": self.total_frames
        })

    def get_player_stats(self, player_id: str) -> Dict[str, Any]:
        """Get statistics for a specific player."""
        scores = self.player_scores[player_id]
        return {
            "games_played": len(scores),
            "wins": self.player_wins[player_id],
            "win_rate": self.player_wins[player_id] / max(1, len(scores)),
            "average_score": sum(scores) / max(1, len(scores)),
            "best_score": max(scores) if scores else 0,
            "total_score": sum(scores)
        }

    def get_leaderboard(self) -> list:
        """Get a leaderboard sorted by wins, then by average score."""
        players = set(self.player_scores.keys())
        leaderboard = []

        for player in players:
            stats = self.get_player_stats(player)
            leaderboard.append({
                "player": player,
                **stats
            })

        # Sort by wins (descending), then by average score (descending)
        leaderboard.sort(key=lambda x: (
            x["wins"], x["average_score"]), reverse=True)
        return leaderboard

    def get_widget(self, asset: str = "default", **kwargs) -> str:
        """Get a text widget representation of current stats."""
        if self.total_games == 0:
            return "Breakout Stats: No games played yet"

        leaderboard = self.get_leaderboard()
        top_player = leaderboard[0] if leaderboard else None

        if top_player:
            return (f"Breakout Stats: {self.total_games} games, "
                    f"Leader: {top_player['player']} ({top_player['wins']} wins, "
                    f"avg score: {top_player['average_score']:.1f})")
        else:
            return f"Breakout Stats: {self.total_games} games played"

    def get_render_data(self) -> Dict[str, Any]:
        """Get stats data for rendering."""
        return {
            "stats": self.get_stats_summary(),
            "players": {player: self.get_player_stats(player)
                        for player in self.player_scores.keys()},
            "leaderboard": self.get_leaderboard()
        }

    def __render__(self, width=300, height=80, asset="default", style="default", font=None, color=None, text_color=None, **kwargs):
        """Unified render method for dashboard/compositor use."""
        # For now, just call get_default_asset if present, else raise
        if hasattr(self, 'get_default_asset'):
            return self.get_default_asset(width=width, height=height)
        raise NotImplementedError(
            f"__render__ not implemented for {self.__class__.__name__}")

    def get_default_asset(self, width=300, height=80):
        from PIL import Image, ImageDraw
        img = Image.new('RGB', (width, height), color=(80, 40, 120))
        draw = ImageDraw.Draw(img)
        draw.rectangle([10, 10, width-10, height-10],
                       outline=(255, 255, 255), width=2)
        draw.text((20, 20), "Breakout Stats", fill=(255, 255, 0))
        return img
