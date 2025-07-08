"""
TurnBasedTournament: A generic harness for running turn-based, sequential tournaments.
Each agent/player takes turns; when a player is out (e.g., out of lives), the next player takes over.
The tournament ends when all players are out or a win condition is met.
"""
import asyncio
from typing import List, Dict, Any, Callable, Optional


class TurnBasedTournament:
    def __init__(self, players: List[Any], game_factory: Callable, max_lives: int = 3, on_update: Optional[Callable] = None):
        """
        players: list of agent/player objects (must have unique 'id')
        game_factory: function to create a new game instance for a player (player_id) -> game
        max_lives: number of lives per player
        on_update: optional callback for UI/dashboard updates
        """
        self.players = players
        self.game_factory = game_factory
        self.max_lives = max_lives
        self.on_update = on_update
        self.player_lives = {p.id: max_lives for p in players}
        self.player_scores = {p.id: 0 for p in players}
        self.active_players = [p.id for p in players]
        self.current_player_idx = 0
        self.tournament_over = False

    async def run(self):
        """Run the tournament loop until all players are out of lives."""
        while self.active_players and not self.tournament_over:
            current_id = self.active_players[self.current_player_idx]
            player = next(p for p in self.players if p.id == current_id)
            game = self.game_factory(player)
            result = await self.run_single_game(game, player)
            self.player_scores[current_id] += result.get('score', 0)
            if result.get('life_lost', False):
                self.player_lives[current_id] -= 1
                if self.player_lives[current_id] <= 0:
                    self.active_players.remove(current_id)
                    if self.current_player_idx >= len(self.active_players):
                        self.current_player_idx = 0
                else:
                    self.current_player_idx = (
                        self.current_player_idx + 1) % len(self.active_players)
            else:
                self.current_player_idx = (
                    self.current_player_idx + 1) % len(self.active_players)
            if self.on_update:
                self.on_update(self.get_status())
        # Ensure UI is updated at the end
        if self.on_update:
            self.on_update(self.get_status())
        return self.get_results()

    async def run_single_game(self, game, player):
        """Override or pass in a function to run a single game turn for a player. Should return a dict with at least 'score' and 'life_lost'."""
        # Placeholder: implement game logic or override this method
        await asyncio.sleep(0.1)
        return {'score': 0, 'life_lost': True}

    def get_status(self):
        return {
            'player_lives': self.player_lives.copy(),
            'player_scores': self.player_scores.copy(),
            'active_players': self.active_players.copy(),
            'current_player': self.active_players[self.current_player_idx] if self.active_players else None,
            'tournament_over': self.tournament_over
        }

    def get_results(self):
        return {
            'scores': self.player_scores,
            'lives': self.player_lives,
            'winner': max(self.player_scores, key=lambda pid: self.player_scores[pid]) if self.player_scores else None
        }
