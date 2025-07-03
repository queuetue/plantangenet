"""
Banker Protocol and Mixins for Dust Management.
Handles all financial operations, cost negotiation, and transaction management.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Protocol, runtime_checkable
from dataclasses import dataclass


@dataclass
class TransactionResult:
    """Result of a financial transaction."""
    success: bool
    dust_charged: int
    message: str
    transaction_id: Optional[str] = None


@runtime_checkable
class Banker(Protocol):
    """
    Protocol for entities that handle dust transactions and cost negotiation.
    Responsible for all "lies about money" - pricing, negotiation, balances.
    """

    @abstractmethod
    def get_balance(self) -> int:
        """Get current dust balance."""
        ...

    @abstractmethod
    def can_afford(self, amount: int) -> bool:
        """Check if the balance can cover the amount."""
        ...

    @abstractmethod
    def deduct_dust(self, amount: int, reason: str) -> TransactionResult:
        """
        Deduct dust from balance.

        Args:
            amount: Amount to deduct
            reason: Reason for the transaction

        Returns:
            TransactionResult with success status
        """
        ...

    @abstractmethod
    def add_dust(self, amount: int, reason: str) -> TransactionResult:
        """
        Add dust to balance.

        Args:
            amount: Amount to add
            reason: Reason for the transaction

        Returns:
            TransactionResult with success status
        """
        ...

    @abstractmethod
    def get_cost_estimate(self, action: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Get cost estimate for an action.

        Args:
            action: The action to estimate
            params: Parameters for the action

        Returns:
            Cost estimate or None if action not supported
        """
        ...

    @abstractmethod
    def negotiate_transaction(self, action: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Negotiate a transaction with cost options.

        Args:
            action: The action to negotiate
            params: Parameters for the action

        Returns:
            Negotiation result with options or None if not supported
        """
        ...

    @abstractmethod
    def commit_transaction(self, action: str, params: Dict[str, Any],
                           selected_cost: Optional[int] = None) -> TransactionResult:
        """
        Commit a transaction after negotiation.

        Args:
            action: The action to perform
            params: Parameters for the action
            selected_cost: The selected cost option

        Returns:
            TransactionResult
        """
        ...

    @abstractmethod
    def get_transaction_history(self) -> List[Dict[str, Any]]:
        """Get transaction history."""
        ...


class BankerMixin:
    """
    Mixin providing common banker functionality.
    Concrete bankers can inherit from this for basic implementations.
    """

    def __init__(self):
        self._dust_balance: int = 100  # Default starting balance
        self._transaction_log: List[Dict[str, Any]] = []
        self._transaction_counter: int = 0

    def get_balance(self) -> int:
        """Get current dust balance."""
        return self._dust_balance

    def can_afford(self, amount: int) -> bool:
        """Check if the balance can cover the amount."""
        return self._dust_balance >= amount

    def _log_transaction(self, transaction_type: str, amount: int, reason: str,
                         success: bool, balance_before: int) -> str:
        """Log a transaction and return transaction ID."""
        self._transaction_counter += 1
        transaction_id = f"txn_{self._transaction_counter:06d}"

        log_entry = {
            "transaction_id": transaction_id,
            "type": transaction_type,
            "amount": amount,
            "reason": reason,
            "success": success,
            "balance_before": balance_before,
            "balance_after": self._dust_balance,
            "timestamp": None  # Would be datetime in real implementation
        }

        self._transaction_log.append(log_entry)
        return transaction_id

    def deduct_dust(self, amount: int, reason: str) -> TransactionResult:
        """Deduct dust from balance."""
        balance_before = self._dust_balance

        if self._dust_balance >= amount:
            self._dust_balance -= amount
            transaction_id = self._log_transaction(
                "debit", amount, reason, True, balance_before)
            return TransactionResult(
                success=True,
                dust_charged=amount,
                message=f"Deducted {amount} dust: {reason}",
                transaction_id=transaction_id
            )
        else:
            transaction_id = self._log_transaction(
                "debit", amount, reason, False, balance_before)
            return TransactionResult(
                success=False,
                dust_charged=0,
                message=f"Insufficient funds: need {amount}, have {self._dust_balance}",
                transaction_id=transaction_id
            )

    def add_dust(self, amount: int, reason: str) -> TransactionResult:
        """Add dust to balance."""
        balance_before = self._dust_balance
        self._dust_balance += amount
        transaction_id = self._log_transaction(
            "credit", amount, reason, True, balance_before)

        return TransactionResult(
            success=True,
            dust_charged=-amount,  # Negative charge for credits
            message=f"Added {amount} dust: {reason}",
            transaction_id=transaction_id
        )

    def get_transaction_history(self) -> List[Dict[str, Any]]:
        """Get transaction history."""
        return list(self._transaction_log)


class NullBanker(BankerMixin):
    """
    A banker that allows all operations for free.
    Useful for development and testing.
    """

    def get_cost_estimate(self, action: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """All actions are free."""
        return {
            "action": action,
            "dust_cost": 0,
            "allowed": True,
            "message": "Free operation (NullBanker)"
        }

    def negotiate_transaction(self, action: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """No negotiation needed - everything is free."""
        return {
            "action": action,
            "dust_cost": 0,
            "allowed": True,
            "message": "Free operation (NullBanker)"
        }

    def commit_transaction(self, action: str, params: Dict[str, Any],
                           selected_cost: Optional[int] = None) -> TransactionResult:
        """Commit a free transaction."""
        return TransactionResult(
            success=True,
            dust_charged=0,
            message=f"Completed {action} for free (NullBanker)"
        )
