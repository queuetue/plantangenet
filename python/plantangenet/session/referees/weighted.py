from typing import List, Dict
from plantangenet.session.referee import BaseReferee, AdjudicationResult, Judgement


class WeightedReferee:
    """
    Weighted referee: votes weighted by 'weight' field in state dict.
    """

    def adjudicate(self, states: List[dict]) -> AdjudicationResult:
        from collections import defaultdict
        weight_map = defaultdict(float)
        for s in states:
            key = str(s)
            weight = s.get('weight', 1.0)
            weight_map[key] += weight
        if not weight_map:
            return AdjudicationResult(Judgement.UNKNOWN, {}, {'weights': dict(weight_map)})
        best_state, best_weight = max(weight_map.items(), key=lambda x: x[1])
        return AdjudicationResult(Judgement.WIN, eval(best_state), {'weights': dict(weight_map)})
