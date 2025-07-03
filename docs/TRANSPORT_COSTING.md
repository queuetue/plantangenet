# Transport Operations Costing

This document describes the integration of cost-aware transport operations (publish/subscribe) with the Banker agent system in Plantangenet.

## Overview

Transport operations (publishing messages and subscribing to topics) now integrate with the Banker agent system to provide:

- **Cost estimation** for publish/subscribe operations
- **Transaction previews** with negotiation options
- **Auditable transaction tracking** for all transport activities
- **Dust-based pricing** with topic complexity and data size factors
- **Graceful fallback** to free operations when using the default NullBanker

## Key Components

### TransportOperationsManager

The main interface for cost-aware transport operations:

```python
from plantangenet.transport_operations import TransportOperationsManager
from plantangenet.session import Session

session = Session(session_id="my_session")
transport_manager = TransportOperationsManager(session)
```

### Core Methods

#### Cost Estimation and Previews

```python
# Get cost preview for publishing
preview = transport_manager.get_publish_preview("topic.name", "message data")
print(f"Publishing will cost: {preview['quote']['dust_cost']} Dust")

# Get cost preview for subscribing
sub_preview = transport_manager.get_subscribe_preview("topic.pattern.*")
print(f"Subscribing will cost: {sub_preview['quote']['dust_cost']} Dust")
```

#### Cost-Aware Operations

```python
# Publish with automatic cost deduction
result = await transport_manager.publish_with_cost(
    "events.user.login", 
    "user123 logged in", 
    transport_client
)
print(f"Published successfully, cost: {result['cost_paid']} Dust")

# Subscribe with automatic cost deduction
result = await transport_manager.subscribe_with_cost(
    "events.system.*", 
    message_handler, 
    transport_client
)
print(f"Subscribed successfully, cost: {result['cost_paid']} Dust")
```

## Cost Factors

Transport operation costs are calculated based on several factors:

### Base Costs

Defined in the cost base under `api_costs`:

```json
{
  "api_costs": {
    "transport.publish": 5,
    "transport.subscribe": 10
  }
}
```

### Topic Complexity

Topics are analyzed for complexity, which affects the final cost:

- **Segments**: Each dot-separated segment adds to complexity
- **Wildcards**: `*` adds +2 complexity, `>` adds +3 complexity
- **Examples**:
  - `simple` → complexity 1
  - `domain.service.action` → complexity 3
  - `domain.*.action` → complexity 5 (3 + 2)
  - `domain.>` → complexity 5 (2 + 3)

### Data Size (Publishing Only)

For publish operations, the size of the data affects cost:

- Calculated based on UTF-8 encoded size
- Supports strings, bytes, and JSON-serializable dictionaries
- Larger messages cost more Dust

### Final Cost Calculation

```
final_cost = base_cost + (complexity * 10) + data_size_factor
```

## Integration with Banker Agents

### Setting Up Transport Costs

```python
# Create session with banker
session = Session(session_id="demo")
banker = create_vanilla_banker_agent(initial_balance=100)
session.add_banker_agent(banker)

# Add transport cost base
transport_costs = {
    "name": "Transport Pricing",
    "api_costs": {
        "transport.publish": 5,
        "transport.subscribe": 10
    }
}
banker.add_cost_base_data("transport", transport_costs)
```

### Using with Real Transport Clients

The TransportOperationsManager works with any transport client that implements the expected interface:

```python
# Example with NATS
from plantangenet.mixins.nats import NATSMixin

class MyTransportClient(NATSMixin):
    # ... NATS implementation
    pass

client = MyTransportClient()
await client.setup_transport(["nats://localhost:4222"])

# Use with cost management
transport_manager = TransportOperationsManager(session)
result = await transport_manager.publish_with_cost(
    "my.topic", 
    "my data", 
    client
)
```

## Backward Compatibility

The system maintains backward compatibility:

- **NullBanker**: Default banker that allows all operations at 0 cost
- **Graceful degradation**: Operations proceed even without explicit banker setup
- **Existing code**: Works unchanged with new cost tracking as an optional layer

## Error Handling

### Insufficient Funds

```python
result = await transport_manager.publish_with_cost("topic", "data", client)
if not result["success"]:
    print(f"Operation failed: {result['error']}")
    # Message was NOT published
```

### Cost Negotiation

```python
# Get preview with options
preview = transport_manager.get_publish_preview("topic", data)
if preview["quote"]["dust_cost"] > budget:
    print("Too expensive, skipping operation")
else:
    # Proceed with selected cost
    result = await transport_manager.publish_with_cost(
        "topic", data, client, 
        selected_cost=preview["quote"]["dust_cost"]
    )
```

## Transaction Tracking

All transport operations are tracked in the session's transaction history:

```python
# View transaction history
history = session.get_transaction_history()
for transaction in history:
    print(f"Transaction {transaction['transaction_id']}: "
          f"{transaction['type']} {transaction['amount']} Dust "
          f"for {transaction['reason']}")
```

## Example: Complete Integration

```python
import asyncio
from plantangenet.session import Session
from plantangenet.vanilla_banker import create_vanilla_banker_agent
from plantangenet.transport_operations import TransportOperationsManager

async def transport_with_costing():
    # Setup
    session = Session(session_id="transport_demo")
    banker = create_vanilla_banker_agent(initial_balance=100)
    session.add_banker_agent(banker)
    
    # Add transport costs
    banker.add_cost_base_data("transport", {
        "api_costs": {
            "transport.publish": 5,
            "transport.subscribe": 3
        }
    })
    
    # Create manager and mock client
    transport_manager = TransportOperationsManager(session)
    # ... setup real transport client ...
    
    # Get cost estimate
    preview = transport_manager.get_publish_preview("events.user", "data")
    print(f"Will cost: {preview['quote']['dust_cost']} Dust")
    
    # Publish with cost tracking
    result = await transport_manager.publish_with_cost(
        "events.user", "user data", transport_client
    )
    
    print(f"Published: {result['success']}, Cost: {result['cost_paid']}")
    print(f"Balance: {session.get_dust_balance()} Dust")

asyncio.run(transport_with_costing())
```

## Testing

Comprehensive test suite available in `test_transport_operations.py`:

```bash
# Run transport operation tests
python -m pytest test_transport_operations.py -v
```

## Profit, Fees, and Distributions

All transport operation costs, agent profits, and banker's fees are now handled via the generalized distribution system. This means:

- The Banker can automatically insert its own cut (fee) into any transport transaction.
- Agents can define custom profit strategies and distribute surplus or bonuses using the same mechanism.
- All distributions are explicit, policy-driven, and fully auditable in the transaction history.

See also: [Banker Agent Integration](BANKER_AGENT_INTEGRATION.md), [Agent vs API Cost Model](AGENT_VS_API_COSTS.md), and [Dust Documentation](DUST.md) for more details and examples.

## See Also

- [Banker Agent Integration](BANKER_AGENT_INTEGRATION.md): Core banker concepts
- [Cost Base System](COST_BASE.md): Cost base format and negotiation
- [Session Documentation](SESSION.md): Session and agent management
- [Transport Mixins](../python/plantangenet/mixins/transport.py): Base transport interfaces
