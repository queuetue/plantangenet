# Copyright (c) 1998-2025 Scott Russell
# SPDX-License-Identifier: MIT

from typing import Optional, Dict, List, Union, Any, Set
from ulid import ULID
from .role import Role
from .statement import Statement
from .identity import Identity
from .evaluator import GuardClauseEvaluator, DisallowedEvaluator, EvaluationResult
from ..logger import Logger
from pydantic import Field
from .base import BasePolicy


class Policy(BasePolicy):
    id: str = Field(default_factory=lambda: str(ULID()))
    policies: List[Statement] = Field(default_factory=list)
    identities: Dict[str, Identity] = Field(default_factory=dict)
    roles: Dict[str, Role] = Field(default_factory=dict)
    identity_roles: Dict[str, Set[str]] = Field(default_factory=dict)
    peer: Optional[Any] = Field(default=None)
    evaluators: List[Any] = Field(default_factory=list)

    @property
    def logger(self) -> Logger: ...

    def __init__(self, **data) -> None:
        """ 
        This is a reference implementation of the plantangenet security
        engine designed for clarity and correctness. It favors
        conservative defaults and defensive programming. It is intentionally
        not the fastest, strictest, or most negotiable engine. It is 
        intended as a foundation on which environment-specific engines can
        be built. But you can run a plantangenet ocean with it.
        """
        super().__init__(**data)
        # Initialize evaluators after Pydantic initialization
        if not self.evaluators:
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
                self.peer, 'id', '<unknown>'))

            # Normalize identity
            if isinstance(identity, Identity):
                id = identity.id
                identity_roles = list(
                    self.identity_roles.get(id, set()))
            elif isinstance(identity, str):
                id = identity
                identity_roles = list(
                    self.identity_roles.get(id, set()))
            else:
                # Try to convert to string
                try:
                    id = str(identity)
                    identity_roles = []
                    if self.logger:
                        self.logger.warning(
                            f"Converted identity {identity} to string: {id}")
                except Exception as e:
                    if self.logger:
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

            for stmt in self.policies:
                try:
                    # Check if this is a deny policy
                    if stmt.effect == "deny":
                        # Check if the deny policy applies
                        if self._policy_matches(stmt, identity_roles, action, resource, context):
                            return EvaluationResult(passed=False, reason="Policy matched with deny effect")

                    elif stmt.effect == "allow":
                        if self._policy_matches(stmt, identity_roles, action, resource, context):
                            matched_allow = True

                except Exception as e:
                    self.logger.warning(
                        f"Error evaluating policy statement: {e}")
                    continue  # Skip malformed policies

            if matched_allow:
                return EvaluationResult(passed=True, reason="Policy matched with allow effect")
            else:
                return EvaluationResult(passed=False, reason="No policy explicitly allowed this action")

        except Exception as e:
            self.logger.error(
                f"Unexpected error during policy evaluation: {e}")
            # Fail secure - deny by default
            return EvaluationResult(passed=False, reason=f"Evaluation failed: {e}")

    def _policy_matches(self, stmt: Statement, identity_roles: List[str], action: str, resource: str, context: dict) -> bool:
        """Check if a policy statement matches the given parameters."""
        try:
            # 1. Role match (at least one role in identity_roles must be in stmt.role_ids, or stmt.role_ids contains '*')
            if not stmt.role_ids:
                return False
            if '*' not in stmt.role_ids and not any(role in stmt.role_ids for role in identity_roles):
                return False

            # 2. Action match (support wildcard)
            if not stmt.action or not self._matches_action(stmt.action, action):
                return False

            # 3. Resource match (support wildcard)
            if not stmt.resource or not self._matches_resource(stmt.resource, resource):
                return False

            # 4. Condition match (if any)
            if stmt.condition:
                if not self._check_conditions(stmt.condition, context):
                    return False

            return True
        except Exception as e:
            if self.logger:
                self.logger.warning(f"Error in _policy_matches: {e}")
            return False

    def _matches_action(self, actions, action) -> bool:
        """Check if an action matches any of the action patterns.

        Supports:
        - Exact match: "move" matches "move"
        - Wildcard: "*" matches anything
        """
        return "*" in actions or action in actions

    def _matches_resource(self, resources, resource) -> bool:
        """Check if a resource matches any of the resource patterns.

        Supports:
        - Exact match: "activity:game1" matches "activity:game1"
        - Wildcard: "activity:*" matches "activity:game1", "activity:game2", etc.
        - Global wildcard: "*" matches anything
        """
        for pattern in resources:
            if pattern == "*":  # Global wildcard
                return True
            elif pattern == resource:  # Exact match
                return True
            elif pattern.endswith("*"):  # Prefix wildcard
                prefix = pattern[:-1]  # Remove the *
                if resource.startswith(prefix):
                    return True
        return False

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

    def has_role(self, id: str, role_name: str) -> bool:
        """Check if an identity has a specific role.

        Gracefully handles:
        - Missing identities (returns False)
        - Missing roles (returns False)
        - None/empty inputs (returns False)
        - Type coercion where reasonable
        """
        if not id or not role_name:
            return False

        try:
            id = str(id)
            role_name = str(role_name)
            return role_name in self.identity_roles.get(id, set())
        except Exception as e:
            if self.logger:
                self.logger.warning(
                    f"Error checking role {role_name} for identity {id}: {e}")
            return False

    def get_role(self, role_name: str) -> Optional[Role]:
        """Get a role by ID or name.

        Gracefully handles:
        - Missing roles (returns None)
        - None/empty inputs (returns None)
        - Type coercion where reasonable
        - Lookup by either role.id or role.name
        """
        if not role_name:
            return None  # type: ignore

        try:
            role_name = str(role_name)

            # First try by role.id (primary key)
            role = self.roles.get(role_name)
            if role is not None:
                return role

            # Fallback: search by role.name
            for role in self.roles.values():
                if role.name == role_name:
                    return role

            return None
        except Exception as e:
            if self.logger:
                self.logger.warning(f"Error getting role {role_name}: {e}")
            return None

    def add_identity(self, identity: Identity, nickname=None, metadata=None) -> str:
        """Add an identity to the policy system.

        Gracefully handles:
        - None/empty metadata and nickname (uses defaults)
        - Storage failures (logs warning but continues)
        - Duplicate identities (updates existing)
        """
        try:
            if not identity or not identity.id:
                raise ValueError("Identity and id are required")

            # Apply nickname and metadata if provided
            # if nickname is not None:
            #     identity.name = nickname
            if metadata is not None:
                if identity.metadata is None:
                    identity.metadata = {}
                identity.metadata.update(metadata)

            # Store the identity
            self.identities[identity.id] = identity

            # Initialize role mapping if not exists
            if identity.id not in self.identity_roles:
                self.identity_roles[identity.id] = set()

            if self.logger:
                self.logger.info(f"Added identity {identity.id}")
            return identity.id

        except Exception as e:
            if self.logger:
                self.logger.warning(f"Error adding identity: {e}")
            # Return a default ID for graceful handling
            return identity.id if identity and hasattr(identity, 'id') else str(ULID())

    def get_identity(self, id: str) -> Optional[Identity]:
        """Get an identity by ID.

        Gracefully handles:
        - Missing identities (returns None)
        - None/empty inputs (returns None)
        - Type coercion where reasonable
        """
        if not id:
            return None

        try:
            id = str(id)
            return self.identities.get(id)
        except Exception as e:
            if self.logger:
                self.logger.warning(
                    f"Error getting identity {id}: {e}")
            return None

    def add_identity_to_role(self, identity: Identity, role: Role) -> None:
        """Add an identity to a role.

        Gracefully handles:
        - Missing identities (logs warning, does nothing)
        - Missing roles (logs warning, does nothing)
        - Storage failures (logs warning but continues)
        - Duplicate identities in role (does nothing)
        """
        try:
            if not identity or not identity.id:
                if self.logger:
                    self.logger.warning(
                        "Missing identity in add_identity_to_role")
                return

            if not role or not role.id:
                if self.logger:
                    self.logger.warning("Missing role in add_identity_to_role")
                return

            # Ensure identity exists in our system
            if identity.id not in self.identities:
                self.add_identity(identity)

            # Ensure role exists in our system
            if role.id not in self.roles:
                self.add_role(role)

            # Add identity to role (use role.id for consistency with statements)
            if identity.id not in self.identity_roles:
                self.identity_roles[identity.id] = set()

            self.identity_roles[identity.id].add(
                role.id)  # Use role.id, not role.name

            # Update role members
            if role.members is None:
                role.members = []
            if identity.id not in role.members:
                role.members.append(identity.id)

            if self.logger:
                self.logger.info(
                    f"Added identity {identity.id} to role {role.name}")

        except Exception as e:
            if self.logger:
                self.logger.warning(
                    f"Error adding identity {identity.id if identity else 'None'} to role {role.name if role else 'None'}: {e}")

    def remove_identity_from_role(self, identity: Identity, role: Role) -> None:
        """Remove an identity from a role.

        Gracefully handles:
        - Missing identities (logs warning, does nothing)
        - Missing roles (logs warning, does nothing)
        - Storage failures (logs warning but continues)
        - Identity not found in role (does nothing)
        """
        try:
            if not identity or not identity.id:
                if self.logger:
                    self.logger.warning(
                        "Missing identity in remove_identity_from_role")
                return

            if not role or not role.name:
                if self.logger:
                    self.logger.warning(
                        "Missing role in remove_identity_from_role")
                return

            # Remove from identity_roles mapping (use role.id for consistency)
            if identity.id in self.identity_roles:
                self.identity_roles[identity.id].discard(
                    role.id)  # Use role.id, not role.name

            # Remove from role members
            if role.members is not None and identity.id in role.members:
                role.members.remove(identity.id)

            if self.logger:
                self.logger.info(
                    f"Removed identity {identity.id} from role {role.name}")

        except Exception as e:
            if self.logger:
                self.logger.warning(
                    f"Error removing identity {identity.id if identity else 'None'} from role {role.name if role else 'None'}: {e}")

    def delete_identity(self, identity: Identity) -> None:
        """Delete an identity from the policy system.

        Gracefully handles:
        - Missing identities (logs warning, does nothing)
        - Storage failures (logs warning but continues)
        - Identity not found (does nothing)
        """
        try:
            if not identity or not identity.id:
                if self.logger:
                    self.logger.warning("Missing identity in delete_identity")
                return

            id = identity.id

            # Remove from identities
            if id in self.identities:
                del self.identities[id]

            # Remove from all roles
            if id in self.identity_roles:
                roles_to_update = list(self.identity_roles[id])
                del self.identity_roles[id]

                # Update role members
                for role_name in roles_to_update:
                    if role_name in self.roles:
                        role_obj = self.roles[role_name]
                        if role_obj.members is not None and id in role_obj.members:
                            role_obj.members.remove(id)

            if self.logger:
                self.logger.info(f"Deleted identity {id}")

        except Exception as e:
            if self.logger:
                self.logger.warning(
                    f"Error deleting identity {identity.id if identity else 'None'}: {e}")

    def add_role(self, role: Role, description=None, members=None) -> str:
        """Add a role to the policy system.

        Gracefully handles:
        - None/empty description and members (uses defaults)
        - Storage failures (logs warning but continues)
        - Duplicate roles (updates existing)
        - Invalid member IDs (logs warning but includes them)
        """
        try:
            if not role or not role.id:
                raise ValueError("Role and role ID are required")

            # Apply description and members if provided
            if description is not None:
                role.description = description
            if members is not None:
                role.members = members if isinstance(members, list) else []

            # Ensure members list exists
            if role.members is None:
                role.members = []

            # Store the role using role.id as key for consistency
            self.roles[role.id] = role

            # Update identity_roles mapping for existing members (use role.id)
            for member_id in role.members:
                try:
                    if member_id not in self.identity_roles:
                        self.identity_roles[member_id] = set()
                    self.identity_roles[member_id].add(
                        role.id)  # Use role.id, not role.name
                except Exception as e:
                    if self.logger:
                        self.logger.warning(
                            f"Error adding member {member_id} to role {role.name}: {e}")

            if self.logger:
                self.logger.info(f"Added role {role.name} with ID {role.id}")
            return role.id  # Return role.id for consistency

        except Exception as e:
            if self.logger:
                self.logger.warning(f"Error adding role: {e}")
            return role.id if role and hasattr(role, 'id') else str(ULID())

    def delete_role(self, role: Role) -> None:
        """Delete a role from the policy system.

        Gracefully handles:
        - Missing roles (logs warning, does nothing)
        - Storage failures (logs warning but continues)
        """
        try:
            if not role or not role.id:  # Check role.id instead of role.name
                if self.logger:
                    self.logger.warning("Missing role in delete_role")
                return

            role_id = role.id  # Use role.id consistently

            # Remove from roles (roles are still stored by name in self.roles)
            # Delete from roles dictionary using role.id
            if role.id in self.roles:
                del self.roles[role.id]

            # Remove from all identity mappings (use role.id)
            for id in list(self.identity_roles.keys()):
                if role_id in self.identity_roles[id]:
                    self.identity_roles[id].discard(role_id)

            # Remove from statements (use role.id)
            for statement in list(self.policies):
                if hasattr(statement, 'role_ids') and role_id in statement.role_ids:
                    statement.role_ids.remove(role_id)

            if self.logger:
                self.logger.info(f"Deleted role {role_id}")

        except Exception as e:
            if self.logger:
                self.logger.warning(
                    f"Error deleting role {role.id if role else 'None'}: {e}")

    def includes_any_role(self, roles: List[str]) -> bool:
        """
        Check if any role in the list natches our any role or the generic wildcard '*'.
        Args:
            roles (List[str]): List of role names to check.
        Returns:
            bool: True if any role matches, False otherwise.
        """
        if not roles:
            return False

        try:
            # Check for wildcard
            if '*' in roles:
                return True

            # Check if any role exists in our role store
            for role_name in roles:
                if str(role_name) in self.roles:
                    return True

            return False
        except Exception as e:
            if self.logger:
                self.logger.warning(f"Error checking roles {roles}: {e}")
            return False

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
        try:
            # Generate statement ID
            statement_id = str(ULID())

            # Normalize roles to strings (using role.id for consistency)
            normalized_role_ids = []
            if roles:
                for role in roles:
                    try:
                        if isinstance(role, Role):
                            # Use role.id consistently
                            normalized_role_ids.append(role.id)
                        elif isinstance(role, str):
                            normalized_role_ids.append(role)
                        else:
                            if self.logger:
                                self.logger.warning(
                                    f"Invalid role type: {type(role)}")
                    except Exception as e:
                        if self.logger:
                            self.logger.warning(
                                f"Error processing role {role}: {e}")

            # Normalize effect
            normalized_effect = "deny"  # Default for safety
            if effect:
                effect_str = str(effect).lower()
                if effect_str in ["allow", "permit", "grant"]:
                    normalized_effect = "allow"
                elif effect_str in ["deny", "block", "reject"]:
                    normalized_effect = "deny"

            # Normalize action to list
            normalized_action = []
            if action is not None:
                if isinstance(action, list):
                    normalized_action = [str(a) for a in action]
                else:
                    normalized_action = [str(action)]

            # Normalize resource to list
            normalized_resource = []
            if resource is not None:
                if isinstance(resource, list):
                    normalized_resource = [str(r) for r in resource]
                else:
                    normalized_resource = [str(resource)]

            # Create statement (cost and capabilities are optional and default to None)
            statement = Statement(
                id=statement_id,
                role_ids=normalized_role_ids,
                effect=normalized_effect,
                action=normalized_action,
                resource=normalized_resource,
                condition=condition or {},
                delivery=delivery,
                cost=None,
                capabilities=None
            )

            # Store statement
            self.policies.append(statement)

            if self.logger:
                self.logger.info(f"Added statement {statement_id}")
            return statement_id

        except Exception as e:
            if self.logger:
                self.logger.warning(f"Error adding statement: {e}")
            # Return a default ID for graceful handling
            return str(ULID())

    def delete_statement(self, policy_statement: Statement) -> None:
        """Delete a policy statement.

        Gracefully handles:
        - Missing statements (logs warning, does nothing)
        - Storage failures (logs warning but continues)
        - Invalid policy types (logs warning, skips)
        """
        try:
            if not policy_statement or not policy_statement.id:
                if self.logger:
                    self.logger.warning(
                        "Missing statement in delete_statement")
                return

            statement_id = policy_statement.id

            # Find and remove statement from list
            for i, stmt in enumerate(self.policies):
                if stmt.id == statement_id:
                    del self.policies[i]
                    if self.logger:
                        self.logger.info(f"Deleted statement {statement_id}")
                    return

            if self.logger:
                self.logger.info(
                    f"Statement {statement_id} not found (already deleted or never existed)")

        except Exception as e:
            if self.logger:
                self.logger.warning(
                    f"Error deleting statement {policy_statement.id if policy_statement else 'None'}: {e}")

    def add_role_to_statement(self, policy_statement: Statement, role: Role) -> None:
        """Add a role to a policy statement.

        Gracefully handles:
        - Missing statements (logs warning, does nothing)
        - Missing roles (logs warning, does nothing)
        - Storage failures (logs warning but continues)
        - Duplicate roles in statement (does nothing)
        """
        try:
            if not policy_statement or not policy_statement.id:
                if self.logger:
                    self.logger.warning(
                        "Missing statement in add_role_to_statement")
                return

            if not role or not role.id:
                if self.logger:
                    self.logger.warning(
                        "Missing role in add_role_to_statement")
                return

            statement_id = policy_statement.id

            # Find statement in list
            for stmt in self.policies:
                if stmt.id == statement_id:
                    if hasattr(stmt, 'role_ids') and role.id not in stmt.role_ids:
                        stmt.role_ids.append(role.id)
                        if self.logger:
                            self.logger.info(
                                f"Added role {role.name} (ID: {role.id}) to statement {statement_id}")
                    else:
                        if self.logger:
                            self.logger.info(
                                f"Role {role.name} (ID: {role.id}) already in statement {statement_id}")
                    return

            if self.logger:
                self.logger.warning(f"Statement {statement_id} not found")

        except Exception as e:
            if self.logger:
                self.logger.warning(f"Error adding role to statement: {e}")

    def remove_role_from_statement(self, policy_statement: Statement, role: Role) -> None:
        """Remove a role from a policy statement.

        Gracefully handles:
        - Missing statements (logs warning, does nothing)
        - Missing roles (logs warning, does nothing)
        - Storage failures (logs warning but continues)
        - Role not found in statement (does nothing)
        """
        try:
            if not policy_statement or not policy_statement.id:
                if self.logger:
                    self.logger.warning(
                        "Missing statement in remove_role_from_statement")
                return

            if not role or not role.id:
                if self.logger:
                    self.logger.warning(
                        "Missing role in remove_role_from_statement")
                return

            statement_id = policy_statement.id

            # Find statement in list
            for stmt in self.policies:
                if stmt.id == statement_id:
                    if hasattr(stmt, 'role_ids') and role.id in stmt.role_ids:
                        stmt.role_ids.remove(role.id)
                        if self.logger:
                            self.logger.info(
                                f"Removed role {role.name} (ID: {role.id}) from statement {statement_id}")
                    else:
                        if self.logger:
                            self.logger.info(
                                f"Role {role.name} (ID: {role.id}) not found in statement {statement_id}")
                    return

            if self.logger:
                self.logger.warning(f"Statement {statement_id} not found")

        except Exception as e:
            if self.logger:
                self.logger.warning(f"Error removing role from statement: {e}")

    def _commit(self) -> None:
        """Commit any pending changes to the policy store.

        Gracefully handles:
        - Storage failures (logs warning but continues)
        - No changes to commit (does nothing)
        """
        try:
            # In this naive implementation, everything is in-memory, so no commit needed
            if self.logger:
                self.logger.info("Commit completed (in-memory implementation)")
        except Exception as e:
            if self.logger:
                self.logger.warning(f"Error during commit: {e}")

    def teardown(self) -> None:
        """Teardown the policy system.

        Gracefully handles:
        - Cleanup of resources (logs success)
        - No resources to cleanup (does nothing)
        - Storage failures (logs warning but continues)
        """
        try:
            # Clear all in-memory storage
            self.identities.clear()
            self.roles.clear()
            self.policies.clear()
            self.identity_roles.clear()
            if self.logger:
                self.logger.info("Policy system teardown completed")
        except Exception as e:
            if self.logger:
                self.logger.warning(f"Error during teardown: {e}")

    def setup(self, *args, **kwargs) -> None:
        """Setup the policy system.

        Gracefully handles:
        - Initialization of resources (logs success)
        - No resources to initialize (does nothing)
        - Storage failures (logs warning but continues)
        """
        try:
            # Initialize storage if needed (already done in __init__)
            if self.logger:
                self.logger.info("Policy system setup completed")
        except Exception as e:
            if self.logger:
                self.logger.warning(f"Error during setup: {e}")
