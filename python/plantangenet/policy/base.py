from typing import Optional, Protocol, Union
from pyparsing import abstractmethod
from plantangenet.policy.identity import Identity
from plantangenet.policy.evaluator import EvaluationResult


class Policy(Protocol):

    @abstractmethod
    def evaluate(self, identity: Union[Identity, str], action, resource, context: Optional[dict] = None) -> EvaluationResult:
        """
            Evaluate whether an identity can perform an action on a resource.

            Gracefully handles:
            - Identity objects or string IDs
            - Missing identities (creates minimal identity)
            - None/invalid actions and resources (converts to strings)
            - Malformed policies (logs warnings, skips)
            - Missing context (creates default)
            - Exception during evaluation (defaults to deny)
        """

    # @abstractmethod
    # def get_statement(self, identity: Union[Identity, str], action: str, resource: Any, context: Optional[dict] = None) -> str:
    #     """
    #         Get the policy statement for an identity, action, and resource.

    #         Returns a string representation of the policy statement.
    #         Handles missing identities, actions, resources, and context gracefully.
    #     """

    # @abstractmethod
    # def get_identity_statements(self, identity: Union[Identity, str], context: Optional[dict] = None) -> List[str]:
    #     """
    #         Get all policy statements for an identity.

    #         Returns a list of strings representing the policy statements.
    #         Handles missing identities and context gracefully.
    #     """

    # @abstractmethod
    # def get_resource_statements(self, resource: Any, context: Optional[dict] = None) -> List[str]:
    #     """
    #         Get all policy statements for a resource.

    #         Returns a list of strings representing the policy statements.
    #         Handles missing resources and context gracefully.
    #     """
