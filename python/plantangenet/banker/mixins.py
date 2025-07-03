"""
BankerMixin implementation for agent functionality.
"""

import datetime
from typing import Dict, Any, Optional, List

from ..mixins.base import OceanMixinBase
from .types import (
    TransactionResult, FinancialIdentity, FinancialAccessRequest,
    Distributor, DistributionResult
)
from .policies import FinancialPolicy, FeePolicy
from .banker import Banker


class BankerMixin(Banker, OceanMixinBase):
    """
    Mixin providing common banker functionality for agents.
    Emits a structured ECONOMIC log event for every transaction (debit, credit, distribution, etc).
    The log event includes all relevant transaction fields (timestamp, transaction_id, type, amount, from_account, to_account, reason, balances, success, etc).
    If a logger is configured (self.logger: Logger), the event is emitted at ECONOMIC level.
    This enables external log handlers to capture, persist, or forward transaction events for audit and analysis.
    """

    def __init__(self):
        """Initialize banker state."""
        super().__init__()
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
        Log a transaction and return transaction ID. Emits a structured ECONOMIC event if logger is set.
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

        # Emit economic log event if logger is available
        if hasattr(self, 'logger') and self.logger:
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
            system_identity: Identity for overflow handling (optional)

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

            # Only process distributors with positive amounts
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
        # Placeholder implementation - in real system, would calculate actual API costs
        api_cost = 10  # Simple fixed cost for demo

        result = self.deduct_dust(api_cost, f"API usage: {action}")
        result.agent_declared_cost = agent_declared_cost
        result.api_actual_cost = api_cost
        result.cost_discrepancy = api_cost - agent_declared_cost

        return result

    def get_cost_estimate(self, action: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get cost estimate for an action."""
        # Simple cost estimation
        base_costs = {
            "data_transport": 10,
            "computation": 20,
            "storage": 5
        }

        cost = base_costs.get(action, 15)  # Default cost

        return {
            "action": action,
            "dust_cost": cost,
            "allowed": True,
            "message": f"Estimated cost for {action}"
        }

    def negotiate_transaction(self, action: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Negotiate a transaction with cost options."""
        estimate = self.get_cost_estimate(action, params)
        if not estimate:
            return None

        base_cost = estimate["dust_cost"]

        return {
            "action": action,
            "options": [
                {"cost": base_cost, "quality": "standard"},
                {"cost": int(base_cost * 1.5), "quality": "premium"},
                {"cost": int(base_cost * 0.7), "quality": "economy"}
            ],
            "recommended": 0  # Index of recommended option
        }

    def commit_transaction(self, action: str, params: Dict[str, Any],
                           selected_cost: Optional[int] = None) -> TransactionResult:
        """Commit a transaction after negotiation."""
        if selected_cost is None:
            estimate = self.get_cost_estimate(action, params)
            cost = estimate["dust_cost"] if estimate else 10
        else:
            cost = selected_cost

        return self.deduct_dust(cost, f"Transaction: {action}")

    # Override high-level methods to add logging
    def distribute_dust(self, total_amount: int, distribution_type: str,
                        context: Dict[str, Any],
                        identity: Optional[FinancialIdentity] = None) -> Dict[str, int]:
        """
        High-level method for distributing dust according to policies.
        Overrides the protocol default to add logging.
        """
        # Call the parent implementation
        distributions = super().distribute_dust(
            total_amount, distribution_type, context, identity)

        # Add logging
        if hasattr(self, 'logger') and self.logger:
            self.logger.economic("dust_distribution", {
                "total_amount": total_amount,
                "distribution_type": distribution_type,
                "distributions": distributions,
                "context": context
            })

        return distributions
