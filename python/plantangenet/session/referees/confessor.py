from typing import List, Dict
from plantangenet.session.referee import BaseReferee, AdjudicationResult, Judgement


class ConfessorReferee:
    """
    Confessor referee: allows bias change tracking (e.g., 'confession' field).
    """

    def adjudicate(self, states: List[dict]) -> AdjudicationResult:
        confessions = [s for s in states if s.get('confession')]
        if confessions:
            return AdjudicationResult(Judgement.ERROR, confessions[0], {'reason': 'Confession present'})
        return AdjudicationResult(Judgement.WIN, states[0] if states else {}, {'reason': 'No confessions'})
