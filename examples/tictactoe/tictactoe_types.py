from enum import Enum
from typing import List, Optional
from dataclasses import dataclass, asdict


class GameState(Enum):
    WAITING = "waiting"
    IN_PROGRESS = "in_progress"
    FINISHED = "finished"


class PlayerSymbol(Enum):
    X = "X"
    O = "O"
    EMPTY = " "


@dataclass
class GameBoard:
    board: List[List[str]]
    current_player: str
    state: GameState
    winner: Optional[str] = None
    game_id: str = ""
    player_x: str = ""
    player_o: str = ""

    def __init__(self, game_id: str = "", player_x: str = "", player_o: str = ""):
        self.board = [[" " for _ in range(3)] for _ in range(3)]
        self.current_player = PlayerSymbol.X.value
        self.state = GameState.WAITING
        self.winner = None
        self.game_id = game_id
        self.player_x = player_x
        self.player_o = player_o

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'GameBoard':
        board = cls()
        board.board = data['board']
        board.current_player = data['current_player']
        board.state = GameState(data['state'])
        board.winner = data['winner']
        board.game_id = data['game_id']
        board.player_x = data['player_x']
        board.player_o = data['player_o']
        return board
