# Copyright (c) 1998-2025 Scott Russell
# SPDX-License-Identifier: MIT

from typing import Optional, Dict, List, Union
from plantangenet.policy.base import Policy
from plantangenet.policy.role import Role
from plantangenet.policy.identity import Identity
from plantangenet.policy.statement import Statement
from plantangenet.policy.evaluator import GuardClauseEvaluator, DisallowedEvaluator, EvaluationResult


class Vanilla(Policy):

    def __init__(self, logger, namespace) -> None:
        """ 

        Vanilla is a reference implementation of the plantangenet sercutiy 
        engine designed for clarity and correctness. It favors 
        conservative defaults and defensive programming. It is intentionally 
        not the fastest, strictest, or most negotiable engine. It is 
        intended as a foundation on which environment-specific engines can
        be built. But you can run a plantangenet ocean with it.

        Initialize the Vanilla policy engine.
        Args:
            namespace (str): Namespace for the policy engine.
            logger (SafeLogger, optional): Logger instance for logging.
        """
        self.logger = logger
        self._namespace = namespace
        self._policies: List[Statement] = []
        self._identities: Dict[str, Identity] = {}
        self._roles: Dict[str, Role] = {}
        self.evaluators = [
            GuardClauseEvaluator(self),
            DisallowedEvaluator(self),
        ]

    def evaluate(self, identity: Union[Identity, str], action, resource, context: Optional[dict] = None) -> EvaluationResult:
        """Evaluate whether an identity can perform an action on a resource.

        Gracefully handles:
        - Identity objects or string IDs
        - Missing identities (creates minimal identity)
        - None/invalid actions and resources (converts to strings)
        - Malformed policies (logs warnings, skips)
        - Missing context (creates default)
        - Exception during evaluation (defaults to deny)
        """
        try:
            # Defensive context handling
            context = context or {}
            if not isinstance(context, dict):
                self.logger.warning(
                    f"Invalid context type {type(context)}, using empty dict")
                context = {}

            context.setdefault('messages', [])
            context.setdefault('peer_id', getattr(
                self._peer, 'id', '<unknown>'))

            # Normalize identity
            if isinstance(identity, Identity):
                identity_id = identity.id
                identity_roles = identity.roles or []
            elif isinstance(identity, str):
                identity_id = identity
                if identity_id in self._identities:
                    identity_roles = self._identities[identity_id].roles or []
                else:
                    self.logger.warning(
                        f"Unknown identity {identity_id}, treating as having no roles")
                    identity_roles = []
            else:
                # Try to convert to string
                try:
                    identity_id = str(identity)
                    identity_roles = []
                    self.logger.warning(
                        f"Converted identity {identity} to string: {identity_id}")
                except Exception as e:
                    self.logger.error(
                        f"Invalid identity type {type(identity)}: {e}")
                    return EvaluationResult(False, f"Invalid identity: {e}")

            # Normalize action and resource
            try:
                action = str(action) if action is not None else "*"
                resource = str(resource) if resource is not None else "*"
            except Exception as e:
                self.logger.warning(
                    f"Failed to convert action/resource to string: {e}")
                action = "*"
                resource = "*"

            # Evaluate policies - deny takes precedence
            matched_allow = False

            for stmt in self._policies:
                try:
                    # Check if this is a deny policy
                    if stmt.effect == "deny":
                        # Check if the deny policy applies
                        if self._policy_matches(stmt, identity_roles, action, resource, context):
                            return EvaluationResult(False, "Policy matched with deny effect", statement=stmt)

                    elif stmt.effect == "allow":
                        # Check if the allow policy applies
                        if self._policy_matches(stmt, identity_roles, action, resource, context):
                            matched_allow = True

                except Exception as e:
                    self.logger.warning(
                        f"Error evaluating policy statement: {e}")
                    continue  # Skip malformed policies

            if matched_allow:
                return EvaluationResult(True, "Policy matched with allow effect")
            else:
                return EvaluationResult(False, "No policy explicitly allowed this action")

        except Exception as e:
            self.logger.error(
                f"Unexpected error during policy evaluation: {e}")
            # Fail secure - deny by default
            return EvaluationResult(False, f"Evaluation failed: {e}")

    def _policy_matches(self, stmt: Statement, identity_roles: List[str], action: str, resource: str, context: dict) -> bool:
        """Check if a policy statement matches the given parameters."""
        # Check roles
        if stmt.role_names:
            role_match = (
                "*" in stmt.role_names or
                any(role in identity_roles for role in stmt.role_names) or
                self.includes_any_role(stmt.role_names)
            )
            if not role_match:
                return False

        # Check action
        if stmt.action:
            action_match = "*" in stmt.action or action in stmt.action
            if not action_match:
                return False

        # Check resource
        if stmt.resource:
            resource_match = "*" in stmt.resource or resource in stmt.resource
            if not resource_match:
                return False

        # Check conditions
        if stmt.condition:
            try:
                for k, v in stmt.condition.items():
                    if context.get(k) != v:
                        return False
            except Exception as e:
                self.logger.warning(f"Error checking policy condition: {e}")
                return False

        return True

        # result = self.evaluator.evaluate(identity, action, resource, context)

        # # Attach final audit to context (for debug or downstream emission)
        # evaluation_log = {
        #     "identity": getattr(identity, "id", identity),
        #     "action": action,
        #     "resource": resource,
        #     "passed": result.passed,
        #     "reason": result.reason
        # }
        # context.setdefault("evaluations", []).append(evaluation_log)

        # if not result.passed:
        #     context["disallowed"] = getattr(self._peer, "id", "unknown")

        # return result

    def _matches_action(self, actions, action) -> bool:
        return "*" in actions or action in actions

    def _matches_resource(self, resources, resource) -> bool:
        return "*" in resources or resource in resources

    def _check_conditions(self, conditions, context) -> bool:
        for key, expected in conditions.items():
            if key not in context:
                return False
            if isinstance(expected, bool):
                if bool(context[key]) != expected:
                    return False
            elif context[key] != expected:
                return False
        return True
