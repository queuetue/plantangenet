from plantangenet.session.referees.consensus import ConsensusReferee
from plantangenet.session.referee import Judgement


def test_consensus_unanimous():
    referee = ConsensusReferee()
    states = [{"score": 1}, {"score": 1}, {"score": 1}]
    result = referee.adjudicate(states)
    assert result.judgement == Judgement.WIN
    assert result.info["consensus"] is True


def test_consensus_disagreement():
    referee = ConsensusReferee()
    states = [{"score": 1}, {"score": 2}]
    result = referee.adjudicate(states)
    assert result.judgement == Judgement.CONTEST
    assert result.info["consensus"] is False
