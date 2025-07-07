#!/usr/bin/env python3
"""
Example demonstrating financial access control in Plantangenet.

This example shows how policy-based access control works for financial
information (balance and transaction history) in the banker system.
"""

from plantangenet.dust import (
    FinancialIdentity, FinancialAccessRequest, FinancialPolicy,
    PermissiveFinancialPolicy, BankerMixin
)
from plantangenet.vanilla_banker import VanillaBankerAgent


def create_test_identities():
    """Create test identities with different roles and permissions."""

    # Regular user
    user = FinancialIdentity(
        user_id="alice_trader",
        session_id="session_001",
        roles=["user"]
    )

    # Admin user
    admin = FinancialIdentity(
        user_id="bob_admin",
        session_id="session_002",
        roles=["admin", "user"]
    )

    # Financial auditor
    auditor = FinancialIdentity(
        user_id="carol_auditor",
        session_id="session_003",
        roles=["financial_auditor"]
    )

    # Compliance officer
    compliance = FinancialIdentity(
        user_id="dave_compliance",
        session_id="session_004",
        roles=["compliance"]
    )

    # Special user with permissions
    special = FinancialIdentity(
        user_id="eve_special",
        session_id="session_005",
        roles=["user"],
        permissions=["read_any_balance"]
    )

    return {
        "user": user,
        "admin": admin,
        "auditor": auditor,
        "compliance": compliance,
        "special": special
    }


def demonstrate_balance_access(banker, identities):
    """Demonstrate balance access control."""
    print("=== Balance Access Control Demo ===")

    for role, identity in identities.items():
        print(f"\n{role.upper()} ({identity.user_id}):")

        # Self-access (should always work)
        try:
            balance = banker.get_balance(identity=identity)
            print(f"  ✓ Own balance: {balance} Dust")
        except PermissionError as e:
            print(f"  ✗ Own balance: {e}")

        # Cross-account access (depends on role)
        try:
            balance = banker.get_balance(
                identity=identity, target_account="alice_trader")
            print(f"  ✓ Alice's balance: {balance} Dust")
        except PermissionError as e:
            print(f"  ✗ Alice's balance: Access denied")


def demonstrate_transaction_history_access(banker, identities):
    """Demonstrate transaction history access control."""
    print("\n=== Transaction History Access Control Demo ===")

    for role, identity in identities.items():
        print(f"\n{role.upper()} ({identity.user_id}):")

        # Self-access (should always work)
        try:
            history = banker.get_transaction_history(identity=identity)
            print(f"  ✓ Own history: {len(history)} transactions")
            if history:
                print(
                    f"    Latest: {history[-1]['type']} of {history[-1]['amount']} Dust")
        except PermissionError as e:
            print(f"  ✗ Own history: {e}")

        # Cross-account access (depends on role)
        try:
            history = banker.get_transaction_history(
                identity=identity,
                target_account="alice_trader"
            )
            print(f"  ✓ Alice's history: {len(history)} transactions")

            # Show filtering effects
            if history:
                first_txn = history[0]
                if "reason" in first_txn:
                    print(f"    Full detail access: {first_txn['reason']}")
                else:
                    print(f"    Filtered access: sensitive details hidden")

        except PermissionError as e:
            print(f"  ✗ Alice's history: Access denied")


def demonstrate_policy_customization():
    """Demonstrate custom policy configuration."""
    print("\n=== Custom Policy Demo ===")

    # Create banker with default policy
    banker = VanillaBankerAgent(initial_balance=1000)
    banker.add_dust(500, "Initial funding")
    banker.deduct_dust(200, "Sample purchase")

    regular_user = FinancialIdentity(user_id="regular_user")

    print("1. Default Policy (Restrictive):")
    try:
        balance = banker.get_balance(
            identity=regular_user, target_account="other_user")
        print(f"   ✓ Cross-account balance: {balance}")
    except PermissionError:
        print("   ✗ Cross-account balance: Access denied")

    # Switch to permissive policy
    print("\n2. Permissive Policy:")
    banker.set_financial_policy(PermissiveFinancialPolicy())

    try:
        balance = banker.get_balance(
            identity=regular_user, target_account="other_user")
        print(f"   ✓ Cross-account balance: {balance}")
    except PermissionError:
        print("   ✗ Cross-account balance: Access denied")


def demonstrate_backward_compatibility():
    """Demonstrate that old code still works."""
    print("\n=== Backward Compatibility Demo ===")

    banker = VanillaBankerAgent(initial_balance=750)
    banker.add_dust(250, "Compatibility test")

    # Old way (no identity) should still work
    print(f"Balance (old API): {banker.get_balance()}")
    print(f"History length (old API): {len(banker.get_transaction_history())}")

    # New way should also work
    identity = FinancialIdentity(user_id="test_user")
    print(f"Balance (new API): {banker.get_balance(identity=identity)}")
    print(
        f"History length (new API): {len(banker.get_transaction_history(identity=identity))}")


def main():
    """Run the access control demonstration."""
    print("Financial Access Control Demo")
    print("============================")

    # Create a banker with some transaction history
    banker = VanillaBankerAgent(initial_balance=2000)

    # Add some transactions to make the demo interesting
    banker.add_dust(500, "Monthly allowance")
    banker.deduct_dust(300, "API usage")
    banker.deduct_dust(150, "Storage costs")
    banker.add_dust(100, "Refund")

    # Create test identities
    identities = create_test_identities()

    # Demonstrate access control
    demonstrate_balance_access(banker, identities)
    demonstrate_transaction_history_access(banker, identities)
    demonstrate_policy_customization()
    demonstrate_backward_compatibility()

    print("\n=== Summary ===")
    print("Access control features:")
    print("• Role-based access (admin, auditor, compliance)")
    print("• Permission-based access (explicit grants)")
    print("• Policy-based filtering (sensitive data protection)")
    print("• Backward compatibility (old code still works)")
    print("• Configurable policies (permissive vs restrictive)")


if __name__ == "__main__":
    main()
