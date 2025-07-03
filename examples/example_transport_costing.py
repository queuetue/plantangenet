"""
Example: Transport Operations with Banker Agent Integration

This demonstrates how to use the transport operations manager with cost estimation,
negotiation, and transaction tracking for publish/subscribe operations.
"""

import asyncio
import logging
from plantangenet.session import Session
from plantangenet.vanilla_banker import create_vanilla_banker_agent
from plantangenet.transport_operations import TransportOperationsManager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MockTransportClient:
    """Mock transport client for demonstration."""

    def __init__(self):
        self.published_messages = []
        self.subscriptions = {}

    async def publish(self, topic: str, data):
        logger.info(f"TRANSPORT: Published to {topic}: {data}")
        self.published_messages.append({"topic": topic, "data": data})

    async def subscribe(self, topic: str, callback):
        subscription_id = f"sub_{len(self.subscriptions)}"
        logger.info(
            f"TRANSPORT: Subscribed to {topic} with ID {subscription_id}")
        self.subscriptions[topic] = {
            "callback": callback, "id": subscription_id}
        return subscription_id


async def message_handler(message):
    """Example message handler for subscriptions."""
    logger.info(f"HANDLER: Received message: {message}")


async def demonstrate_transport_costing():
    """Demonstrate transport operations with cost integration."""
    logger.info("=== Transport Operations with Banker Agent Demo ===")

    # Create a session and banker
    session = Session(session_id="transport_demo")
    banker = create_vanilla_banker_agent(initial_balance=100)
    session.add_banker_agent(banker)

    # Add transport cost base
    transport_cost_base = {
        "name": "Transport Cost Base",
        "version": "1.0.0",
        "api_costs": {
            "transport.publish": 5,      # Base cost for publishing
            "transport.subscribe": 10,   # Base cost for subscribing
        },
        "package_deals": {},
        "modifiers": {}
    }
    banker.add_cost_base_data("transport", transport_cost_base)

    # Create transport manager and mock client
    transport_manager = TransportOperationsManager(session)
    transport_client = MockTransportClient()

    logger.info(f"Initial balance: {session.get_dust_balance()} Dust")

    # === Publishing Examples ===
    logger.info("\n--- Publishing Examples ---")

    # Get preview for a simple publish
    simple_topic = "events.user.login"
    simple_data = "user123 logged in"

    publish_preview = transport_manager.get_publish_preview(
        simple_topic, simple_data)
    logger.info(
        f"Publish preview for '{simple_topic}': {publish_preview['quote']['dust_cost']} Dust")

    # Publish with cost
    publish_result = await transport_manager.publish_with_cost(simple_topic, simple_data, transport_client)
    logger.info(f"Publish result: {publish_result}")
    logger.info(f"Balance after publish: {session.get_dust_balance()} Dust")

    # Get preview for a complex publish (larger data, complex topic)
    complex_topic = "system.analytics.user.behavior.tracking"
    complex_data = {
        "user_id": "user123",
        "event": "page_view",
        "page": "/dashboard",
        "timestamp": "2025-07-02T20:00:00Z",
        "metadata": {
            "browser": "Chrome",
            "device": "desktop",
            "session_id": "sess_456"
        }
    }

    complex_preview = transport_manager.get_publish_preview(
        complex_topic, complex_data)
    logger.info(
        f"Complex publish preview for '{complex_topic}': {complex_preview['quote']['dust_cost']} Dust")

    # Publish complex message
    complex_result = await transport_manager.publish_with_cost(complex_topic, complex_data, transport_client)
    logger.info(f"Complex publish result: {complex_result}")
    logger.info(
        f"Balance after complex publish: {session.get_dust_balance()} Dust")

    # === Subscription Examples ===
    logger.info("\n--- Subscription Examples ---")

    # Get preview for subscription
    sub_topic = "events.system.*"

    sub_preview = transport_manager.get_subscribe_preview(sub_topic)
    logger.info(
        f"Subscribe preview for '{sub_topic}': {sub_preview['quote']['dust_cost']} Dust")

    # Subscribe with cost
    sub_result = await transport_manager.subscribe_with_cost(sub_topic, message_handler, transport_client)
    logger.info(f"Subscribe result: {sub_result}")
    logger.info(f"Balance after subscribe: {session.get_dust_balance()} Dust")

    # Subscribe to a complex wildcard topic
    complex_sub_topic = "system.alerts.>"

    complex_sub_preview = transport_manager.get_subscribe_preview(
        complex_sub_topic)
    logger.info(
        f"Complex subscribe preview for '{complex_sub_topic}': {complex_sub_preview['quote']['dust_cost']} Dust")

    complex_sub_result = await transport_manager.subscribe_with_cost(complex_sub_topic, message_handler, transport_client)
    logger.info(f"Complex subscribe result: {complex_sub_result}")
    logger.info(
        f"Balance after complex subscribe: {session.get_dust_balance()} Dust")

    # === Transaction History ===
    logger.info("\n--- Transaction History ---")

    history = session.get_transaction_history()
    for i, transaction in enumerate(history, 1):
        logger.info(f"Transaction {i}: {transaction}")

    # === Summary ===
    logger.info("\n--- Summary ---")
    logger.info(
        f"Total messages published: {len(transport_client.published_messages)}")
    logger.info(f"Total subscriptions: {len(transport_client.subscriptions)}")
    logger.info(f"Final balance: {session.get_dust_balance()} Dust")
    logger.info(f"Total transactions: {len(history)}")

    return {
        "final_balance": session.get_dust_balance(),
        "published_count": len(transport_client.published_messages),
        "subscription_count": len(transport_client.subscriptions),
        "transaction_count": len(history)
    }


async def demonstrate_insufficient_funds():
    """Demonstrate what happens when there are insufficient funds."""
    logger.info("\n=== Insufficient Funds Demo ===")

    # Create a session with very low balance
    session = Session(session_id="low_balance_demo")
    banker = create_vanilla_banker_agent(initial_balance=3)  # Very low balance
    session.add_banker_agent(banker)

    # Add expensive transport costs
    expensive_cost_base = {
        "name": "Expensive Transport",
        "version": "1.0.0",
        "api_costs": {
            "transport.publish": 100,    # More than available balance
            "transport.subscribe": 50,   # Also more than available
        }
    }
    banker.add_cost_base_data("expensive", expensive_cost_base)

    transport_manager = TransportOperationsManager(session)
    transport_client = MockTransportClient()

    logger.info(f"Low balance: {session.get_dust_balance()} Dust")

    # Try to publish - should fail
    expensive_result = await transport_manager.publish_with_cost("expensive.topic", "data", transport_client)
    logger.info(f"Expensive publish result: {expensive_result}")
    logger.info(
        f"Balance after failed publish: {session.get_dust_balance()} Dust")
    logger.info(
        f"Messages actually published: {len(transport_client.published_messages)}")


async def main():
    """Run all demonstrations."""
    try:
        # Main demo
        demo_result = await demonstrate_transport_costing()

        # Insufficient funds demo
        await demonstrate_insufficient_funds()

        logger.info(f"\n=== Demo Complete ===")
        logger.info(f"Final demo result: {demo_result}")

    except Exception as e:
        logger.error(f"Demo failed: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())
