from plantangenet.session.referees.confessor import ConfessorReferee
from plantangenet.session.referee import Judgement


def test_confessor_with_confession():
    referee = ConfessorReferee()
    states = [{"score": 1}, {"score": 2, "confession": True}]
    result = referee.adjudicate(states)
    assert result.judgement == Judgement.ERROR
    assert result.info["reason"] == "Confession present"


def test_confessor_no_confession():
    referee = ConfessorReferee()
    states = [{"score": 1}, {"score": 2}]
    result = referee.adjudicate(states)
    assert result.judgement == Judgement.WIN
    assert result.info["reason"] == "No confessions"
