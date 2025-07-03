"""
Banker Protocol and Mixins for Dust Management.
Handles all financial operations, cost negotiation, and transaction management.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Protocol, runtime_checkable
from dataclasses import dataclass
import json
import os
import datetime
from .mixins.base import OceanMixinBase


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

        # Always return 0 for admin users as a failsafe
        if identity_class == "admin":
            return 0

        # Get fee structure
        fee_structure = self.fee_structures.get(
            identity_class, self.fee_structures["default"])

        # Get transaction count for this user/period
        period_key = "today"  # In real implementation, this would be actual date
        if user_key not in self.transaction_counts:
            self.transaction_counts[user_key] = {}
        if period_key not in self.transaction_counts[user_key]:
            self.transaction_counts[user_key][period_key] = 0

        transaction_count = self.transaction_counts[user_key][period_key]

        fee = fee_structure.calculate_fee(base_amount, transaction_count)

        # Update transaction count
        self.transaction_counts[user_key][period_key] += 1

        return fee

    def create_banker_distributor(self, identity: Optional[FinancialIdentity],
                                  base_amount: int) -> Optional[Distributor]:
        """
        Create a distributor for the banker's cut.

        Args:
            identity: The financial identity making the transaction
            base_amount: The base transaction amount

        Returns:
            Distributor for banker's cut, or None if no fee
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


@runtime_checkable
class Banker(Protocol):
    """
    Protocol for entities that handle dust transactions and cost negotiation.
    Responsible for all "lies about money" - pricing, negotiation, balances.
    """

    @abstractmethod
    def get_balance(self, identity: Optional[FinancialIdentity] = None,
                    target_account: Optional[str] = None) -> int:
        """
        Get current dust balance with access control.

        Args:
            identity: Identity of the requestor (optional for backward compatibility)
            target_account: Account to check (optional, defaults to requestor's account)

        Returns:
            Dust balance or raises PermissionError if access denied
        """
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
    def get_transaction_history(self, identity: Optional[FinancialIdentity] = None,
                                target_account: Optional[str] = None,
                                filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Get transaction history with access control.

        Args:
            identity: Identity of the requestor (optional for backward compatibility)
            target_account: Account to check (optional, defaults to requestor's account)
            filters: Optional filters for the history

        Returns:
            Filtered transaction history or raises PermissionError if access denied
        """
        ...

    @abstractmethod
    def charge_agent_for_api_usage(self, action: str, params: Dict[str, Any],
                                   agent_declared_cost: int) -> TransactionResult:
        """
        Charge an agent for actual API usage costs.

        This is separate from what the agent charges its clients.
        The banker tracks discrepancies between agent pricing and API costs.

        Args:
            action: The API action performed
            params: Parameters for the action
            agent_declared_cost: What the agent charged its client

        Returns:
            TransactionResult with cost tracking
        """
        ...

    @abstractmethod
    def distribute_amount(self, amount: int, distributors: List[Distributor],
                          identity: Optional[FinancialIdentity] = None,
                          include_banker_cut: bool = True) -> DistributionResult:
        """
        Distribute an amount according to a list of distributors.
        The banker automatically adds its own cut unless disabled.

        Args:
            amount: The total amount to distribute
            distributors: List of distribution rules
            identity: The identity for banker's cut calculation (optional)
            include_banker_cut: Whether to include banker's cut (default True)

        Returns:
            DistributionResult with distribution details
        """
        ...


class BankerMixin(OceanMixinBase):
    """
    Mixin providing common banker functionality for agents.
    Emits a structured ECON log event for every transaction (debit, credit, distribution, etc).
    The log event includes all relevant transaction fields (timestamp, transaction_id, type, amount, from_account, to_account, reason, balances, success, etc).
    If a logger is configured (self.logger: Logger), the event is emitted at ECON level.
    This enables external log handlers to capture, persist, or forward transaction events for audit and analysis.
    """

    def __init__(self):
        """Initialize banker state."""
        self._dust_balance = 0
        self._transaction_log: List[Dict[str, Any]] = []
        self._transaction_counter = 0
        # New policy configuration
        self._allow_overdraft = True  # Policy: allow operations even with insufficient funds
        self._overdraft_limit = -10000  # Maximum negative balance allowed
        self._financial_policy = FinancialPolicy()  # Access control policy
        self._fee_policy = FeePolicy()  # Fee policy for banker's cut
        # Path to transaction log file (JSON Lines)
        self._transaction_log_path = None
        # File handle (optional, for performance)
        self._transaction_log_file = None
        # Use agent logger if present
        self._logger = getattr(self, 'logger', None)

    def set_logger(self, logger):
        """Set or update the logger for trace events."""
        self._logger = logger

    def set_transaction_log_path(self, log_path: str, append: bool = True):
        """
        Set the path for the transaction log file. If append is False, overwrites existing file.
        """
        self._transaction_log_path = log_path
        mode = 'a' if append else 'w'
        # Optionally open file handle for performance (not required, can use context manager)
        self._transaction_log_file = open(log_path, mode)

    def close_transaction_log(self):
        """Close the transaction log file handle if open."""
        if self._transaction_log_file:
            self._transaction_log_file.close()
            self._transaction_log_file = None

    def get_balance(self, identity: Optional[FinancialIdentity] = None,
                    target_account: Optional[str] = None) -> int:
        """
        Get current dust balance with access control.

        Args:
            identity: Identity of the requestor (optional for backward compatibility)
            target_account: Account to check (optional, defaults to requestor's account)

        Returns:
            Dust balance or raises PermissionError if access denied
        """
        # If no identity provided, assume self-access (backward compatibility)
        if identity is None:
            return self._dust_balance

        # Create access request
        request = FinancialAccessRequest(
            requestor=identity,
            operation="get_balance",
            target_account=target_account
        )

        # Check policy
        if not self._financial_policy.can_access_balance(request):
            raise PermissionError(
                f"Access denied: {identity.user_id} cannot access balance for account {target_account or identity.user_id}"
            )

        return self._dust_balance

    def can_afford(self, amount: int) -> bool:
        """Check if the balance can cover the amount."""
        return self._dust_balance >= amount

    def _log_transaction(self, transaction_type: str, amount: int, reason: str,
                         success: bool, balance_before: int,
                         from_account: Optional[str] = None, to_account: Optional[str] = None,
                         extra: Optional[dict] = None) -> str:
        """
        Log a transaction and return transaction ID. Emits a structured ECON event if logger is set.
        The log entry is a dict with all relevant fields, suitable for ingestion by log analysis tools.
        """
        self._transaction_counter += 1
        transaction_id = f"txn_{self._transaction_counter:06d}"
        timestamp = datetime.datetime.now().isoformat()
        log_entry = {
            "transaction_id": transaction_id,
            "type": transaction_type,
            "amount": amount,
            "reason": reason,
            "success": success,
            "balance_before": balance_before,
            "balance_after": self._dust_balance,
            "timestamp": timestamp,
            "from_account": from_account,
            "to_account": to_account
        }
        if extra:
            log_entry.update(extra)
        self._transaction_log.append(log_entry)
        self.logger.economic("plantangenet.transaction", context=log_entry)
        return transaction_id

    def deduct_dust(self, amount: int, reason: str) -> TransactionResult:
        """Deduct dust from balance with policy-based overdraft support."""
        balance_before = self._dust_balance

        # Check if we can afford it normally
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
            # Policy decision: allow overdraft?
            if self._allow_overdraft and (self._dust_balance - amount) >= self._overdraft_limit:
                # Allow the operation but go into overdraft
                self._dust_balance -= amount
                transaction_id = self._log_transaction(
                    "debit_overdraft", amount, reason, True, balance_before)
                return TransactionResult(
                    success=True,
                    dust_charged=amount,
                    message=f"Deducted {amount} dust (overdraft): {reason}. Balance: {self._dust_balance}",
                    transaction_id=transaction_id
                )
            else:
                # Hard limit reached or overdraft disabled
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

    def get_transaction_history(self, identity: Optional[FinancialIdentity] = None,
                                target_account: Optional[str] = None,
                                filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Get transaction history with access control.

        Args:
            identity: Identity of the requestor (optional for backward compatibility)
            target_account: Account to check (optional, defaults to requestor's account)
            filters: Optional filters for the history

        Returns:
            Filtered transaction history or raises PermissionError if access denied
        """
        # If no identity provided, assume self-access (backward compatibility)
        if identity is None:
            return list(self._transaction_log)

        # Create access request
        request = FinancialAccessRequest(
            requestor=identity,
            operation="get_history",
            target_account=target_account,
            filters=filters
        )

        # Check policy
        if not self._financial_policy.can_access_transaction_history(request):
            raise PermissionError(
                f"Access denied: {identity.user_id} cannot access transaction history for account {target_account or identity.user_id}"
            )

        # Get transactions and apply filtering
        transactions = list(self._transaction_log)
        filtered_transactions = self._financial_policy.filter_transaction_history(
            request, transactions)

        # Apply additional filters if provided
        if filters:
            # Simple filtering by transaction type, amount, etc.
            if "type" in filters:
                filtered_transactions = [
                    t for t in filtered_transactions if t.get("type") == filters["type"]]
            if "min_amount" in filters:
                filtered_transactions = [t for t in filtered_transactions if t.get(
                    "amount", 0) >= filters["min_amount"]]
            if "max_amount" in filters:
                filtered_transactions = [t for t in filtered_transactions if t.get(
                    "amount", 0) <= filters["max_amount"]]

        return filtered_transactions

    def distribute_amount(self, amount: int, distributors: List[Distributor],
                          identity: Optional[FinancialIdentity] = None,
                          include_banker_cut: bool = True,
                          system_identity: Optional[FinancialIdentity] = None) -> DistributionResult:
        """
        Distribute an amount according to a list of distributors.
        Enforces max_dust per account; overflow is redirected to system_identity (if provided).
        The banker automatically adds its own cut unless disabled.

        Args:
            amount: The total amount to distribute
            distributors: List of distribution rules
            identity: The identity for banker's cut calculation (optional)
            include_banker_cut: Whether to include banker's cut (default True)

        Returns:
            DistributionResult with distribution details
        """
        # Copy distributors to avoid modifying the original list
        all_distributors = list(distributors)

        # Add banker's cut if enabled
        if include_banker_cut:
            banker_distributor = self._fee_policy.create_banker_distributor(
                identity, amount)
            if banker_distributor:
                all_distributors.insert(0, banker_distributor)

        # Track distributions
        distributions = []
        remaining_amount = amount
        total_distributed = 0
        overflow_total = 0

        # Process each distributor
        for distributor in all_distributors:
            if remaining_amount <= 0:
                break

            # Calculate distribution amount
            distribution_amount = distributor.calculate_distribution(
                amount, remaining_amount)

            if distribution_amount > 0:
                # Simulate account max_dust enforcement
                account_max = getattr(distributor, 'max_dust', None)
                # For this example, assume all accounts have max_dust=1000 unless otherwise set
                # Banker account gets higher limit to accommodate fees
                if account_max is None:
                    if distributor.account_id == "banker":
                        account_max = 100000  # Much higher limit for banker
                    else:
                        account_max = 1000
                # Simulate current balance (in real system, fetch from account)
                current_balance = 0
                # For banker, use self._dust_balance
                if distributor.account_id == "banker":
                    current_balance = self._dust_balance
                # Enforce max_dust
                allowed = min(distribution_amount, max(
                    0, account_max - current_balance))
                overflow = distribution_amount - allowed
                
                if allowed > 0:
                    if distributor.account_id == "banker":
                        balance_before = self._dust_balance
                        self._dust_balance += allowed
                        transaction_id = self._log_transaction(
                            "credit_fee", allowed, distributor.reason, True, balance_before)
                    else:
                        transaction_id = self._log_transaction(
                            "distribution", allowed,
                            f"Distribution to {distributor.account_id}: {distributor.reason}",
                            True, self._dust_balance)
                    distributions.append({
                        "account_id": distributor.account_id,
                        "amount": allowed,
                        "reason": distributor.reason,
                        "transaction_id": transaction_id
                    })
                    remaining_amount -= allowed
                    total_distributed += allowed
                if overflow > 0 and system_identity:
                    # Redirect overflow to system account
                    overflow_total += overflow
                    overflow_txn = self._log_transaction(
                        "overflow", overflow,
                        f"Overflow from {distributor.account_id} to system", True, self._dust_balance)
                    distributions.append({
                        "account_id": system_identity.user_id,
                        "amount": overflow,
                        "reason": f"Overflow from {distributor.account_id}",
                        "transaction_id": overflow_txn
                    })
                    remaining_amount -= overflow

        return DistributionResult(
            success=True,
            total_amount=amount,
            distributions=distributions,
            remaining_amount=remaining_amount,
            message=f"Distributed {total_distributed} dust to {len(distributions)} accounts, {overflow_total} overflow redirected"
        )

    def apply_bankers_cut(self, base_amount: int, identity: Optional[FinancialIdentity] = None,
                          reason: str = "banker's cut") -> TransactionResult:
        """
        Apply the banker's cut (fee) to a transaction.
        DEPRECATED: Use distribute_amount instead.

        Args:
            base_amount: The base transaction amount
            identity: The identity making the transaction (for fee calculation)
            reason: Reason for the fee

        Returns:
            TransactionResult with fee information
        """
        # Use the new distribution system for backward compatibility
        result = self.distribute_amount(
            base_amount, [], identity, include_banker_cut=True)

        if result.success and result.distributions:
            banker_dist = next(
                (d for d in result.distributions if d["account_id"] == "banker"), None)
            if banker_dist:
                return TransactionResult(
                    success=True,
                    dust_charged=banker_dist["amount"],
                    message=f"Applied banker's cut: {banker_dist['amount']} dust",
                    transaction_id=banker_dist["transaction_id"]
                )

        return TransactionResult(
            success=True,
            dust_charged=0,
            message="No banker's cut applied"
        )

    def get_fee_estimate(self, base_amount: int, identity: Optional[FinancialIdentity] = None) -> Dict[str, Any]:
        """
        Get an estimate of the banker's cut for a transaction.

        Args:
            base_amount: The base transaction amount
            identity: The identity making the transaction

        Returns:
            Fee information dictionary
        """
        fee_amount = self._fee_policy.calculate_fee(identity, base_amount)
        identity_class = self._fee_policy.get_identity_class(
            identity) if identity else "default"
        fee_structure = self._fee_policy.get_fee_structure(identity_class)

        return {
            "fee_amount": fee_amount,
            "identity_class": identity_class,
            "fee_structure": {
                "base_rate": fee_structure.base_rate,
                "fixed_fee": fee_structure.fixed_fee,
                "minimum_fee": fee_structure.minimum_fee,
                "maximum_fee": fee_structure.maximum_fee
            }
        }

        # Create access request
        request = FinancialAccessRequest(
            requestor=identity,
            operation="get_transaction_history",
            target_account=target_account,
            filters=filters
        )

        # Check policy
        if not self._financial_policy.can_access_transaction_history(request):
            raise PermissionError(
                f"Access denied: {identity.user_id} cannot access transaction history for account {target_account or identity.user_id}"
            )

        # Apply policy-based filtering
        return self._financial_policy.filter_transaction_history(request, self._transaction_log)

    def charge_agent_for_api_usage(self, action: str, params: Dict[str, Any],
                                   agent_declared_cost: int) -> TransactionResult:
        """
        Charge an agent for actual API usage costs.

        This is separate from what the agent charges its clients.
        The banker tracks discrepancies between agent pricing and API costs.

        Args:
            action: The API action performed
            params: Parameters for the action
            agent_declared_cost: What the agent charged its client

        Returns:
            TransactionResult with cost tracking
        """
        ...


class NullBanker(BankerMixin):
    """
    A banker that allows all operations for free.
    Useful for development and testing.
    """

    def __init__(self):
        """Initialize NullBanker."""
        super().__init__()
        # Override policy to be more permissive
        self._financial_policy = PermissiveFinancialPolicy()

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

    def charge_agent_for_api_usage(self, action: str, params: Dict[str, Any],
                                   agent_declared_cost: int) -> TransactionResult:
        """No API charges in NullBanker."""
        return TransactionResult(
            success=True,
            dust_charged=0,
            message=f"No API charge for {action} (NullBanker)",
            agent_declared_cost=agent_declared_cost,
            api_actual_cost=0,
            cost_discrepancy=agent_declared_cost
        )

    def apply_bankers_cut(self, base_amount: int, identity: Optional[FinancialIdentity] = None,
                          reason: str = "banker's cut") -> TransactionResult:
        """No fees in NullBanker."""
        return TransactionResult(
            success=True,
            dust_charged=0,
            message=f"No fee applied: {reason} (NullBanker)"
        )

    def distribute_amount(self, amount: int, distributors: List[Distributor],
                          identity: Optional[FinancialIdentity] = None,
                          include_banker_cut: bool = True,
                          system_identity: Optional[FinancialIdentity] = None) -> DistributionResult:
        """No distributions in NullBanker - all amounts go nowhere."""
        return DistributionResult(
            success=True,
            total_amount=amount,
            distributions=[],
            remaining_amount=amount,
            message=f"No distributions applied: {amount} dust (NullBanker)"
        )

    # High-level convenience APIs for common operations

    def credit_dust(self, amount: int, reason: str,
                    identity: Optional[FinancialIdentity] = None) -> TransactionResult:
        """
        High-level method for crediting dust to an account.

        Args:
            amount: Amount of dust to credit
            reason: Reason for the credit
            identity: Financial identity for access control

        Returns:
            TransactionResult indicating success/failure
        """
        return self.add_dust(amount, reason)

    def preview_operation_cost(self, operation_type: str,
                               operation_params: Dict[str, Any],
                               identity: Optional[FinancialIdentity] = None) -> Dict[str, Any]:
        """
        Preview the cost of an operation before committing to it.

        Args:
            operation_type: Type of operation (e.g., "data_transport", "computation")
            operation_params: Parameters for the operation
            identity: Financial identity for cost calculations

        Returns:
            Dict with estimated_cost and other cost details
        """
        # Base implementation provides simple cost estimation
        base_costs = {
            "data_transport": 10,
            "data_storage": 5,
            "computation": 20,
            "nats_publish": 15,
            "redis_set": 8,
            "redis_get": 3,
            "network_fee": 25
        }

        base_cost = base_costs.get(operation_type, 50)  # Default cost

        # Adjust based on parameters
        if "data_size" in operation_params:
            size_factor = max(
                1, operation_params["data_size"] // 1024)  # Per KB
            base_cost += size_factor * 2

        if operation_params.get("priority") == "high":
            base_cost = int(base_cost * 1.5)

        return {
            "estimated_cost": base_cost,
            "operation_type": operation_type,
            "base_cost": base_costs.get(operation_type, 50),
            "parameters": operation_params,
            "cost_breakdown": {
                "base": base_costs.get(operation_type, 50),
                "size_adjustment": base_cost - base_costs.get(operation_type, 50),
                "priority_multiplier": 1.5 if operation_params.get("priority") == "high" else 1.0
            }
        }

    def charge_for_operation(self, cost: int, operation_type: str,
                             operation_details: Dict[str, Any],
                             identity: Optional[FinancialIdentity] = None,
                             agent_declared_cost: Optional[int] = None) -> TransactionResult:
        """
        Charge for an operation with optional cost negotiation.

        Args:
            cost: The cost to charge
            operation_type: Type of operation being charged for
            operation_details: Details about the operation
            identity: Financial identity
            agent_declared_cost: Cost the agent declared/negotiated

        Returns:
            TransactionResult with cost tracking and discrepancy information
        """
        # Build a comprehensive reason
        reason = f"{operation_type}"
        if "destination" in operation_details:
            reason += f" to {operation_details['destination']}"
        if "data_size" in operation_details:
            reason += f" ({operation_details['data_size']} bytes)"

        # Perform the deduction
        result = self.deduct_dust(cost, reason)

        # Add cost tracking information
        if agent_declared_cost is not None and agent_declared_cost != cost:
            result.agent_declared_cost = agent_declared_cost
            result.api_actual_cost = cost
            result.cost_discrepancy = cost - agent_declared_cost

        return result

    def distribute_dust(self, total_amount: int, distribution_type: str,
                        context: Dict[str, Any],
                        identity: Optional[FinancialIdentity] = None) -> Dict[str, int]:
        """
        High-level method for distributing dust according to policies.

        Args:
            total_amount: Total amount to distribute
            distribution_type: Type of distribution ("agent_profit", "service_revenue", etc.)
            context: Context information for the distribution
            identity: Financial identity

        Returns:
            Dict mapping recipient names to amounts
        """
        # Simple policy-based distribution
        distributions = {}

        if distribution_type == "agent_profit":
            # Agent profit distribution
            agent_cut = int(total_amount * 0.70)  # 70% to agent
            banker_cut = int(total_amount * 0.10)  # 10% to banker
            operational_reserve = total_amount - agent_cut - banker_cut  # Remainder

            distributions = {
                "agent_profit": agent_cut,
                "banker_fee": banker_cut,
                "operational_reserve": operational_reserve
            }

        elif distribution_type == "service_revenue":
            # Service revenue distribution
            service_cut = int(total_amount * 0.80)  # 80% to service provider
            platform_cut = int(total_amount * 0.15)  # 15% to platform
            banker_cut = total_amount - service_cut - platform_cut  # Remainder

            distributions = {
                "service_provider": service_cut,
                "platform_fee": platform_cut,
                "banker_fee": banker_cut
            }

        else:
            # Default equal distribution
            distributions = {
                "primary_recipient": total_amount
            }

        # Log the distribution
        if hasattr(self, '_logger') and self._logger:
            self._logger.economic("dust_distribution", {
                "total_amount": total_amount,
                "distribution_type": distribution_type,
                "distributions": distributions,
                "context": context
            })

        return distributions
