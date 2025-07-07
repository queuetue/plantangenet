# Copyright (c) 1998-2025 Scott Russell
# SPDX-License-Identifier: MIT

"""
Omni-enhanced Squad implementation that inherits from OmniBase for persistence,
policy-awareness, and unified management capabilities.
"""

from typing import Any, Callable, Optional, Dict, List
from ..omni.base import OmniBase
from ..omni.helpers import watch, persist
from ..session.session import Session
from ..policy.policy import Policy
from ..policy.identity import Identity
from ..agents.agent import Agent  # Import Agent for inheritance
import uuid
import time


class OmniSquad(OmniBase, Agent):
    """
    Enhanced Squad that inherits from both OmniBase and Agent, providing:
    - Persistent identity and state (from Omni)
    - Agent-like capabilities for distributed coordination (from Agent)
    - Policy-aware access control
    - Storage integration
    - Session management with full audit trail

    This unifies Squad with both the Omni and Agent systems for consistent 
    management, persistence, and distributed coordination.
    """

    # Note: Omni field declarations require the OmniMixin pattern
    # These will be properly declared when we integrate with the mixin system

    def __init__(self, name: Optional[str] = None, policy: Optional[Policy] = None,
                 session: Optional[Session] = None, **kwargs):
        """
        Initialize OmniSquad with both Omni and Agent capabilities.

        Args:
            name: Squad name
            policy: Squad-level policy (can cascade to sessions)
            session: Parent session context
            **kwargs: Additional initialization parameters
        """
        # Initialize Agent first (provides logger, id, etc.)
        Agent.__init__(self, namespace=kwargs.get('namespace', 'plantangenet'))

        # Initialize Omni base
        OmniBase.__init__(self, session=session, policy=policy, **kwargs)

        # Squad-specific initialization
        self._squad_name = name or f"squad_{self.short_id}"
        self._creation_timestamp = time.time()
        self._member_count = 0
        self._session_count = 0
        self._policy_cache_hits = 0
        self._last_activity = time.time()
        self._squad_config = {}
        self._distributed_enabled = False

        # Core squad functionality
        self._groups: Dict[str, List[Any]] = {}
        self._sessions: Dict[str, Session] = {}
        self._policy_cache: Dict[str, Dict[str, Any]] = {}
        self._cache_timeout = 600  # 10 minutes

        # Set up as a manager for duck-typing compatibility
        self.is_manager = True

    @property
    def squad_name(self) -> str:
        return self._squad_name

    @property
    def member_count(self) -> int:
        return self._member_count

    @property
    def session_count(self) -> int:
        return self._session_count

    @property
    def distributed_enabled(self) -> bool:
        return self._distributed_enabled

    def _update_member_count(self):
        """Update member count and last activity."""
        self._member_count = sum(len(g) for g in self._groups.values())
        self._last_activity = time.time()

    def _update_session_count(self):
        """Update session count and last activity."""
        self._session_count = len(self._sessions)
        self._last_activity = time.time()

    # Group management methods (BaseSquad compatibility, renamed to avoid conflicts)
    def add_to_group(self, group: str, obj: Any):
        """Add object to a group, with policy checks and audit trail."""
        if not self._check_omni_access("write"):
            raise PermissionError("Access denied to add to squad")

        if group not in self._groups:
            self._groups[group] = []
        self._groups[group].append(obj)
        self._update_member_count()

    def remove_from_group(self, group: str, obj: Any):
        """Remove object from a group, with policy checks and audit trail."""
        if not self._check_omni_access("write"):
            raise PermissionError("Access denied to remove from squad")

        if group in self._groups:
            self._groups[group] = [o for o in self._groups[group] if o != obj]
            self._update_member_count()

    def get_group(self, group: str) -> List[Any]:
        """Get objects in a group, with policy checks."""
        if not self._check_omni_access("read"):
            raise PermissionError("Access denied to read squad")
        return self._groups.get(group, [])

    def get_all_groups(self) -> Dict[str, List[Any]]:
        """Get all groups, with policy checks."""
        if not self._check_omni_access("read"):
            raise PermissionError("Access denied to read squad")
        return self._groups

    def query_group(self, group: str, predicate: Callable[[Any], bool]) -> List[Any]:
        """Query objects in a group with predicate."""
        if not self._check_omni_access("read"):
            raise PermissionError("Access denied to query squad")
        return [o for o in self._groups.get(group, []) if predicate(o)]

    def group_difference(self, group_a: str, group_b: str) -> List[Any]:
        """Return items in group_a that are not in group_b."""
        if not self._check_omni_access("read"):
            raise PermissionError("Access denied to compare groups")
        set_b = set(self._groups.get(group_b, []))
        return [o for o in self._groups.get(group_a, []) if o not in set_b]

    def transform_group(self, group: str, data: Any, frame: Any = None) -> Any:
        """Apply all transformers in the group to the data."""
        if not self._check_omni_access("read"):
            raise PermissionError("Access denied to transform")
        for transformer in self._groups.get(group, []):
            if callable(transformer):
                data = transformer(data, frame)
        return data

    # Legacy BaseSquad compatibility methods
    def add(self, group: str, obj: Any):
        """Legacy compatibility method."""
        return self.add_to_group(group, obj)

    def remove(self, group: str, obj: Any):
        """Legacy compatibility method."""
        return self.remove_from_group(group, obj)

    def all(self) -> Dict[str, List[Any]]:
        """Legacy compatibility method."""
        return self.get_all_groups()

    def query(self, group: str, predicate: Callable[[Any], bool]) -> List[Any]:
        """Legacy compatibility method."""
        return self.query_group(group, predicate)

    def difference(self, group_a: str, group_b: str) -> List[Any]:
        """Legacy compatibility method."""
        return self.group_difference(group_a, group_b)

    def transform(self, group: str, data: Any, frame: Any = None) -> Any:
        """Legacy compatibility method."""
        return self.transform_group(group, data, frame)

    # Session management methods (enhanced with Omni capabilities)
    def create_session(self, identity: Identity, session_policy: Optional[Policy] = None) -> Session:
        """Create a new session within this squad context."""
        if not self._check_omni_access("write"):
            raise PermissionError("Access denied to create session")

        # Use squad policy as fallback if no session policy provided
        effective_policy = session_policy or self._omni__policy

        # Create session with required id parameter
        session_id = str(uuid.uuid4())
        session = Session(
            id=session_id,
            identity=identity,
            policy=effective_policy
        )

        self._sessions[session_id] = session
        self._update_session_count()

        return session

    def remove_session(self, session_id: str) -> bool:
        """Remove a session from squad management."""
        if not self._check_omni_access("write"):
            raise PermissionError("Access denied to remove session")

        if session_id in self._sessions:
            del self._sessions[session_id]
            self._update_session_count()
            return True
        return False

    def get_sessions(self) -> List[Session]:
        """Get all managed sessions."""
        if not self._check_omni_access("read"):
            raise PermissionError("Access denied to read sessions")
        return list(self._sessions.values())

    # Policy and cache management (enhanced with Omni tracking)
    def evaluate_policy_cached(self, identity: Identity, action: str, resource: str) -> bool:
        """Evaluate policy with caching and performance tracking."""
        if not self._check_omni_access("read"):
            return False

        # Use identity.id instead of identity_id
        cache_key = f"{identity.id}:{action}:{resource}"

        # Check cache first
        if cache_key in self._policy_cache:
            cache_entry = self._policy_cache[cache_key]
            if time.time() - cache_entry['timestamp'] < self._cache_timeout:
                self._policy_cache_hits += 1
                return cache_entry['allowed']

        # Evaluate policy
        if self._omni__policy:
            result = self._omni__policy.evaluate(
                identity=identity,
                action=action,
                resource=resource
            )
            allowed = result.passed
        else:
            allowed = True  # No policy means allow

        # Cache result
        self._policy_cache[cache_key] = {
            'allowed': allowed,
            'timestamp': time.time()
        }

        return allowed

    # Object creation with policy context (key enhancement)
    def create_managed_object(self, obj_class: type, identity: Identity, **kwargs) -> Any:
        """
        Create objects with squad/session context for policy-aware instantiation.
        This addresses the test failures from strict policy enforcement.
        """
        if not self._check_omni_access("write"):
            raise PermissionError("Access denied to create managed objects")

        # Create object with squad context
        obj = obj_class(
            session=self._omni__session,  # Pass through session context
            policy=self._omni__policy,    # Pass through policy context
            identity=identity,            # Ensure identity is set
            **kwargs
        )

        # Track the object if it's an Omni
        if hasattr(obj, '_omni_id'):
            self.add('managed_objects', obj)

        return obj

    # Agent-like capabilities for distributed coordination
    async def update(self) -> bool:
        """Agent-style update method for coordination tasks."""
        try:
            # Clean up expired cache entries
            current_time = time.time()
            expired_keys = [
                key for key, entry in self._policy_cache.items()
                if current_time - entry['timestamp'] > self._cache_timeout
            ]
            for key in expired_keys:
                del self._policy_cache[key]

            # Update activity timestamp
            self.last_activity = current_time

            # Perform distributed coordination if enabled
            if self.distributed_enabled:
                await self._sync_with_distributed_peers()

            return True
        except Exception as e:
            if self.logger:
                self.logger.error(f"Squad update failed: {e}")
            return False

    async def _sync_with_distributed_peers(self):
        """Placeholder for distributed squad coordination."""
        # This would implement the distributed coordination logic
        # from the DistributedSquad concept
        pass

    # Persistence integration (inherited from Omni)
    async def save_squad_state(self, incremental: bool = True) -> bool:
        """Save squad state using Omni persistence."""
        try:
            # Save the squad's omni state
            if hasattr(self, 'save_to_storage'):
                success = await self.save_to_storage(incremental=incremental)
                if success and self.logger:
                    self.logger.info(
                        f"Squad {self.squad_name} state saved successfully")
                return success
            return False
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to save squad state: {e}")
            return False

    # Status and introspection (enhanced with Omni capabilities)
    def get_squad_status(self) -> Dict[str, Any]:
        """Get comprehensive squad status including Omni state."""
        base_status = {
            'squad_id': self._ocean__id,
            'squad_name': self._squad_name,
            'nickname': self._ocean__nickname,
            'groups': {k: len(v) for k, v in self._groups.items()},
            'sessions': len(self._sessions),
            'cache_entries': len(self._policy_cache),
            'last_activity': self._last_activity,
            'distributed_enabled': self._distributed_enabled,
            'member_count': self._member_count,
            'session_count': self._session_count,
            'policy_cache_hits': self._policy_cache_hits
        }

        # Add Omni status if available (use getattr to safely check)
        omni_status = getattr(self, 'status', None)
        if omni_status:
            base_status['omni_state'] = omni_status

        return base_status

    # Common manager interface compatibility
    def get_preview(self, action: str, **params) -> Dict[str, Any]:
        """Manager interface compatibility for uniform management."""
        return {
            'action': f'squad.{action}',
            'squad_id': self._ocean__id,
            'params': params,
            'allowed': self._check_omni_access('read'),
            'estimated_cost': 0  # Squads don't typically have direct costs
        }

    async def execute_with_cost(self, action: str, **params) -> Dict[str, Any]:
        """Manager interface compatibility for uniform execution."""
        try:
            result = await getattr(self, action)(**params)
            return {
                'success': True,
                'result': result,
                'actual_cost': 0
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'actual_cost': 0
            }


class ManagerMixin:
    """
    Mixin to provide common manager interface for all operational managers.
    This allows Squad to manage Transport, Storage, and Transaction managers uniformly.
    """

    def get_preview(self, action: str, **params) -> Dict[str, Any]:
        """Get cost/feasibility preview for an action."""
        raise NotImplementedError("Managers must implement get_preview")

    async def execute_with_cost(self, action: str, **params) -> Dict[str, Any]:
        """Execute action with cost tracking."""
        raise NotImplementedError("Managers must implement execute_with_cost")

    def get_manager_status(self) -> Dict[str, Any]:
        """Get manager status for monitoring."""
        return {
            'manager_type': self.__class__.__name__,
            'active': True
        }
