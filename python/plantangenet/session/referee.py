from abc import abstractmethod
from enum import Enum
from typing import List, Optional, Protocol, Any


class Judgement(Enum):
    UNKNOWN = None
    CONTEST = 100
    WIN = 1
    LOSE = 2
    DRAW = 3
    CHEAT = 110
    ERROR = 120


class RefereeState:
    """
    State for the Breakout game referee.
    This class holds the state information required for adjudicating the game.
    """

    def __init__(self,
                 identities: List[str],
                 state: dict,
                 claims: Optional[dict] = None):
        self.identities = identities  # identities that support this state
        self._state = state
        self._claims = claims or {}


class AdjudicationResult:
    """
    Represents the result of an adjudication.
    Contains the judgement and any additional information.
    """

    def __init__(self, judgement: Judgement, state: dict, info: Any = None):
        self.judgement = judgement
        self.state = state
        self.info = info


class BaseReferee(Protocol):
    def adjudicate(self, states: List[dict]) -> AdjudicationResult:
        """
        Adjudicate the given states and return the result.
        """

        return AdjudicationResult(Judgement.UNKNOWN, {})
