# Agent vs API Cost Model

This document describes the advanced economic model in Plantangenet where agents can declare their own prices, charge clients, and are separately charged for actual API usage, with the Banker tracking discrepancies for system oversight.

## Overview

The Agent vs API Cost Model introduces several key concepts:

1. **Agent-Declared Pricing**: Agents can set their own prices and charge clients
2. **API Actual Costs**: The system charges agents based on actual resource usage (~100 Dust baseline)
3. **Cost Discrepancy Tracking**: The Banker records differences between agent pricing and API costs
4. **Overdraft Policy**: Operations can proceed even with insufficient funds (policy decision)
5. **Agent Profit/Loss**: Agents can build up or lose Dust based on their pricing strategies

## Key Components

### Realistic Cost Base

Operations now have realistic baseline costs reflecting actual system resource usage:

```python
{
  "api_costs": {
    "transport.publish": 120,     # ~100 Dust baseline + complexity
    "transport.subscribe": 100,   
    "save_object": 150,          
    "save_per_field": 25,        
    "bulk_save": 80,             # Bulk discount
    "self_maintained": 200       # Premium service
  }
}
```

### Enhanced Transaction Results

```python
@dataclass
class TransactionResult:
    success: bool
    dust_charged: int
    message: str
    transaction_id: Optional[str] = None
    # New fields for agent/API cost tracking
    agent_declared_cost: Optional[int] = None
    api_actual_cost: Optional[int] = None
    cost_discrepancy: Optional[int] = None
```

### Agent API Charging

```python
# Charge agent for actual API usage after they've charged their client
api_result = banker.charge_agent_for_api_usage(
    "transport.publish", 
    {"topic": "events.user", "data_size": 100},
    agent_declared_cost=200  # What the agent charged their client
)

print(f"API charged agent: {api_result.api_actual_cost} Dust")
print(f"Agent profit/loss: {api_result.cost_discrepancy} Dust")
```

## Agent Profit Strategies

### Example: Profitable Transport Agent

```python
class ProfitableTransportAgent:
    def __init__(self, session: Session, markup_percentage: float = 50.0):
        self.session = session
        self.markup_percentage = markup_percentage
        self.transport_manager = TransportOperationsManager(session)
        
    async def publish_for_client(self, topic: str, data, transport_client, client_id: str):
        # Get API cost estimate
        api_preview = self.transport_manager.get_publish_preview(topic, data)
        api_cost = api_preview["quote"]["dust_cost"]
        
        # Calculate our price (markup)
        our_price = int(api_cost * (1 + self.markup_percentage / 100))
        
        # "Charge" the client
        self.session._banker.add_dust(our_price, f"Client payment from {client_id}")
        
        # Perform operation and pay API costs
        result = await self.transport_manager.publish_with_cost(topic, data, transport_client)
        
        if result["success"]:
            # Pay actual API cost
            api_charge = self.session._banker.charge_agent_for_api_usage(
                "transport.publish", 
                {"topic": topic, "data_size": len(str(data))},
                our_price
            )
            
            return {
                "success": True,
                "client_charged": our_price,
                "api_cost": api_charge.api_actual_cost,
                "profit": api_charge.cost_discrepancy
            }
```

### Profit Optimization Strategies

Agents can optimize profits through:

1. **Efficient Compression**: Reduce data size to lower API costs while maintaining client pricing
2. **Bulk Operations**: Use bulk APIs when available for better rates
3. **Smart Routing**: Choose cheaper transport paths
4. **Caching**: Avoid redundant API calls
5. **Quality-Based Pricing**: Charge premium for guaranteed delivery, standard for best-effort

## Overdraft Policy

### Policy Configuration

```python
class BankerMixin:
    def __init__(self):
        self._allow_overdraft = True      # Allow operations with insufficient funds
        self._overdraft_limit = -10000    # Maximum negative balance
```

### Overdraft Behavior

```python
# Operation proceeds even with insufficient funds
result = banker.deduct_dust(200, "expensive operation")
# With balance of 50 Dust:
# - Operation succeeds
# - Balance becomes -150 Dust
# - Transaction marked as "debit_overdraft"
# - System continues operating
```

Operations are allowed to proceed with insufficient funds, creating negative balances up to the overdraft limit. This prevents the economic system from blocking legitimate operations while still providing financial oversight.

## Cost Discrepancy Tracking

### Automatic Tracking

The Banker automatically tracks discrepancies between agent pricing and API costs:

```python
# Agent charges client 200 Dust, API costs 120 Dust
api_result = banker.charge_agent_for_api_usage("action", params, 200)

# Creates discrepancy record:
{
    "transaction_id": "disc_000001",
    "type": "discrepancy_record", 
    "amount": 80,  # profit
    "reason": "Cost discrepancy for action: agent=200, api=120",
    "metadata": {
        "discrepancy_type": "profit",
        "agent_declared_cost": 200,
        "api_actual_cost": 120,
        "discrepancy": 80
    }
}
```

### System Oversight

Discrepancy records provide system oversight capabilities:

- **Audit Trail**: Complete record of agent pricing vs actual costs
- **Performance Monitoring**: Track which agents are profitable/unprofitable
- **Policy Enforcement**: Identify excessive markups or concerning patterns
- **Economic Health**: Monitor overall system economic dynamics

## Profit, Fees, and the Distribution System

With the new distribution mechanism, agents and the Banker can both participate in profit-taking and surplus distribution:

- **Banker's Cut**: The Banker can insert its own fee into any transaction, based on policy and identity class.
- **Agent Profit**: Agents can declare their own prices, charge clients, and use the distribution system to allocate profit, bonuses, or surplus to any set of recipients.
- **Custom Distributions**: Any Dust (profit, surplus, or refund) can be distributed to multiple accounts, pools, or burned, according to explicit, auditable policy.

All distributions are tracked in the transaction history, supporting full auditability and system oversight.

See also: [Banker Agent Integration](BANKER_AGENT_INTEGRATION.md), [Dust Documentation](DUST.md), and [Transport Costing](TRANSPORT_COSTING.md).

## Integration Examples

### Basic Agent Setup

```python
# Create session with realistic costs
session = Session(session_id="agent_demo")
banker = create_vanilla_banker_agent(initial_balance=1000)
session.add_banker_agent(banker)

# Agent automatically gets realistic default costs
# No additional cost base needed
```

### Agent with Custom Pricing

```python
class OptimizedAgent:
    async def efficient_publish(self, topic, data, client):
        # Compress data to reduce API costs
        compressed_data = self.compress(data)
        
        # Still charge client for original data size
        original_cost = self.estimate_cost(topic, data)
        client_price = int(original_cost * 1.3)  # 30% markup
        
        # Add client payment
        self.session._banker.add_dust(client_price, f"Client payment")
        
        # Publish compressed data (lower API cost)
        result = await self.transport_manager.publish_with_cost(
            topic, compressed_data, transport_client
        )
        
        # Pay actual API cost for compressed data
        api_charge = self.session._banker.charge_agent_for_api_usage(
            "transport.publish", 
            {"topic": topic, "data_size": len(compressed_data)},
            client_price
        )
        
        # Profit from compression efficiency
        return api_charge.cost_discrepancy
```

### Transaction Analysis

```python
# Analyze agent performance
history = session.get_transaction_history()

profits = []
losses = []

for transaction in history:
    if transaction["type"] == "discrepancy_record":
        metadata = transaction.get("metadata", {})
        if metadata.get("discrepancy_type") == "profit":
            profits.append(metadata["discrepancy"])
        else:
            losses.append(abs(metadata["discrepancy"]))

total_profit = sum(profits) - sum(losses)
print(f"Net agent profit: {total_profit} Dust")
```

## Policy Implications

### Economic Freedom vs Control

- **Freedom**: Agents can set prices, compete, and profit from efficiency
- **Oversight**: All transactions are tracked and auditable
- **Flexibility**: Overdraft policy prevents economic gridlock
- **Accountability**: Clear separation between agent pricing and system costs

### System Sustainability

- **Resource Pricing**: API costs reflect actual system resource usage
- **Economic Incentives**: Agents rewarded for efficiency, penalized for waste
- **Market Dynamics**: Competition drives pricing optimization
- **System Health**: Tracking prevents economic exploitation

## See Also

- [Transport Operations Costing](TRANSPORT_COSTING.md): Transport-specific cost implementation
- [Banker Agent Integration](BANKER_AGENT_INTEGRATION.md): Core banker concepts
- [Cost Base System](COST_BASE.md): Cost base format and pricing
- [Session Documentation](SESSION.md): Session and agent management
