"""
Financial and fee policies for the banker module.
"""

from typing import Dict, Any, Optional, List
from .econ_types import FinancialIdentity, FinancialAccessRequest, FeeStructure, Distributor


class FinancialPolicy:
    """Policy engine for financial access control."""

    def can_access_balance(self, request: FinancialAccessRequest) -> bool:
        """Check if requestor can access balance information."""
        # Self-access always allowed
        if not request.target_account or request.target_account == request.requestor.user_id:
            return True

        # Admin role can access any balance
        if request.requestor.roles and "admin" in request.requestor.roles:
            return True

        # Financial auditor can read balances
        if request.requestor.roles and "financial_auditor" in request.requestor.roles:
            return True

        # Explicit permission
        if request.requestor.permissions and "read_any_balance" in request.requestor.permissions:
            return True

        return False

    def can_access_transaction_history(self, request: FinancialAccessRequest) -> bool:
        """Check if requestor can access transaction history."""
        # Self-access always allowed
        if not request.target_account or request.target_account == request.requestor.user_id:
            return True

        # Admin role can access any history
        if request.requestor.roles and "admin" in request.requestor.roles:
            return True

        # Financial auditor can read transaction history
        if request.requestor.roles and "financial_auditor" in request.requestor.roles:
            return True

        # Compliance officer can read for audit purposes
        if request.requestor.roles and "compliance" in request.requestor.roles:
            return True

        # Explicit permission
        if request.requestor.permissions and "read_any_transactions" in request.requestor.permissions:
            return True

        return False

    def filter_transaction_history(self, request: FinancialAccessRequest,
                                   transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter transaction history based on requestor permissions."""
        # Full access roles get everything
        if (request.requestor.roles and
            ("admin" in request.requestor.roles or
             "financial_auditor" in request.requestor.roles)):
            return transactions

        # Self-access gets full own history
        if not request.target_account or request.target_account == request.requestor.user_id:
            return transactions

        # Compliance officers get limited sensitive data
        if request.requestor.roles and "compliance" in request.requestor.roles:
            filtered = []
            for txn in transactions:
                # Remove sensitive details but keep audit trail
                filtered_txn = {
                    "transaction_id": txn["transaction_id"],
                    "type": txn["type"],
                    "amount": txn["amount"],
                    "timestamp": txn.get("timestamp"),
                    "success": txn["success"]
                    # Remove reason, balance details for privacy
                }
                filtered.append(filtered_txn)
            return filtered

        return []  # Default: no access


class PermissiveFinancialPolicy(FinancialPolicy):
    """Policy that allows access to everything - useful for testing and NullBanker."""

    def can_access_balance(self, request: FinancialAccessRequest) -> bool:
        """Allow all balance access."""
        return True

    def can_access_transaction_history(self, request: FinancialAccessRequest) -> bool:
        """Allow all transaction history access."""
        return True


class FeePolicy:
    """Policy engine for determining fees based on identity classes."""

    def __init__(self):
        """Initialize with default fee structures."""
        self.fee_structures: Dict[str, FeeStructure] = {
            # Default fee structure for unknown identities
            "default": FeeStructure(
                base_rate=0.05,  # 5% fee
                fixed_fee=5,     # 5 dust per transaction
                minimum_fee=1    # At least 1 dust
            ),

            # Premium users get lower fees
            "premium": FeeStructure(
                base_rate=0.02,  # 2% fee
                fixed_fee=2,     # 2 dust per transaction
                minimum_fee=1,   # At least 1 dust
                free_transactions_per_period=10  # 10 free transactions daily
            ),

            # VIP users get even better rates
            "vip": FeeStructure(
                base_rate=0.01,  # 1% fee
                fixed_fee=1,     # 1 dust per transaction
                minimum_fee=0,   # Can be free
                free_transactions_per_period=50  # 50 free transactions daily
            ),

            # System agents get minimal fees
            "system": FeeStructure(
                base_rate=0.001,  # 0.1% fee
                fixed_fee=0,     # No fixed fee
                minimum_fee=0,   # Can be free
                free_transactions_per_period=1000  # Essentially unlimited
            ),

            # Admin operations are free
            "admin": FeeStructure(
                base_rate=0.0,   # No percentage fee
                fixed_fee=0,     # No fixed fee
                minimum_fee=0    # Free
            )
        }

        # Track transaction counts for free transaction limits
        self.transaction_counts: Dict[str, Dict[str, int]] = {}

    def get_identity_class(self, identity: Optional[FinancialIdentity]) -> str:
        """
        Determine the identity class for fee calculation.

        Args:
            identity: The financial identity

        Returns:
            Identity class string
        """
        if not identity:
            return "default"

        # Check roles for special classes
        if identity.roles and "admin" in identity.roles:
            return "admin"
        if identity.roles and "system" in identity.roles:
            return "system"
        if identity.roles and "vip" in identity.roles:
            return "vip"
        if identity.roles and "premium" in identity.roles:
            return "premium"

        # Check permissions for special access
        if identity.permissions and "fee_exempt" in identity.permissions:
            return "admin"
        if identity.permissions and "reduced_fees" in identity.permissions:
            return "premium"

        return "default"

    def calculate_fee(self, identity: Optional[FinancialIdentity],
                      base_amount: int) -> int:
        """
        Calculate the banker's cut for a transaction.

        Args:
            identity: The financial identity making the transaction
            base_amount: The base transaction amount

        Returns:
            Fee amount in dust
        """
        if not identity:
            identity_class = "default"
            user_key = "anonymous"
        else:
            identity_class = self.get_identity_class(identity)
            user_key = f"{identity.user_id}:{identity_class}"

        # Get fee structure
        fee_structure = self.fee_structures.get(
            identity_class, self.fee_structures["default"])

        # Get transaction count for this user/period
        # For simplicity, we'll track daily counts
        period_key = "today"  # In real implementation, this would be actual date
        if user_key not in self.transaction_counts:
            self.transaction_counts[user_key] = {}
        if period_key not in self.transaction_counts[user_key]:
            self.transaction_counts[user_key][period_key] = 0

        transaction_count = self.transaction_counts[user_key][period_key]

        # Calculate fee
        fee = fee_structure.calculate_fee(base_amount, transaction_count)

        # Update transaction count
        self.transaction_counts[user_key][period_key] += 1

        return fee

    def create_banker_distributor(self, identity: Optional[FinancialIdentity],
                                  base_amount: int) -> Optional[Distributor]:
        """
        Create a distributor for the banker's cut.
        Returns None if the fee is zero (e.g., admin or free transaction).
        """
        fee_amount = self.calculate_fee(identity, base_amount)
        if fee_amount == 0:
            return None
        identity_class = self.get_identity_class(
            identity) if identity else "default"
        return Distributor(
            account_id="banker",
            distribution_type="fixed",
            amount=float(fee_amount),
            reason=f"banker's cut ({identity_class} rate)",
            minimum=0
        )

    def set_fee_structure(self, identity_class: str, fee_structure: FeeStructure):
        """Set the fee structure for an identity class."""
        self.fee_structures[identity_class] = fee_structure

    def get_fee_structure(self, identity_class: str) -> FeeStructure:
        """Get the fee structure for an identity class."""
        return self.fee_structures.get(identity_class, self.fee_structures["default"])
