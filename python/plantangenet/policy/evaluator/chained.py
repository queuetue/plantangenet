# Copyright (c) 1998-2025 Scott Russell
# SPDX-License-Identifier: MIT

from typing import Optional, List
from plantangenet.policy.identity import Identity
from .result import EvaluationResult
from .base import Evaluator


class ChainedEvaluator(Evaluator):
    def __init__(self, evaluators: List[Evaluator]):
        super().__init__(policy_engine=None)
        self.evaluators = evaluators

    def evaluate(self, context: Optional[dict] = None, **kwargs: Optional[dict]) -> EvaluationResult:
        for evaluator in self.evaluators:
            result = evaluator.evaluate(context=context, **kwargs)
            if not result:
                return result
        return EvaluationResult(passed=True, reason="All evaluators approved")
