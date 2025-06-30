# Copyright (c) 1998-2025 Scott Russell
# SPDX-License-Identifier: MIT

from abc import ABC, abstractmethod
from dataclasses import dataclass
import json
from typing import Optional, List, Union
from plantangenet.policy.identity import Identity
from plantangenet.policy.statement import Statement
from plantangenet.message import Message


@dataclass
class EvaluationResult:
    def __init__(self, passed: bool, reason: str, statement: Optional[Statement] = None, messages: Optional[List[Message]] = None):
        self.passed = passed
        self.reason = reason
        self.statement = statement
        self.messages = messages or []

    def to_message(self, subject: str = "policy.evaluation", sender: Optional[str] = None, target: Optional[str] = None) -> Message:

        payload = self.to_dict()
        if self.messages:
            payload['messages'] = [m.dict() for m in self.messages]

        return Message(
            subject=subject,
            sender=sender,
            target=target,
            payload=json.dumps(payload).encode('utf-8'),
            priority=1
        )

    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "reason": self.reason,
            "statement": str(self.statement) if self.statement else None,
            "messages": [m.dict() for m in self.messages]
        }

    def __bool__(self):
        return self.passed


class PolicyEvaluator(ABC):
    def __init__(self, policy_engine, peer=None):
        self.policy = policy_engine
        self.peer = peer

    @abstractmethod
    def evaluate(self, identity: Identity, action, resource, context: Optional[dict] = None) -> EvaluationResult:
        pass


class ChainedPolicyEvaluator(PolicyEvaluator):
    def __init__(self, evaluators: List[PolicyEvaluator]):
        super().__init__(policy_engine=None)
        self.evaluators = evaluators

    def evaluate(self, identity: Identity, action, resource, context: Optional[dict] = None) -> EvaluationResult:
        for evaluator in self.evaluators:
            result = evaluator.evaluate(identity, action, resource, context)
            if not result:
                return result
        return EvaluationResult(True, "All evaluators approved")


class GuardClauseEvaluator(PolicyEvaluator):
    def evaluate(self, identity: Identity, action, resource, context: Optional[dict] = None) -> EvaluationResult:
        if not self.policy._initialized:
            return EvaluationResult(False, "Policy engine not initialized")
        return EvaluationResult(True, "Policy engine ready")


class DisallowedEvaluator(PolicyEvaluator):
    def evaluate(self, identity: Identity, action, resource, context: Optional[dict] = None) -> EvaluationResult:
        if context and context.get("disallowed"):
            return EvaluationResult(False, "Evaluation explicitly disallowed")
        return EvaluationResult(True, "No disallow override present")


class PolicyCostEvaluator(PolicyEvaluator):
    def evaluate(self, identity: Identity, action, resource, context: Optional[dict] = None) -> EvaluationResult:
        context = context or {}
        messages = context.setdefault('messages', [])
        peer_fsm = getattr(self.peer, "_fsm", None)
        current_dust = getattr(peer_fsm, "dust_balance", float("inf"))

        for stmt in self.policy._policies:
            if stmt.effect not in {"allow", "deny"}:
                continue

            required_dust = getattr(stmt, "cost", 0)
            if required_dust and current_dust < required_dust:
                messages.append(Message(
                    subject="policy.cost",
                    payload=json.dumps({
                        "reason": "Insufficient dust balance",
                        "required": required_dust,
                        "current": current_dust
                    }).encode('utf-8')
                ))
                return EvaluationResult(False, "Insufficient dust balance for policy cost")

        return EvaluationResult(True, "Sufficient dust balance for policy cost")
