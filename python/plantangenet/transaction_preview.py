"""
Transaction preview system for the cost base framework.
Provides detailed previews of what users are purchasing before they commit Dust.
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class LineItem:
    """Individual line item in a transaction preview."""
    action: str
    description: str
    dust_cost: int
    parameters: Dict[str, Any]
    package_deal: Optional[str] = None  # e.g., "bulk_save", "premium_bundle"


@dataclass
class TransactionSummary:
    """Summary of transaction costs and savings."""
    base_cost: int  # What it would cost without any deals
    final_cost: int  # Actual cost with deals applied
    savings: int    # Amount saved through package deals
    items_count: int


@dataclass
class TransactionPreview:
    """Complete transaction preview with all details."""
    session_id: str
    timestamp: str
    line_items: List[LineItem]
    summary: TransactionSummary
    user_balance: int
    balance_after: int
    expires_at: Optional[str] = None  # Quote expiry
    warnings: List[str] = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


class TransactionBuilder:
    """Builder for creating transaction previews."""

    def __init__(self, session_id: str, user_balance: int):
        self.session_id = session_id
        self.user_balance = user_balance
        self.line_items: List[LineItem] = []
        self.warnings: List[str] = []
        self.quote_duration_minutes = 5  # Default quote validity

    def add_action(self, action: str, description: str, dust_cost: int,
                   parameters: Dict[str, Any], package_deal: Optional[str] = None) -> 'TransactionBuilder':
        """Add an action to the transaction."""
        line_item = LineItem(
            action=action,
            description=description,
            dust_cost=dust_cost,
            parameters=parameters,
            package_deal=package_deal
        )
        self.line_items.append(line_item)
        return self

    def add_warning(self, warning: str) -> 'TransactionBuilder':
        """Add a warning to the transaction."""
        self.warnings.append(warning)
        return self

    def set_quote_duration(self, minutes: int) -> 'TransactionBuilder':
        """Set how long this quote is valid for."""
        self.quote_duration_minutes = minutes
        return self

    def build(self) -> TransactionPreview:
        """Build the final transaction preview."""
        # Calculate costs
        total_cost = sum(item.dust_cost for item in self.line_items)

        # Calculate what it would cost without package deals
        base_cost = 0
        for item in self.line_items:
            if item.package_deal:
                # Estimate base cost (this would use the individual action costs)
                base_cost += self._estimate_base_cost(item)
            else:
                base_cost += item.dust_cost

        savings = max(0, base_cost - total_cost)

        summary = TransactionSummary(
            base_cost=base_cost,
            final_cost=total_cost,
            savings=savings,
            items_count=len(self.line_items)
        )

        # Calculate balance after transaction
        balance_after = self.user_balance - total_cost

        # Add automatic warnings
        if balance_after < 0:
            self.warnings.append(
                f"Insufficient funds! You need {abs(balance_after)} more dust.")
        elif balance_after < 10:
            self.warnings.append(
                "Low balance warning: Less than 10 dust remaining after transaction.")

        # Set expiry
        expires_at = (
            datetime.now() + timedelta(minutes=self.quote_duration_minutes)).isoformat()

        return TransactionPreview(
            session_id=self.session_id,
            timestamp=datetime.now().isoformat(),
            line_items=self.line_items,
            summary=summary,
            user_balance=self.user_balance,
            balance_after=balance_after,
            expires_at=expires_at,
            warnings=self.warnings
        )

    def _estimate_base_cost(self, item: LineItem) -> int:
        """Estimate what this item would cost without package deals."""
        # This is a simple heuristic - in practice you'd look up individual costs
        if item.package_deal == "bulk_save":
            # Assume bulk save gives you a deal on multiple field saves
            field_count = len(item.parameters.get("fields", []))
            return field_count * 35  # Individual save_per_field cost
        elif item.package_deal == "premium_bundle":
            return int(item.dust_cost * 1.3)  # Assume 30% savings
        else:
            return item.dust_cost


class TransactionFormatter:
    """Formats transaction previews for display."""

    @staticmethod
    def to_console(preview: TransactionPreview) -> str:
        """Format transaction preview for console display."""
        lines = []
        lines.append(
            "╔══════════════════════════════════════════════════════════════╗")
        lines.append(
            "║                    TRANSACTION PREVIEW                       ║")
        lines.append(
            "╠══════════════════════════════════════════════════════════════╣")
        lines.append(f"║ Session: {preview.session_id[:50]:<50} ║")
        lines.append(f"║ Time: {preview.timestamp[:53]:<53} ║")
        if preview.expires_at:
            lines.append(f"║ Expires: {preview.expires_at[:52]:<52} ║")
        lines.append(
            "╠══════════════════════════════════════════════════════════════╣")

        # Line items
        lines.append(
            "║ ITEMS:                                                       ║")
        for i, item in enumerate(preview.line_items, 1):
            action_line = f"║ {i}. {item.action} - {item.description[:35]:<35}"
            cost_line = f"{item.dust_cost:>6} dust ║"
            lines.append(action_line + cost_line)

            if item.package_deal:
                deal_line = f"║    📦 Package Deal: {item.package_deal:<37} ║"
                lines.append(deal_line)

            # Show key parameters
            if item.parameters:
                key_params = []
                # Show first 2 params
                for key, value in list(item.parameters.items())[:2]:
                    if isinstance(value, list):
                        key_params.append(f"{key}: {len(value)} items")
                    else:
                        key_params.append(f"{key}: {str(value)[:20]}")

                if key_params:
                    param_text = ", ".join(key_params)
                    param_line = f"║    ↳ {param_text[:55]:<55} ║"
                    lines.append(param_line)

        lines.append(
            "╠══════════════════════════════════════════════════════════════╣")

        # Summary
        lines.append(
            "║ COST SUMMARY:                                                ║")
        if preview.summary.savings > 0:
            lines.append(
                f"║ Base Cost: {preview.summary.base_cost:>45} dust ║")
            lines.append(
                f"║ Package Savings: {preview.summary.savings:>39} dust ║")
            lines.append(
                f"║ Final Cost: {preview.summary.final_cost:>44} dust ║")
        else:
            lines.append(
                f"║ Total Cost: {preview.summary.final_cost:>44} dust ║")

        lines.append(
            "╠══════════════════════════════════════════════════════════════╣")

        # Balance info
        lines.append(
            "║ BALANCE:                                                     ║")
        lines.append(f"║ Current Balance: {preview.user_balance:>41} dust ║")
        lines.append(
            f"║ After Transaction: {preview.balance_after:>39} dust ║")

        # Warnings
        if preview.warnings:
            lines.append(
                "╠══════════════════════════════════════════════════════════════╣")
            lines.append(
                "║ ⚠️  WARNINGS:                                                ║")
            for warning in preview.warnings:
                # Word wrap warnings to fit in box
                words = warning.split()
                current_line = "║ "
                for word in words:
                    if len(current_line + word + " ") <= 63:
                        current_line += word + " "
                    else:
                        lines.append(f"{current_line:<63} ║")
                        current_line = "║   " + word + " "
                if current_line.strip() != "║":
                    lines.append(f"{current_line:<63} ║")

        lines.append(
            "╚══════════════════════════════════════════════════════════════╝")

        return "\n".join(lines)

    @staticmethod
    def to_json(preview: TransactionPreview) -> str:
        """Format transaction preview as JSON."""
        return json.dumps(asdict(preview), indent=2)

    @staticmethod
    def to_summary(preview: TransactionPreview) -> str:
        """Format as a brief summary."""
        items_text = f"{preview.summary.items_count} item{'s' if preview.summary.items_count != 1 else ''}"
        cost_text = f"{preview.summary.final_cost} dust"

        if preview.summary.savings > 0:
            cost_text += f" (saved {preview.summary.savings})"

        balance_text = f"Balance: {preview.user_balance} → {preview.balance_after}"

        warning_text = ""
        if preview.warnings:
            warning_text = f" ⚠️ {len(preview.warnings)} warning{'s' if len(preview.warnings) != 1 else ''}"

        return f"Transaction: {items_text}, {cost_text}, {balance_text}{warning_text}"


def create_transaction_preview(session_id: str, user_balance: int) -> TransactionBuilder:
    """Convenience function to create a transaction builder."""
    return TransactionBuilder(session_id, user_balance)
