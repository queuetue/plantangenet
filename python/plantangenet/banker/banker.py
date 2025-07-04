"""
Core Banker protocol and interface definition.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Protocol, runtime_checkable

from .econ_types import (
    TransactionResult, FinancialIdentity, Distributor, DistributionResult
)


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
                          include_banker_cut: bool = True,
                          system_identity: Optional[FinancialIdentity] = None) -> DistributionResult:
        """
        Distribute an amount according to a list of distributors.
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
        ...

    # High-level convenience APIs
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

        # Log the distribution if logger is available (implementation-specific)
        # Implementations should override this method to add logging

        return distributions
