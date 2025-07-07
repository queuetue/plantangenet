from typing import Any, Callable, List, Optional
import random
import asyncio


class TournamentManager:
    """
    Tournament manager: runs a batch of players in a competitive, round-based fashion.
    Handles player registration, round management, and result aggregation.
    """

    def __init__(
        self,
        players: List[Any],
        game_factory: Callable[[str, Any, Any], Any],
        stats_agent: Optional[Any] = None,
        num_rounds: int = 1,
        games_per_round: int = 1,
        result_callback: Optional[Callable[[Any], None]] = None,
    ):
        self.players = players
        self.game_factory = game_factory
        self.stats_agent = stats_agent
        self.num_rounds = num_rounds
        self.games_per_round = games_per_round
        self.result_callback = result_callback
        self.games_played = 0
        self.rounds = []
        self.results = []

    def add_participant(self, participant):
        if participant not in self.players:
            self.players.append(participant)

    def record_result(self, result):
        self.results.append(result)

    def get_leaderboard(self):
        # Basic leaderboard based on wins
        leaderboard = {}
        for result in self.results:
            winner = getattr(result, 'winner', None)
            if winner:
                leaderboard[winner] = leaderboard.get(winner, 0) + 1
        return sorted(leaderboard.items(), key=lambda x: x[1], reverse=True)

    async def run(self):
        for round_num in range(self.num_rounds):
            round_games = []
            for game_num in range(self.games_per_round):
                if len(self.players) < 2:
                    break
                p1, p2 = random.sample(self.players, 2)
                game_id = f"game_{round_num+1}_{game_num+1}"
                game = self.game_factory(game_id, p1, p2)
                round_games.append(game)

                # Play the game to completion
                if hasattr(game, 'play'):
                    result = await game.play()
                else:
                    # Fallback: step through moves until done
                    while getattr(game, 'is_in_progress', lambda: False)():
                        if hasattr(game, 'step'):
                            game.step()
                        else:
                            break
                    result = getattr(game, 'result', None)

                # Record result in stats agent if present
                if self.stats_agent and hasattr(self.stats_agent, 'record_game_result'):
                    self.stats_agent.record_game_result(
                        p1, p2, getattr(game, 'winner', None))

                if self.result_callback:
                    self.result_callback(game)

                self.record_result(game)
                self.games_played += 1

            self.rounds.append(round_games)

        # Output stats if possible
        if self.stats_agent and hasattr(self.stats_agent, 'output_all'):
            await self.stats_agent.output_all()
