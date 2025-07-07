# Copyright (c) 1998-2025 Scott Russell
# SPDX-License-Identifier: MIT

from typing import Optional
from .result import EvaluationResult
from .base import Evaluator


class GuardClauseEvaluator(Evaluator):
    def evaluate(self, context: Optional[dict] = None, **kwargs: Optional[dict]) -> EvaluationResult:
        clauses = kwargs.get('clauses', [])
        if not clauses or not isinstance(clauses, list):
            return EvaluationResult(
                passed=False,
                reason="No guard clauses provided for evaluation"
            )
        for clause in clauses:
            if not clause.evaluate(context=context, **kwargs):
                return EvaluationResult(
                    passed=False,
                    reason=f"Guard clause failed: {clause}"
                )
        return EvaluationResult(
            passed=True,
            reason="Guard clause passed"
        )
