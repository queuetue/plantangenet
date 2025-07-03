# Plantangenet Banker: Economic Authority, Logging, and Distribution

## Overview

The **Banker** is the economic authority in Plantangenet. It is responsible for all Dust (currency) operations, pricing, negotiation, logging, and distribution within a session or reference frame. The Banker is the *single source of economic truth*—all Dust movement, pricing, and policy enforcement must go through it.

---

## Core Responsibilities

- **Pricing & Quoting:** Estimate and preview the Dust cost of any action or resource usage.
- **Negotiation:** Offer package deals, dynamic pricing, and user-facing transaction previews.
- **Transaction Commitment:** Deduct Dust, log all debits/credits, and enforce economic policy.
- **Distribution:** Split Dust among agents, the Banker (fees), and other pools, with explicit, auditable logic.
- **Audit & Logging:** Record every economic event in a structured, queryable log for audit and analysis.
- **Access Control:** Enforce who can spend, receive, or view Dust, using pluggable policy modules.
- **Extensibility:** Support custom economic policies, currencies, and negotiation strategies via modular design.

---

## Banker Protocol: API & Contract

A Banker agent must implement the following methods (see `banker.py` and `banker/mixins.py`):

### Cost Estimation
- `get_cost_estimate(action, params)`
  - Returns a best-guess price for an action, with options if available.

### Negotiation
- `negotiate_transaction(action, params)`
  - Returns a set of possible deals, previews, or warnings for the user.

### Transaction Commitment
- `commit_transaction(action, params, selected_cost=None)`
  - Deducts Dust, logs the transaction, and returns a result object.

### Balance Inquiry
- `get_balance(identity=None, target_account=None)`
  - Returns the current Dust balance for the session or agent, with access control.

### History/Audit
- `get_transaction_history(identity=None, target_account=None, filters=None)`
  - Returns a log of all debits, credits, and transaction metadata, with filtering and access control.

### Distribution
- `distribute_amount(amount, distributors, identity=None, include_banker_cut=True, system_identity=None)`
  - Distributes Dust to recipients (including the Banker for fees), with explicit, auditable splits. Always includes a banker's cut entry if requested, even for zero-fee cases.

---

## Economic Logging & Guarantees

- **Every transaction (debit, credit, distribution, fee, refund) is logged** with timestamp, transaction ID, type, amount, accounts, reason, and result.
- **All logs are structured** for ingestion by analysis tools and external loggers.
- **Zero-fee (free) operations are always recorded**—the Banker logs every action, even if no Dust is charged or distributed.
- **Auditability is guaranteed:** The log is the canonical record for all economic activity.

---

## Distribution, Fees, and Zero-Fee Operations

- The Banker supports a policy-driven distribution system for all Dust flows.
- **Fees (banker's cut) are always explicit:**
  - If a fee is zero, a dummy entry is still included in the distribution result for auditability.
- **Distributions can use fixed, percentage, or remainder-based splits.**
- **Overflow handling:** If a recipient cannot accept the full amount (e.g., max_dust reached), overflow is redirected to a system account if provided.
- **All distribution logic is testable and auditable.**

---

## Testability & Best Practices

- **All Banker APIs are robust and testable.**
- **Tests must cover:**
  - Fee/distribution logic (including zero-fee cases)
  - Transaction counting and logging
  - Access control and policy enforcement
  - Integration with session and transport layers
- **Best Practices:**
  - Only the Banker mutates Dust balances or records economic events.
  - All economic operations (pricing, negotiation, payment, refund) go through the Banker.
  - Use specialized Bankers for different economic policies or domains.
  - Leverage the audit log for transparency and debugging.

---

## Example Usage

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

## Migration & Compatibility Notes

- The Banker logic is now modularized: see `banker/` for `types.py`, `policies.py`, `banker.py`, `mixins.py`, and `null_banker.py`.
- All imports and code references should use the new module structure.
- The API for distribution/fee reporting is now explicit: always includes a banker's cut entry if requested, even for zero-fee cases.
- All tests and demos should be updated to use the new APIs and structure.

---

## See Also

- [Session Documentation](SESSION.md): How Bankers fit into the session/agent lifecycle
- [Dust/Economics](DUST.md): Philosophy and design of Dust as a currency
- [Cost Base System](COST_BASE.md): How Bankers use cost bases to price actions
- [Policy System](POLICY.md): Economic policy and access control
- [Agents and Drifts](AGENTS.md): Agent hierarchy and distributed/federated economic models

---

**In summary:**

> The Banker is the economic authority for a session or frame. All pricing, negotiation, and Dust movement must go through the Banker, ensuring a single, auditable, and extensible source of economic truth in Plantangenet.
