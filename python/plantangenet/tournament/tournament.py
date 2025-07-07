from .batch import Batch
import random
from typing import Any, Callable, List, Optional


class Tournament(Batch):
    """
    Tournament manager: runs a batch of agents/omnis in a competitive, round-based fashion.
    Inherits from Batch, adds rounds/games/game_factory logic.
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
        super().__init__(agents=players, steps=num_rounds)
        self.players = players
        self.game_factory = game_factory
        self.stats_agent = stats_agent
        self.num_rounds = num_rounds
        self.games_per_round = games_per_round
        self.result_callback = result_callback
        self.games_played = 0

    async def run(self):
        for round_num in range(self.num_rounds):
            for game_num in range(self.games_per_round):
                p1, p2 = random.sample(self.players, 2)
                game_id = f"game_{round_num+1}_{game_num+1}"
                game = self.game_factory(game_id, p1, p2)
                # Play the game to completion (assume .play() or .run() or similar)
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
                self.games_played += 1
        # Output stats if possible
        if self.stats_agent and hasattr(self.stats_agent, 'output_all'):
            await self.stats_agent.output_all()
