#!/usr/bin/env python3
"""
Example of Session with Banker Agent integration.
Demonstrates the new agent-based financial management.
"""

import tempfile
import zipfile
import json
from plantangenet.session import Session
from ..agent import VanillaBankerAgent, create_vanilla_banker_agent
from ..banker import Banker


def create_test_cost_base() -> str:
    """Create a test cost base package."""
    manifest = {
        "name": "SessionTestPackage",
        "version": "1.0.0",
        "description": "Test cost base for session integration",
        "api_costs": {
            "save_object": 15,
            "load_object": 5,
            "delete_object": 3,
            "save_per_field": 25,
            "bulk_save": 8,
            "self_maintained": 4
        },
        "signature": "VALID_TEST_SIGNATURE"
    }

    with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp_file:
        with zipfile.ZipFile(tmp_file.name, 'w') as zf:
            zf.writestr('manifest.json', json.dumps(manifest, indent=2))
        return tmp_file.name


def demonstrate_session_banker_integration():
    """Demonstrate Session with Banker Agent integration."""

    print("=== Session + Banker Agent Integration Demo ===\n")

    # 1. Create a session
    print("1. Creating session...")
    session = Session(session_id="demo_session")
    print(f"   Session ID: {session.session_id}")
    print(
        f"   Initial balance: {session.get_dust_balance()} dust (from NullBanker)")

    # 2. Create and add a VanillaBanker agent
    print("\n2. Creating and adding VanillaBanker agent...")
    # Start with a banker without cost bases for this demo
    banker_agent = create_vanilla_banker_agent(
        initial_balance=150,
        cost_base_paths=None,  # No cost bases for this demo
        namespace="financial_services"
    )

    print(f"   Banker Agent ID: {banker_agent.id}")
    print(f"   Banker Agent Name: {banker_agent.name}")
    print(f"   Banker capabilities: {banker_agent.capabilities}")

    # Add a cost base later (after creation)
    print("   Loading cost base...")
    cost_base_path = create_test_cost_base()
    try:
        # For demo purposes, let's skip the signature verification by patching
        from plantangenet.cost_base import CostBaseVerifier
        original_verify = CostBaseVerifier.verify_signature
        CostBaseVerifier.verify_signature = lambda self, manifest: True

        banker_agent.load_cost_base(cost_base_path, "demo_package")
        print("   ✓ Cost base loaded successfully (signature check bypassed for demo)")

        # Restore original method
        CostBaseVerifier.verify_signature = original_verify
    except Exception as e:
        print(f"   ✗ Failed to load cost base: {e}")
        print("   Continuing with NullBanker behavior...")

    # 3. Add banker to session
    session.add_banker_agent(banker_agent)
    print(f"   Session now has {len(session.agents)} agents")
    print(
        f"   New balance: {session.get_dust_balance()} dust (from VanillaBanker)")

    # 4. Test cost estimation through session
    print("\n3. Testing cost estimation through session...")
    estimate = session.get_cost_estimate(
        "save_object", {"fields": ["name", "email"]})
    print(f"   Cost estimate: {estimate}")

    # 5. Test transaction negotiation
    print("\n4. Testing transaction negotiation...")
    negotiation = session.negotiate_transaction(
        "save_object", {"fields": ["name", "email", "age"]})
    if negotiation:
        print(f"   Negotiation successful!")
        print(f"   Quote ID: {negotiation['quote_id']}")
        print(f"   Cost base: {negotiation['cost_base']}")
        # Note: In a real app, you'd format the preview nicely
        print(f"   Preview available: {negotiation['preview'] is not None}")

    # 6. Test transaction commitment
    print("\n5. Testing transaction commitment...")
    balance_before = session.get_dust_balance()
    result = session.commit_transaction(
        "save_object", {"fields": ["name", "email"]}, selected_cost=15)
    balance_after = session.get_dust_balance()

    print(f"   Transaction result: {result}")
    print(f"   Balance before: {balance_before} dust")
    print(f"   Balance after: {balance_after} dust")

    # 7. Test transaction history
    print("\n6. Transaction history...")
    history = session.get_transaction_history()
    for i, tx in enumerate(history[-3:], 1):  # Show last 3 transactions
        print(f"   {i}. {tx['type']} - {tx['amount']} dust - {tx['reason']}")

    # 8. Show agent management
    print("\n7. Agent management...")
    print(f"   Total agents: {len(session.agents)}")
    banker_agents = session.get_banker_agents()
    print(f"   Banker agents: {len(banker_agents)}")
    for banker in banker_agents:
        banker_cast = banker if isinstance(banker, Banker) else None
        if banker_cast:
            print(
                f"     - {banker.name} ({banker.short_id}) - Balance: {banker_cast.get_balance()}")
        else:
            print(f"     - {banker.name} ({banker.short_id}) - (not a banker)")

    # 9. Test agent updates
    print("\n8. Testing agent updates...")
    print("   Running agent updates...")
    import asyncio
    asyncio.run(session.update_agents())
    print("   Agent updates completed")

    print(f"\n=== Final State ===")
    print(f"Session balance: {session.get_dust_balance()} dust")
    print(f"Transaction count: {len(session.get_transaction_history())}")
    print(f"Active agents: {[agent.name for agent in session.agents]}")


if __name__ == "__main__":
    demonstrate_session_banker_integration()
