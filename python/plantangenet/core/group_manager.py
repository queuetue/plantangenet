from typing import Callable, Any, List, Protocol, Optional
from abc import abstractmethod
from ..squad.base import BaseSquad
from ..squad.squad import Squad


class StorageSquad(BaseSquad):
    """Manages storage operations with integrated banker agent cost negotiation."""

    def __init__(self, session, name: Optional[str] = None):
        super().__init__(name)
        self.session = session

    def generate(self, group: str, omni_type: str, *args, **kwargs):
        """Generate a new storage operation or omni object."""
        # Create storage operation metadata
        operation = {
            "type": omni_type,
            "created_at": kwargs.get("timestamp"),
            "params": kwargs
        }
        self.add(group, operation)
        return operation

    def get_save_preview(self, omni: Any, incremental: bool = True):
        """Get a preview of the cost to save an omni object."""
        fields = list(omni.get_dirty_fields().keys()) if incremental and hasattr(
            omni, 'get_dirty_fields') else []
        params = {"fields": fields, "omni_id": getattr(
            omni, '_omni_id', 'unknown')}
        return self.session.negotiate_transaction("save_object", params)

    async def save_omni_with_cost(self, omni: Any, incremental: bool = True, selected_cost: Optional[int] = None):
        """Save an omni object with cost negotiation and preview."""
        fields = list(omni.get_dirty_fields().keys()) if incremental and hasattr(
            omni, 'get_dirty_fields') else []
        params = {"fields": fields, "omni_id": getattr(
            omni, '_omni_id', 'unknown')}

        estimate = self.session.get_cost_estimate("save_object", params)
        if not estimate:
            success = await omni.save_to_storage(incremental)
            return {"success": success, "dust_charged": 0, "message": "Saved without cost"}

        cost = selected_cost or estimate.get("dust_cost")
        if not self.session.can_afford(cost):
            return {"success": False, "dust_charged": 0, "message": f"Insufficient dust. Need {cost}"}

        tx_result = self.session.commit_transaction(
            "save_object", params, cost)
        if tx_result["success"]:
            success = await omni.save_to_storage(incremental)
            # Track the save operation in our groups
            self.add("completed_saves", {"omni_id": getattr(
                omni, '_omni_id', 'unknown'), "cost": tx_result["dust_charged"]})
            return {"success": success, "dust_charged": tx_result["dust_charged"], "transaction_id": tx_result.get("transaction_id")}
        else:
            return {"success": False, "dust_charged": 0, "message": tx_result["message"]}


class TransportSquad(BaseSquad):
    """Manages transport operations with integrated banker agent cost negotiation."""

    def __init__(self, session, name: Optional[str] = None):
        super().__init__(name)
        self.session = session

    def generate(self, group: str, operation_type: str, topic: str, *args, **kwargs):
        """Generate a new transport operation."""
        operation = {
            "type": operation_type,
            "topic": topic,
            "created_at": kwargs.get("timestamp"),
            "params": kwargs
        }
        self.add(group, operation)
        return operation

    def get_publish_preview(self, topic: str, data: Any):
        """Get a preview of the cost to publish a message."""
        data_size = self._calculate_data_size(data)
        params = {"topic": topic, "data_size": data_size,
                  "topic_complexity": self._calculate_topic_complexity(topic)}
        result = self.session.negotiate_transaction(
            "transport.publish", params)
        return result or {"action": "transport.publish", "allowed": False, "dust_cost": 0, "error": "No quote available"}

    async def publish_with_cost(self, topic: str, data: Any, transport_client: Any, selected_cost: Optional[int] = None):
        """Publish a message with banker agent cost deduction."""
        data_size = self._calculate_data_size(data)
        params = {"topic": topic, "data_size": data_size,
                  "topic_complexity": self._calculate_topic_complexity(topic)}

        result = self.session.commit_transaction(
            "transport.publish", params, selected_cost=selected_cost)
        if result["success"]:
            await transport_client.publish(topic, data)
            # Track the publish operation
            self.add("completed_publishes", {
                     "topic": topic, "cost": result["dust_charged"]})
            return {"success": True, "cost_paid": result["dust_charged"], "transaction_id": result.get("transaction_id")}
        else:
            return {"success": False, "error": result["message"], "cost_paid": 0}

    async def subscribe_with_cost(self, topic: str, callback: Callable, transport_client: Any, selected_cost: Optional[int] = None):
        """Subscribe to a topic with banker agent cost deduction."""
        params = {"topic": topic,
                  "topic_complexity": self._calculate_topic_complexity(topic)}

        result = self.session.commit_transaction(
            "transport.subscribe", params, selected_cost=selected_cost)
        if result["success"]:
            subscription = await transport_client.subscribe(topic, callback)
            # Track the subscription
            self.add("active_subscriptions", {
                     "topic": topic, "subscription": subscription, "cost": result["dust_charged"]})
            return {"success": True, "cost_paid": result["dust_charged"], "subscription": subscription}
        else:
            return {"success": False, "error": result["message"], "subscription": None}

    def _calculate_data_size(self, data: Any) -> int:
        """Calculate the size of data for costing purposes."""
        if isinstance(data, dict):
            import json
            return len(json.dumps(data).encode('utf-8'))
        elif isinstance(data, str):
            return len(data.encode('utf-8'))
        elif isinstance(data, bytes):
            return len(data)
        else:
            return len(str(data).encode('utf-8'))

    def _calculate_topic_complexity(self, topic: str) -> int:
        """Calculate topic complexity for costing."""
        segments = topic.split('.')
        complexity = len(segments)
        if '*' in topic:
            complexity += 2
        if '>' in topic:
            complexity += 3
        return complexity


class SessionSquad(BaseSquad):
    """Manages session components like policies, gatekeepers, matchmakers, etc."""

    def __init__(self, session, name: Optional[str] = None):
        super().__init__(name)
        self.session = session

    def generate(self, group: str, component_type: str, *args, **kwargs):
        """Generate session components based on type."""
        # TODO: Implement specific component creation
        # Most of these components don't exist yet in the current codebase
        if component_type == "local_policy":
            # from ..session.local_policy import LocalPolicy
            # component = LocalPolicy(*args, **kwargs)
            component = {"type": "local_policy",
                         "args": args, "kwargs": kwargs}
        elif component_type == "gatekeeper":
            # from ..session.gatekeeper import Gatekeeper
            # component = Gatekeeper(*args, **kwargs)
            component = {"type": "gatekeeper", "args": args, "kwargs": kwargs}
        elif component_type == "matchmaker":
            # from ..session.matchmaker import Matchmaker
            # component = Matchmaker(*args, **kwargs)
            component = {"type": "matchmaker", "args": args, "kwargs": kwargs}
        elif component_type == "referee":
            # from ..session.referee import Referee
            # component = Referee(*args, **kwargs)
            component = {"type": "referee", "args": args, "kwargs": kwargs}
        elif component_type == "stats":
            # from ..session.stats import Stats
            # component = Stats(*args, **kwargs)
            component = {"type": "stats", "args": args, "kwargs": kwargs}
        else:
            raise ValueError(f"Unknown component type: {component_type}")

        self.add(group, component)
        return component


class GameSquad(Squad):
    """Specialized Squad for managing game-specific objects like activities, agents, etc."""

    def __init__(self, session, name: Optional[str] = None):
        super().__init__(name)
        self.session = session

    def generate(self, group: str, object_type: str, *args, **kwargs):
        """Generate game objects based on type."""
        if object_type == "activity":
            # This would create game activities
            activity = self._create_activity(*args, **kwargs)
        elif object_type == "agent":
            # This would create game agents
            activity = self._create_agent(*args, **kwargs)
        else:
            raise ValueError(f"Unknown game object type: {object_type}")

        self.add(group, activity)
        return activity

    def _create_activity(self, *args, **kwargs):
        """Create a game activity - to be implemented by specific games."""
        raise NotImplementedError(
            "Specific games must implement activity creation")

    def _create_agent(self, *args, **kwargs):
        """Create a game agent - to be implemented by specific games."""
        raise NotImplementedError(
            "Specific games must implement agent creation")
