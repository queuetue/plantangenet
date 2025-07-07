"""
NullBanker implementation for testing and development.
"""

from typing import Dict, Any, Optional, List

from .mixin import BankerMixin
from .econ_types import TransactionResult, FinancialIdentity, Distributor, DistributionResult
from .policies import PermissiveFinancialPolicy


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

    # Override high-level convenience APIs for NullBanker behavior
    def credit_dust(self, amount: int, reason: str,
                    identity: Optional[FinancialIdentity] = None) -> TransactionResult:
        """No-op credit for NullBanker."""
        return TransactionResult(
            success=True,
            dust_charged=-amount,  # Negative for credit
            message=f"Credited {amount} dust (NullBanker): {reason}"
        )

    def preview_operation_cost(self, operation_type: str,
                               operation_params: Dict[str, Any],
                               identity: Optional[FinancialIdentity] = None) -> Dict[str, Any]:
        """Always return zero cost for NullBanker."""
        return {
            "estimated_cost": 0,
            "operation_type": operation_type,
            "base_cost": 0,
            "parameters": operation_params,
            "cost_breakdown": {
                "base": 0,
                "size_adjustment": 0,
                "priority_multiplier": 1.0
            },
            "note": "NullBanker - all operations are free"
        }

    def charge_for_operation(self, cost: int, operation_type: str,
                             operation_details: Dict[str, Any],
                             identity: Optional[FinancialIdentity] = None,
                             agent_declared_cost: Optional[int] = None) -> TransactionResult:
        """No charges in NullBanker."""
        return TransactionResult(
            success=True,
            dust_charged=0,
            message=f"No charge for {operation_type} (NullBanker)",
            agent_declared_cost=agent_declared_cost,
            api_actual_cost=0,
            cost_discrepancy=-
            (agent_declared_cost or 0) if agent_declared_cost else 0
        )

    def distribute_dust(self, total_amount: int, distribution_type: str,
                        context: Dict[str, Any],
                        identity: Optional[FinancialIdentity] = None) -> Dict[str, int]:
        """No distributions in NullBanker."""
        return {
            "null_distribution": total_amount
        }
