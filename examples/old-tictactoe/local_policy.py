from typing import Optional, Any, Tuple
from plantangenet.policy.policy import Policy, EvaluationResult


class LocalPolicy:
    """
    Delegating, memoizing local policy. Checks local cache/rules first, then delegates to parent/global policy.
    If no parent, defaults to deny. Memoizes delegated answers for efficiency.

    This class acts as a policy-compatible wrapper that can be used anywhere a Policy is expected.
    """

    def __init__(self, parent_policy: Optional[Policy] = None, local_policy: Optional[Policy] = None):
        self.parent_policy = parent_policy
        self.local_policy = local_policy
        # (identity, action, resource, frozenset(context.items())) -> EvaluationResult
        self._cache = {}

    def _cache_key(self, identity, action, resource, context: Optional[dict]) -> Tuple:
        # Use only hashable, relevant context for cache key
        def make_hashable(val):
            if isinstance(val, (list, dict, set)):
                return repr(val)
            return val
        context_items = frozenset((k, make_hashable(v))
                                  for k, v in context.items()) if context else frozenset()
        return (str(getattr(identity, 'id', identity)), str(action), str(resource), context_items)

    def evaluate(self, identity, action, resource, context: Optional[dict] = None) -> EvaluationResult:
        """Primary policy evaluation method - compatible with Policy interface."""
        key = self._cache_key(identity, action, resource, context)
        if key in self._cache:
            return self._cache[key]

        # Try local policy if present
        if self.local_policy:
            result = self.local_policy.evaluate(
                identity, action, resource, context)
            if result.passed or result.passed is False:
                self._cache[key] = result
                return result

        # Delegate to parent/global policy if available
        if self.parent_policy:
            result = self.parent_policy.evaluate(
                identity, action, resource, context)
            self._cache[key] = result
            return result

        # No answer, default deny
        result = EvaluationResult(
            passed=False, reason="No policy or parent policy available")
        self._cache[key] = result
        return result

    def set_local_policy(self, policy: Policy):
        """Set or update the local policy override."""
        self.local_policy = policy

    def clear_cache(self):
        """Clear the evaluation cache."""
        self._cache.clear()

    # Additional methods to make this more Policy-compatible if needed
    def has_role(self, identity_id: str, role_name: str) -> bool:
        """Delegate role checking to parent policy."""
        if self.parent_policy and hasattr(self.parent_policy, 'has_role'):
            return self.parent_policy.has_role(identity_id, role_name)
        return False

    def get_role(self, role_name: str):
        """Delegate role lookup to parent policy."""
        if self.parent_policy and hasattr(self.parent_policy, 'get_role'):
            return self.parent_policy.get_role(role_name)
        return None
