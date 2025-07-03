import asyncio
import random
from plantangenet.agent import Agent
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
