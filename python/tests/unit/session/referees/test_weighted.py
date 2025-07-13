from plantangenet.session.referees.weighted import WeightedReferee
from plantangenet.session.referee import Judgement


def test_weighted_highest_weight():
    referee = WeightedReferee()
    states = [
        {"score": 1, "weight": 1.0},
        {"score": 2, "weight": 2.0},
        {"score": 2, "weight": 1.0},
    ]
    result = referee.adjudicate(states)
    assert result.judgement == Judgement.WIN
    assert result.state["score"] == 2
    assert result.info["weights"]
