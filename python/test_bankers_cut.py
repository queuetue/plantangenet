"""
Tests for banker's cut functionality - policy-driven fee system.
Now includes tests for the generalized distribution mechanism.
"""

import pytest
from plantangenet.banker import (
    FinancialIdentity, FeeStructure, FeePolicy, BankerMixin, NullBanker,
    Distributor, DistributionResult
)
from plantangenet.vanilla_banker import VanillaBankerAgent


class TestFeeStructure:
    """Test fee structure calculations."""

    def test_default_fee_structure(self):
        """Test default fee structure."""
        fee_structure = FeeStructure()

        # Default is no fees
        assert fee_structure.calculate_fee(100) == 0
        assert fee_structure.calculate_fee(1000) == 0

    def test_percentage_fee(self):
        """Test percentage-based fees."""
        fee_structure = FeeStructure(base_rate=0.05)  # 5%

        assert fee_structure.calculate_fee(100) == 5
        assert fee_structure.calculate_fee(1000) == 50

    def test_fixed_fee(self):
        """Test fixed fees."""
        fee_structure = FeeStructure(fixed_fee=10)

        assert fee_structure.calculate_fee(100) == 10
        assert fee_structure.calculate_fee(1000) == 10

    def test_combined_fees(self):
        """Test percentage + fixed fees."""
        fee_structure = FeeStructure(base_rate=0.02, fixed_fee=5)  # 2% + 5

        assert fee_structure.calculate_fee(100) == 7  # 2 + 5
        assert fee_structure.calculate_fee(1000) == 25  # 20 + 5

    def test_minimum_fee(self):
        """Test minimum fee enforcement."""
        fee_structure = FeeStructure(
            base_rate=0.01, minimum_fee=10)  # 1% with 10 min

        assert fee_structure.calculate_fee(100) == 10  # 1 < 10, so 10
        assert fee_structure.calculate_fee(2000) == 20  # 20 > 10, so 20

    def test_maximum_fee(self):
        """Test maximum fee enforcement."""
        fee_structure = FeeStructure(
            base_rate=0.1, maximum_fee=50)  # 10% with 50 max

        assert fee_structure.calculate_fee(100) == 10  # 10 < 50, so 10
        assert fee_structure.calculate_fee(1000) == 50  # 100 > 50, so 50

    def test_free_transactions(self):
        """Test free transaction allowances."""
        fee_structure = FeeStructure(
            base_rate=0.05,
            fixed_fee=5,
            free_transactions_per_period=2
        )

        # First two transactions are free
        assert fee_structure.calculate_fee(100, transaction_count=0) == 0
        assert fee_structure.calculate_fee(100, transaction_count=1) == 0

        # Third transaction has fees
        assert fee_structure.calculate_fee(
            100, transaction_count=2) == 10  # 5% + 5


class TestFeePolicy:
    """Test fee policy logic."""

    def test_default_identity_class(self):
        """Test default identity class assignment."""
        policy = FeePolicy()

        # No identity should get default
        assert policy.get_identity_class(None) == "default"

        # Basic identity should get default
        basic_identity = FinancialIdentity(user_id="test_user")
        assert policy.get_identity_class(basic_identity) == "default"

    def test_role_based_identity_classes(self):
        """Test role-based identity class assignment."""
        policy = FeePolicy()

        # Admin role
        admin_identity = FinancialIdentity(user_id="admin", roles=["admin"])
        assert policy.get_identity_class(admin_identity) == "admin"

        # VIP role
        vip_identity = FinancialIdentity(user_id="vip", roles=["vip"])
        assert policy.get_identity_class(vip_identity) == "vip"

        # Premium role
        premium_identity = FinancialIdentity(
            user_id="premium", roles=["premium"])
        assert policy.get_identity_class(premium_identity) == "premium"

        # System role
        system_identity = FinancialIdentity(user_id="system", roles=["system"])
        assert policy.get_identity_class(system_identity) == "system"

    def test_permission_based_identity_classes(self):
        """Test permission-based identity class assignment."""
        policy = FeePolicy()

        # Fee exempt permission -> admin class
        exempt_identity = FinancialIdentity(
            user_id="exempt",
            permissions=["fee_exempt"]
        )
        assert policy.get_identity_class(exempt_identity) == "admin"

        # Reduced fees permission -> premium class
        reduced_identity = FinancialIdentity(
            user_id="reduced",
            permissions=["reduced_fees"]
        )
        assert policy.get_identity_class(reduced_identity) == "premium"

    def test_fee_calculation_different_classes(self):
        """Test fee calculation for different identity classes."""
        policy = FeePolicy()

        # Default user (5% + 5 fixed, min 1)
        default_identity = FinancialIdentity(user_id="default")
        assert policy.calculate_fee(default_identity, 100) == 10  # 5 + 5

        # Premium user (2% + 2 fixed, min 1, 10 free)
        premium_identity = FinancialIdentity(
            user_id="premium", roles=["premium"])
        assert policy.calculate_fee(
            premium_identity, 100) == 0  # First transaction free

        # VIP user (1% + 1 fixed, min 0, 50 free)
        vip_identity = FinancialIdentity(user_id="vip", roles=["vip"])
        assert policy.calculate_fee(vip_identity, 100) == 0  # Free transaction

        # Admin user (0% + 0 fixed)
        admin_identity = FinancialIdentity(user_id="admin", roles=["admin"])
        assert policy.calculate_fee(admin_identity, 100) == 0  # Always free

    def test_transaction_counting(self):
        """Test transaction counting for free transaction limits."""
        policy = FeePolicy()

        premium_identity = FinancialIdentity(
            user_id="premium", roles=["premium"])

        # First 10 transactions should be free
        for i in range(10):
            fee = policy.calculate_fee(premium_identity, 100)
            assert fee == 0, f"Transaction {i} should be free"

        # 11th transaction should have fee
        fee = policy.calculate_fee(premium_identity, 100)
        assert fee == 4  # 2% + 2 fixed, min 1

    def test_custom_fee_structure(self):
        """Test setting custom fee structures."""
        policy = FeePolicy()

        # Define custom fee structure
        custom_fee = FeeStructure(base_rate=0.1, fixed_fee=20, minimum_fee=25)
        policy.set_fee_structure("custom", custom_fee)

        # Get fee structure back
        retrieved = policy.get_fee_structure("custom")
        assert retrieved.base_rate == 0.1
        assert retrieved.fixed_fee == 20
        assert retrieved.minimum_fee == 25


class TestBankerMixinWithFees:
    """Test BankerMixin with fee functionality."""

    def test_apply_bankers_cut_default_user(self):
        """Test banker's cut for default user."""
        banker = BankerMixin()
        banker._dust_balance = 1000

        default_identity = FinancialIdentity(user_id="test")
        result = banker.apply_bankers_cut(100, default_identity)

        assert result.success is True
        assert result.dust_charged == 10  # 5% + 5 fixed
        assert banker._dust_balance == 1010  # 1000 + 10 (banker gets the fee)

    def test_apply_bankers_cut_admin_user(self):
        """Test banker's cut for admin user (should be free)."""
        banker = BankerMixin()
        banker._dust_balance = 1000

        admin_identity = FinancialIdentity(user_id="admin", roles=["admin"])
        result = banker.apply_bankers_cut(100, admin_identity)

        assert result.success is True
        assert result.dust_charged == 0  # Admin fees are free
        assert banker._dust_balance == 1000  # No change

    def test_apply_bankers_cut_premium_user(self):
        """Test banker's cut for premium user."""
        banker = BankerMixin()
        banker._dust_balance = 1000

        premium_identity = FinancialIdentity(
            user_id="premium", roles=["premium"])

        # First transaction should be free
        result = banker.apply_bankers_cut(100, premium_identity)
        assert result.success is True
        assert result.dust_charged == 0

        # Subsequent transactions after free limit should have fees
        # Simulate multiple transactions to exceed free limit
        for i in range(10):  # Use up free transactions
            banker.apply_bankers_cut(100, premium_identity)

        # This should now charge a fee
        result = banker.apply_bankers_cut(100, premium_identity)
        assert result.success is True
        assert result.dust_charged == 4  # 2% + 2 fixed, min 1

    def test_get_fee_estimate(self):
        """Test fee estimation."""
        banker = BankerMixin()

        default_identity = FinancialIdentity(user_id="test")
        estimate = banker.get_fee_estimate(100, default_identity)

        assert estimate["fee_amount"] == 10
        assert estimate["identity_class"] == "default"
        assert estimate["fee_structure"]["base_rate"] == 0.05
        assert estimate["fee_structure"]["fixed_fee"] == 5


class TestNullBankerWithFees:
    """Test NullBanker fee functionality."""

    def test_null_banker_no_fees(self):
        """Test that NullBanker applies no fees."""
        banker = NullBanker()

        default_identity = FinancialIdentity(user_id="test")
        result = banker.apply_bankers_cut(100, default_identity)

        assert result.success is True
        assert result.dust_charged == 0
        assert "NullBanker" in result.message


class TestVanillaBankerWithFees:
    """Test VanillaBankerAgent with fee functionality."""

    def test_commit_transaction_with_fees(self):
        """Test transaction commit includes banker's cut."""
        banker = VanillaBankerAgent(initial_balance=1000)

        # Add basic cost base
        banker.add_cost_base_data("test", {
            "name": "Test Costs",
            "api_costs": {"test_action": 50}
        })

        default_identity = FinancialIdentity(user_id="test")

        result = banker.commit_transaction(
            "test_action",
            {},
            identity=default_identity
        )

        assert result.success is True
        # Should charge base cost (50) + fee (5% of 50 + 5 fixed = 7.5 + 5 = 12.5 = 12)
        expected_total = 50 + 7  # 50 base + 7 fee (2.5 + 5, rounded to 7)
        assert result.dust_charged == expected_total
        # User's balance is reduced by base cost, banker gets the fee
        assert banker.get_balance() == 950 + 7  # 1000 - 50 + 7 = 957

    def test_commit_transaction_insufficient_funds_with_fees(self):
        """Test transaction fails when insufficient funds including fees."""
        banker = VanillaBankerAgent(
            initial_balance=50)  # Just enough for base cost

        banker.add_cost_base_data("test", {
            "name": "Test Costs",
            "api_costs": {"test_action": 50}
        })

        default_identity = FinancialIdentity(user_id="test")

        result = banker.commit_transaction(
            "test_action",
            {},
            identity=default_identity
        )

        # Should fail because 50 balance < 50 base + ~7 fee
        assert result.success is False
        assert "Insufficient funds" in result.message
        assert "fee:" in result.message  # Should mention the fee in error


class TestDistributor:
    """Test distributor calculations."""

    def test_percentage_distributor(self):
        """Test percentage-based distribution."""
        distributor = Distributor(
            account_id="test",
            distribution_type="percentage",
            amount=0.1,  # 10%
            reason="test distribution"
        )

        assert distributor.calculate_distribution(1000, 1000) == 100
        assert distributor.calculate_distribution(500, 500) == 50

    def test_fixed_distributor(self):
        """Test fixed amount distribution."""
        distributor = Distributor(
            account_id="test",
            distribution_type="fixed",
            amount=50,
            reason="test distribution"
        )

        assert distributor.calculate_distribution(1000, 1000) == 50
        assert distributor.calculate_distribution(100, 100) == 50

    def test_remainder_distributor(self):
        """Test remainder distribution."""
        distributor = Distributor(
            account_id="test",
            distribution_type="remainder",
            amount=0,
            reason="test distribution"
        )

        assert distributor.calculate_distribution(1000, 800) == 800
        assert distributor.calculate_distribution(1000, 200) == 200

    def test_minimum_maximum_constraints(self):
        """Test minimum and maximum constraints."""
        distributor = Distributor(
            account_id="test",
            distribution_type="percentage",
            amount=0.01,  # 1%
            reason="test distribution",
            minimum=10,
            maximum=50
        )

        # Below minimum
        assert distributor.calculate_distribution(
            500, 500) == 10  # 1% of 500 = 5, but min is 10

        # Above maximum
        assert distributor.calculate_distribution(
            10000, 10000) == 50  # 1% of 10000 = 100, but max is 50

        # Within range
        assert distributor.calculate_distribution(
            3000, 3000) == 30  # 1% of 3000 = 30

    def test_remaining_amount_constraint(self):
        """Test that distribution can't exceed remaining amount."""
        distributor = Distributor(
            account_id="test",
            distribution_type="fixed",
            amount=100,
            reason="test distribution"
        )

        # Can't distribute more than remaining
        assert distributor.calculate_distribution(1000, 50) == 50


class TestDistributionSystem:
    """Test the generalized distribution system."""

    def test_simple_banker_cut_distribution(self):
        """Test distribution with only banker's cut."""
        banker = BankerMixin()
        banker._dust_balance = 1000

        default_identity = FinancialIdentity(user_id="test")
        result = banker.distribute_amount(100, [], default_identity)

        assert result.success is True
        assert len(result.distributions) == 1  # Only banker's cut
        assert result.distributions[0]["account_id"] == "banker"
        assert result.distributions[0]["amount"] == 10  # 5% + 5 fixed
        assert banker.get_balance() == 1010  # Banker gets the fee

    def test_multiple_distributors(self):
        """Test distribution to multiple accounts."""
        banker = BankerMixin()
        banker._dust_balance = 1000

        distributors = [
            Distributor("agent", "percentage", 0.1, "agent commission"),  # 10%
            Distributor("charity", "fixed", 25, "charity donation"),
            Distributor("remainder", "remainder", 0, "remainder pool")
        ]

        default_identity = FinancialIdentity(user_id="test")
        result = banker.distribute_amount(1000, distributors, default_identity)

        assert result.success is True
        assert len(result.distributions) == 4  # 3 + banker's cut

        # Check banker's cut (first)
        banker_dist = result.distributions[0]
        assert banker_dist["account_id"] == "banker"
        assert banker_dist["amount"] == 55  # 5% of 1000 + 5 fixed

        # Check other distributions
        agent_dist = next(
            d for d in result.distributions if d["account_id"] == "agent")
        assert agent_dist["amount"] == 100  # 10% of 1000

        charity_dist = next(
            d for d in result.distributions if d["account_id"] == "charity")
        assert charity_dist["amount"] == 25  # Fixed 25

        remainder_dist = next(
            d for d in result.distributions if d["account_id"] == "remainder")
        # Remainder = 1000 - 55 (banker) - 100 (agent) - 25 (charity) = 820
        assert remainder_dist["amount"] == 820

        # Banker balance should increase by banker's cut
        assert banker.get_balance() == 1055

    def test_distribution_without_banker_cut(self):
        """Test distribution with banker's cut disabled."""
        banker = BankerMixin()
        banker._dust_balance = 1000

        distributors = [
            Distributor("refund", "percentage", 0.9, "user refund"),  # 90%
            Distributor("tip", "remainder", 0, "tip pool")
        ]

        default_identity = FinancialIdentity(user_id="test")
        result = banker.distribute_amount(
            500, distributors, default_identity, include_banker_cut=False)

        assert result.success is True
        assert len(result.distributions) == 2  # No banker's cut

        # Check distributions
        refund_dist = next(
            d for d in result.distributions if d["account_id"] == "refund")
        assert refund_dist["amount"] == 450  # 90% of 500

        tip_dist = next(
            d for d in result.distributions if d["account_id"] == "tip")
        assert tip_dist["amount"] == 50  # Remainder

        # Banker balance unchanged (no banker's cut)
        assert banker.get_balance() == 1000

    def test_admin_user_no_banker_cut(self):
        """Test that admin users don't pay banker's cut."""
        banker = BankerMixin()
        banker._dust_balance = 1000

        admin_identity = FinancialIdentity(user_id="admin", roles=["admin"])

        distributors = [
            Distributor("service", "percentage", 0.1, "service fee")
        ]

        result = banker.distribute_amount(1000, distributors, admin_identity)

        # Should only have the service distributor, no banker's cut
        service_distributions = [
            d for d in result.distributions if d["account_id"] != "banker"]
        banker_distributions = [
            d for d in result.distributions if d["account_id"] == "banker"]

        assert len(service_distributions) == 1
        assert len(banker_distributions) == 0  # Admin doesn't pay banker's cut
        assert banker.get_balance() == 1000  # No change to banker balance

    def test_create_banker_distributor(self):
        """Test creating banker distributor from fee policy."""
        policy = FeePolicy()

        # Test default user
        default_identity = FinancialIdentity(user_id="test")
        distributor = policy.create_banker_distributor(default_identity, 100)

        assert distributor is not None
        assert distributor.account_id == "banker"
        assert distributor.distribution_type == "fixed"
        assert distributor.amount == 10.0  # 5% + 5 fixed
        assert "default rate" in distributor.reason

        # Test admin user (should get None)
        admin_identity = FinancialIdentity(user_id="admin", roles=["admin"])
        distributor = policy.create_banker_distributor(admin_identity, 100)

        assert distributor is None  # Admin pays no fees

    def test_dust_overflow_to_system_account(self):
        """Test that overflow is redirected to system account when max_dust is exceeded."""
        banker = BankerMixin()
        banker._dust_balance = 0

        # Distributor with max_dust=100, but we try to distribute 200
        distributor = Distributor(
            account_id="limited_account",
            distribution_type="fixed",
            amount=200,
            reason="test overflow"
        )
        distributor.max_dust = 100  # Only allow up to 100

        # System identity to receive overflow
        system_identity = FinancialIdentity(
            user_id="system_account", roles=["system"])

        result = banker.distribute_amount(
            200, [distributor], identity=None, include_banker_cut=False, system_identity=system_identity
        )

        # Should be two distributions: one to limited_account (100), one to system_account (100)
        limited_dist = next(
            d for d in result.distributions if d["account_id"] == "limited_account")
        system_dist = next(
            d for d in result.distributions if d["account_id"] == "system_account")

        assert limited_dist["amount"] == 100
        assert system_dist["amount"] == 100
        assert result.remaining_amount == 0
        assert "overflow" in system_dist["reason"].lower()
        assert result.success is True


class TestNullBankerDistribution:
    """Test NullBanker distribution functionality."""

    def test_null_banker_no_distributions(self):
        """Test that NullBanker applies no distributions."""
        banker = NullBanker()

        distributors = [
            Distributor("test", "percentage", 0.5, "test distribution")
        ]

        default_identity = FinancialIdentity(user_id="test")
        result = banker.distribute_amount(100, distributors, default_identity)

        assert result.success is True
        assert len(result.distributions) == 0
        assert result.remaining_amount == 100
        assert "NullBanker" in result.message


class TestVanillaBankerDistribution:
    """Test VanillaBankerAgent with distribution functionality."""

    def test_commit_transaction_with_distributions(self):
        """Test transaction commit includes distributions."""
        banker = VanillaBankerAgent(initial_balance=1000)

        # Add basic cost base
        banker.add_cost_base_data("test", {
            "name": "Test Costs",
            "api_costs": {"test_action": 50}
        })

        default_identity = FinancialIdentity(user_id="test")

        result = banker.commit_transaction(
            "test_action",
            {},
            identity=default_identity
        )

        assert result.success is True
        # Should charge base cost (50) + banker's cut (7: 2.5% + 5 fixed)
        expected_total = 50 + 7
        assert result.dust_charged == expected_total
        # User's balance is reduced by base cost, banker gets the fee
        assert banker.get_balance() == 950 + 7  # 1000 - 50 + 7 = 957


if __name__ == "__main__":
    pytest.main([__file__])
