# Copyright (c) 1998-2025 Scott Russell
# SPDX-License-Identifier: MIT

from abc import abstractmethod
from typing import Optional
from plantangenet.policy.identity import Identity
from .result import EvaluationResult
from .base import Evaluator


class PolicyEvaluator(Evaluator):
    def __init__(self, policy_engine, peer=None):
        self.policy = policy_engine

    def evaluate(self, context: Optional[dict] = None, **kwargs: Optional[dict]) -> EvaluationResult:
        """
        Evaluate the policy against the provided context and additional keyword arguments.

        :param context: Optional dictionary containing context for evaluation.
        :param kwargs: Additional keyword arguments for evaluation.
        :return: EvaluationResult indicating the outcome of the evaluation.
        """
        if not self.policy:
            return EvaluationResult(
                passed=False,
                reason="No policy engine provided for evaluation"
            )

        return self.policy.evaluate(context=context, **kwargs)
