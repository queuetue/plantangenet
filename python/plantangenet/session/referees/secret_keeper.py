from typing import List, Dict
from plantangenet.session.referee import BaseReferee, AdjudicationResult, Judgement


class SecretKeeperReferee:
    """
    Secret Keeper referee: considers hidden evidence (e.g., 'secret' field).
    """

    def adjudicate(self, states: List[dict]) -> AdjudicationResult:
        for s in states:
            if s.get('secret'):
                return AdjudicationResult(Judgement.CHEAT, s, {'reason': 'Secret evidence found'})
        return AdjudicationResult(Judgement.WIN, states[0] if states else {}, {'reason': 'No secrets'})
