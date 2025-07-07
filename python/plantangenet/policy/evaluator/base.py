# Copyright (c) 1998-2025 Scott Russell
# SPDX-License-Identifier: MIT

from abc import ABC, abstractmethod
from typing import Optional
from plantangenet.policy.identity import Identity
from .result import EvaluationResult


class Evaluator(ABC):
    def __init__(self, policy_engine):
        self.policy = policy_engine

    @abstractmethod
    def evaluate(self, context: Optional[dict] = None, **kwargs: Optional[dict]) -> EvaluationResult:
        pass
