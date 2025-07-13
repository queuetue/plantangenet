from typing import List, Dict
from plantangenet.session.referee import BaseReferee, AdjudicationResult, Judgement


class InvestigatorReferee:
    """
    Investigator referee: forces truth via verification (e.g., 'verified' field).
    """

    def adjudicate(self, states: List[dict]) -> AdjudicationResult:
        verified = [s for s in states if s.get('verified')]
        if verified:
            return AdjudicationResult(Judgement.WIN, verified[0], {'reason': 'Verified state'})
        return AdjudicationResult(Judgement.CONTEST, {}, {'reason': 'No verified state'})
