"""
Vanilla Banker Agent - A concrete banker implementation with cost base integration.
Handles all financial operations using loaded cost bases and provides negotiation.
This is an Agent that can be managed by Sessions.
"""

from typing import Dict, Any, Optional, List
from .agent import Agent
from .banker import Banker, BankerMixin, TransactionResult
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
        if cost_base_paths:
            for path in cost_base_paths:
                self.load_cost_base(path)

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
                           quote_id: Optional[str] = None) -> TransactionResult:
        """
        Commit a transaction after negotiation.

        Args:
            action: The action to perform
            params: Parameters for the action
            selected_cost: The selected cost option
            quote_id: ID from previous negotiation (optional)

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

        # Check affordability
        if not self.can_afford(final_cost):
            return TransactionResult(
                success=False,
                dust_charged=0,
                message=f"Insufficient funds: need {final_cost}, have {self._dust_balance}"
            )

        # Deduct dust
        deduct_result = self.deduct_dust(
            final_cost, f"{action} via {cost_base_name}")

        if deduct_result.success:
            # Clean up quote cache
            if quote_id and quote_id in self.active_quotes:
                del self.active_quotes[quote_id]

            return TransactionResult(
                success=True,
                dust_charged=final_cost,
                message=f"Completed {action} for {final_cost} dust using {cost_base_name}",
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
