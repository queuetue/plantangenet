"""
Data types and structures for the banker module.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Protocol, runtime_checkable
from dataclasses import dataclass
import datetime


@dataclass
class TransactionResult:
    """Result of a financial transaction."""
    success: bool
    dust_charged: int
    message: str
    transaction_id: Optional[str] = None
    # New fields for agent/API cost tracking
    agent_declared_cost: Optional[int] = None
    api_actual_cost: Optional[int] = None
    cost_discrepancy: Optional[int] = None


@dataclass
class FinancialIdentity:
    """Identity information for financial access control."""
    user_id: str
    session_id: Optional[str] = None
    agent_id: Optional[str] = None
    roles: Optional[List[str]] = None
    permissions: Optional[List[str]] = None

    def __post_init__(self):
        if self.roles is None:
            self.roles = []
        if self.permissions is None:
            self.permissions = []


@dataclass
class FinancialAccessRequest:
    """Request for financial information access."""
    requestor: FinancialIdentity
    operation: str  # "get_balance", "get_history", "get_transactions"
    target_account: Optional[str] = None  # For cross-account access
    filters: Optional[Dict[str, Any]] = None  # For filtered access


@dataclass
class FeeStructure:
    """Defines fee rates and rules for a specific identity class."""
    base_rate: float = 0.0  # Base percentage fee (0.05 = 5%)
    fixed_fee: int = 0      # Fixed dust amount per transaction
    minimum_fee: int = 0    # Minimum fee to charge
    # Maximum fee to charge (None = no limit)
    maximum_fee: Optional[int] = None
    free_transactions_per_period: int = 0  # Number of free transactions
    period_type: str = "daily"  # "daily", "weekly", "monthly", "lifetime"

    def calculate_fee(self, base_amount: int, transaction_count: int = 0) -> int:
        """
        Calculate the fee for a transaction.

        Args:
            base_amount: The base transaction amount
            transaction_count: Number of transactions in current period

        Returns:
            Fee amount in dust
        """
        # Check if transaction is free
        if transaction_count < self.free_transactions_per_period:
            return 0

        # Calculate percentage fee
        percentage_fee = int(base_amount * self.base_rate)

        # Add fixed fee
        total_fee = percentage_fee + self.fixed_fee

        # Apply minimum
        total_fee = max(total_fee, self.minimum_fee)

        # Apply maximum if set
        if self.maximum_fee is not None:
            total_fee = min(total_fee, self.maximum_fee)

        return total_fee


@dataclass
class Distributor:
    """Defines a distribution recipient and calculation method."""
    account_id: str  # Account to receive distribution
    distribution_type: str  # "percentage", "fixed", "remainder"
    amount: float  # Percentage (0.0-1.0) or fixed amount
    reason: str  # Description of distribution
    minimum: int = 0  # Minimum amount to distribute
    maximum: Optional[int] = None  # Maximum amount to distribute

    def calculate_distribution(self, total_amount: int, remaining_amount: int) -> int:
        """
        Calculate the distribution amount.

        Args:
            total_amount: The total amount being distributed
            remaining_amount: Amount remaining after previous distributions

        Returns:
            Amount to distribute to this account
        """
        if self.distribution_type == "percentage":
            amount = int(total_amount * self.amount)
        elif self.distribution_type == "fixed":
            amount = int(self.amount)
        elif self.distribution_type == "remainder":
            amount = remaining_amount
        else:
            raise ValueError(
                f"Unknown distribution type: {self.distribution_type}")

        # Apply minimum
        amount = max(amount, self.minimum)

        # Apply maximum if set
        if self.maximum is not None:
            amount = min(amount, self.maximum)

        # Can't distribute more than remaining
        amount = min(amount, remaining_amount)

        return amount


@dataclass
class DistributionResult:
    """Result of a distribution operation."""
    success: bool
    total_amount: int
    # List of {account_id, amount, reason, transaction_id}
    distributions: List[Dict[str, Any]]
    remaining_amount: int
    message: str
