from typing import Any, Callable, Optional, Dict, List
from .base import BaseSquad
from ..session.session import Session
from ..policy.policy import Policy
from ..policy.identity import Identity
import uuid
import time


class Squad(BaseSquad):
    """
    Manages collections of agents, transformers, and other session participants.
    Supports registration, removal, querying, and transformation operations.
    Can itself be managed (added to other managers/groups).

    Extended with session management capabilities to act as a local squad manager
    that sessions can join and operate within.
    """

    def __init__(self, name: Optional[str] = None, policy: Optional[Policy] = None):
        super().__init__(name)
        self.squad_policy = policy  # Squad-level policy that can cascade to sessions
        print(f"DEBUG: Squad created with policy: {policy}")
        print(
            f"DEBUG: Squad policy statements: {getattr(policy, 'policies', 'NO_POLICIES') if policy else 'None'}")
        self._sessions: Dict[str, Session] = {}  # Managed sessions
        # Squad-level policy cache
        self._policy_cache: Dict[str, Dict[str, Any]] = {}
        self._cache_timeout = 600  # 10 minutes for squad-level cache

    def add(self, group: str, obj: Any):
        if group not in self._groups:
            self._groups[group] = []
        self._groups[group].append(obj)

    def remove(self, group: str, obj: Any):
        if group in self._groups:
            self._groups[group] = [o for o in self._groups[group] if o != obj]

    def get(self, group: str) -> list:
        return self._groups.get(group, [])

    def all(self) -> dict:
        return self._groups

    def query(self, group: str, predicate: Callable[[Any], bool]) -> list:
        return [o for o in self._groups.get(group, []) if predicate(o)]

    def difference(self, group_a: str, group_b: str) -> list:
        """Return items in group_a that are not in group_b (by identity)."""
        set_b = set(self._groups.get(group_b, []))
        return [o for o in self._groups.get(group_a, []) if o not in set_b]

    def transform(self, group: str, data: Any, frame: Any = None) -> Any:
        """Apply all transformers in the group to the data, in order."""
        for transformer in self._groups.get(group, []):
            if callable(transformer):
                data = transformer(data, frame)
        return data

    # Session Management API
    def create_session(
        self,
        identity: Identity,
        policy: Optional[Policy] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Session:
        """Create a new session within this squad's management."""
        session_id = str(uuid.uuid4())

        # Use squad policy if no specific policy provided, or create default
        effective_policy = policy or self.squad_policy
        print(
            f"DEBUG: Session creation - passed policy: {policy}, squad_policy: {self.squad_policy}")
        print(f"DEBUG: Effective policy: {effective_policy}")
        print(
            f"DEBUG: Effective policy statements: {getattr(effective_policy, 'policies', 'NO_POLICIES') if effective_policy else 'None'}")
        if effective_policy is None:
            # Create a minimal default policy if none available
            effective_policy = Policy()

        session = Session(
            id=session_id,
            policy=effective_policy,
            identity=identity,
            metadata=metadata or {}
        )

        # Add session to our managed sessions
        self._sessions[session_id] = session
        self.add("sessions", session)

        return session

    def join_session(self, session: Session) -> bool:
        """Allow an existing session to join this squad."""
        if session._id not in self._sessions:
            self._sessions[session._id] = session
            self.add("sessions", session)
            return True
        return False

    def leave_session(self, session_id: str) -> bool:
        """Remove a session from this squad's management."""
        if session_id in self._sessions:
            session = self._sessions[session_id]
            del self._sessions[session_id]
            self.remove("sessions", session)
            return True
        return False

    def get_session(self, session_id: str) -> Optional[Session]:
        """Get a managed session by ID."""
        return self._sessions.get(session_id)

    def list_sessions(self) -> List[Session]:
        """List all managed sessions."""
        return list(self._sessions.values())

    # Object Creation within Sessions
    def create_omni_in_session(self, session: Session, omni_class, **kwargs):
        """Create an Omni object within a managed session's context."""
        if session._id not in self._sessions:
            raise ValueError(
                "Session must be managed by this squad to create objects")

        # Create omni with session context
        omni = omni_class(**{
            'session': session,
            'policy': session.policy,
            'identity': session.identity,
            **kwargs
        })

        # Track the omni in the session's objects
        self.add(f"session_{session._id}_omnis", omni)

        return omni

    # Policy Distribution and Caching
    def evaluate_policy_for_session(
        self,
        session: Session,
        identity: Identity,
        action: str,
        resource: str
    ) -> bool:
        """Evaluate policy for a session, using squad-level caching."""
        cache_key = f"{session._id}:{identity.id}:{action}:{resource}"

        # Check squad-level cache first
        if cache_key in self._policy_cache:
            cache_entry = self._policy_cache[cache_key]
            if time.time() - cache_entry['timestamp'] < self._cache_timeout:
                return cache_entry['allowed']

        # Evaluate using session's policy
        if session.policy:
            result = session.policy.evaluate(identity, action, resource)
            allowed = result.passed
        else:
            allowed = True  # No policy means allow

        # Cache the result at squad level
        self._policy_cache[cache_key] = {
            'allowed': allowed,
            'timestamp': time.time()
        }

        return allowed

    # Squad-level resource management
    def get_session_objects(self, session: Session, object_type: str = "omnis") -> List[Any]:
        """Get all objects of a specific type for a session."""
        return self.get(f"session_{session._id}_{object_type}")

    def cleanup_session(self, session_id: str):
        """Clean up all resources associated with a session."""
        if session_id in self._sessions:
            # Remove all objects associated with this session
            session_groups = [group for group in self._groups.keys()
                              if group.startswith(f"session_{session_id}_")]

            for group in session_groups:
                del self._groups[group]

            # Remove the session itself
            self.leave_session(session_id)

    # Distributed squad interface (placeholder for future implementation)
    def connect_to_distributed_squad(self, distributed_squad_endpoint: str):
        """Connect this local squad manager to a distributed squad."""
        # TODO: Implement distributed coordination
        pass

    def sync_policies(self):
        """Sync policies from the distributed squad."""
        # TODO: Implement policy synchronization
        pass
