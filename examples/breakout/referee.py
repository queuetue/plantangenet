from typing import List, Dict, Any
from plantangenet.session.referee import BaseReferee, AdjudicationResult, Judgement


class DigitalHandballReferee:
    """
    Referee for digital handball/breakout: ensures legal ball and paddle movement, no cheating.
    """

    def __init__(self, max_ball_speed: float = 10.0, max_paddle_speed: float = 5.0):
        self.max_ball_speed = max_ball_speed
        self.max_paddle_speed = max_paddle_speed

    def adjudicate(self, states: List[dict]) -> AdjudicationResult:
        """
        Each state should include: 'ball', 'paddle', 'blocks', 'score', 'lives', 'action', 'player'.
        - Accept if all states are identical and valid.
        - If states differ, accept the only valid one, else flag as error/cheat.
        """
        if not states:
            return AdjudicationResult(Judgement.UNKNOWN, {}, {'reason': 'No states provided'})
        if self._all_states_identical(states):
            state = states[0]
            if self._is_valid_state(state):
                return AdjudicationResult(Judgement.WIN, state, {'reason': 'Consensus on valid state'})
            else:
                return AdjudicationResult(Judgement.CHEAT, state, {'reason': 'Consensus on invalid state'})
        valid_states = [s for s in states if self._is_valid_state(s)]
        if len(valid_states) == 1:
            return AdjudicationResult(Judgement.WIN, valid_states[0], {'reason': 'One valid state'})
        elif len(valid_states) > 1:
            return AdjudicationResult(Judgement.CONTEST, {}, {'reason': 'Multiple valid states'})
        else:
            return AdjudicationResult(Judgement.ERROR, {}, {'reason': 'No valid states'})

    def _all_states_identical(self, states: List[dict]) -> bool:
        if len(states) <= 1:
            return True
        first = states[0]
        for s in states[1:]:
            if s != first:
                return False
        return True

    def _is_valid_state(self, state: dict) -> bool:
        # Check ball speed
        ball = state.get('ball', {})
        if not self._is_valid_ball(ball):
            return False
        # Check paddle speed/position
        paddle = state.get('paddle', {})
        if not self._is_valid_paddle(paddle):
            return False
        # Check score/lives are non-negative
        if state.get('score', 0) < 0 or state.get('lives', 1) < 0:
            return False
        # TODO: Add more checks for blocks, collisions, etc.
        return True

    def _is_valid_ball(self, ball: dict) -> bool:
        vx = abs(ball.get('vx', 0))
        vy = abs(ball.get('vy', 0))
        return vx <= self.max_ball_speed and vy <= self.max_ball_speed

    def _is_valid_paddle(self, paddle: dict) -> bool:
        vx = abs(paddle.get('vx', 0))
        return vx <= self.max_paddle_speed
