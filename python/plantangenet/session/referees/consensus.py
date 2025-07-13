from typing import List, Dict
from plantangenet.session.referee import BaseReferee, AdjudicationResult, Judgement


class ConsensusReferee:
    """
    Consensus referee: unanimous agreement required.
    """

    def adjudicate(self, states: List[dict]) -> AdjudicationResult:
        if all(s == states[0] for s in states):
            return AdjudicationResult(Judgement.WIN, states[0], {'consensus': True})
        else:
            return AdjudicationResult(Judgement.CONTEST, {}, {'consensus': False})
