from plantangenet.session.referees.democratic import DemocraticReferee
from plantangenet.session.referee import Judgement


def test_democratic_majority():
    referee = DemocraticReferee()
    states = [{"score": 1}, {"score": 1}, {"score": 2}]
    result = referee.adjudicate(states)
    assert result.judgement == Judgement.WIN
    assert result.state == {"score": 1}
    assert result.info["votes"]


def test_democratic_no_majority():
    referee = DemocraticReferee()
    states = [{"score": 1}, {"score": 2}, {"score": 3}]
    result = referee.adjudicate(states)
    assert result.judgement == Judgement.CONTEST
