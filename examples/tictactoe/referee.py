import random
import time
from typing import Dict, List
from plantangenet.agents.agent import Agent
from examples.tictactoe.player import TicTacToePlayer
from examples.tictactoe.tictactoe_types import GameState, PlayerSymbol
from examples.tictactoe.game import TicTacToeGame
from examples.tictactoe.local_policy import LocalPolicy
from examples.tictactoe.stats import TicTacToeStats


class TicTacToeReferee(Agent):
    def __init__(self, namespace: str = "tictactoe", logger=None, benchmark_mode: bool = False, policy=None):
        super().__init__(namespace, logger)
        self.active_games: Dict[str, TicTacToeGame] = {}
        self.waiting_players: List[str] = []
        self.game_counter = 0
        self.completed_games = 0
        self.total_moves = 0
        self.benchmark_mode = benchmark_mode
        self.benchmark_start_time = None
        self.benchmark_end_time = None
        # player_id -> player object
        self.player_map: Dict[str, TicTacToePlayer] = {}
        self.policy = policy
        self.session = None  # Will be set by session.add_agent
        self._raised_hand = False

    @property
    def logger(self):
        return self._ocean__logger

    async def update(self) -> bool:
        if self.benchmark_start_time is None and (self.waiting_players or self.active_games):
            self.benchmark_start_time = time.time()
        await self._create_games()
        await self._process_moves()
        await self._check_finished_games()
        return True

    async def _create_games(self):
        self.logger.debug(
            f"Referee checking for games: {len(self.waiting_players)} waiting players")
        while len(self.waiting_players) >= 2:
            player1 = self.waiting_players.pop(0)
            player2 = self.waiting_players.pop(0)

            self.game_counter += 1
            game_id = f"game_{self.game_counter}"

            game = TicTacToeGame(game_id, player1, player2)
            if self.policy:
                # Create a LocalPolicy for this game that delegates to the session policy
                local_policy = LocalPolicy(parent_policy=self.policy)
                game.set_policy(local_policy)  # type: ignore
            self.active_games[game_id] = game

    async def _process_moves(self):
        for game_id, game in list(self.active_games.items()):
            if game.board.state == GameState.IN_PROGRESS:
                # In benchmark mode, always make a move if possible
                if self.benchmark_mode or random.random() < 0.3:
                    current_player_id = game.board.player_x if game.board.current_player == PlayerSymbol.X.value else game.board.player_o
                    empty_spots = [(r, c) for r in range(3)
                                   for c in range(3) if game.board.board[r][c] == " "]
                    if empty_spots:
                        row, col = random.choice(empty_spots)
                        success, message = game.make_move(
                            current_player_id, row, col)
                        if success:
                            self.total_moves += 1

    async def _check_finished_games(self):
        finished_games = []
        refs = None
        # Try to get refs from session if available
        if hasattr(self, 'session') and self.session is not None:
            refs = [agent for agent in getattr(
                self.session, 'agents', []) if isinstance(agent, TicTacToeReferee)]
        for game_id, game in self.active_games.items():
            if game.board.state == GameState.FINISHED:
                finished_games.append(game_id)
                self.completed_games += 1
                # Recycle both players to a random referee's queue
                import random
                for pid in [game.board.player_x, game.board.player_o]:
                    if refs:
                        random.choice(refs).add_player_to_queue(pid)
                    else:
                        self.add_player_to_queue(pid)
                # Update player stats
                for pid in [game.board.player_x, game.board.player_o]:
                    player = self.player_map.get(pid)
                    if player:
                        winner = game.board.winner if game.board.winner is not None else "DRAW"
                        player.game_finished(winner)
                # Record game result in stats agent if present
                if hasattr(self, 'session') and self.session is not None:
                    stats_agent = None
                    for agent in getattr(self.session, 'agents', []):
                        if isinstance(agent, TicTacToeStats):
                            stats_agent = agent
                            break
                    if stats_agent:
                        stats_agent.record_game_result(
                            game.board.player_x, game.board.player_o, game.board.winner)
        for game_id in finished_games:
            del self.active_games[game_id]
        # End benchmark if a condition is met (e.g., 1000 games)
        if self.benchmark_mode and self.completed_games >= 1000 and self.benchmark_end_time is None:
            self.benchmark_end_time = time.time()

    def add_player_to_queue(self, player_id: str):
        if player_id not in self.waiting_players:
            self.waiting_players.append(player_id)

    def get_benchmark_report(self):
        if self.benchmark_start_time is None:
            return "Benchmark not started."
        end_time = self.benchmark_end_time or time.time()
        elapsed = end_time - self.benchmark_start_time
        games = self.completed_games
        moves = self.total_moves
        games_per_sec = games / elapsed if elapsed > 0 else 0
        moves_per_sec = moves / elapsed if elapsed > 0 else 0
        return (f"Benchmark: {games} games, {moves} moves in {elapsed:.2f}s | "
                f"{games_per_sec:.2f} games/s, {moves_per_sec:.2f} moves/s")

    def __render__(self, width=300, height=80, asset="default", style="default", font=None, color=None, text_color=None):
        """
        Render a widget representing this referee for the dashboard.
        Returns a Pillow Image object.
        """
        from PIL import Image, ImageDraw, ImageFont
        img = Image.new("RGB", (width, height), color or (40, 60, 120))
        draw = ImageDraw.Draw(img)
        # Use provided font or default
        if font is None:
            try:
                font = ImageFont.truetype("DejaVuSans-Bold.ttf", 10)
            except Exception:
                font = ImageFont.load_default()
        # Draw border
        border_color = (255, 215, 0)  # gold for referee
        draw.rectangle([0, 0, width-1, height-1],
                       outline=border_color, width=3)
        # Draw referee info
        text = f"Referee: {self.namespace}\nActive: {len(self.active_games)} | Completed: {self.completed_games}"
        draw.multiline_text((10, 10), text, font=font,
                            fill=text_color or (255, 255, 255))
        return img

    def is_idle(self):
        """Return True if this referee has no active games and not enough players to start a game."""
        return len(self.active_games) == 0 and len(self.waiting_players) < 2

    def return_all_players_to_queue(self):
        """Return all waiting players to the queue (for restart coordination)."""
        players = list(self.waiting_players)
        self.waiting_players.clear()
        return players

    def raise_hand(self):
        """Signal that this referee is ready for a restart (used for coordination)."""
        self._raised_hand = True

    def clear_hand(self):
        self._raised_hand = False

    def has_raised_hand(self):
        return getattr(self, '_raised_hand', False)
