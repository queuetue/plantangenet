from dataclasses import dataclass
from typing import List, Optional, Protocol, Union
from pyparsing import abstractmethod
from plantangenet.policy.evaluator import EvaluationResult


@dataclass
class Role:
    role_id: str
    name: str
    description: Optional[str] = None
    members: Optional[List[str]] = None


@dataclass
class Statement:
    statement_id: str
    roles: List[str]
    effect: str
    actions: List[str]
    resources: List[str]
    condition: Optional[dict] = None
    delivery: Optional[dict] = None


@dataclass
class Identity:
    identity_id: str
    name: Optional[str] = None
    metadata: Optional[dict] = None


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

    @abstractmethod
    def has_role(self, identity_id: str, role_name: str) -> bool:
        """Check if an identity has a specific role.

        Gracefully handles:
        - Missing identities (returns False)
        - Missing roles (returns False)
        - None/empty inputs (returns False)
        - Type coercion where reasonable
        """

    @abstractmethod
    def get_role(self, role_name: str) -> Role:
        """Get a role by name.

        Gracefully handles:
        - Missing roles (returns None)
        - None/empty inputs (returns None)
        - Type coercion where reasonable
        """

    @abstractmethod
    def add_identity(self, identity: Identity, nickname=None, metadata=None) -> str:
        """Add an identity to the policy system.

        Gracefully handles:
        - None/empty metadata and nickname (uses defaults)
        - Storage failures (logs warning but continues)
        - Duplicate identities (updates existing)
        """

    @abstractmethod
    def get_identity(self, identity_id: str) -> Optional[Identity]:
        """Get an identity by ID.

        Gracefully handles:
        - Missing identities (returns None)
        - None/empty inputs (returns None)
        - Type coercion where reasonable
        """

    @abstractmethod
    def add_identity_to_role(self, identity: Identity, role: Role) -> None:
        """Add an identity to a role.

        Gracefully handles:
        - Missing identities (logs warning, does nothing)
        - Missing roles (logs warning, does nothing)
        - Storage failures (logs warning but continues)
        - Duplicate identities in role (does nothing)
        """

    @abstractmethod
    def remove_identity_from_role(self, identity: Identity, role: Role) -> None:
        """Remove an identity from a role.

        Gracefully handles:
        - Missing identities (logs warning, does nothing)
        - Missing roles (logs warning, does nothing)
        - Storage failures (logs warning but continues)
        - Identity not found in role (does nothing)
        """

    @abstractmethod
    def delete_identity(self, identity: Identity) -> None:
        """Delete an identity from the policy system.

        Gracefully handles:
        - Missing identities (logs warning, does nothing)
        - Storage failures (logs warning but continues)
        - Identity not found (does nothing)
        """

    @abstractmethod
    def add_role(self, role: Role, description=None, members=None) -> str:
        """Add a role to the policy system.

        Gracefully handles:
        - None/empty description and members (uses defaults)
        - Storage failures (logs warning but continues)
        - Duplicate roles (updates existing)
        - Invalid member IDs (logs warning but includes them)
        """

    @abstractmethod
    def delete_role(self, role: Role) -> None:
        """Delete a role from the policy system.

        Gracefully handles:
        - Missing roles (logs warning, does nothing)
        - Storage failures (logs warning but continues)
        """

    @abstractmethod
    def includes_any_role(self, roles: List[str]) -> bool:
        """
        Check if any role in the list natches our any role or the generic wildcard '*'.
        Args:
            roles (List[str]): List of role names to check.
        Returns:
            bool: True if any role matches, False otherwise.
        """

    @abstractmethod
    def add_statement(self, roles: List[Union[str, Role]], effect, action, resource, condition=None, delivery=None) -> str:
        """Add a policy statement.

        Gracefully handles:
        - Mixed role types (Role objects, strings, or mix)
        - Invalid role types (logs warning, skips invalid)
        - Single values instead of lists for action/resource
        - Invalid effect values (defaults to "deny" for safety)
        - Storage failures (continues with memory-only)
        - None/invalid conditions

        Args:
            roles: List of role names (strings) or Role objects (or mix of both)
            effect: "allow" or "deny" (or variations, normalized)
            action: Action string or list of action strings
            resource: Resource string or list of resource strings
            condition: Optional condition dictionary
            delivery: Optional delivery configuration

        Returns:
            Storage key for the saved policy
        """

    @abstractmethod
    def delete_statement(self, policy_statement: Statement) -> None:
        """Delete a policy statement.

        Gracefully handles:
        - Missing statements (logs warning, does nothing)
        - Storage failures (logs warning but continues)
        - Invalid policy types (logs warning, skips)
        """

    @abstractmethod
    def add_role_to_statement(self, policy_statement: Statement, role: Role) -> None:
        """Add a role to a policy statement.

        Gracefully handles:
        - Missing statements (logs warning, does nothing)
        - Missing roles (logs warning, does nothing)
        - Storage failures (logs warning but continues)
        - Duplicate roles in statement (does nothing)
        """

    @abstractmethod
    def remove_role_from_statement(self, policy_statement: Statement, role: Role) -> None:
        """Remove a role from a policy statement.

        Gracefully handles:
        - Missing statements (logs warning, does nothing)
        - Missing roles (logs warning, does nothing)
        - Storage failures (logs warning but continues)
        - Role not found in statement (does nothing)
        """

    @abstractmethod
    def _commit(self) -> None:
        """Commit any pending changes to the policy store.

        Gracefully handles:
        - Storage failures (logs warning but continues)
        - No changes to commit (does nothing)
        """

    @abstractmethod
    def teardown(self) -> None:
        """Teardown the policy system.

        Gracefully handles:
        - Cleanup of resources (logs success)
        - No resources to cleanup (does nothing)
        - Storage failures (logs warning but continues)
        """

    @abstractmethod
    def setup(self, *args, **kwargs) -> None:
        """Setup the policy system.

        Gracefully handles:
        - Initialization of resources (logs success)
        - No resources to initialize (does nothing)
        - Storage failures (logs warning but continues)
        """
