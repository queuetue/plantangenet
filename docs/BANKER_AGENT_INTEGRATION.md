# Banker Agent: Economic Authority and Accountability in Plantangenet

## What is a Banker?

A **Banker** is a specialized agent in Plantangenet responsible for all economic operations within a session or reference frame. The Banker is the *sole authority* for:

- Pricing and quoting resource usage (Dust cost estimation)
- Negotiating and previewing transactions
- Auditing and recording all Dust movements (debits/credits)
- Enforcing economic policy and limits ("who can spend what, and when")
- Providing a transparent, auditable ledger for all economic activity

**Bankers are not just helpers—they are the *source of truth* for all "lies about money" in a session.**

---

## Why Use a Banker Agent?

- **Separation of Concerns:** Sessions manage lifecycle, trust, and policy; Bankers manage all economic logic.
- **Auditability:** All Dust transactions are logged and can be reviewed or reconciled.
- **Negotiation:** Bankers can offer package deals, dynamic pricing, and user-facing transaction previews.
- **Extensibility:** Different banker agents can implement different economic policies, currencies, or negotiation strategies.
- **Federation:** In distributed/federated systems, Bankers can coordinate or compete, supporting complex economic topologies.

---

## Banker Protocol: The Contract

A Banker agent must implement the following core responsibilities:

- **Cost Estimation:**
  - `get_cost_estimate(action, params)`
  - Returns a best-guess price for an action, with options if available.
- **Negotiation:**
  - `negotiate_transaction(action, params)`
  - Returns a set of possible deals, previews, or warnings for the user.
- **Transaction Commitment:**
  - `commit_transaction(action, params, selected_cost=None)`
  - Deducts Dust, logs the transaction, and returns a result.
- **Balance Inquiry:**
  - `get_balance()`
  - Returns the current Dust balance for the session or agent.
- **History/Audit:**
  - `get_transaction_history()`
  - Returns a log of all debits, credits, and transaction metadata.

See the `Banker` protocol in `banker.py` for the full contract.

---

## How Does a Banker Fit Into the System?

- **Session delegates all economic operations to its Banker(s).**
- **Bankers are managed as first-class agents:**
  - Can be added/removed dynamically
  - Can be specialized (e.g., for games, streaming, infrastructure)
  - Can be replaced or federated for advanced scenarios
- **All Dust pricing, negotiation, and enforcement flows through the Banker.**
- **Other agents (e.g., bots, bridges) interact with the Banker for quotes, payments, and refunds.**

---

## Example: Using a Banker Agent

```python
# Create a session and add a banker agent
session = Session(session_id="user_session")
banker = create_vanilla_banker_agent(initial_balance=100, cost_base_paths=["./effects.zip"])
session.add_banker_agent(banker)

# Get a quote for an action
quote = session.get_cost_estimate("save_object", {"fields": ["name", "email"]})

# Negotiate a transaction (get options, preview)
negotiation = session.negotiate_transaction("save_object", {"fields": ["name", "email"]})

# Commit a transaction (spend Dust)
result = session.commit_transaction("save_object", {"fields": ["name", "email"]}, selected_cost=quote["dust_cost"])

# Check balance and history
balance = session.get_dust_balance()
history = session.get_transaction_history()
```

---

## Best Practices

- **One source of truth:** Only the Banker should mutate Dust balances or record economic events.
- **Session should never manage Dust directly.**
- **All economic operations (pricing, negotiation, payment, refund) should go through the Banker.**
- **Use specialized Bankers for different economic policies or domains.**
- **Leverage the audit log for transparency and debugging.**

---

## See Also

- [Session Documentation](SESSION.md): For how Bankers fit into the session/agent lifecycle
- [Dust/Economics](DUST.md): For the philosophy and design of Dust as a currency
- [Cost Base System](COST_BASE.md): For how Bankers use cost bases to price actions
- [Policy System](POLICY.md): For how economic policy and access control interact
- [Agents and Drifts](AGENTS.md): For the agent hierarchy and future distributed/federated economic models

---

**In summary:**

> The Banker is the economic authority for a session or frame. All pricing, negotiation, and Dust movement must go through the Banker, ensuring a single, auditable, and extensible source of economic truth in Plantangenet.
