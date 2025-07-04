"""
Vanilla Banker Agent - A concrete banker implementation with cost base integration.
Handles all financial operations using loaded cost bases and provides negotiation.
This is an Agent that can be managed by Sessions.
"""

from typing import Dict, Any, Optional, List
from .agents.agent import Agent
from .banker import BankerMixin, TransactionResult, FinancialIdentity
from .cost_base import ApiNegotiator, CostBaseError, load_and_verify_cost_base
from .transaction_preview import TransactionBuilder


class VanillaBankerAgent(Agent, BankerMixin):
    """
    A concrete banker agent that uses cost bases for pricing and negotiation.
    This is the "worker" responsible for all lies about money.
    Inherits from Agent so it can be managed by Sessions.
    """

    def __init__(self, initial_balance: int = 100, cost_base_paths: Optional[List[str]] = None,
                 namespace: str = "plantangenet", logger: Any = None):
        """
        Initialize the vanilla banker agent.

        Args:
            initial_balance: Starting dust balance
            cost_base_paths: Paths to cost base packages to load
            namespace: Agent namespace
            logger: Agent logger
        """
        # Initialize Agent first
        Agent.__init__(self, namespace=namespace, logger=logger)
        # Initialize BankerMixin
        BankerMixin.__init__(self)

        self._dust_balance = initial_balance
        self.negotiators: Dict[str, ApiNegotiator] = {}
        self.active_quotes: Dict[str, Dict[str, Any]] = {}

        # Load cost bases if provided
        # Add transport cost base with realistic pricing (around 100 Dust base)
        default_transport_costs = {
            "name": "Default Transport Costs",
            "api_costs": {
                "transport.publish": 120,     # Higher base cost
                "transport.subscribe": 100,   # Higher base cost
                "save_object": 150,          # Higher storage cost
                "save_per_field": 25,        # Higher per-field cost
                "bulk_save": 80,             # Bulk discount
                "self_maintained": 200       # Premium for self-maintained
            }
        }

        if cost_base_paths:
            for path in cost_base_paths:
                self.load_cost_base(path)
        else:
            # Load default realistic costs
            self.add_cost_base_data(
                "default_realistic", default_transport_costs)

    async def update(self) -> bool:
        """
        Perform periodic update tasks for the banker agent.
        Could include tasks like clearing old quotes, updating exchange rates, etc.
        """
        # Clear old quotes periodically (simple implementation)
        if len(self.active_quotes) > 100:  # Arbitrary threshold
            # Keep only the most recent 50 quotes
            recent_quotes = dict(list(self.active_quotes.items())[-50:])
            self.active_quotes = recent_quotes

        return True

    @property
    def message_types(self):
        """Return the banker's message types."""
        base_types = super().message_types
        return base_types.union({
            "banker.quote_request",
            "banker.transaction_commit",
            "banker.balance_inquiry",
            "banker.cost_estimate"
        })

    @property
    def capabilities(self):
        """Return banker capabilities."""
        base_caps = super().capabilities
        return {
            **base_caps,
            "financial_services": {
                "cost_estimation": True,
                "transaction_negotiation": True,
                "dust_management": True,
                "cost_bases": list(self.negotiators.keys())
            }
        }

    def load_cost_base(self, package_path: str, package_name: Optional[str] = None) -> str:
        """
        Load a cost base package.

        Args:
            package_path: Path to the cost base package
            package_name: Optional name for the package

        Returns:
            Package identifier
        """
        try:
            cost_base = load_and_verify_cost_base(package_path)
            name = package_name or cost_base.get(
                "name", f"package_{len(self.negotiators)}")

            self.negotiators[name] = ApiNegotiator(cost_base)
            return name
        except Exception as e:
            raise ValueError(
                f"Failed to load cost base from {package_path}: {e}")

    def add_cost_base_data(self, name: str, cost_base_data: Dict[str, Any]) -> str:
        """
        Add a cost base from data rather than a file.

        Args:
            name: Name for the cost base
            cost_base_data: The cost base data dictionary

        Returns:
            Package identifier
        """
        from .cost_base import ApiNegotiator
        self.negotiators[name] = ApiNegotiator(cost_base_data)
        return name

    def get_cost_estimate(self, action: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Get a best-guess cost estimate for an action.

        Args:
            action: The action to estimate
            params: Parameters for the action

        Returns:
            Cost estimate or None if action not supported by any cost base
        """
        if not self.negotiators:
            return None

        # Try each negotiator until one works
        for name, negotiator in self.negotiators.items():
            try:
                quote = negotiator.get_quote(action, params)

                # Add metadata about which cost base provided the estimate
                estimate = {
                    "action": action,
                    "cost_base": name,
                    "allowed": quote.get("allowed", True)
                }

                if "options" in quote:
                    # Multiple pricing options available
                    estimate["has_options"] = True
                    estimate["min_cost"] = min(
                        opt["dust_cost"] for opt in quote["options"])
                    estimate["max_cost"] = max(
                        opt["dust_cost"] for opt in quote["options"])
                    # Default to cheapest
                    estimate["dust_cost"] = estimate["min_cost"]
                    estimate["options"] = quote["options"]
                else:
                    # Single pricing
                    estimate["has_options"] = False
                    estimate["dust_cost"] = quote["dust_cost"]

                return estimate

            except CostBaseError:
                continue

        return None

    def negotiate_transaction(self, action: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Negotiate a transaction with full cost options and preview.

        Args:
            action: The action to negotiate
            params: Parameters for the action

        Returns:
            Negotiation result with options and preview
        """
        if not self.negotiators:
            return None

        # Find a negotiator that can handle this action
        for name, negotiator in self.negotiators.items():
            try:
                quote = negotiator.get_quote(action, params)

                # Create transaction builder for preview
                builder = TransactionBuilder(
                    session_id=f"banker_{id(self)}",
                    user_balance=self._dust_balance
                )

                if "options" in quote:
                    # Add all pricing options
                    for option in quote["options"]:
                        builder.add_action(
                            action=f"{action} ({option['type']})",
                            description=option["description"],
                            dust_cost=option["dust_cost"],
                            parameters=params,
                            package_deal=option.get("type")
                        )
                else:
                    # Single option
                    builder.add_action(
                        action=action,
                        description=f"Perform {action}",
                        dust_cost=quote["dust_cost"],
                        parameters=params
                    )

                builder.add_warning(f"Using cost base: {name}")

                # Check affordability and add warnings
                if "options" in quote:
                    min_cost = min(opt["dust_cost"]
                                   for opt in quote["options"])
                    if not self.can_afford(min_cost):
                        builder.add_warning("Cannot afford any option!")
                else:
                    if not self.can_afford(quote["dust_cost"]):
                        builder.add_warning("Insufficient funds!")

                # Build the preview
                preview = builder.build()

                # Store quote for later commit
                quote_id = f"quote_{len(self.active_quotes)}"
                self.active_quotes[quote_id] = {
                    "action": action,
                    "params": params,
                    "quote": quote,
                    "negotiator": negotiator,
                    "cost_base": name
                }

                return {
                    "quote_id": quote_id,
                    "preview": preview,
                    "quote": quote,
                    "cost_base": name
                }

            except CostBaseError:
                continue

        return None

    def commit_transaction(self, action: str, params: Dict[str, Any],
                           selected_cost: Optional[int] = None,
                           quote_id: Optional[str] = None,
                           identity: Optional[FinancialIdentity] = None) -> TransactionResult:
        """
        Commit a transaction after negotiation.

        Args:
            action: The action to perform
            params: Parameters for the action
            selected_cost: The selected cost option
            quote_id: ID from previous negotiation (optional)
            identity: Identity for fee calculation (optional)

        Returns:
            TransactionResult
        """
        # If we have a quote ID, use the cached negotiation
        if quote_id and quote_id in self.active_quotes:
            cached = self.active_quotes[quote_id]
            negotiator = cached["negotiator"]
            quote = cached["quote"]
            cost_base_name = cached["cost_base"]
        else:
            # Find a negotiator that can handle this action
            negotiator = None
            quote = None
            cost_base_name = None

            for name, neg in self.negotiators.items():
                try:
                    quote = neg.get_quote(action, params)
                    negotiator = neg
                    cost_base_name = name
                    break
                except CostBaseError:
                    continue

            if not negotiator:
                return TransactionResult(
                    success=False,
                    dust_charged=0,
                    message=f"No cost base supports action: {action}"
                )

        # Determine final cost
        if selected_cost is not None:
            final_cost = selected_cost
        elif quote and "options" in quote:
            # Default to cheapest option
            final_cost = min(opt["dust_cost"] for opt in quote["options"])
        elif quote:
            final_cost = quote["dust_cost"]
        else:
            return TransactionResult(
                success=False,
                dust_charged=0,
                message="Unable to determine cost for action"
            )

        # Check affordability (including potential fees)
        fee_estimate = self.get_fee_estimate(final_cost, identity)
        total_cost = final_cost + fee_estimate["fee_amount"]

        if not self.can_afford(total_cost):
            return TransactionResult(
                success=False,
                dust_charged=0,
                message=f"Insufficient funds: need {total_cost} (base: {final_cost}, fee: {fee_estimate['fee_amount']}), have {self._dust_balance}"
            )

        # Deduct base cost
        deduct_result = self.deduct_dust(
            final_cost, f"{action} via {cost_base_name}")

        if not deduct_result.success:
            return deduct_result

        # Apply distributions (including banker's cut)
        distribution_result = self.distribute_amount(
            final_cost, [], identity, include_banker_cut=True)

        if deduct_result.success:
            # Clean up quote cache
            if quote_id and quote_id in self.active_quotes:
                del self.active_quotes[quote_id]

            # Calculate total charged
            banker_fee = 0
            for dist in distribution_result.distributions:
                if dist["account_id"] == "banker":
                    banker_fee = dist["amount"]
                    break

            total_charged = final_cost + banker_fee
            fee_message = f" + {banker_fee} fee" if banker_fee > 0 else ""

            return TransactionResult(
                success=True,
                dust_charged=total_charged,
                message=f"Completed {action} for {final_cost} dust{fee_message} using {cost_base_name}",
                transaction_id=deduct_result.transaction_id
            )
        else:
            return deduct_result

    def get_available_actions(self) -> List[str]:
        """Get list of all actions supported by loaded cost bases."""
        actions = set()
        for negotiator in self.negotiators.values():
            if hasattr(negotiator, 'api_costs'):
                actions.update(negotiator.api_costs.keys())
        return sorted(list(actions))

    def get_cost_base_info(self) -> Dict[str, Dict[str, Any]]:
        """Get information about loaded cost bases."""
        info = {}
        for name, negotiator in self.negotiators.items():
            if hasattr(negotiator, 'cost_base'):
                cost_base = negotiator.cost_base
                info[name] = {
                    "name": cost_base.get("name", name),
                    "version": cost_base.get("version", "unknown"),
                    "description": cost_base.get("description", ""),
                    "actions": list(negotiator.api_costs.keys()) if hasattr(negotiator, 'api_costs') else []
                }
        return info

    def clear_quotes(self):
        """Clear cached quotes (useful for cleanup)."""
        self.active_quotes.clear()

    def charge_agent_for_api_usage(self, action: str, params: Dict[str, Any],
                                   agent_declared_cost: int) -> TransactionResult:
        """
        Charge an agent for actual API usage costs.
        Tracks discrepancies between agent pricing and actual API costs.
        """
        # Get the actual API cost for this action
        api_cost = self._calculate_api_cost(action, params)

        # Calculate discrepancy
        discrepancy = agent_declared_cost - api_cost

        # Record the API usage transaction
        result = self.deduct_dust(api_cost, f"API usage: {action}")

        # Update result with cost tracking
        result.agent_declared_cost = agent_declared_cost
        result.api_actual_cost = api_cost
        result.cost_discrepancy = discrepancy

        # Log discrepancy for system oversight
        if discrepancy != 0:
            self._record_cost_discrepancy(
                action, agent_declared_cost, api_cost, discrepancy)

        return result

    def _calculate_api_cost(self, action: str, params: Dict[str, Any]) -> int:
        """Calculate the actual API cost for an action."""
        if not self.negotiators:
            return 100  # Default realistic cost

        # Use first available negotiator to get API cost
        for negotiator in self.negotiators.values():
            quote = negotiator.get_quote(action, params)
            if quote and quote.get("allowed", False):
                return quote.get("dust_cost", 100)

        return 100  # Fallback realistic cost

    def _record_cost_discrepancy(self, action: str, agent_cost: int, api_cost: int, discrepancy: int):
        """Record cost discrepancy for system oversight."""
        import datetime

        discrepancy_record = {
            "timestamp": datetime.datetime.now().isoformat(),
            "action": action,
            "agent_declared_cost": agent_cost,
            "api_actual_cost": api_cost,
            "discrepancy": discrepancy,
            "discrepancy_type": "profit" if discrepancy > 0 else "loss"
        }

        # Add to transaction history as a system record
        self._transaction_log.append({
            "transaction_id": f"disc_{len(self._transaction_log) + 1:06d}",
            "type": "discrepancy_record",
            "amount": discrepancy,
            "reason": f"Cost discrepancy for {action}: agent={agent_cost}, api={api_cost}",
            "success": True,
            "balance_before": self._dust_balance + api_cost,  # Before the API charge
            "balance_after": self._dust_balance,
            "timestamp": discrepancy_record["timestamp"],
            "metadata": discrepancy_record
        })

    def set_financial_policy(self, policy):
        """
        Set a custom financial policy for access control.

        Args:
            policy: A FinancialPolicy instance
        """
        self._financial_policy = policy

    def get_financial_policy(self):
        """Get the current financial policy."""
        return self._financial_policy


# Convenience function for creating a banker agent with cost bases
def create_vanilla_banker_agent(initial_balance: int = 100, cost_base_paths: Optional[List[str]] = None,
                                namespace: str = "plantangenet", logger: Any = None) -> VanillaBankerAgent:
    """
    Create a vanilla banker agent with optional cost bases.

    Args:
        initial_balance: Starting dust balance
        cost_base_paths: Paths to cost base packages
        namespace: Agent namespace
        logger: Agent logger

    Returns:
        Configured VanillaBankerAgent
    """
    return VanillaBankerAgent(initial_balance, cost_base_paths or [], namespace, logger)
