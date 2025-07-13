from plantangenet.session.referees.secret_keeper import SecretKeeperReferee
from plantangenet.session.referee import Judgement


def test_secret_keeper_cheat():
    referee = SecretKeeperReferee()
    states = [{"score": 1}, {"score": 2, "secret": True}]
    result = referee.adjudicate(states)
    assert result.judgement == Judgement.CHEAT
    assert result.info["reason"] == "Secret evidence found"


def test_secret_keeper_no_secret():
    referee = SecretKeeperReferee()
    states = [{"score": 1}, {"score": 2}]
    result = referee.adjudicate(states)
    assert result.judgement == Judgement.WIN
    assert result.info["reason"] == "No secrets"
