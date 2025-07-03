"""
Tests for financial access control in the banker system.
"""

import pytest
from plantangenet.banker import (
    FinancialIdentity, FinancialAccessRequest, FinancialPolicy,
    PermissiveFinancialPolicy, BankerMixin, NullBanker
)
from plantangenet.vanilla_banker import VanillaBankerAgent


class TestFinancialIdentity:
    """Test financial identity functionality."""

    def test_basic_identity_creation(self):
        """Test creating basic financial identity."""
        identity = FinancialIdentity(user_id="user123")
        assert identity.user_id == "user123"
        assert identity.session_id is None
        assert identity.agent_id is None
        assert identity.roles == []
        assert identity.permissions == []

    def test_full_identity_creation(self):
        """Test creating full financial identity."""
        identity = FinancialIdentity(
            user_id="user123",
            session_id="session456",
            agent_id="agent789",
            roles=["admin", "auditor"],
            permissions=["read_any_balance"]
        )
        assert identity.user_id == "user123"
        assert identity.session_id == "session456"
        assert identity.agent_id == "agent789"
        assert "admin" in identity.roles
        assert "auditor" in identity.roles
        assert "read_any_balance" in identity.permissions


class TestFinancialPolicy:
    """Test financial policy functionality."""

    def test_self_access_balance(self):
        """Test that users can always access their own balance."""
        policy = FinancialPolicy()
        identity = FinancialIdentity(user_id="user123")
        request = FinancialAccessRequest(
            requestor=identity,
            operation="get_balance"
        )
        assert policy.can_access_balance(request)

    def test_admin_access_any_balance(self):
        """Test that admins can access any balance."""
        policy = FinancialPolicy()
        identity = FinancialIdentity(
            user_id="admin_user",
            roles=["admin"]
        )
        request = FinancialAccessRequest(
            requestor=identity,
            operation="get_balance",
            target_account="other_user"
        )
        assert policy.can_access_balance(request)

    def test_auditor_access_any_balance(self):
        """Test that financial auditors can access any balance."""
        policy = FinancialPolicy()
        identity = FinancialIdentity(
            user_id="auditor_user",
            roles=["financial_auditor"]
        )
        request = FinancialAccessRequest(
            requestor=identity,
            operation="get_balance",
            target_account="other_user"
        )
        assert policy.can_access_balance(request)

    def test_permission_based_balance_access(self):
        """Test that explicit permissions allow balance access."""
        policy = FinancialPolicy()
        identity = FinancialIdentity(
            user_id="special_user",
            permissions=["read_any_balance"]
        )
        request = FinancialAccessRequest(
            requestor=identity,
            operation="get_balance",
            target_account="other_user"
        )
        assert policy.can_access_balance(request)

    def test_denied_balance_access(self):
        """Test that unauthorized users are denied balance access."""
        policy = FinancialPolicy()
        identity = FinancialIdentity(user_id="regular_user")
        request = FinancialAccessRequest(
            requestor=identity,
            operation="get_balance",
            target_account="other_user"
        )
        assert not policy.can_access_balance(request)

    def test_self_access_transaction_history(self):
        """Test that users can access their own transaction history."""
        policy = FinancialPolicy()
        identity = FinancialIdentity(user_id="user123")
        request = FinancialAccessRequest(
            requestor=identity,
            operation="get_transaction_history"
        )
        assert policy.can_access_transaction_history(request)

    def test_compliance_access_transaction_history(self):
        """Test that compliance officers can access transaction history."""
        policy = FinancialPolicy()
        identity = FinancialIdentity(
            user_id="compliance_user",
            roles=["compliance"]
        )
        request = FinancialAccessRequest(
            requestor=identity,
            operation="get_transaction_history",
            target_account="other_user"
        )
        assert policy.can_access_transaction_history(request)

    def test_transaction_history_filtering(self):
        """Test transaction history filtering based on roles."""
        policy = FinancialPolicy()

        # Create sample transactions
        transactions = [
            {
                "transaction_id": "txn_001",
                "type": "debit",
                "amount": 100,
                "reason": "API call",
                "success": True,
                "timestamp": "2024-01-01T10:00:00Z",
                "balance_before": 500,
                "balance_after": 400
            },
            {
                "transaction_id": "txn_002",
                "type": "credit",
                "amount": 50,
                "reason": "Refund",
                "success": True,
                "timestamp": "2024-01-01T11:00:00Z",
                "balance_before": 400,
                "balance_after": 450
            }
        ]

        # Admin gets full access
        admin_identity = FinancialIdentity(
            user_id="admin_user",
            roles=["admin"]
        )
        admin_request = FinancialAccessRequest(
            requestor=admin_identity,
            operation="get_transaction_history",
            target_account="other_user"
        )
        admin_filtered = policy.filter_transaction_history(
            admin_request, transactions)
        assert len(admin_filtered) == 2
        # Full details preserved
        assert admin_filtered[0]["reason"] == "API call"

        # Compliance gets filtered access
        compliance_identity = FinancialIdentity(
            user_id="compliance_user",
            roles=["compliance"]
        )
        compliance_request = FinancialAccessRequest(
            requestor=compliance_identity,
            operation="get_transaction_history",
            target_account="other_user"
        )
        compliance_filtered = policy.filter_transaction_history(
            compliance_request, transactions)
        assert len(compliance_filtered) == 2
        # Sensitive details removed
        assert "reason" not in compliance_filtered[0]
        # Audit trail preserved
        assert "transaction_id" in compliance_filtered[0]

    def test_permissive_policy(self):
        """Test that permissive policy allows everything."""
        policy = PermissiveFinancialPolicy()
        identity = FinancialIdentity(user_id="regular_user")

        balance_request = FinancialAccessRequest(
            requestor=identity,
            operation="get_balance",
            target_account="other_user"
        )
        assert policy.can_access_balance(balance_request)

        history_request = FinancialAccessRequest(
            requestor=identity,
            operation="get_transaction_history",
            target_account="other_user"
        )
        assert policy.can_access_transaction_history(history_request)


class TestBankerAccessControl:
    """Test access control integration in banker implementations."""

    def test_banker_mixin_backward_compatibility(self):
        """Test that BankerMixin maintains backward compatibility."""
        banker = BankerMixin()
        banker.__init__()

        # Old interface should still work
        balance = banker.get_balance()
        assert balance == 0

        history = banker.get_transaction_history()
        assert history == []

    def test_banker_mixin_access_control(self):
        """Test that BankerMixin enforces access control with identity."""
        banker = BankerMixin()
        banker.__init__()
        banker._dust_balance = 1000

        # Self-access should work
        user_identity = FinancialIdentity(user_id="user123")
        balance = banker.get_balance(identity=user_identity)
        assert balance == 1000

        # Cross-account access should be denied for regular users
        with pytest.raises(PermissionError):
            banker.get_balance(identity=user_identity,
                               target_account="other_user")

        # Admin access should work
        admin_identity = FinancialIdentity(
            user_id="admin_user",
            roles=["admin"]
        )
        balance = banker.get_balance(
            identity=admin_identity, target_account="other_user")
        assert balance == 1000

    def test_transaction_history_access_control(self):
        """Test transaction history access control."""
        banker = BankerMixin()
        banker.__init__()

        # Add some test transactions
        banker.add_dust(100, "Initial deposit")
        banker.deduct_dust(50, "Test purchase")

        user_identity = FinancialIdentity(user_id="user123")

        # Self-access should work
        history = banker.get_transaction_history(identity=user_identity)
        assert len(history) == 2

        # Cross-account access should be denied
        with pytest.raises(PermissionError):
            banker.get_transaction_history(
                identity=user_identity,
                target_account="other_user"
            )

        # Compliance access should work but be filtered
        compliance_identity = FinancialIdentity(
            user_id="compliance_user",
            roles=["compliance"]
        )
        compliance_history = banker.get_transaction_history(
            identity=compliance_identity,
            target_account="user123"
        )
        assert len(compliance_history) == 2
        # Check that sensitive data is filtered
        assert "reason" not in compliance_history[0]

    def test_null_banker_permissive_access(self):
        """Test that NullBanker allows all access."""
        banker = NullBanker()

        user_identity = FinancialIdentity(user_id="user123")

        # Cross-account access should work in NullBanker
        balance = banker.get_balance(
            identity=user_identity, target_account="other_user")
        assert balance == 0

        history = banker.get_transaction_history(
            identity=user_identity,
            target_account="other_user"
        )
        assert history == []


class TestVanillaBankerAgent:
    """Test VanillaBankerAgent access control integration."""

    def test_vanilla_banker_access_control(self):
        """Test that VanillaBankerAgent supports access control."""
        banker = VanillaBankerAgent(initial_balance=1000)

        # Test policy configuration
        original_policy = banker.get_financial_policy()
        assert isinstance(original_policy, FinancialPolicy)

        # Set permissive policy
        permissive_policy = PermissiveFinancialPolicy()
        banker.set_financial_policy(permissive_policy)
        assert banker.get_financial_policy() is permissive_policy

        # Test access with new policy
        user_identity = FinancialIdentity(user_id="user123")
        balance = banker.get_balance(
            identity=user_identity, target_account="other_user")
        assert balance == 1000

    def test_vanilla_banker_maintains_functionality(self):
        """Test that access control doesn't break existing functionality."""
        banker = VanillaBankerAgent(initial_balance=500)

        # Standard operations should still work
        assert banker.can_afford(100)
        assert not banker.can_afford(1000)

        result = banker.add_dust(200, "Test credit")
        assert result.success
        assert banker.get_balance() == 700

        result = banker.deduct_dust(50, "Test debit")
        assert result.success
        assert banker.get_balance() == 650

        # Transaction history should work
        history = banker.get_transaction_history()
        assert len(history) == 2


if __name__ == "__main__":
    pytest.main([__file__])
