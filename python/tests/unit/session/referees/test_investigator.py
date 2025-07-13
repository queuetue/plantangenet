from plantangenet.session.referees.investigator import InvestigatorReferee
from plantangenet.session.referee import Judgement


def test_investigator_verified():
    referee = InvestigatorReferee()
    states = [{"score": 1}, {"score": 2, "verified": True}]
    result = referee.adjudicate(states)
    assert result.judgement == Judgement.WIN
    assert result.info["reason"] == "Verified state"


def test_investigator_no_verified():
    referee = InvestigatorReferee()
    states = [{"score": 1}, {"score": 2}]
    result = referee.adjudicate(states)
    assert result.judgement == Judgement.CONTEST
    assert result.info["reason"] == "No verified state"
