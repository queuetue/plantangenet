from typing import Callable, Any, Optional
from .base import BaseSquad


class TransportSquad(BaseSquad):
    """Manages transport operations with integrated banker agent cost negotiation."""

    def __init__(self, session, name: Optional[str] = None):
        super().__init__(name)
        self.session = session

    def generate(self, group: str, operation_type: str, topic: str, *args, **kwargs):
        operation = {
            "type": operation_type,
            "topic": topic,
            "created_at": kwargs.get("timestamp"),
            "params": kwargs
        }
        self.add(group, operation)
        return operation

    def get_publish_preview(self, topic: str, data: Any):
        data_size = self._calculate_data_size(data)
        params = {"topic": topic, "data_size": data_size,
                  "topic_complexity": self._calculate_topic_complexity(topic)}
        result = self.session.negotiate_transaction(
            "transport.publish", params)
        return result or {"action": "transport.publish", "allowed": False, "dust_cost": 0, "error": "No quote available"}

    async def publish_with_cost(self, topic: str, data: Any, transport_client: Any, selected_cost: Optional[int] = None):
        data_size = self._calculate_data_size(data)
        params = {"topic": topic, "data_size": data_size,
                  "topic_complexity": self._calculate_topic_complexity(topic)}

        result = self.session.commit_transaction(
            "transport.publish", params, selected_cost=selected_cost)
        if result["success"]:
            await transport_client.publish(topic, data)
            self.add("completed_publishes", {
                     "topic": topic, "cost": result["dust_charged"]})
            return {"success": True, "cost_paid": result["dust_charged"], "transaction_id": result.get("transaction_id")}
        else:
            return {"success": False, "error": result["message"], "cost_paid": 0}

    async def subscribe_with_cost(self, topic: str, callback: Callable, transport_client: Any, selected_cost: Optional[int] = None):
        params = {"topic": topic,
                  "topic_complexity": self._calculate_topic_complexity(topic)}

        result = self.session.commit_transaction(
            "transport.subscribe", params, selected_cost=selected_cost)
        if result["success"]:
            subscription = await transport_client.subscribe(topic, callback)
            self.add("active_subscriptions", {
                     "topic": topic, "subscription": subscription, "cost": result["dust_charged"]})
            return {"success": True, "cost_paid": result["dust_charged"], "subscription": subscription}
        else:
            return {"success": False, "error": result["message"], "subscription": None}

    def _calculate_data_size(self, data: Any) -> int:
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
        segments = topic.split('.')
        complexity = len(segments)
        if '*' in topic:
            complexity += 2
        if '>' in topic:
            complexity += 3
        return complexity
