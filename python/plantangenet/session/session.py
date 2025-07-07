# Copyright (c) 1998-2025 Scott Russell
# SPDX-License-Identifier: MIT

import uuid
import time
import json
import yaml
from typing import List, Dict, Any, Optional, Callable, Union
from plantangenet.policy.identity import Identity
from plantangenet.policy.policy import Policy
from plantangenet.compositor.base import BaseCompositor

from ..cursor import Cursor
from ..agents.agent import Agent


class Session:
    """
    Represents a policy-bound lifecycle and trust boundary.
    Manages Compositors (including Squads, ML, Framebuffer compositors), Agents, Cursors.
    Acts as the central coordinator for all compositor outputs and shared state.
    Only id, metadata, identity_key, and policy_key are persisted.
    """

    def __init__(
            self,
            id: str,
            policy: Policy,
            identity: Identity,
            metadata: Dict[str, Any] = {}):
        self._id = id or str(uuid.uuid4())
        self._metadata = metadata or {}
        self._identity = identity
        self._policy = policy
        self.agents: List[Agent] = []
        self.cursors: List[Cursor] = []
        self.on_change_callbacks: List[Callable[['Session'], None]] = []

        # Compositor management - squads are core compositors
        self.compositors: Dict[str, BaseCompositor] = {}
        self._compositor_outputs: Dict[str, Any] = {}
        self._shared_state: Dict[str, Any] = {}

        # Session-level policy cache for performance
        self._policy_cache: Dict[str, Dict[str, Any]] = {}
        self._cache_timeout = 300  # 5 minutes default

    @property
    def identity(self) -> Optional[Identity]:
        if self._identity:
            return self._identity
        return None

    @property
    def policy(self) -> Optional[Policy]:
        if self._policy:
            return self._policy
        return None

    def persisted_state(self) -> dict:
        """Get the basic state that can be persisted for this session."""
        return {
            "id": self._id,
            "metadata": self._metadata,
            "identity_id": getattr(self._identity, 'id', None),
            "policy_namespace": getattr(self._policy, 'namespace', None),
            "cursor_count": len(self.cursors),
            "compositor_count": len(self.compositors),
            "active_compositors": list(self.compositors.keys())
        }

    # Agent management
    def add_agent(self, agent: Agent):
        self.agents.append(agent)
        # If the agent has a 'session' attribute, set it
        if hasattr(agent, 'session'):
            agent.session = self
        self._notify_change()

    def remove_agent(self, agent: Agent):
        if agent in self.agents:
            self.agents.remove(agent)
            self._notify_change()

    def list_agents(self) -> List[Agent]:
        return list(self.agents)

    async def update_agents(self):
        for agent in self.agents:
            await agent.update()

    # Cursor management
    def add_cursor(self, agent: Agent, cursor: Cursor):
        if self.evaluate_policy(agent, "add_cursor", resource=cursor.axes):
            cursor.owner = agent.id
            self.cursors.append(cursor)
            self._notify_change()
        else:
            raise PermissionError("Policy denied adding cursor.")

    def remove_cursor(self, cursor: Cursor):
        if cursor in self.cursors:
            self.cursors.remove(cursor)
            self._notify_change()

    def list_cursors(self) -> List[Cursor]:
        return list(self.cursors)

    def get_relevant_frames(self, buffer, axis_filter: Optional[List[str]] = None) -> List[Any]:
        frames = []
        for cursor in self.cursors:
            for tick in range(cursor.tick_range[0], cursor.tick_range[1] + 1):
                frame = buffer.get_frame(tick)
                if frame:
                    if axis_filter:
                        filtered_axes = {
                            a: f for a, f in frame.axes.items() if a in axis_filter}
                        if filtered_axes:
                            frames.append((tick, filtered_axes))
                    else:
                        frames.append(frame)
        return frames

    def evaluate_policy(self, identity: Union[Identity, Agent, str, None], action: str, resource: Any, context: Optional[dict] = None) -> bool:
        """
        Evaluate policy with session-level caching for performance.

        :param identity: Identity, agent, or string performing the action
        :param action: Action being performed ('read', 'write', etc.)
        :param resource: Resource being accessed
        :param context: Optional context dictionary
        :return: True if access is allowed
        """
        if not self._policy:
            return True  # No policy enforcement

        # Use session identity if none provided
        if identity is None:
            identity = self._identity

        # Get identity for policy evaluation
        eval_identity = self._identity  # Always use session identity for policy evaluation
        if hasattr(identity, 'id'):
            identity_id = getattr(identity, 'id')
        else:
            identity_id = str(identity)

        # Create cache key
        cache_key = f"{identity_id}:{action}:{resource}"

        # Check cache first
        if cache_key in self._policy_cache:
            cache_entry = self._policy_cache[cache_key]
            if time.time() - cache_entry['timestamp'] < self._cache_timeout:
                return cache_entry['allowed']

        # Evaluate policy
        try:
            print(
                f"DEBUG: Session policy eval - eval_identity: {eval_identity}, action: {action}, resource: {resource}")
            print(
                f"DEBUG: eval_identity.roles: {getattr(eval_identity, 'roles', 'NO_ROLES')}")
            print(
                f"DEBUG: Policy statements in _policy: {getattr(self._policy, 'policies', 'NO_POLICIES')}")
            result = self._policy.evaluate(
                eval_identity, action, resource, context)
            print(f"DEBUG: Raw policy result: {result}")
            allowed = result.passed if hasattr(
                result, 'passed') else bool(result)
            reason = result.reason if hasattr(
                result, 'reason') else 'policy_evaluated'
            print(f"DEBUG: Final allowed: {allowed}, reason: {reason}")

            # Cache result
            self._policy_cache[cache_key] = {
                'allowed': allowed,
                'timestamp': time.time(),
                'reason': reason
            }

            return allowed

        except Exception as e:
            # Cache failure for security
            self._policy_cache[cache_key] = {
                'allowed': False,
                'timestamp': time.time(),
                'reason': f'evaluation_error: {str(e)}'
            }
            return False

    def clear_policy_cache(self):
        """Clear the session's policy cache"""
        self._policy_cache.clear()

    def get_policy_cache_stats(self) -> Dict[str, Any]:
        """Get statistics about the policy cache"""
        current_time = time.time()
        valid_entries = sum(1 for entry in self._policy_cache.values()
                            if current_time - entry['timestamp'] < self._cache_timeout)

        return {
            'total_entries': len(self._policy_cache),
            'valid_entries': valid_entries,
            'expired_entries': len(self._policy_cache) - valid_entries,
            'cache_timeout': self._cache_timeout
        }

    async def setup(self):
        pass

    async def teardown(self):
        self.agents.clear()
        self.cursors.clear()

    def add_on_change_callback(self, callback: Callable[['Session'], None]):
        self.on_change_callbacks.append(callback)

    def _notify_change(self):
        for callback in self.on_change_callbacks:
            callback(self)

    # Financial delegation methods (delegate to banker)
    def get_dust_balance(self) -> int:
        return 0

    def can_afford(self, amount: int) -> bool:
        """Check if session can afford an amount."""
        return True

    def get_cost_estimate(self, action: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get cost estimate for an action."""
        return {
            "success": True,
            "estimated_cost": 100,  # Placeholder value
            "message": "Estimated cost calculated successfully."
        }

    def negotiate_transaction(self, action: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Negotiate a transaction with cost options."""
        return {
            "success": True,
            "message": "Transaction negotiated successfully."
        }

    def commit_transaction(self, action: str, params: Dict[str, Any],
                           selected_cost: Optional[int] = None) -> Dict[str, Any]:
        """Commit a transaction through the banker."""

        return {
            "success": True,
            "dust_charged": 0,
            "message": "Transaction committed successfully.",
            "transaction_id": "tx_123456"
        }

    def get_transaction_history(self) -> List[Dict[str, Any]]:
        """Get transaction history from banker."""
        return []

    # Compositor management - squads are core compositors
    def add_compositor(self, name: str, compositor: BaseCompositor) -> None:
        """Add a compositor (squad, ML model, framebuffer, etc.) to the session."""
        if not isinstance(compositor, BaseCompositor):
            raise TypeError(
                f"Compositor must be a BaseCompositor, got {type(compositor)}")

        self.compositors[name] = compositor
        self._compositor_outputs[name] = None
        self._notify_change()

    def remove_compositor(self, name: str) -> bool:
        """Remove a compositor from the session."""
        if name in self.compositors:
            del self.compositors[name]
            if name in self._compositor_outputs:
                del self._compositor_outputs[name]
            self._notify_change()
            return True
        return False

    def get_compositor(self, name: str) -> Optional[BaseCompositor]:
        """Get a specific compositor by name."""
        return self.compositors.get(name)

    def list_compositors(self) -> Dict[str, str]:
        """List all compositors and their types."""
        return {name: type(comp).__name__ for name, comp in self.compositors.items()}

    def transform_compositor(self, name: str, data: Any, **kwargs) -> Any:
        """Transform data using a specific compositor."""
        if name not in self.compositors:
            raise KeyError(f"Compositor '{name}' not found")

        result = self.compositors[name].transform(data, **kwargs)
        self._compositor_outputs[name] = result
        self._notify_change()
        return result

    def transform_all_compositors(self, data_map: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Transform data using all compositors with mapped inputs."""
        results = {}
        for name, compositor in self.compositors.items():
            if name in data_map:
                result = compositor.transform(data_map[name], **kwargs)
                self._compositor_outputs[name] = result
                results[name] = result
            else:
                # Use existing output if no new data provided
                results[name] = self._compositor_outputs.get(name)

        self._notify_change()
        return results

    def compose_compositor(self, name: str, *args, **kwargs) -> Any:
        """Compose output from a specific compositor."""
        if name not in self.compositors:
            raise KeyError(f"Compositor '{name}' not found")

        result = self.compositors[name].compose(*args, **kwargs)
        self._compositor_outputs[name] = result
        self._notify_change()
        return result

    def compose_all_compositors(self, **kwargs) -> Dict[str, Any]:
        """Compose outputs from all compositors."""
        results = {}
        for name, compositor in self.compositors.items():
            result = compositor.compose(**kwargs)
            self._compositor_outputs[name] = result
            results[name] = result

        self._notify_change()
        return results

    def get_compositor_output(self, name: str) -> Any:
        """Get the last output from a compositor."""
        return self._compositor_outputs.get(name)

    def get_all_compositor_outputs(self) -> Dict[str, Any]:
        """Get outputs from all compositors."""
        return self._compositor_outputs.copy()

    def set_shared_state(self, key: str, value: Any) -> None:
        """Set shared state accessible to all compositors."""
        self._shared_state[key] = value
        self._notify_change()

    def get_shared_state(self, key: Optional[str] = None) -> Any:
        """Get shared state. If key is None, returns all shared state."""
        if key is None:
            return self._shared_state.copy()
        return self._shared_state.get(key)

    def clear_shared_state(self) -> None:
        """Clear all shared state."""
        self._shared_state.clear()
        self._notify_change()

    def broadcast_to_compositors(self, data: Any, compositor_filter: Optional[List[str]] = None) -> Dict[str, Any]:
        """Broadcast data to all or filtered compositors."""
        results = {}
        target_compositors = (
            {name: comp for name, comp in self.compositors.items()
             if name in compositor_filter}
            if compositor_filter
            else self.compositors
        )

        for name, compositor in target_compositors.items():
            try:
                result = compositor.transform(data)
                self._compositor_outputs[name] = result
                results[name] = result
            except Exception as e:
                results[name] = {"error": str(e)}

        self._notify_change()
        return results

    def get_all_status_json(self) -> str:
        """Aggregate .status from all registered omnis/agents as JSON."""
        state = {}
        for agent in self.agents:
            if hasattr(agent, "status"):
                state[agent.__class__.__name__] = agent.status
        return json.dumps(state, default=str)

    def get_all_flat_state_json(self, include_sensitive=False) -> str:
        """Aggregate .to_dict() from all registered omnis/agents as JSON."""
        state = {}
        for agent in self.agents:
            if hasattr(agent, "to_dict"):
                state[agent.__class__.__name__] = agent.to_dict(
                    include_sensitive=include_sensitive)
        return json.dumps(state, default=str)

    def get_all_status_yaml(self) -> str:
        """Aggregate .status from all registered omnis/agents as YAML."""
        state = {}
        for agent in self.agents:
            if hasattr(agent, "status"):
                status_attr = getattr(agent, "status")
                if callable(status_attr):
                    state[agent.__class__.__name__] = status_attr()
                else:
                    state[agent.__class__.__name__] = status_attr
        return yaml.safe_dump(state, sort_keys=False)

    def get_all_flat_state_yaml(self, include_sensitive=False) -> str:
        """Aggregate .to_dict() from all registered omnis/agents as YAML."""
        state = {}
        for agent in self.agents:
            if hasattr(agent, "to_dict"):
                to_dict_attr = getattr(agent, "to_dict")
                if callable(to_dict_attr):
                    state[agent.__class__.__name__] = to_dict_attr(
                        include_sensitive=include_sensitive)
                else:
                    state[agent.__class__.__name__] = to_dict_attr
        return yaml.safe_dump(state, sort_keys=False)
