#!/usr/bin/env python3
"""
Enhanced demonstration of Plantangenet's economic and logging system.

This example showcases the new high-level APIs:
- credit_dust() - High-level dust crediting with identity support
- preview_operation_cost() - Cost estimation before operations
- charge_for_operation() - Operation charging with cost negotiation
- distribute_dust() - Policy-driven dust distribution
"""

from plantangenet.omni.mixins.mixin import OmniMixin
from plantangenet.omni.mixins.redis import RedisMixin
from plantangenet.omni.mixins.nats import NatsMixin
from plantangenet.logger import Logger
from plantangenet.dust import (
    BankerMixin, TransactionResult, FinancialIdentity
)
import asyncio
import json
import tempfile
import os
import datetime
from typing import Dict, Any, List

# Import Plantangenet components
import sys
sys.path.append('/home/srussell/Development/groovebox/python')


class EconAgent(BankerMixin, NatsMixin, RedisMixin, OmniMixin):
    """Enhanced agent demonstrating new high-level economic APIs."""

    def __init__(self, agent_id: str):
        super().__init__()
        self.agent_id = agent_id
        self._logger = Logger()

        # Set up log capture for demo
        self.captured_logs: List[Dict[str, Any]] = []
        self._logger.on_log = self._capture_log

    @property
    def logger(self):
        """Required by mixins."""
        return self._logger

    @property
    def disposition(self) -> str:
        """Required by NatsMixin."""
        return "enhanced_agent"

    async def update_storage(self):
        """Required by StorageMixin."""
        pass

    def _capture_log(self, level: str, category: str, data: Any):
        """Capture log events for demonstration."""
        self.captured_logs.append({
            'level': level,
            'category': category,
            'data': data,
            'timestamp': datetime.datetime.now().isoformat()
        })

    async def initialize(self):
        """Initialize the agent with enhanced setup."""
        # Create financial identity
        self.financial_identity = FinancialIdentity(
            user_id=f"user_{self.agent_id}",
            agent_id=self.agent_id,
            roles=["enhanced_agent", "trader"],
            permissions=["economic_operations",
                         "transport_operations", "storage_operations"]
        )

        # Use the new credit_dust API
        result = self.credit_dust(
            amount=1500,
            reason="Enhanced agent initial funding",
            identity=self.financial_identity
        )
        print(
            f"Enhanced initialization: {result.success}, credited: {abs(result.dust_charged)} dust")

        return result.success

    async def demonstrate_cost_preview_and_negotiation(self):
        """Demonstrate cost preview and negotiation features."""
        print(f"\n=== Cost Preview & Negotiation Demo for {self.agent_id} ===")

        # Preview various operations
        print("\n--- Cost Previews ---")

        operations = [
            ("data_transport", {
             "data_size": 2048, "priority": "high", "destination": "remote_cluster"}),
            ("computation", {"complexity": "high", "cpu_hours": 2}),
            ("redis_set", {"data_size": 512, "ttl": 3600}),
            ("nats_publish", {"data_size": 1024, "subscribers": 5})
        ]

        operation_costs = {}
        for op_type, params in operations:
            preview = self.preview_operation_cost(
                op_type, params, self.financial_identity)
            operation_costs[op_type] = preview
            print(f"{op_type}: {preview['estimated_cost']} dust")
            print(f"  Breakdown: {preview['cost_breakdown']}")

        # Now perform operations with cost negotiation
        print("\n--- Operations with Cost Negotiation ---")

        current_balance = self.get_balance(self.financial_identity)
        print(f"Balance before operations: {current_balance} dust")

        for op_type, params in operations[:2]:  # Do first two operations
            preview = operation_costs[op_type]
            estimated_cost = preview['estimated_cost']

            # Agent negotiates a lower cost
            agent_negotiated_cost = max(1, estimated_cost - 5)

            print(f"\n{op_type}:")
            print(f"  System estimate: {estimated_cost} dust")
            print(f"  Agent negotiated: {agent_negotiated_cost} dust")

            # Charge for the operation
            result = self.charge_for_operation(
                cost=estimated_cost,  # System charges actual cost
                operation_type=op_type,
                operation_details=params,
                identity=self.financial_identity,
                agent_declared_cost=agent_negotiated_cost
            )

            print(f"  Result: {result.success}")
            print(f"  Charged: {result.dust_charged} dust")
            if result.cost_discrepancy:
                print(f"  Cost discrepancy: {result.cost_discrepancy} dust")

        final_balance = self.get_balance(self.financial_identity)
        print(f"\nBalance after operations: {final_balance} dust")
        print(f"Total spent: {current_balance - final_balance} dust")

    async def demonstrate_revenue_and_distribution(self):
        """Demonstrate revenue earning and distribution."""
        print(f"\n=== Revenue & Distribution Demo for {self.agent_id} ===")

        # Simulate earning revenue from providing services
        service_revenues = [
            (300, "agent_profit", {
             "service": "data_analysis", "client": "client_001"}),
            (450, "service_revenue", {
             "service": "api_hosting", "client": "client_002"}),
            (200, "agent_profit", {
             "service": "consulting", "client": "client_003"})
        ]

        total_earned = 0
        for revenue, distribution_type, context in service_revenues:
            # Credit the revenue
            credit_result = self.credit_dust(
                amount=revenue,
                reason=f"Revenue from {context['service']} for {context['client']}",
                identity=self.financial_identity
            )
            print(f"Earned {revenue} dust from {context['service']}")

            # Distribute according to policy
            distribution = self.distribute_dust(
                total_amount=revenue,
                distribution_type=distribution_type,
                context=context,
                identity=self.financial_identity
            )

            print(f"  Distribution ({distribution_type}):")
            for recipient, amount in distribution.items():
                print(f"    {recipient}: {amount} dust")

            total_earned += revenue

        print(f"\nTotal revenue earned: {total_earned} dust")

        current_balance = self.get_balance(self.financial_identity)
        print(f"Current balance: {current_balance} dust")

    async def demonstrate_complex_economic_scenario(self):
        """Demonstrate a complex economic scenario."""
        print(f"\n=== Complex Economic Scenario for {self.agent_id} ===")

        # Scenario: Agent provides a complex service requiring multiple sub-operations
        print("Scenario: Multi-step data processing pipeline")

        # Step 1: Preview all costs
        pipeline_steps = [
            ("data_transport", {"data_size": 5120,
             "priority": "normal"}, "Input data ingestion"),
            ("computation", {"complexity": "medium",
             "cpu_hours": 1}, "Data processing"),
            ("redis_set", {"data_size": 2048, "ttl": 7200}, "Cache results"),
            ("nats_publish", {"data_size": 1024,
             "subscribers": 3}, "Notify completion")
        ]

        total_estimated_cost = 0
        step_costs = []

        print("\n--- Pipeline Cost Analysis ---")
        for op_type, params, description in pipeline_steps:
            preview = self.preview_operation_cost(
                op_type, params, self.financial_identity)
            cost = preview['estimated_cost']
            total_estimated_cost += cost
            step_costs.append(cost)

            print(f"{description}: {cost} dust ({op_type})")

        print(f"Total estimated pipeline cost: {total_estimated_cost} dust")

        # Step 2: Check if we can afford it
        current_balance = self.get_balance(self.financial_identity)
        print(f"Current balance: {current_balance} dust")

        if current_balance >= total_estimated_cost:
            print("✅ Pipeline is affordable, proceeding...")

            # Step 3: Execute pipeline
            print("\n--- Executing Pipeline ---")
            for i, ((op_type, params, description), cost) in enumerate(zip(pipeline_steps, step_costs)):
                print(f"Step {i+1}: {description}")

                result = self.charge_for_operation(
                    cost=cost,
                    operation_type=op_type,
                    operation_details=params,
                    identity=self.financial_identity
                )

                if result.success:
                    print(f"  ✅ Completed: {result.dust_charged} dust charged")
                else:
                    print(f"  ❌ Failed: {result.message}")
                    break

            # Step 4: Calculate profit and distribute
            client_payment = 500  # What client paid
            actual_cost = total_estimated_cost
            profit = client_payment - actual_cost

            print(f"\n--- Financial Summary ---")
            print(f"Client payment: {client_payment} dust")
            print(f"Actual costs: {actual_cost} dust")
            print(f"Profit: {profit} dust")

            if profit > 0:
                # Credit the client payment
                self.credit_dust(
                    amount=client_payment,
                    reason="Payment for data processing pipeline",
                    identity=self.financial_identity
                )

                # Distribute the profit
                profit_distribution = self.distribute_dust(
                    total_amount=profit,
                    distribution_type="agent_profit",
                    context={"service": "data_pipeline",
                             "client": "enterprise_client"},
                    identity=self.financial_identity
                )

                print("Profit distribution:")
                for recipient, amount in profit_distribution.items():
                    print(f"  {recipient}: {amount} dust")

        else:
            print("❌ Insufficient funds for pipeline")

        final_balance = self.get_balance(self.financial_identity)
        print(f"Final balance: {final_balance} dust")

    def show_enhanced_logs(self):
        """Display enhanced log analysis."""
        print(f"\n=== Enhanced Log Analysis for {self.agent_id} ===")

        # Categorize logs
        categories = {}
        economic_events = []

        for log_entry in self.captured_logs:
            category = log_entry['category']
            categories[category] = categories.get(category, 0) + 1

            if log_entry['level'] == 'ECONOMIC':
                economic_events.append(log_entry)

        print(f"Total log entries: {len(self.captured_logs)}")
        print("Log categories:")
        for category, count in categories.items():
            print(f"  {category}: {count}")

        # Economic event analysis
        if economic_events:
            print(f"\nEconomic events analysis:")
            transaction_types = {}
            total_value = 0

            for event in economic_events:
                if 'data' in event and isinstance(event['data'], dict):
                    event_data = event['data']
                    if 'type' in event_data:
                        tx_type = event_data['type']
                        transaction_types[tx_type] = transaction_types.get(
                            tx_type, 0) + 1

                        if 'amount' in event_data:
                            amount = event_data['amount']
                            if tx_type == 'credit':
                                total_value += amount
                            elif tx_type in ['debit', 'debit_overdraft']:
                                total_value -= amount

            print(f"Transaction types:")
            for tx_type, count in transaction_types.items():
                print(f"  {tx_type}: {count}")
            print(f"Net economic value: {total_value} dust")


async def run_demo():
    """Run the enhanced economic system demonstration."""
    print("=== Enhanced Plantangenet Economic System Demo ===\n")

    # Create an enhanced agent
    agent = EconAgent("enhanced_001")

    # Initialize the agent
    await agent.initialize()

    # Demonstrate cost preview and negotiation
    await agent.demonstrate_cost_preview_and_negotiation()

    # Demonstrate revenue and distribution
    await agent.demonstrate_revenue_and_distribution()

    # Demonstrate complex economic scenario
    await agent.demonstrate_complex_economic_scenario()

    # Show enhanced log analysis
    agent.show_enhanced_logs()

    print(f"\n=== Enhanced Demo Complete ===")
    print(f"Agent: {agent.agent_id}")
    print(f"Final balance: {agent.get_balance(agent.financial_identity)} dust")
    print(f"Total log entries: {len(agent.captured_logs)}")

    return agent


if __name__ == "__main__":
    asyncio.run(run_demo())
