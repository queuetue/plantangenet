#!/usr/bin/env python3
"""
Example script demonstrating the generalized distribution mechanism.
Shows how the banker's cut integrates with other distributions.
"""

from plantangenet.dust import (
    FinancialIdentity, Distributor, BankerMixin, NullBanker
)
from plantangenet.vanilla_banker import VanillaBankerAgent


def main():
    """Demonstrate the distribution system."""
    print("=== Plantangenet Distribution System Demo ===\n")

    # Create identities with different classes
    basic_user = FinancialIdentity(user_id="basic_user")
    premium_user = FinancialIdentity(user_id="premium_user", roles=["premium"])
    vip_user = FinancialIdentity(user_id="vip_user", roles=["vip"])
    admin_user = FinancialIdentity(user_id="admin_user", roles=["admin"])

    # Create a banker with initial balance
    banker = VanillaBankerAgent(initial_balance=10000)

    print("1. Testing Basic Distribution (Banker's Cut Only)")
    print("=" * 50)

    # Test basic banker's cut for different user types
    test_amount = 1000

    for user in [basic_user, premium_user, vip_user, admin_user]:
        print(f"\nUser: {user.user_id} (roles: {user.roles or ['none']})")

        # Get fee estimate
        fee_estimate = banker.get_fee_estimate(test_amount, user)
        print(
            f"Fee estimate: {fee_estimate['fee_amount']} dust ({fee_estimate['identity_class']} rate)")

        # Apply distribution (just banker's cut)
        initial_balance = banker.get_balance()
        result = banker.distribute_amount(test_amount, [], user)

        print(f"Distribution result: {result.message}")
        print(
            f"Banker balance change: {banker.get_balance() - initial_balance}")

        for dist in result.distributions:
            print(
                f"  → {dist['account_id']}: {dist['amount']} dust ({dist['reason']})")

    print("\n\n2. Testing Complex Distribution (Multiple Recipients)")
    print("=" * 55)

    # Create complex distributors
    distributors = [
        Distributor(
            account_id="agent_commission",
            distribution_type="percentage",
            amount=0.1,  # 10% commission
            reason="agent commission",
            minimum=10
        ),
        Distributor(
            account_id="referral_bonus",
            distribution_type="fixed",
            amount=50,  # Fixed 50 dust bonus
            reason="referral bonus"
        ),
        Distributor(
            account_id="charity_fund",
            distribution_type="percentage",
            amount=0.02,  # 2% to charity
            reason="charity donation",
            maximum=25  # Cap at 25 dust
        ),
        Distributor(
            account_id="remainder_pool",
            distribution_type="remainder",
            amount=0,  # Takes whatever is left
            reason="remainder distribution"
        )
    ]

    print(
        f"\nDistributing {test_amount} dust for premium user with complex rules:")
    print("Distributors:")
    for i, dist in enumerate(distributors, 1):
        if dist.distribution_type == "percentage":
            print(f"  {i}. {dist.account_id}: {dist.amount*100}% ({dist.reason})")
        elif dist.distribution_type == "fixed":
            print(f"  {i}. {dist.account_id}: {dist.amount} dust ({dist.reason})")
        else:
            print(f"  {i}. {dist.account_id}: remainder ({dist.reason})")

    initial_balance = banker.get_balance()
    result = banker.distribute_amount(test_amount, distributors, premium_user)

    print(f"\nDistribution completed: {result.message}")
    print(f"Banker balance change: {banker.get_balance() - initial_balance}")
    print(f"Remaining amount: {result.remaining_amount}")

    print("\nDetailed distributions:")
    total_distributed = 0
    for dist in result.distributions:
        print(
            f"  → {dist['account_id']}: {dist['amount']} dust ({dist['reason']})")
        total_distributed += dist['amount']

    print(f"\nTotal distributed: {total_distributed} dust")

    print("\n\n3. Testing Agent Unused Dust Distribution")
    print("=" * 48)

    # Simulate agent returning unused dust with distribution
    unused_dust = 500
    agent_distributors = [
        Distributor(
            account_id="efficiency_bonus",
            distribution_type="percentage",
            amount=0.05,  # 5% efficiency bonus
            reason="efficiency bonus for unused dust"
        ),
        Distributor(
            account_id="user_refund",
            distribution_type="remainder",
            amount=0,
            reason="unused dust refund to user"
        )
    ]

    print(f"\nAgent returning {unused_dust} unused dust:")
    print("Distribution rules:")
    for i, dist in enumerate(agent_distributors, 1):
        if dist.distribution_type == "percentage":
            print(f"  {i}. {dist.account_id}: {dist.amount*100}% ({dist.reason})")
        else:
            print(f"  {i}. {dist.account_id}: remainder ({dist.reason})")

    initial_balance = banker.get_balance()
    result = banker.distribute_amount(
        unused_dust, agent_distributors, vip_user, include_banker_cut=False)

    print(f"\nDistribution completed: {result.message}")
    print(f"Banker balance change: {banker.get_balance() - initial_balance}")

    print("\nDetailed distributions:")
    for dist in result.distributions:
        print(
            f"  → {dist['account_id']}: {dist['amount']} dust ({dist['reason']})")

    print("\n\n4. Testing NullBanker (No Distributions)")
    print("=" * 45)

    null_banker = NullBanker()
    result = null_banker.distribute_amount(
        test_amount, distributors, basic_user)

    print(f"NullBanker distribution: {result.message}")
    print(f"Distributions: {len(result.distributions)}")
    print(f"Remaining amount: {result.remaining_amount}")

    print("\n=== Demo Complete ===")


if __name__ == "__main__":
    main()
