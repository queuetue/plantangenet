# Copyright (c) 1998-2025 Scott Russell
# SPDX-License-Identifier: MIT

from typing import Optional, Dict, List, Union
from plantangenet.policy.role import Role
from plantangenet.policy.identity import Identity
from plantangenet.policy.statement import Statement
from plantangenet.policy.evaluator import GuardClauseEvaluator, DisallowedEvaluator, EvaluationResult


class Vanilla:

    def __init__(self, peer) -> None:
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
        self.logger = peer.logger
        self._initialized = False
        self._peer = peer
        self._namespace = peer.namespace
        self._policies: List[Statement] = []
        self._identities: Dict[str, Identity] = {}
        self._roles: Dict[str, Role] = {}
        self.evaluators = [
            GuardClauseEvaluator(self, self._peer),
            DisallowedEvaluator(self, self._peer),
        ]

    async def setup(self, *args, **kwargs) -> None:
        self._initialized = True
        self.logger.info("Policy engine started")

    def has_role(self, identity_id: str, role_name: str) -> bool:
        """Check if an identity has a specific role.

        Gracefully handles:
        - Missing identities (returns False)
        - Missing roles (returns False)
        - None/empty inputs (returns False)
        - Type coercion where reasonable
        """

        # Defensive type handling
        try:
            identity_id = str(identity_id) if identity_id is not None else ""
            role_name = str(role_name) if role_name is not None else ""
        except (TypeError, ValueError):
            self.logger.warning(
                f"Invalid types for has_role: identity_id={identity_id}, role_name={role_name}")
            return False

        if not identity_id or not role_name:
            return False

        if identity_id not in self._identities:
            return False
        if role_name not in self._roles:
            return False

        identity = self._identities[identity_id]
        return role_name in identity.roles

    def get_role(self, role_name: str) -> Role:
        if role_name not in self._roles:
            raise ValueError(f"Role '{role_name}' does not exist.")
        return self._roles[role_name]

    async def add_identity(self, identity: Identity, nickname=None, metadata=None) -> str:
        """Add an identity to the policy system.

        Gracefully handles:
        - None/empty metadata and nickname (uses defaults)
        - Storage failures (logs warning but continues)
        - Duplicate identities (updates existing)
        """
        if not isinstance(identity, Identity):
            raise ValueError("Identity must be an Identity model.")

        # Be flexible with optional parameters
        if nickname is not None:
            identity.nickname = str(nickname)
        if metadata is not None:
            # Ensure metadata is a dict, handle common mistakes
            if isinstance(metadata, str):
                self.logger.warning(
                    f"Converting string metadata to dict for {identity.id}")
                metadata = {"note": metadata}
            elif not isinstance(metadata, dict):
                self.logger.warning(
                    f"Converting non-dict metadata to dict for {identity.id}")
                metadata = {"value": str(metadata)}
            identity.metadata = metadata

        # Store the identity
        existing = self._identities.get(identity.id)
        if existing:
            self.logger.info(f"Updating existing identity {identity.id}")

        self._identities[identity.id] = identity
        self.logger.debug("Identity created", context=identity.dict())

        # Try to save to storage, but don't fail if storage is unavailable
        key = None
        if self._peer.storage:
            try:
                key = await self._peer.storage.save_identity(identity)
                self.logger.debug(
                    f'Identity saved: {key}', context=identity.dict())
            except Exception as e:
                self.logger.warning(f"Failed to save identity to storage: {e}")
                # Continue without storage - policy engine should work in memory

        self._sync_roles()
        return key or f"memory:{identity.id}"

    async def get_identity(self, identity_id: str) -> Optional[Identity]:
        if identity_id not in self._identities:
            raise ValueError(f"Identity '{identity_id}' does not exist.")
        return self._identities[identity_id]

    async def add_identity_to_role(self, identity: Identity, role: Role) -> None:
        if identity.id not in self._identities:
            raise ValueError(f"Identity '{identity.id}' does not exist.")

        if identity.id not in role.members:
            role.members.append(identity.id)
        if role.name not in identity.roles:
            identity.roles.append(role.name)

    async def remove_identity_from_role(self, identity: Identity, role: Role) -> None:
        if identity.id not in self._identities:
            raise ValueError(f"Identity '{identity.id}' does not exist.")
        if identity.id in role.members:
            role.members.remove(identity.id)
        if role.name in identity.roles:
            identity.roles.remove(role.name)

    async def delete_identity(self, identity: Identity) -> None:
        if identity.id not in self._identities:
            raise ValueError(f"Identity '{identity.id}' does not exist.")
        for role in self._roles.values():
            if identity.id in role.members:
                role.members.remove(identity.id)
        del self._identities[identity.id]

    async def add_role(self, role: Role, description=None, members=None) -> str:
        """Add a role to the policy system.

        Gracefully handles:
        - None/empty description and members (uses defaults)
        - Storage failures (logs warning but continues)
        - Duplicate roles (updates existing)
        - Invalid member IDs (logs warning but includes them)
        """
        if not isinstance(role, Role):
            raise ValueError("Role must be a Role model.")

        # Be flexible with optional parameters
        if description is not None:
            role.description = str(description)

        if members is not None:
            # Handle various member formats
            if isinstance(members, str):
                members = [members]  # Single string -> list
            elif not isinstance(members, list):
                try:
                    members = list(members)  # Try to convert iterable
                except (TypeError, ValueError):
                    self.logger.warning(
                        f"Invalid members format for role {role.name}, using empty list")
                    members = []

            # Ensure all members are strings
            clean_members = []
            for member in members:
                try:
                    clean_members.append(str(member))
                except (TypeError, ValueError):
                    self.logger.warning(
                        f"Skipping invalid member {member} for role {role.name}")

            role.members = clean_members

        # Store the role
        existing = self._roles.get(role.name)
        if existing:
            self.logger.info(f"Updating existing role {role.name}")

        self._roles[role.name] = role
        self.logger.debug("Role added", context=role.dict())

        # Try to save to storage, but don't fail if storage is unavailable
        key = None
        if self._peer.storage:
            try:
                key = await self._peer.storage.save_role(role)
            except Exception as e:
                self.logger.warning(f"Failed to save role to storage: {e}")
                # Continue without storage - policy engine should work in memory

        self._sync_roles()
        return key or f"memory:{role.name}"

    async def delete_role(self, role: Role) -> None:
        if role.name not in self._roles:
            raise ValueError(f"Role '{role.name}' does not exist.")
        del self._roles[role.name]

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
        if "*" in roles:
            return True
        for role in roles:
            if role == self._peer.any_role.name:
                return True
        return False

    async def add_policy(self, roles: List[Union[str, Role]], effect, action, resource, condition=None, delivery=None) -> str:
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
        # Normalize roles to strings with defensive handling
        role_names = []
        if not isinstance(roles, list):
            roles = [roles]  # Convert single role to list

        for role in roles:
            try:
                if isinstance(role, Role):
                    role_names.append(role.name)
                elif isinstance(role, str) and role.strip():
                    role_names.append(role.strip())
                elif role is not None:
                    # Try to convert to string
                    role_str = str(role).strip()
                    if role_str:
                        role_names.append(role_str)
                        self.logger.warning(
                            f"Converted role {role} to string: {role_str}")
            except Exception as e:
                self.logger.warning(f"Skipping invalid role {role}: {e}")

        if not role_names:
            self.logger.warning(
                "No valid roles provided for policy, using ['*'] as default")
            role_names = ["*"]

        # Normalize effect with defensive handling
        if not isinstance(effect, str):
            effect = str(effect) if effect is not None else ""
        effect = effect.lower().strip()
        if effect not in ["allow", "deny"]:
            self.logger.warning(
                f"Invalid effect '{effect}', defaulting to 'deny' for safety")
            effect = "deny"

        # Normalize action and resource lists
        action = action if isinstance(action, list) else [
            action] if action is not None else ["*"]
        resource = resource if isinstance(resource, list) else [
            resource] if resource is not None else ["*"]

        # Clean up action and resource lists
        action = [str(a).strip()
                  for a in action if a is not None and str(a).strip()]
        resource = [str(r).strip()
                    for r in resource if r is not None and str(r).strip()]

        if not action:
            action = ["*"]
        if not resource:
            resource = ["*"]

        # Handle condition safely
        if condition is not None and not isinstance(condition, dict):
            self.logger.warning(
                f"Invalid condition type {type(condition)}, using empty dict")
            condition = {}
        condition = condition or {}

        try:
            policy_statement = Statement(
                id=self._peer.fresh_id() if hasattr(
                    self._peer, 'fresh_id') else f"policy-{len(self._policies)}",
                role_names=role_names,
                effect=effect,
                action=action,
                resource=resource,
                condition=condition,
                delivery=delivery
            )
        except Exception as e:
            self.logger.error(f"Failed to create policy statement: {e}")
            raise ValueError(f"Invalid policy statement parameters: {e}")

        self._policies.append(policy_statement)

        # Try to save to storage, but don't fail if storage is unavailable
        key = None
        if self._peer.storage:
            try:
                key = await self._peer.storage.save_statement(policy_statement)
            except Exception as e:
                self.logger.warning(f"Failed to save policy to storage: {e}")
                # Continue without storage - policy engine should work in memory

        return key or f"memory:policy-{len(self._policies)-1}"

    async def delete_policy(self, policy_statement: Statement) -> None:
        try:
            self._policies.remove(policy_statement)
        except ValueError:
            raise ValueError("Policy statement does not exist.")

    async def add_role_to_policy(self, policy_statement: Statement, role: Role) -> None:
        if role.name not in policy_statement.role_names:
            policy_statement.role_names.append(role.name)
        if self._peer.storage:
            await self._peer.storage.save_statement(policy_statement)
        else:
            raise RuntimeError(
                "Storage backend not available for saving policy")

    async def remove_role_from_policy(self, policy_statement: Statement, role: Role) -> None:
        if role in policy_statement.role_names:
            policy_statement.role_names.remove(role.name)
        if self._peer.storage:
            await self._peer.storage.save_statement(policy_statement)
        else:
            raise RuntimeError(
                "Storage backend not available for saving policy")

    def _identity_roles(self, identity: Identity) -> List[str]:
        if isinstance(identity, Identity):
            return identity.roles
        return []

    async def _commit(self) -> None:
        """Commit changes to the storage backend if available."""
        if self._peer.storage:
            self._peer.storage.commit()
        else:
            raise RuntimeError(
                "Storage backend not available for committing changes")
        self._sync_roles()
        self.logger.debug("Changes committed to storage")

    def _sync_roles(self) -> None:
        for role in self._roles.values():
            for member_id in role.members:
                if member_id in self._identities:
                    identity = self._identities[member_id]
                    if role.name not in identity.roles:
                        identity.roles.append(role.name)

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

    async def teardown(self) -> None:
        self.logger.info("Policy engine stopped")

    async def to_dict(self) -> Dict[str, Union[List[Statement], Dict[str, Identity], Dict[str, Role]]]:
        statements = await self._peer.storage.list_statements()
        identities = await self._peer.storage.list_identities()
        roles = await self._peer.storage.list_roles()
        return {
            "statements": statements,
            "identities": identities,
            "roles": roles
        }
