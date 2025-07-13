from typing import List, Optional, Callable
from .base import BaseSquad
from examples.tictactoe.game import TicTacToeGame
from examples.tictactoe.referee import TicTacToeReferee
from examples.tictactoe.player import TicTacToePlayer
from plantangenet.game import GameState


class PlayerManagerSquad(BaseSquad):
    """
    Squad-based player manager for TicTacToe (or similar games).
    Handles player queueing, matchmaking, and assignment to games/referees.
    """

    def __init__(self, session=None, name: Optional[str] = None):
        super().__init__(name)
        self.session = session
        self.waiting_players: List[str] = []
        self.active_games: List[TicTacToeGame] = []
        self.on_game_completed: Optional[Callable[[
            TicTacToeGame], None]] = None

    def add_player(self, player_id: str):
        """Add a player to the waiting queue if not already present."""
        if player_id not in self.waiting_players:
            self.waiting_players.append(player_id)
        self.try_match_players()

    def try_match_players(self):
        """Attempt to match players into games (pairs for TicTacToe)."""
        while len(self.waiting_players) >= 2:
            p1 = self.waiting_players.pop(0)
            p2 = self.waiting_players.pop(0)
            self.assign_to_game(p1, p2)

    def assign_to_game(self, player1: str, player2: str):
        """Assign two players to a new game and referee."""
        game_id = f"game_{len(self.active_games) + 1}"
        game = TicTacToeGame(game_id, player1, player2)
        # Ensure game is in progress and has a valid current_turn
        game.game_state = GameState.IN_PROGRESS
        if not getattr(game, 'current_turn', None):
            game._current_turn = player1  # X goes first
        self.active_games.append(game)
        # Optionally, notify session or other components
        if self.session and hasattr(self.session, "on_players_matched"):
            self.session.on_players_matched(player1, player2)

    def remove_player(self, player_id: str):
        """Remove a player from the waiting queue if present."""
        if player_id in self.waiting_players:
            self.waiting_players.remove(player_id)

    def get_waiting_players(self) -> List[str]:
        return list(self.waiting_players)

    def get_active_games(self):
        return self.active_games

    def step_games(self):
        """Step all active games by making a move using the real player agent for the current player."""
        import random
        from plantangenet.game import GameState
        finished_games = []
        player_agents = getattr(self.session, 'players',
                                {}) if self.session else {}
        for game in self.active_games:
            if game.game_state != GameState.IN_PROGRESS:
                finished_games.append(game)
                continue
            current_player_id = game.current_turn
            if not current_player_id:
                print(f"[DEBUG] Game {game.game_id} has no current_turn set!")
                continue
            player_agent = player_agents.get(current_player_id)
            if not player_agent:
                moves = [(r, c) for r in range(3)
                         for c in range(3) if game.board.board[r][c] == " "]
                if not moves:
                    finished_games.append(game)
                    continue
                row, col = random.choice(moves)
            else:
                board_state = [list(r) for r in game.board.board]
                my_symbol = "X" if current_player_id == game.player_x else "O"
                row, col = player_agent.choose_action(board_state, my_symbol)
            print(
                f"[DEBUG] Game {game.game_id}: {current_player_id} moves to ({row},{col})")
            success, msg = game.make_game_move(current_player_id, row, col)
            print(f"[DEBUG] Move result: {success}, {msg}")
            if game.game_state != GameState.IN_PROGRESS:
                finished_games.append(game)
                if self.on_game_completed:
                    self.on_game_completed(game)
        for game in finished_games:
            self.active_games.remove(game)
