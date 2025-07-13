from typing import List, Dict
from plantangenet.session.referee import BaseReferee, AdjudicationResult, Judgement


class DemocraticReferee:
    """
    Democratic referee: majority rules.
    """

    def adjudicate(self, states: List[dict]) -> AdjudicationResult:
        # Count votes for each unique state
        from collections import Counter
        state_votes = Counter([str(s) for s in states])
        most_common, count = state_votes.most_common(1)[0]
        # If majority, return WIN, else CONTEST
        if count > len(states) // 2:
            return AdjudicationResult(Judgement.WIN, eval(most_common), {'votes': dict(state_votes)})
        else:
            return AdjudicationResult(Judgement.CONTEST, {}, {'votes': dict(state_votes)})
