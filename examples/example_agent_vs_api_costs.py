"""
Example: Agent Cost vs API Cost Model

This demonstrates the new economic model where:
1. Agents can declare their own prices and charge clients
2. The API charges agents the actual resource costs  
3. The Banker tracks discrepancies for system oversight
4. Operations can proceed even with insufficient funds (policy decision)
5. Agents can profit/lose by optimizing their operations
"""

import asyncio
import logging
from plantangenet.session import Session
from plantangenet.vanilla_banker import create_vanilla_banker_agent
from plantangenet.transport_operations import TransportOperationsManager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProfitableTransportAgent:
    """
    An agent that tries to profit from transport operations by:
    - Charging clients more than the API costs
    - Using efficient compression/batching
    - Building up Dust reserves
    """

    def __init__(self, session: Session, markup_percentage: float = 50.0):
        """
        Initialize the agent.

        Args:
            session: The session with banker
            markup_percentage: How much to mark up API costs
        """
        self.session = session
        self.markup_percentage = markup_percentage
        self.transport_manager = TransportOperationsManager(session)
        self.client_charges = []  # Track what we charged clients

    async def publish_for_client(self, topic: str, data, transport_client, client_id: str):
        """
        Publish a message on behalf of a client, charging them our rate.
        Then pay the actual API cost.
        """
        # Get API cost estimate
        api_preview = self.transport_manager.get_publish_preview(topic, data)
        api_cost = api_preview["quote"]["dust_cost"]

        # Calculate our price (markup)
        our_price = int(api_cost * (1 + self.markup_percentage / 100))

        logger.info(f"AGENT: API cost for '{topic}': {api_cost} Dust")
        logger.info(
            f"AGENT: Charging client {client_id}: {our_price} Dust (markup: {self.markup_percentage}%)")

        # "Charge" the client (simulate)
        self.client_charges.append({
            "client_id": client_id,
            "topic": topic,
            "amount_charged": our_price,
            "api_cost": api_cost,
            "profit": our_price - api_cost
        })

        # Add the client's payment to our banker
        self.session._banker.add_dust(
            our_price, f"Client payment from {client_id}")

        # Now perform the actual operation and pay API costs
        result = await self.transport_manager.publish_with_cost(topic, data, transport_client)

        if result["success"]:
            # Charge ourselves the actual API cost
            api_charge_result = self.session._banker.charge_agent_for_api_usage(
                "transport.publish",
                {"topic": topic, "data_size": len(str(data))},
                our_price  # What we charged the client
            )

            logger.info(
                f"AGENT: API charged us: {api_charge_result.api_actual_cost} Dust")
            logger.info(
                f"AGENT: Cost discrepancy: {api_charge_result.cost_discrepancy} Dust")

            return {
                "success": True,
                "client_charged": our_price,
                "api_cost": api_charge_result.api_actual_cost,
                "profit": api_charge_result.cost_discrepancy,
                "message": f"Published for {client_id}, profit: {api_charge_result.cost_discrepancy} Dust"
            }
        else:
            return {
                "success": False,
                "error": result.get("error", "Unknown error"),
                "client_charged": our_price,
                "api_cost": 0
            }

    def get_total_profit(self):
        """Calculate total profit from all client operations."""
        return sum(charge["profit"] for charge in self.client_charges)


class MockTransportClient:
    """Mock transport client for demonstration."""

    def __init__(self):
        self.published_messages = []

    async def publish(self, topic: str, data):
        logger.info(f"TRANSPORT: Published to {topic}: {data}")
        self.published_messages.append({"topic": topic, "data": data})


async def demonstrate_agent_vs_api_costs():
    """Demonstrate the agent vs API cost model."""
    logger.info("=== Agent vs API Cost Model Demo ===")

    # Create session with realistic high costs
    session = Session(session_id="agent_profit_demo")
    banker = create_vanilla_banker_agent(
        initial_balance=500)  # Start with reasonable balance
    session.add_banker_agent(banker)

    logger.info(f"Initial banker balance: {session.get_dust_balance()} Dust")

    # Create a profitable agent with 50% markup
    profit_agent = ProfitableTransportAgent(session, markup_percentage=50.0)
    transport_client = MockTransportClient()

    # === Client Operations ===
    logger.info("\n--- Client Operations ---")

    # Client 1: Simple message
    client1_result = await profit_agent.publish_for_client(
        "events.user.login",
        "user123 logged in",
        transport_client,
        "client_001"
    )
    logger.info(f"Client 1 result: {client1_result}")

    # Client 2: Complex message
    complex_data = {
        "user_id": "user456",
        "event": "purchase",
        # Larger data
        "items": [{"id": 1, "name": "Widget", "price": 19.99}] * 10,
        "metadata": {"session": "sess_789", "timestamp": "2025-07-02T20:00:00Z"}
    }

    client2_result = await profit_agent.publish_for_client(
        "commerce.purchase.completed",
        complex_data,
        transport_client,
        "client_002"
    )
    logger.info(f"Client 2 result: {client2_result}")

    # Client 3: Efficient message (agent can optimize)
    client3_result = await profit_agent.publish_for_client(
        "ping",
        "ping",
        transport_client,
        "client_003"
    )
    logger.info(f"Client 3 result: {client3_result}")

    # === Agent Summary ===
    logger.info("\n--- Agent Performance Summary ---")
    logger.info(f"Final banker balance: {session.get_dust_balance()} Dust")
    logger.info(
        f"Total profit from clients: {profit_agent.get_total_profit()} Dust")

    # Show client charges
    logger.info("\nClient Charges:")
    for charge in profit_agent.client_charges:
        logger.info(f"  {charge['client_id']}: charged {charge['amount_charged']}, "
                    f"API cost {charge['api_cost']}, profit {charge['profit']}")

    # === Transaction History with Discrepancies ===
    logger.info("\n--- Transaction History (including discrepancies) ---")
    history = session.get_transaction_history()
    for transaction in history:
        if transaction["type"] == "discrepancy_record":
            metadata = transaction.get("metadata", {})
            logger.info(f"DISCREPANCY: {transaction['reason']} "
                        f"({metadata.get('discrepancy_type', 'unknown')})")
        else:
            logger.info(
                f"TRANSACTION: {transaction['type']} {transaction['amount']} Dust - {transaction['reason']}")

    return {
        "final_balance": session.get_dust_balance(),
        "total_profit": profit_agent.get_total_profit(),
        "client_count": len(profit_agent.client_charges),
        "messages_published": len(transport_client.published_messages)
    }


async def demonstrate_overdraft_policy():
    """Demonstrate the overdraft policy (operations allowed with insufficient funds)."""
    logger.info("\n=== Overdraft Policy Demo ===")

    # Create session with very low balance
    session = Session(session_id="overdraft_demo")
    banker = create_vanilla_banker_agent(
        initial_balance=50)  # Low balance vs realistic costs
    session.add_banker_agent(banker)

    logger.info(f"Low balance: {session.get_dust_balance()} Dust")

    # Create agent and try expensive operation
    agent = ProfitableTransportAgent(session, markup_percentage=20.0)
    transport_client = MockTransportClient()

    # Try expensive operation that would exceed balance
    expensive_data = {"large_payload": "x" * 1000}  # Large message

    result = await agent.publish_for_client(
        "system.big.data.transfer",
        expensive_data,
        transport_client,
        "client_overdraft"
    )

    logger.info(f"Overdraft operation result: {result}")
    logger.info(f"Balance after overdraft: {session.get_dust_balance()} Dust")

    # Show that operation succeeded despite insufficient initial funds
    logger.info(
        f"Messages published: {len(transport_client.published_messages)}")

    # Show transaction history
    logger.info("\nOverdraft Transaction History:")
    history = session.get_transaction_history()
    for transaction in history[-5:]:  # Last 5 transactions
        logger.info(f"  {transaction['type']}: {transaction['amount']} Dust, "
                    f"balance: {transaction['balance_before']} -> {transaction['balance_after']}")


async def main():
    """Run all demonstrations."""
    try:
        # Main agent vs API cost demo
        demo_result = await demonstrate_agent_vs_api_costs()

        # Overdraft policy demo
        await demonstrate_overdraft_policy()

        logger.info(f"\n=== Demo Complete ===")
        logger.info(f"Final demo result: {demo_result}")

    except Exception as e:
        logger.error(f"Demo failed: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())
