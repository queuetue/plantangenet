"""
Transport Operations with Banker Agent Integration.
Provides cost-aware transport operations (publish/subscribe) with transaction previews using banker agents.
"""

from typing import Dict, Any, Optional, List, Union, Callable, Coroutine
from .session import Session
from .banker import Banker, TransactionResult


class TransportOperationsManager:
    """
    Manages transport operations with integrated banker agent cost negotiation and previews.
    """

    def __init__(self, session: Session):
        """
        Initialize transport operations manager.

        Args:
            session: The user session with banker agents
        """
        self.session = session

    def get_publish_preview(self, topic: str, data: Union[str, bytes, dict]) -> Dict[str, Any]:
        """
        Get a preview of the cost to publish a message using the session's banker.

        Args:
            topic: The topic to publish to
            data: The data to publish

        Returns:
            Negotiation result with preview, or None if no banker available
        """
        # Calculate data size for costing
        data_size = self._calculate_data_size(data)

        params = {
            "topic": topic,
            "data_size": data_size,
            "topic_complexity": self._calculate_topic_complexity(topic)
        }

        result = self.session._banker.negotiate_transaction(
            "transport.publish", params)
        return result or {"action": "transport.publish", "allowed": False, "dust_cost": 0, "error": "No quote available"}

    def get_subscribe_preview(self, topic: str) -> Dict[str, Any]:
        """
        Get a preview of the cost to subscribe to a topic using the session's banker.

        Args:
            topic: The topic to subscribe to

        Returns:
            Negotiation result with preview, or None if no banker available
        """
        params = {
            "topic": topic,
            "topic_complexity": self._calculate_topic_complexity(topic)
        }

        result = self.session._banker.negotiate_transaction(
            "transport.subscribe", params)
        return result or {"action": "transport.subscribe", "allowed": False, "dust_cost": 0, "error": "No quote available"}

    async def publish_with_cost(self, topic: str, data: Union[str, bytes, dict],
                                transport_client: Any, selected_cost: Optional[int] = None) -> Dict[str, Any]:
        """
        Publish a message with banker agent cost deduction.

        Args:
            topic: The topic to publish to
            data: The data to publish
            transport_client: The transport client (e.g., NATS mixin) to use for actual publish
            selected_cost: Optional pre-selected cost for the transaction

        Returns:
            Transaction result with cost information
        """
        # Calculate data size for costing
        data_size = self._calculate_data_size(data)

        params = {
            "topic": topic,
            "data_size": data_size,
            "topic_complexity": self._calculate_topic_complexity(topic)
        }

        # Commit the transaction (this deducts Dust and logs the transaction)
        result = self.session._banker.commit_transaction(
            "transport.publish", params, selected_cost=selected_cost)

        if result.success:
            # Only publish if payment succeeded
            await transport_client.publish(topic, data)
            return {
                "success": True,
                "cost_paid": result.dust_charged,
                "transaction_id": result.transaction_id,
                "message": f"Published to {topic}, cost: {result.dust_charged} Dust"
            }
        else:
            return {
                "success": False,
                "error": result.message,
                "cost_paid": 0
            }

    async def subscribe_with_cost(self, topic: str, callback: Callable[..., Coroutine[Any, Any, Any]],
                                  transport_client: Any, selected_cost: Optional[int] = None) -> Dict[str, Any]:
        """
        Subscribe to a topic with banker agent cost deduction.

        Args:
            topic: The topic to subscribe to
            callback: The callback function for messages
            transport_client: The transport client (e.g., NATS mixin) to use for actual subscribe
            selected_cost: Optional pre-selected cost for the transaction

        Returns:
            Transaction result with cost information
        """
        params = {
            "topic": topic,
            "topic_complexity": self._calculate_topic_complexity(topic)
        }

        # Commit the transaction (this deducts Dust and logs the transaction)
        result = self.session._banker.commit_transaction(
            "transport.subscribe", params, selected_cost=selected_cost)

        if result.success:
            # Only subscribe if payment succeeded
            subscription = await transport_client.subscribe(topic, callback)
            return {
                "success": True,
                "cost_paid": result.dust_charged,
                "transaction_id": result.transaction_id,
                "subscription": subscription,
                "message": f"Subscribed to {topic}, cost: {result.dust_charged} Dust"
            }
        else:
            return {
                "success": False,
                "error": result.message,
                "cost_paid": 0,
                "subscription": None
            }

    def _calculate_data_size(self, data: Union[str, bytes, dict]) -> int:
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
        """
        Calculate topic complexity for costing.
        More complex topics (more segments, wildcards) cost more.
        """
        segments = topic.split('.')
        complexity = len(segments)

        # Add complexity for wildcards
        if '*' in topic:
            complexity += 2
        if '>' in topic:
            complexity += 3

        return complexity
