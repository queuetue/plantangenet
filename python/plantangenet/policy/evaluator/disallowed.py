# Copyright (c) 1998-2025 Scott Russell
# SPDX-License-Identifier: MIT

import json
from typing import Optional
from plantangenet.policy.identity import Identity
from .result import EvaluationResult
from ...message import Message
from .base import Evaluator


class DisallowedEvaluator(Evaluator):
    def evaluate(self, context: Optional[dict] = None, **kwargs: Optional[dict]) -> EvaluationResult:
        if context and context.get("disallowed"):
            return EvaluationResult(passed=False, reason="Disallowed action detected")
        return EvaluationResult(passed=True, reason="No disallow override present")
