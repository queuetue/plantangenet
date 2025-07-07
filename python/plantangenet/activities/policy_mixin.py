"""
Policy mixin for activities and games.

This module provides a mixin that makes activities policy-aware,
allowing them to be subject to policy enforcement for actions like:
- Joining games
- Making moves
- Viewing game state
- Administrative actions

The mixin integrates with Plantangenet's policy system to provide
consistent governance across all activity types.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Union
from plantangenet.policy.policy import Policy
from plantangenet.policy.identity import Identity
from plantangenet.policy.evaluator import EvaluationResult


class PolicyEnforcedActivity(ABC):
    """
    Mixin that makes activities subject to policy enforcement.

    This mixin should be used alongside activity base classes to ensure
    that all game actions are subject to policy evaluation. It provides
    a consistent interface for policy checking across all activity types.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._policy: Optional[Policy] = None
        self._activity_context: Dict[str, Any] = {}

    def set_policy(self, policy: Policy) -> None:
        """Set the policy instance for this activity."""
        self._policy = policy

    @property
    def policy(self) -> Optional[Policy]:
        """Get the current policy instance."""
        return self._policy

    def set_activity_context(self, context: Dict[str, Any]) -> None:
        """Set additional context for policy evaluation."""
        self._activity_context = context

    def get_activity_context(self) -> Dict[str, Any]:
        """Get the current activity context."""
        return self._activity_context.copy()

    def evaluate_policy(
        self,
        identity: Union[Identity, str],
        action: str,
        resource: Optional[str] = None,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> EvaluationResult:
        """
        Evaluate whether an identity can perform an action in this activity.

        Args:
            identity: The identity attempting the action
            action: The action being attempted (e.g., "join", "move", "view")
            resource: The resource being acted upon (optional)
            additional_context: Additional context for evaluation (optional)

        Returns:
            EvaluationResult: The result of the policy evaluation
        """
        if not self._policy:
            # No policy set - default to allow (permissive default)
            return EvaluationResult(passed=True, reason="No policy configured - allowing")

        # Build context for policy evaluation
        context = self.get_activity_context()
        if additional_context:
            context.update(additional_context)

        # Add activity-specific context
        context.update({
            'activity_type': self.__class__.__name__,
            'activity_id': getattr(self, 'id', 'unknown'),
            'activity_state': getattr(self, 'state', 'unknown'),
        })

        # Default resource to the activity itself if not specified
        if resource is None:
            resource = f"activity:{getattr(self, 'id', 'unknown')}"

        return self._policy.evaluate(identity, action, resource, context)

    def require_permission(
        self,
        identity: Union[Identity, str],
        action: str,
        resource: Optional[str] = None,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Require permission for an action, raising an exception if denied.

        Args:
            identity: The identity attempting the action
            action: The action being attempted
            resource: The resource being acted upon (optional)
            additional_context: Additional context for evaluation (optional)

        Raises:
            PermissionError: If the action is not permitted
        """
        result = self.evaluate_policy(
            identity, action, resource, additional_context)
        if not result.passed:
            raise PermissionError(
                f"Policy denied action '{action}': {result.reason}")

    @abstractmethod
    def get_activity_specific_permissions(self) -> Dict[str, str]:
        """
        Return a mapping of activity-specific actions to their descriptions.

        This method should be implemented by each activity type to define
        what actions are available for policy enforcement.

        Returns:
            Dict[str, str]: Mapping of action names to descriptions
        """
        pass

    def get_all_permissions(self) -> Dict[str, str]:
        """
        Get all permissions (common + activity-specific) for this activity.

        Returns:
            Dict[str, str]: Mapping of all action names to descriptions
        """
        common_permissions = {
            'join': 'Join the activity',
            'leave': 'Leave the activity',
            'view': 'View activity state',
            'admin': 'Perform administrative actions'
        }

        activity_permissions = self.get_activity_specific_permissions()

        # Merge permissions (activity-specific overrides common)
        all_permissions = common_permissions.copy()
        all_permissions.update(activity_permissions)

        return all_permissions


class TurnBasedPolicyMixin(PolicyEnforcedActivity):
    """
    Policy mixin specifically for turn-based activities.

    Adds turn-specific policy enforcement for actions like making moves
    when it's not your turn, or attempting to move for other players.
    """

    def evaluate_turn_policy(
        self,
        identity: Union[Identity, str],
        action: str,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> EvaluationResult:
        """
        Evaluate policy with turn-based context.

        Args:
            identity: The identity attempting the action
            action: The action being attempted
            additional_context: Additional context for evaluation

        Returns:
            EvaluationResult: The result of the policy evaluation
        """
        context = additional_context or {}

        # Add turn-based context
        context.update({
            'current_turn': getattr(self, 'current_turn', None),
            'turn_count': getattr(self, 'turn_count', 0),
            'is_active_player': self._is_active_player(identity),
        })

        return self.evaluate_policy(identity, action, additional_context=context)

    def _is_active_player(self, identity: Union[Identity, str]) -> bool:
        """
        Check if the given identity is the currently active player.

        This method should be overridden by implementing classes to provide
        the actual turn logic.

        Args:
            identity: The identity to check

        Returns:
            bool: True if this identity can act on the current turn
        """
        # Default implementation - always allow if no turn logic
        return True

    def require_turn_permission(
        self,
        identity: Union[Identity, str],
        action: str,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Require permission for a turn-based action.

        Args:
            identity: The identity attempting the action
            action: The action being attempted
            additional_context: Additional context for evaluation

        Raises:
            PermissionError: If the action is not permitted
        """
        result = self.evaluate_turn_policy(
            identity, action, additional_context)
        if not result.passed:
            raise PermissionError(
                f"Policy denied turn action '{action}': {result.reason}")

    def get_activity_specific_permissions(self) -> Dict[str, str]:
        """Get turn-based activity permissions."""
        return {
            'move': 'Make a move in the game',
            'pass_turn': 'Pass the current turn',
            'forfeit': 'Forfeit the game',
        }
