"""
Statistics tracking for Breakout tournaments.
"""
import json
from typing import Dict, Any
from collections import defaultdict

from plantangenet.agents.agent import Agent
from plantangenet import GLOBAL_LOGGER


class BreakoutStats(Agent):
    """Agent for tracking Breakout tournament statistics."""
    
    def __init__(self, logger=None):
        super().__init__(namespace="breakout", logger=logger or GLOBAL_LOGGER)
        self.total_games = 0
        self.player_wins = defaultdict(int)
        self.player_scores = defaultdict(list)  # List of scores for each player
        self.ties = 0
        self.average_game_length = 0.0
        self.total_frames = 0

    def record_game_result(self, player1: str, player2: str, winner: str, 
                          player1_score: int = 0, player2_score: int = 0, 
                          frames: int = 0):
        """Record the result of a completed game."""
        self.total_games += 1
        self.total_frames += frames
        
        if winner == "tie":
            self.ties += 1
        else:
            self.player_wins[winner] += 1
            
        self.player_scores[player1].append(player1_score)
        self.player_scores[player2].append(player2_score)
        
        if self.total_games > 0:
            self.average_game_length = self.total_frames / self.total_games

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
        leaderboard.sort(key=lambda x: (x["wins"], x["average_score"]), reverse=True)
        return leaderboard

    def get_widget(self) -> str:
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

    def __render__(self) -> str:
        """Render full statistics as JSON."""
        return json.dumps({
            "stats": {
                "total_games": self.total_games,
                "ties": self.ties,
                "average_game_length_frames": self.average_game_length,
                "total_frames": self.total_frames
            },
            "players": {player: self.get_player_stats(player) 
                       for player in self.player_scores.keys()},
            "leaderboard": self.get_leaderboard()
        }, indent=2)
