# Copyright (c) 1998-2025 Scott Russell
# SPDX-License-Identifier: MIT

import json
from typing import Optional
from plantangenet.policy.identity import Identity
from .result import EvaluationResult
from ...message import Message
from .base import Evaluator


class GreaterThanEvaluator(Evaluator):
    def evaluate(self, context: Optional[dict] = None, **kwargs: Optional[dict]) -> EvaluationResult:
        a_value = kwargs.get('a_value', 0)
        b_value = kwargs.get('b_value', 0)
        if not isinstance(a_value, (int, float)) or not isinstance(b_value, (int, float)):
            return EvaluationResult(
                passed=False,
                reason="a_value and b_value must be numeric"
            )
        if a_value > b_value:
            return EvaluationResult(
                passed=True,
                reason="a_value is greater than b_value"
            )
        return EvaluationResult(
            passed=False,
            reason="a_value is not greater than b_value"
        )


class DustEvaluator(Evaluator):
    """Dust-based policy evaluator"""

    def evaluate(self, context: Optional[dict] = None, **kwargs) -> EvaluationResult:
        """Evaluate a policy using dust conditions"""
        # Simple default implementation
        return EvaluationResult(
            passed=True,
            reason="Dust evaluation passed (default implementation)"
        )
