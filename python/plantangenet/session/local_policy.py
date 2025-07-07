from typing import Optional, Protocol, Any, Union

from pyparsing import abstractmethod
from plantangenet.policy import Policy
from plantangenet.policy.evaluator.evaluator import EvaluationResult
from plantangenet.policy.identity import Identity


class LocalPolicy(Protocol):
    _policy: Policy

    @abstractmethod
    def evaluate(self, identity: Union[Identity, str], action, resource, context: Optional[dict] = None) -> EvaluationResult:
        """
        Evaluate whether an identity can perform an action on a resource.
        As a local policy, it is more permissive and locally cached.

        Gracefully handles:
        - Identity objects or string IDs
        - Missing identities (creates minimal identity)
        - None/invalid actions and resources (converts to strings)
        - Malformed policies (logs warnings, skips)
        - Missing context (creates default)
        - Exception during evaluation (defaults to deny)
        """
