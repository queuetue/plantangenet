# Copyright (c) 1998-2025 Scott Russell
# SPDX-License-Identifier: MIT

"""
Agent-based Squad implementation - lightweight, coordination-focused group management.

This is distinct from Omni-based managers which are persistent and policy-heavy.
Agent-based squads are for dynamic coordination, communication, and lightweight orchestration.
"""

from typing import Any, Callable, Optional, Dict, List, Set
from ..agents.agent import Agent
from ..session.session import Session
from ..policy.identity import Identity
import asyncio
import time


class AgentSquad(Agent):
    """
    Agent-based Squad for lightweight coordination and group management.

    Key differences from Omni-based managers:
    - Inherits from Agent (not Omni) for lightweight coordination
    - Focus on real-time coordination rather than persistence
    - Minimal policy overhead (uses agent namespace permissions)
    - Optimized for dynamic group operations and messaging
    - No heavy persistence or audit trails
    - Perfect for temporary coordination tasks, chat groups, game squads, etc.

    Use this when you need:
    - Dynamic group coordination
    - Real-time messaging coordination  
    - Temporary task groups
    - Lightweight orchestration
    - Agent-to-agent communication hubs

    Use Omni-based managers when you need:
    - Persistent state and audit trails
    - Heavy policy enforcement
    - Storage integration
    - Transaction management
    - Long-term resource management
    """

    def __init__(self, name: Optional[str] = None, namespace: str = "plantangenet", logger: Any = None):
        """
        Initialize AgentSquad with lightweight Agent capabilities.

        Args:
            name: Squad name (optional, auto-generated if not provided)
            namespace: Agent namespace
            logger: Logger instance
        """
        super().__init__(namespace=namespace, logger=logger)

        # Squad identity
        self.squad_name = name or f"squad_{self.short_id}"

        # Core coordination data structures
        self._groups: Dict[str, List[Any]] = {}
        self._agent_registry: Dict[str, Agent] = {}  # Known agents
        self._coordination_channels: Dict[str,
                                          # Message channels
                                          List[Callable]] = {}
        self._task_queue: List[Dict[str, Any]] = []  # Coordination tasks

        # Lightweight state tracking
        self._last_activity = time.time()
        self._message_count = 0
        self._coordination_events = 0

        # Agent coordination flags
        self._is_coordinating = False
        self._coordination_interval = 1.0  # seconds

    async def update(self) -> bool:
        """Agent update cycle - handle coordination tasks."""
        try:
            current_time = time.time()

            # Process pending coordination tasks
            tasks_processed = 0
            while self._task_queue and tasks_processed < 10:  # Limit per cycle
                task = self._task_queue.pop(0)
                await self._process_coordination_task(task)
                tasks_processed += 1
                self._coordination_events += 1

            # Clean up stale registrations
            await self._cleanup_stale_agents()

            # Update activity timestamp
            self._last_activity = current_time

            return True

        except Exception as e:
            if self.logger:
                self.logger.error(f"AgentSquad update failed: {e}")
            return False

    # === LIGHTWEIGHT GROUP MANAGEMENT ===

    def add_to_group(self, group: str, obj: Any) -> bool:
        """Add object to a group with minimal overhead."""
        if group not in self._groups:
            self._groups[group] = []

        if obj not in self._groups[group]:
            self._groups[group].append(obj)
            self._last_activity = time.time()

            # If it's an agent, register it
            if isinstance(obj, Agent):
                self._agent_registry[obj.id] = obj

            return True
        return False

    def remove_from_group(self, group: str, obj: Any) -> bool:
        """Remove object from a group."""
        if group in self._groups and obj in self._groups[group]:
            self._groups[group].remove(obj)
            self._last_activity = time.time()

            # Clean up empty groups
            if not self._groups[group]:
                del self._groups[group]

            return True
        return False

    def get_group(self, group: str) -> List[Any]:
        """Get all objects in a group."""
        return self._groups.get(group, []).copy()

    def get_all_groups(self) -> Dict[str, List[Any]]:
        """Get all groups."""
        return {k: v.copy() for k, v in self._groups.items()}

    def query_group(self, group: str, predicate: Callable[[Any], bool]) -> List[Any]:
        """Query objects in a group with a predicate."""
        return [obj for obj in self._groups.get(group, []) if predicate(obj)]

    def get_agents_in_group(self, group: str) -> List[Agent]:
        """Get all agents in a specific group."""
        return [obj for obj in self._groups.get(group, []) if isinstance(obj, Agent)]

    # === AGENT COORDINATION ===

    def register_agent(self, agent: Agent, groups: Optional[List[str]] = None) -> bool:
        """Register an agent and optionally add to groups."""
        self._agent_registry[agent.id] = agent

        if groups:
            for group in groups:
                self.add_to_group(group, agent)

        return True

    def unregister_agent(self, agent_id: str) -> bool:
        """Remove agent from registry and all groups."""
        if agent_id in self._agent_registry:
            agent = self._agent_registry[agent_id]

            # Remove from all groups
            for group_name, group_members in self._groups.items():
                if agent in group_members:
                    group_members.remove(agent)

            # Remove from registry
            del self._agent_registry[agent_id]
            return True
        return False

    def get_registered_agents(self) -> List[Agent]:
        """Get all registered agents."""
        return list(self._agent_registry.values())

    def find_agent(self, agent_id: str) -> Optional[Agent]:
        """Find an agent by ID."""
        return self._agent_registry.get(agent_id)

    # === LIGHTWEIGHT MESSAGING COORDINATION ===

    def add_coordination_channel(self, channel: str, callback: Callable) -> bool:
        """Add a coordination channel callback."""
        if channel not in self._coordination_channels:
            self._coordination_channels[channel] = []

        if callback not in self._coordination_channels[channel]:
            self._coordination_channels[channel].append(callback)
            return True
        return False

    def remove_coordination_channel(self, channel: str, callback: Callable) -> bool:
        """Remove a coordination channel callback."""
        if channel in self._coordination_channels:
            try:
                self._coordination_channels[channel].remove(callback)
                if not self._coordination_channels[channel]:
                    del self._coordination_channels[channel]
                return True
            except ValueError:
                pass
        return False

    async def broadcast_to_channel(self, channel: str, message: Any) -> int:
        """Broadcast a message to all callbacks in a channel."""
        if channel not in self._coordination_channels:
            return 0

        callbacks = self._coordination_channels[channel].copy()
        successful_sends = 0

        for callback in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(message)
                else:
                    callback(message)
                successful_sends += 1
            except Exception as e:
                if self.logger:
                    self.logger.warning(f"Coordination callback failed: {e}")

        self._message_count += successful_sends
        return successful_sends

    async def coordinate_group_action(self, group: str, action: str, data: Any = None) -> Dict[str, Any]:
        """Coordinate an action across all agents in a group."""
        agents = self.get_agents_in_group(group)
        if not agents:
            return {"success": False, "reason": "No agents in group"}

        results = []
        for agent in agents:
            try:
                # Schedule coordination task for each agent
                task = {
                    "type": "group_action",
                    "target_agent": agent.id,
                    "action": action,
                    "data": data,
                    "timestamp": time.time()
                }
                self._task_queue.append(task)
                results.append({"agent_id": agent.id, "status": "queued"})
            except Exception as e:
                results.append(
                    {"agent_id": agent.id, "status": "error", "error": str(e)})

        return {
            "success": True,
            "group": group,
            "action": action,
            "agents_affected": len(results),
            "results": results
        }

    # === TASK COORDINATION ===

    async def _process_coordination_task(self, task: Dict[str, Any]) -> bool:
        """Process a coordination task."""
        try:
            task_type = task.get("type")

            if task_type == "group_action":
                agent_id = task.get("target_agent")
                action = task.get("action")
                data = task.get("data")

                if agent_id and action:
                    agent = self.find_agent(agent_id)
                    if agent and hasattr(agent, action):
                        method = getattr(agent, action)
                        if asyncio.iscoroutinefunction(method):
                            await method(data)
                        else:
                            method(data)
                        return True

            elif task_type == "broadcast":
                channel = task.get("channel")
                message = task.get("message")
                if channel:
                    await self.broadcast_to_channel(channel, message)
                    return True

            return False

        except Exception as e:
            if self.logger:
                self.logger.error(f"Coordination task failed: {e}")
            return False

    async def _cleanup_stale_agents(self) -> int:
        """Remove agents that are no longer responding."""
        stale_agents = []
        current_time = time.time()

        for agent_id, agent in self._agent_registry.items():
            # Simple staleness check - could be enhanced with heartbeats
            # Check if agent has last activity tracking
            last_activity = getattr(agent, '_last_activity', None)
            if last_activity is not None:
                try:
                    if current_time - float(last_activity) > 300:  # 5 minutes
                        stale_agents.append(agent_id)
                except (TypeError, ValueError):
                    # If we can't convert to float, skip this agent
                    pass

        for agent_id in stale_agents:
            self.unregister_agent(agent_id)

        return len(stale_agents)

    # === STATUS AND INTROSPECTION ===

    def get_squad_status(self) -> Dict[str, Any]:
        """Get lightweight squad status."""
        return {
            "squad_id": self.id,
            "squad_name": self.squad_name,
            "nickname": self.name,
            "namespace": self.namespace,
            "groups": {k: len(v) for k, v in self._groups.items()},
            "registered_agents": len(self._agent_registry),
            "coordination_channels": len(self._coordination_channels),
            "pending_tasks": len(self._task_queue),
            "message_count": self._message_count,
            "coordination_events": self._coordination_events,
            "last_activity": self._last_activity,
            "is_coordinating": self._is_coordinating
        }

    def get_coordination_stats(self) -> Dict[str, Any]:
        """Get coordination performance stats."""
        return {
            "messages_processed": self._message_count,
            "coordination_events": self._coordination_events,
            "average_queue_size": len(self._task_queue),
            "channels_active": len(self._coordination_channels),
            "agents_coordinated": len(self._agent_registry)
        }

    # === LEGACY COMPATIBILITY ===

    def add(self, group: str, obj: Any):
        """Legacy BaseSquad compatibility."""
        return self.add_to_group(group, obj)

    def remove(self, group: str, obj: Any):
        """Legacy BaseSquad compatibility."""
        return self.remove_from_group(group, obj)

    def get(self, group: str) -> List[Any]:
        """Legacy BaseSquad compatibility."""
        return self.get_group(group)

    def all(self) -> Dict[str, List[Any]]:
        """Legacy BaseSquad compatibility."""
        return self.get_all_groups()

    def query(self, group: str, predicate: Callable[[Any], bool]) -> List[Any]:
        """Legacy BaseSquad compatibility."""
        return self.query_group(group, predicate)

    def transform(self, group: str, data: Any, frame: Any = None) -> Any:
        """Apply transformers to data - enhanced with coordination."""
        # Get transformers from the group
        transformers = [obj for obj in self.get_group(group) if callable(obj)]

        # Apply each transformer
        for transformer in transformers:
            try:
                data = transformer(data, frame)
            except Exception as e:
                if self.logger:
                    self.logger.warning(f"Transformer failed: {e}")

        return data


class CoordinationMessage:
    """Simple message structure for agent coordination."""

    def __init__(self, sender_id: str, message_type: str, data: Any = None,
                 target_group: Optional[str] = None, target_agent: Optional[str] = None):
        self.sender_id = sender_id
        self.message_type = message_type
        self.data = data
        self.target_group = target_group
        self.target_agent = target_agent
        self.timestamp = time.time()
        self.id = f"msg_{int(self.timestamp * 1000)}"
