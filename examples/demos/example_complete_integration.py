#!/usr/bin/env python3
"""
Complete Integration Demo: Session + Banker Agents + Storage Operations
Demonstrates the full stack of policy-driven, auditable Dust pricing.
"""

import tempfile
import zipfile
import json
from plantangenet.session import Session
from plantangenet.vanilla_banker import create_vanilla_banker_agent, VanillaBankerAgent
from plantangenet.storage_operations import StorageOperationsManager
from plantangenet.cost_base import CostBaseVerifier
from plantangenet.dust import Banker
from typing import Any


# Mock Omni for testing storage operations
class MockOmni:
    """Mock omni object for testing storage operations."""

    _omni_all_fields = ["name", "value", "created_at",
                        "updated_at"]  # Mock class attribute

    def __init__(self, omni_id: str = "test_omni_001"):
        self._omni_id = omni_id
        self._dirty_fields = {"name": "Test Object", "value": 42}

    def get_dirty_fields(self):
        return self._dirty_fields

    async def save_to_storage(self, incremental: bool = True):
        """Mock save that always succeeds."""
        print(
            f"   [Mock] Saving omni {self._omni_id} (incremental: {incremental})")
        return True


def create_test_cost_base() -> str:
    """Create a test cost base package."""
    manifest = {
        "name": "IntegrationTestPackage",
        "version": "1.0.0",
        "description": "Complete integration test cost base",
        "api_costs": {
            "save_object": 20,
            "load_object": 8,
            "delete_object": 5,
            "save_per_field": 30,
            "bulk_save": 12,
            "self_maintained": 6
        },
        "signature": "VALID_TEST_SIGNATURE"
    }

    with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp_file:
        with zipfile.ZipFile(tmp_file.name, 'w') as zf:
            zf.writestr('manifest.json', json.dumps(manifest, indent=2))
        return tmp_file.name


def demonstrate_complete_integration():
    """Demonstrate the complete integration stack."""

    print("=== Complete Integration Demo ===")
    print("Session → Banker Agents → Storage Operations → Cost Bases\n")

    # 1. Create session
    print("1. Setting up Session...")
    session = Session(session_id="integration_demo")
    print(f"   Session ID: {session.session_id}")
    print(
        f"   Initial balance: {session.get_dust_balance()} dust (NullBanker)")

    # 2. Create multiple banker agents with different specializations
    print("\n2. Creating specialized Banker Agents...")

    # Bypass signature verification for demo
    original_verify = CostBaseVerifier.verify_signature
    CostBaseVerifier.verify_signature = lambda self, manifest: True

    # Primary banker with cost base
    cost_base_path = create_test_cost_base()
    primary_banker = create_vanilla_banker_agent(
        initial_balance=200,
        cost_base_paths=[cost_base_path],
        namespace="primary_financial"
    )
    primary_banker._ocean__nickname = "primary-banker"

    # Secondary banker (could have different cost bases in real usage)
    secondary_banker = create_vanilla_banker_agent(
        initial_balance=50,
        cost_base_paths=None,
        namespace="secondary_financial"
    )
    secondary_banker._ocean__nickname = "backup-banker"

    # Add bankers to session
    session.add_banker_agent(primary_banker)  # This becomes the primary banker
    session.add_agent(secondary_banker)  # This is just an additional agent

    print(
        f"   Primary banker: {primary_banker.name} (Balance: {primary_banker.get_balance()})")
    print(
        f"   Secondary banker: {secondary_banker.name} (Balance: {secondary_banker.get_balance()})")
    print(
        f"   Session balance (via primary): {session.get_dust_balance()} dust")

    # 3. Set up storage operations manager
    print("\n3. Setting up Storage Operations Manager...")
    storage_manager = StorageOperationsManager(session)

    # 4. Create mock omni objects
    print("\n4. Creating mock Omni objects...")
    omni1 = MockOmni("user_profile_001")
    omni2 = MockOmni("game_state_002")

    print(
        f"   Created: {omni1._omni_id} with {len(omni1.get_dirty_fields())} dirty fields")
    print(
        f"   Created: {omni2._omni_id} with {len(omni2.get_dirty_fields())} dirty fields")

    # 5. Demonstrate cost estimation
    print("\n5. Cost Estimation...")
    estimate1 = session.get_cost_estimate(
        "save_object", {"fields": ["name", "email"]})
    estimate2 = session.get_cost_estimate(
        "load_object", {"omni_id": "some_object"})

    print(
        f"   Save estimate: {estimate1['dust_cost'] if estimate1 else 'N/A'} dust")
    print(
        f"   Load estimate: {estimate2['dust_cost'] if estimate2 else 'N/A'} dust")

    # 6. Demonstrate storage operations with previews
    print("\n6. Storage Operations with Cost Integration...")

    # Get save preview
    preview = storage_manager.get_save_preview(omni1, incremental=True)
    if preview:
        print("   Save preview available - showing negotiation options")

    # Perform save with cost
    import asyncio

    async def run_storage_operations():
        print("   Performing save operation...")
        result1 = await storage_manager.save_omni_with_cost(omni1, incremental=True, show_preview=True)
        print(f"   Save result: {result1}")

        print("\n   Performing another save operation...")
        result2 = await storage_manager.save_omni_with_cost(omni2, incremental=False, show_preview=True)
        print(f"   Save result: {result2}")

        return result1, result2

    results = asyncio.run(run_storage_operations())

    # 7. Show transaction history across the system
    print("\n7. Transaction History...")
    history = session.get_transaction_history()
    print(f"   Total transactions: {len(history)}")
    for i, tx in enumerate(history, 1):
        print(
            f"   {i}. {tx['type']} - {tx['amount']} dust - {tx['reason']} (ID: {tx['transaction_id']})")

    # 8. Show final system state
    print("\n8. Final System State...")
    print(f"   Session balance: {session.get_dust_balance()} dust")
    print(f"   Total agents: {len(session.agents)}")
    print(f"   Banker agents: {len(session.get_banker_agents())}")

    for banker in session.get_banker_agents():
        banker_cast = banker if isinstance(banker, Banker) else None
        if banker_cast and hasattr(banker_cast, 'get_balance'):
            print(f"     - {banker.name}: {banker_cast.get_balance()} dust")
            # Check if it's specifically a VanillaBankerAgent for cost base info
            if isinstance(banker, VanillaBankerAgent):
                cost_bases = banker.get_cost_base_info()
                for name, info in cost_bases.items():
                    print(
                        f"       Cost base: {info['name']} v{info['version']}")

    # 9. Demonstrate agent updates
    print("\n9. Agent Lifecycle Management...")
    print("   Running agent updates...")

    async def run_agent_updates():
        await session.update_agents()
        return True

    asyncio.run(run_agent_updates())
    print("   ✓ All agents updated successfully")

    # Restore original method
    CostBaseVerifier.verify_signature = original_verify

    print("\n=== Integration Demo Complete ===")
    print("✓ Session managed multiple banker agents")
    print("✓ Storage operations used banker for cost negotiation")
    print("✓ Cost bases provided policy-driven pricing")
    print("✓ All transactions were auditable and transparent")
    print("✓ Agent lifecycle management worked correctly")


if __name__ == "__main__":
    demonstrate_complete_integration()
