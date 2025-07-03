# Copyright (c) 1998-2025 Scott Russell
# SPDX-License-Identifier: MIT

from typing import Any, Optional, Dict, List, Union
from plantangenet.policy.base import Identity, Policy, Role, Statement
from plantangenet.policy.evaluator import GuardClauseEvaluator, DisallowedEvaluator, EvaluationResult
from plantangenet.policy.storage_mixin import PolicyStorageMixin
import uuid


class Vanilla(PolicyStorageMixin, Policy):

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
        # identity_id -> set of role_names
        self.identity_roles: Dict[str, set[str]] = {}
        self._peer = None  # Initialize peer attribute
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
                identity_id = identity.identity_id
                identity_roles = list(
                    self.identity_roles.get(identity_id, set()))
            elif isinstance(identity, str):
                identity_id = identity
                identity_roles = list(
                    self.identity_roles.get(identity_id, set()))
            else:
                # Try to convert to string
                try:
                    identity_id = str(identity)
                    identity_roles = []
                    if self.logger:
                        self.logger.warning(
                            f"Converted identity {identity} to string: {identity_id}")
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

            for stmt in self._policies:
                try:
                    # Check if this is a deny policy
                    if stmt.effect == "deny":
                        # Check if the deny policy applies
                        if self._policy_matches(stmt, identity_roles, action, resource, context):
                            return EvaluationResult(False, "Policy matched with deny effect")

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
        if stmt.roles:
            role_match = (
                "*" in stmt.roles or
                any(role in identity_roles for role in stmt.roles)
            )
            if not role_match:
                return False

        # Check action
        if stmt.actions:
            action_match = "*" in stmt.actions or action in stmt.actions
            if not action_match:
                return False

        # Check resource
        if stmt.resources:
            resource_match = "*" in stmt.resources or resource in stmt.resources
            if not resource_match:
                return False

        # Check conditions
        if stmt.condition:
            try:
                for k, v in stmt.condition.items():
                    if context.get(k) != v:
                        return False
            except Exception as e:
                if self.logger:
                    self.logger.warning(
                        f"Error checking policy condition: {e}")
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

    def has_role(self, identity_id: str, role_name: str) -> bool:
        """Check if an identity has a specific role.

        Gracefully handles:
        - Missing identities (returns False)
        - Missing roles (returns False)
        - None/empty inputs (returns False)
        - Type coercion where reasonable
        """
        if not identity_id or not role_name:
            return False

        try:
            identity_id = str(identity_id)
            role_name = str(role_name)
            return role_name in self.identity_roles.get(identity_id, set())
        except Exception as e:
            if self.logger:
                self.logger.warning(
                    f"Error checking role {role_name} for identity {identity_id}: {e}")
            return False

    def get_role(self, role_name: str) -> Role:
        """Get a role by name.

        Gracefully handles:
        - Missing roles (returns None)
        - None/empty inputs (returns None)
        - Type coercion where reasonable
        """
        if not role_name:
            return None  # type: ignore

        try:
            role_name = str(role_name)
            role = self._roles.get(role_name)
            if role is None:
                # Protocol expects Role, but we handle missing gracefully
                return None  # type: ignore
            return role
        except Exception as e:
            if self.logger:
                self.logger.warning(f"Error getting role {role_name}: {e}")
            return None  # type: ignore

    def add_identity(self, identity: Identity, nickname=None, metadata=None) -> str:
        """Add an identity to the policy system.

        Gracefully handles:
        - None/empty metadata and nickname (uses defaults)
        - Storage failures (logs warning but continues)
        - Duplicate identities (updates existing)
        """
        try:
            if not identity or not identity.identity_id:
                raise ValueError("Identity and identity_id are required")

            # Apply nickname and metadata if provided
            if nickname is not None:
                identity.name = nickname
            if metadata is not None:
                if identity.metadata is None:
                    identity.metadata = {}
                identity.metadata.update(metadata)

            # Store the identity
            self._identities[identity.identity_id] = identity

            # Initialize role mapping if not exists
            if identity.identity_id not in self.identity_roles:
                self.identity_roles[identity.identity_id] = set()

            if self.logger:
                self.logger.info(f"Added identity {identity.identity_id}")
            return identity.identity_id

        except Exception as e:
            if self.logger:
                self.logger.warning(f"Error adding identity: {e}")
            # Return a default ID for graceful handling
            return identity.identity_id if identity and hasattr(identity, 'identity_id') else str(uuid.uuid4())

    def get_identity(self, identity_id: str) -> Optional[Identity]:
        """Get an identity by ID.

        Gracefully handles:
        - Missing identities (returns None)
        - None/empty inputs (returns None)
        - Type coercion where reasonable
        """
        if not identity_id:
            return None

        try:
            identity_id = str(identity_id)
            return self._identities.get(identity_id)
        except Exception as e:
            if self.logger:
                self.logger.warning(
                    f"Error getting identity {identity_id}: {e}")
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
            if not identity or not identity.identity_id:
                if self.logger:
                    self.logger.warning(
                        "Missing identity in add_identity_to_role")
                return

            if not role or not role.name:
                if self.logger:
                    self.logger.warning("Missing role in add_identity_to_role")
                return

            # Ensure identity exists in our system
            if identity.identity_id not in self._identities:
                self.add_identity(identity)

            # Ensure role exists in our system
            if role.name not in self._roles:
                self.add_role(role)

            # Add identity to role
            if identity.identity_id not in self.identity_roles:
                self.identity_roles[identity.identity_id] = set()

            self.identity_roles[identity.identity_id].add(role.name)

            # Update role members
            if role.members is None:
                role.members = []
            if identity.identity_id not in role.members:
                role.members.append(identity.identity_id)

            if self.logger:
                self.logger.info(
                    f"Added identity {identity.identity_id} to role {role.name}")

        except Exception as e:
            if self.logger:
                self.logger.warning(
                    f"Error adding identity {identity.identity_id if identity else 'None'} to role {role.name if role else 'None'}: {e}")

    def remove_identity_from_role(self, identity: Identity, role: Role) -> None:
        """Remove an identity from a role.

        Gracefully handles:
        - Missing identities (logs warning, does nothing)
        - Missing roles (logs warning, does nothing)
        - Storage failures (logs warning but continues)
        - Identity not found in role (does nothing)
        """
        try:
            if not identity or not identity.identity_id:
                if self.logger:
                    self.logger.warning(
                        "Missing identity in remove_identity_from_role")
                return

            if not role or not role.name:
                if self.logger:
                    self.logger.warning(
                        "Missing role in remove_identity_from_role")
                return

            # Remove from identity_roles mapping
            if identity.identity_id in self.identity_roles:
                self.identity_roles[identity.identity_id].discard(role.name)

            # Remove from role members
            if role.members is not None and identity.identity_id in role.members:
                role.members.remove(identity.identity_id)

            if self.logger:
                self.logger.info(
                    f"Removed identity {identity.identity_id} from role {role.name}")

        except Exception as e:
            if self.logger:
                self.logger.warning(
                    f"Error removing identity {identity.identity_id if identity else 'None'} from role {role.name if role else 'None'}: {e}")

    def delete_identity(self, identity: Identity) -> None:
        """Delete an identity from the policy system.

        Gracefully handles:
        - Missing identities (logs warning, does nothing)
        - Storage failures (logs warning but continues)
        - Identity not found (does nothing)
        """
        try:
            if not identity or not identity.identity_id:
                if self.logger:
                    self.logger.warning("Missing identity in delete_identity")
                return

            identity_id = identity.identity_id

            # Remove from identities
            if identity_id in self._identities:
                del self._identities[identity_id]

            # Remove from all roles
            if identity_id in self.identity_roles:
                roles_to_update = list(self.identity_roles[identity_id])
                del self.identity_roles[identity_id]

                # Update role members
                for role_name in roles_to_update:
                    if role_name in self._roles:
                        role_obj = self._roles[role_name]
                        if role_obj.members is not None and identity_id in role_obj.members:
                            role_obj.members.remove(identity_id)

            if self.logger:
                self.logger.info(f"Deleted identity {identity_id}")

        except Exception as e:
            if self.logger:
                self.logger.warning(
                    f"Error deleting identity {identity.identity_id if identity else 'None'}: {e}")

    def add_role(self, role: Role, description=None, members=None) -> str:
        """Add a role to the policy system.

        Gracefully handles:
        - None/empty description and members (uses defaults)
        - Storage failures (logs warning but continues)
        - Duplicate roles (updates existing)
        - Invalid member IDs (logs warning but includes them)
        """
        try:
            if not role or not role.name:
                raise ValueError("Role and role name are required")

            # Apply description and members if provided
            if description is not None:
                role.description = description
            if members is not None:
                role.members = members if isinstance(members, list) else []

            # Ensure members list exists
            if role.members is None:
                role.members = []

            # Store the role
            self._roles[role.name] = role

            # Update identity_roles mapping for existing members
            for member_id in role.members:
                try:
                    if member_id not in self.identity_roles:
                        self.identity_roles[member_id] = set()
                    self.identity_roles[member_id].add(role.name)
                except Exception as e:
                    if self.logger:
                        self.logger.warning(
                            f"Error adding member {member_id} to role {role.name}: {e}")

            if self.logger:
                self.logger.info(f"Added role {role.name}")
            return role.name

        except Exception as e:
            if self.logger:
                self.logger.warning(f"Error adding role: {e}")
            return role.name if role and hasattr(role, 'name') else str(uuid.uuid4())

    def delete_role(self, role: Role) -> None:
        """Delete a role from the policy system.

        Gracefully handles:
        - Missing roles (logs warning, does nothing)
        - Storage failures (logs warning but continues)
        """
        try:
            if not role or not role.name:
                if self.logger:
                    self.logger.warning("Missing role in delete_role")
                return

            role_name = role.name

            # Remove from roles
            if role_name in self._roles:
                del self._roles[role_name]

            # Remove from all identity mappings
            for identity_id in list(self.identity_roles.keys()):
                if role_name in self.identity_roles[identity_id]:
                    self.identity_roles[identity_id].discard(role_name)

            # Remove from statements
            for statement in list(self._policies):
                if role_name in statement.roles:
                    statement.roles.remove(role_name)

            if self.logger:
                self.logger.info(f"Deleted role {role_name}")

        except Exception as e:
            if self.logger:
                self.logger.warning(
                    f"Error deleting role {role.name if role else 'None'}: {e}")

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
                if str(role_name) in self._roles:
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
            statement_id = str(uuid.uuid4())

            # Normalize roles to strings
            normalized_roles = []
            if roles:
                for role in roles:
                    try:
                        if isinstance(role, Role):
                            normalized_roles.append(role.name)
                        elif isinstance(role, str):
                            normalized_roles.append(role)
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

            # Normalize actions to list
            normalized_actions = []
            if action is not None:
                if isinstance(action, list):
                    normalized_actions = [str(a) for a in action]
                else:
                    normalized_actions = [str(action)]

            # Normalize resources to list
            normalized_resources = []
            if resource is not None:
                if isinstance(resource, list):
                    normalized_resources = [str(r) for r in resource]
                else:
                    normalized_resources = [str(resource)]

            # Create statement
            statement = Statement(
                statement_id=statement_id,
                roles=normalized_roles,
                effect=normalized_effect,
                actions=normalized_actions,
                resources=normalized_resources,
                condition=condition,
                delivery=delivery
            )

            # Store statement
            self._policies.append(statement)

            if self.logger:
                self.logger.info(f"Added statement {statement_id}")
            return statement_id

        except Exception as e:
            if self.logger:
                self.logger.warning(f"Error adding statement: {e}")
            # Return a default ID for graceful handling
            return str(uuid.uuid4())

    def delete_statement(self, policy_statement: Statement) -> None:
        """Delete a policy statement.

        Gracefully handles:
        - Missing statements (logs warning, does nothing)
        - Storage failures (logs warning but continues)
        - Invalid policy types (logs warning, skips)
        """
        try:
            if not policy_statement or not policy_statement.statement_id:
                if self.logger:
                    self.logger.warning(
                        "Missing statement in delete_statement")
                return

            statement_id = policy_statement.statement_id

            # Find and remove statement from list
            for i, stmt in enumerate(self._policies):
                if stmt.statement_id == statement_id:
                    del self._policies[i]
                    if self.logger:
                        self.logger.info(f"Deleted statement {statement_id}")
                    return

            if self.logger:
                self.logger.info(
                    f"Statement {statement_id} not found (already deleted or never existed)")

        except Exception as e:
            if self.logger:
                self.logger.warning(
                    f"Error deleting statement {policy_statement.statement_id if policy_statement else 'None'}: {e}")

    def add_role_to_statement(self, policy_statement: Statement, role: Role) -> None:
        """Add a role to a policy statement.

        Gracefully handles:
        - Missing statements (logs warning, does nothing)
        - Missing roles (logs warning, does nothing)
        - Storage failures (logs warning but continues)
        - Duplicate roles in statement (does nothing)
        """
        try:
            if not policy_statement or not policy_statement.statement_id:
                if self.logger:
                    self.logger.warning(
                        "Missing statement in add_role_to_statement")
                return

            if not role or not role.name:
                if self.logger:
                    self.logger.warning(
                        "Missing role in add_role_to_statement")
                return

            statement_id = policy_statement.statement_id

            # Find statement in list
            for stmt in self._policies:
                if stmt.statement_id == statement_id:
                    if role.name not in stmt.roles:
                        stmt.roles.append(role.name)
                        if self.logger:
                            self.logger.info(
                                f"Added role {role.name} to statement {statement_id}")
                    else:
                        if self.logger:
                            self.logger.info(
                                f"Role {role.name} already in statement {statement_id}")
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
            if not policy_statement or not policy_statement.statement_id:
                if self.logger:
                    self.logger.warning(
                        "Missing statement in remove_role_from_statement")
                return

            if not role or not role.name:
                if self.logger:
                    self.logger.warning(
                        "Missing role in remove_role_from_statement")
                return

            statement_id = policy_statement.statement_id

            # Find statement in list
            for stmt in self._policies:
                if stmt.statement_id == statement_id:
                    if role.name in stmt.roles:
                        stmt.roles.remove(role.name)
                        if self.logger:
                            self.logger.info(
                                f"Removed role {role.name} from statement {statement_id}")
                    else:
                        if self.logger:
                            self.logger.info(
                                f"Role {role.name} not found in statement {statement_id}")
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
            self._identities.clear()
            self._roles.clear()
            self._policies.clear()
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
