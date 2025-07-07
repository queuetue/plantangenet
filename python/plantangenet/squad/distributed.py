"""
Distributed Squad Architecture for Plantangenet

This module implements a hierarchical squad management system where:
- DistributedSquad: Manages multiple local squads across a network
- LocalSquadManager: Extends Squad to act as a local node with session management
- Squad: Basic squad functionality (already exists)

The architecture supports:
- Network-aware squad coordination
- Hierarchical policy distribution and caching
- Session lifecycle management across squad boundaries
- Resource pooling and load balancing
- Fault tolerance and failover
"""

from typing import Any, Dict, List, Optional, Set, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import time
import uuid
import logging
from abc import ABC, abstractmethod

from ..squad.squad import Squad
from ..session.session import Session
from ..policy.policy import Policy
from ..policy.identity import Identity


class SquadRole(Enum):
    """Roles that a squad can have in the distributed system."""
    PRIMARY = "primary"      # Main coordinator
    SECONDARY = "secondary"  # Backup coordinator
    WORKER = "worker"       # Worker node
    OBSERVER = "observer"   # Read-only observer


class SquadStatus(Enum):
    """Status of a squad in the distributed system."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    CONNECTING = "connecting"
    DISCONNECTED = "disconnected"
    FAILED = "failed"


@dataclass
class SquadNode:
    """Represents a squad node in the distributed system."""
    id: str
    endpoint: str
    role: SquadRole
    status: SquadStatus
    capabilities: Set[str] = field(default_factory=set)
    load_factor: float = 0.0
    last_heartbeat: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


class DistributedSquadProtocol(ABC):
    """Protocol for distributed squad communication."""

    @abstractmethod
    async def broadcast_message(self, message: Dict[str, Any]) -> bool:
        """Broadcast a message to all nodes in the squad."""
        pass

    @abstractmethod
    async def send_message(self, node_id: str, message: Dict[str, Any]) -> bool:
        """Send a message to a specific node."""
        pass

    @abstractmethod
    async def receive_messages(self) -> List[Dict[str, Any]]:
        """Receive pending messages."""
        pass


class LocalSquadManager(Squad):
    """
    Extended Squad that acts as a local node in a distributed squad system.

    Provides session management, local resource pooling, and communication
    with the distributed squad coordinator.
    """

    def __init__(
        self,
        name: Optional[str] = None,
        policy: Optional[Policy] = None,
        node_id: Optional[str] = None,
        capabilities: Optional[Set[str]] = None
    ):
        super().__init__(name, policy)
        self.node_id = node_id or str(uuid.uuid4())
        self.capabilities = capabilities or {
            "session_management", "object_creation"}
        self.status = SquadStatus.INACTIVE
        self.role = SquadRole.WORKER
        self.distributed_squad: Optional['DistributedSquad'] = None
        self.heartbeat_interval = 30.0  # seconds
        self._heartbeat_task: Optional[asyncio.Task] = None
        self.logger = logging.getLogger(f"LocalSquadManager.{self.node_id}")

        # Local resource tracking
        self.max_sessions = 100
        self.max_objects_per_session = 1000
        self._resource_usage = {
            "active_sessions": 0,
            "total_objects": 0,
            "memory_usage": 0,
            "cpu_usage": 0
        }

    async def join_distributed_squad(self, distributed_squad: 'DistributedSquad') -> bool:
        """Join a distributed squad as a local node."""
        try:
            self.distributed_squad = distributed_squad
            success = await distributed_squad.add_local_squad(self)
            if success:
                self.status = SquadStatus.ACTIVE
                await self._start_heartbeat()
                self.logger.info(
                    f"Joined distributed squad: {distributed_squad.squad_id}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to join distributed squad: {e}")
            self.status = SquadStatus.FAILED
            return False

    async def leave_distributed_squad(self) -> bool:
        """Leave the distributed squad."""
        if self.distributed_squad:
            try:
                await self._stop_heartbeat()
                success = await self.distributed_squad.remove_local_squad(self.node_id)
                self.distributed_squad = None
                self.status = SquadStatus.INACTIVE
                self.logger.info("Left distributed squad")
                return success
            except Exception as e:
                self.logger.error(f"Failed to leave distributed squad: {e}")
                return False
        return True

    def get_load_factor(self) -> float:
        """Calculate current load factor (0.0 to 1.0)."""
        session_load = len(self._sessions) / self.max_sessions
        object_load = sum(
            len(self.get(f"session_{sid}_omnis"))
            for sid in self._sessions.keys()
        ) / (self.max_sessions * self.max_objects_per_session)

        return max(session_load, object_load)

    def can_accept_session(self) -> bool:
        """Check if this node can accept a new session."""
        return (
            len(self._sessions) < self.max_sessions and
            self.get_load_factor() < 0.8 and
            self.status == SquadStatus.ACTIVE
        )

    async def migrate_session(self, session_id: str, target_node: str) -> bool:
        """Migrate a session to another node in the distributed squad."""
        if self.distributed_squad and session_id in self._sessions:
            try:
                session = self._sessions[session_id]
                success = await self.distributed_squad.migrate_session(
                    session, self.node_id, target_node
                )
                if success:
                    self.cleanup_session(session_id)
                    self.logger.info(
                        f"Migrated session {session_id} to {target_node}")
                return success
            except Exception as e:
                self.logger.error(
                    f"Failed to migrate session {session_id}: {e}")
                return False
        return False

    async def _start_heartbeat(self):
        """Start the heartbeat task."""
        if self._heartbeat_task is None:
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

    async def _stop_heartbeat(self):
        """Stop the heartbeat task."""
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
            self._heartbeat_task = None

    async def _heartbeat_loop(self):
        """Send periodic heartbeats to the distributed squad."""
        while self.status == SquadStatus.ACTIVE:
            try:
                if self.distributed_squad:
                    await self.distributed_squad.receive_heartbeat(
                        self.node_id,
                        self.get_load_factor(),
                        self._resource_usage
                    )
                await asyncio.sleep(self.heartbeat_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Heartbeat failed: {e}")
                await asyncio.sleep(5)  # Brief pause before retrying


class DistributedSquad:
    """
    Manages a collection of LocalSquadManagers across a network.

    Provides:
    - Load balancing for session creation
    - Policy distribution and synchronization
    - Resource monitoring and optimization
    - Fault tolerance and failover
    """

    def __init__(
        self,
        squad_id: Optional[str] = None,
        protocol: Optional[DistributedSquadProtocol] = None
    ):
        self.squad_id = squad_id or str(uuid.uuid4())
        self.protocol = protocol
        self.nodes: Dict[str, SquadNode] = {}
        self.local_squads: Dict[str, LocalSquadManager] = {}
        self.global_policy: Optional[Policy] = None
        self.logger = logging.getLogger(f"DistributedSquad.{self.squad_id}")

        # Distributed state
        self._session_registry: Dict[str, str] = {}  # session_id -> node_id
        self._policy_version = 0
        self._heartbeat_timeout = 90.0  # seconds

        # Load balancing
        self._load_balancer: Optional[Callable[[
            List[LocalSquadManager]], LocalSquadManager]] = None

    async def add_local_squad(self, squad: LocalSquadManager) -> bool:
        """Add a local squad to the distributed system."""
        try:
            node = SquadNode(
                id=squad.node_id,
                endpoint="",  # To be filled by protocol
                role=squad.role,
                status=squad.status,
                capabilities=squad.capabilities,
                load_factor=squad.get_load_factor()
            )

            self.nodes[squad.node_id] = node
            self.local_squads[squad.node_id] = squad

            # Sync policies to the new node
            if self.global_policy:
                squad.squad_policy = self.global_policy

            self.logger.info(f"Added local squad: {squad.node_id}")

            # Broadcast node addition to other nodes
            if self.protocol:
                await self.protocol.broadcast_message({
                    "type": "node_added",
                    "node": {
                        "id": node.id,
                        "role": node.role.value,
                        "capabilities": list(node.capabilities)
                    }
                })

            return True
        except Exception as e:
            self.logger.error(
                f"Failed to add local squad {squad.node_id}: {e}")
            return False

    async def remove_local_squad(self, node_id: str) -> bool:
        """Remove a local squad from the distributed system."""
        if node_id in self.local_squads:
            try:
                # Migrate any active sessions to other nodes
                sessions_to_migrate = [
                    sid for sid, nid in self._session_registry.items()
                    if nid == node_id
                ]

                for session_id in sessions_to_migrate:
                    await self._reassign_session(session_id, exclude_node=node_id)

                # Remove the node
                del self.local_squads[node_id]
                del self.nodes[node_id]

                self.logger.info(f"Removed local squad: {node_id}")

                # Broadcast node removal
                if self.protocol:
                    await self.protocol.broadcast_message({
                        "type": "node_removed",
                        "node_id": node_id
                    })

                return True
            except Exception as e:
                self.logger.error(
                    f"Failed to remove local squad {node_id}: {e}")
                return False
        return False

    async def create_distributed_session(
        self,
        identity: Identity,
        policy: Optional[Policy] = None,
        metadata: Optional[Dict[str, Any]] = None,
        preferred_node: Optional[str] = None
    ) -> Optional[Session]:
        """Create a session on the best available node."""
        try:
            # Select the best node for the session
            target_node = await self._select_node_for_session(preferred_node)
            if not target_node:
                self.logger.warning("No available nodes for session creation")
                return None

            # Create session on the selected node
            squad = self.local_squads[target_node]
            session = squad.create_session(identity, policy, metadata)

            # Register the session in our distributed registry
            self._session_registry[session._id] = target_node

            self.logger.info(
                f"Created distributed session {session._id} on node {target_node}")
            return session

        except Exception as e:
            self.logger.error(f"Failed to create distributed session: {e}")
            return None

    async def migrate_session(self, session: Session, from_node: str, to_node: str) -> bool:
        """Migrate a session between nodes."""
        if from_node not in self.local_squads or to_node not in self.local_squads:
            return False

        try:
            target_squad = self.local_squads[to_node]

            # Check if target can accept the session
            if not target_squad.can_accept_session():
                return False

            # Add session to target node
            success = target_squad.join_session(session)
            if success:
                # Update registry
                self._session_registry[session._id] = to_node
                self.logger.info(
                    f"Migrated session {session._id} from {from_node} to {to_node}")
                return True

            return False
        except Exception as e:
            self.logger.error(f"Failed to migrate session: {e}")
            return False

    async def receive_heartbeat(
        self,
        node_id: str,
        load_factor: float,
        resource_usage: Dict[str, Any]
    ):
        """Receive heartbeat from a local squad."""
        if node_id in self.nodes:
            node = self.nodes[node_id]
            node.load_factor = load_factor
            node.last_heartbeat = time.time()
            node.metadata.update(resource_usage)

            # Check if node needs assistance (high load)
            if load_factor > 0.9:
                await self._rebalance_from_node(node_id)

    async def set_global_policy(self, policy: Policy):
        """Set and distribute a global policy to all nodes."""
        self.global_policy = policy
        self._policy_version += 1

        # Distribute to all nodes
        for squad in self.local_squads.values():
            squad.squad_policy = policy
            # Clear policy caches to force re-evaluation
            squad._policy_cache.clear()

        # Broadcast policy update
        if self.protocol:
            await self.protocol.broadcast_message({
                "type": "policy_update",
                "version": self._policy_version,
                "policy_data": policy.to_dict() if hasattr(policy, 'to_dict') else {}
            })

        self.logger.info(
            f"Distributed global policy version {self._policy_version}")

    def get_squad_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics about the distributed squad."""
        total_sessions = len(self._session_registry)
        active_nodes = len([n for n in self.nodes.values()
                           if n.status == SquadStatus.ACTIVE])

        load_distribution = {
            node_id: node.load_factor
            for node_id, node in self.nodes.items()
        }

        return {
            "squad_id": self.squad_id,
            "total_nodes": len(self.nodes),
            "active_nodes": active_nodes,
            "total_sessions": total_sessions,
            "policy_version": self._policy_version,
            "load_distribution": load_distribution,
            "session_distribution": self._get_session_distribution()
        }

    async def _select_node_for_session(self, preferred_node: Optional[str] = None) -> Optional[str]:
        """Select the best node for creating a new session."""
        available_squads = [
            squad for squad in self.local_squads.values()
            if squad.can_accept_session()
        ]

        if not available_squads:
            return None

        # Use preferred node if available and capable
        if preferred_node and preferred_node in self.local_squads:
            preferred_squad = self.local_squads[preferred_node]
            if preferred_squad.can_accept_session():
                return preferred_node

        # Use custom load balancer if available
        if self._load_balancer:
            selected_squad = self._load_balancer(available_squads)
            return selected_squad.node_id

        # Default: select node with lowest load
        best_squad = min(available_squads, key=lambda s: s.get_load_factor())
        return best_squad.node_id

    async def _reassign_session(self, session_id: str, exclude_node: Optional[str] = None):
        """Reassign a session to a different node."""
        if session_id not in self._session_registry:
            return

        current_node = self._session_registry[session_id]
        if current_node in self.local_squads:
            session = self.local_squads[current_node].get_session(session_id)
            if session:
                # Find a new node
                target_node = await self._select_node_for_session()
                if target_node and target_node != exclude_node:
                    await self.migrate_session(session, current_node, target_node)

    async def _rebalance_from_node(self, overloaded_node_id: str):
        """Rebalance sessions from an overloaded node."""
        if overloaded_node_id not in self.local_squads:
            return

        squad = self.local_squads[overloaded_node_id]
        sessions = squad.list_sessions()

        # Move some sessions to less loaded nodes
        # Move 25% of sessions
        sessions_to_move = sessions[:len(sessions) // 4]

        for session in sessions_to_move:
            target_node = await self._select_node_for_session()
            if target_node and target_node != overloaded_node_id:
                await self.migrate_session(session, overloaded_node_id, target_node)

    def _get_session_distribution(self) -> Dict[str, int]:
        """Get the distribution of sessions across nodes."""
        distribution = {}
        for node_id in self.nodes.keys():
            distribution[node_id] = sum(
                1 for session_node in self._session_registry.values()
                if session_node == node_id
            )
        return distribution

    def set_load_balancer(self, balancer: Callable[[List[LocalSquadManager]], LocalSquadManager]):
        """Set a custom load balancing strategy."""
        self._load_balancer = balancer
