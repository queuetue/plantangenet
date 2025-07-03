#!/usr/bin/env python3
"""
Example usage of the cost base system.
Demonstrates creating a mod package, loading it, and using it for API negotiation.
"""

import json
import tempfile
import zipfile
from plantangenet.cost_base import (
    CostBaseLoader,
    CostBaseVerifier,
    ApiNegotiator,
    load_and_verify_cost_base,
    create_api_negotiator
)


class MockSession:
    """Mock session for demonstration."""

    def __init__(self, initial_dust: int = 100):
        self.dust_balance = initial_dust
        self.transaction_log = []

    def deduct_dust(self, amount: int):
        """Deduct dust from balance."""
        self.dust_balance -= amount
        self.transaction_log.append(f"Deducted {amount} dust")
        print(f"Deducted {amount} dust. New balance: {self.dust_balance}")


def create_example_mod_package() -> str:
    """Create an example mod package with cost base."""

    # Define the cost base for our example mod
    manifest = {
        "name": "StreamerEffects",
        "version": "1.0.0",
        "description": "Interactive effects for streamers",
        "api_costs": {
            "send_sticker": 3,
            "send_emoji": 2,
            "clear_screen": 5,
            "save_per_field": 35,
            "bulk_save": 10,
            "self_maintained": 5,
            "extend_stream": 20
        },
        "signature": "VALID_SIGNATURE"  # In production, this would be a real signature
    }

    # Create a temporary zip file
    with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp_file:
        with zipfile.ZipFile(tmp_file.name, 'w') as zf:
            # Add manifest
            zf.writestr('manifest.json', json.dumps(manifest, indent=2))

            # Add some example mod files
            zf.writestr(
                'README.md', '# StreamerEffects Mod\n\nInteractive effects for streamers.')
            zf.writestr(
                'effects.py', '# Python code for effects would go here')

        return tmp_file.name


def demonstrate_api_flow():
    """Demonstrate the complete API negotiation flow."""

    print("=== Cost Base System Demo ===\n")

    # 1. Create example mod package
    print("1. Creating example mod package...")
    package_path = create_example_mod_package()
    print(f"   Created package: {package_path}")

    # 2. Load and verify the cost base
    print("\n2. Loading and verifying cost base...")
    try:
        cost_base = load_and_verify_cost_base(package_path)
        print("   ✓ Cost base loaded and verified successfully")
        print(f"   Available actions: {list(cost_base['api_costs'].keys())}")
    except Exception as e:
        print(f"   ✗ Failed to load cost base: {e}")
        return

    # 3. Create API negotiator
    print("\n3. Creating API negotiator...")
    negotiator = ApiNegotiator(cost_base)

    # 4. Create mock session
    session = MockSession(initial_dust=50)
    print(f"   User session created with {session.dust_balance} dust")

    # 5. Demonstrate simple action quote/commit
    print("\n4. Demonstrating simple action (send_sticker)...")

    # Get quote
    quote = negotiator.get_quote(
        "send_sticker", {"sticker_id": "party_parrot"})
    print(f"   Quote: {quote}")

    # Commit action
    result = negotiator.commit_action(
        "send_sticker", {"sticker_id": "party_parrot"}, session, quote["dust_cost"])
    print(f"   Commit result: {result}")

    # 6. Demonstrate package deals
    print("\n5. Demonstrating package deals (save_object)...")

    # Get quote with multiple options
    quote = negotiator.get_quote(
        "save_object", {"fields": ["name", "age", "email"]})
    print(f"   Quote with options:")
    for option in quote["options"]:
        print(
            f"     - {option['type']}: {option['dust_cost']} dust ({option['description']})")

    # User chooses bulk save option
    bulk_option = next(
        opt for opt in quote["options"] if opt["type"] == "bulk_save")
    result = negotiator.commit_action("save_object", {"fields": [
                                      "name", "age", "email"]}, session, bulk_option["dust_cost"])
    print(f"   Committed bulk save: {result}")

    # 7. Demonstrate insufficient funds
    print("\n6. Demonstrating insufficient funds...")

    # Try an expensive action
    quote = negotiator.get_quote("extend_stream", {"minutes": 30})
    print(f"   Quote for extend_stream: {quote}")

    result = negotiator.commit_action(
        "extend_stream", {"minutes": 30}, session, quote["dust_cost"])
    print(f"   Commit result: {result}")

    # 8. Show final state
    print(f"\n7. Final session state:")
    print(f"   Dust balance: {session.dust_balance}")
    print(f"   Transaction log:")
    for log_entry in session.transaction_log:
        print(f"     - {log_entry}")


def demonstrate_security():
    """Demonstrate security features."""

    print("\n=== Security Demo ===\n")

    # Create a tampered package
    print("1. Creating tampered package...")
    tampered_manifest = {
        "api_costs": {
            "send_sticker": 999,  # Suspiciously high cost
        },
        "signature": "ORIGINAL_SIGNATURE"  # Wrong signature for tampered content
    }

    with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp_file:
        with zipfile.ZipFile(tmp_file.name, 'w') as zf:
            zf.writestr('manifest.json', json.dumps(tampered_manifest))
        tampered_path = tmp_file.name

    # Try to load tampered package
    print("2. Attempting to load tampered package...")
    loader = CostBaseLoader()
    manifest = loader.load_manifest(tampered_path)

    verifier = CostBaseVerifier()
    try:
        verifier.verify_signature(manifest)
        print("   ✗ Tampered package was accepted (this shouldn't happen!)")
    except Exception as e:
        print(f"   ✓ Tampered package rejected: {e}")


if __name__ == "__main__":
    demonstrate_api_flow()
    demonstrate_security()
