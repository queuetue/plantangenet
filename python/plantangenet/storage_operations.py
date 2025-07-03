"""
Storage Operations with Banker Agent Integration.
Provides cost-aware storage operations with transaction previews using banker agents.
"""

from typing import Dict, Any, Optional, List
from .session import Session
from .banker import Banker
from .omni.enhanced_omni import EnhancedOmni


class StorageOperationsManager:
    """
    Manages storage operations with integrated banker agent cost negotiation and previews.
    """

    def __init__(self, session: Session):
        """
        Initialize storage operations manager.

        Args:
            session: The user session with banker agents
        """
        self.session = session

    def get_save_preview(self, omni: Any, incremental: bool = True) -> Optional[Dict[str, Any]]:
        """
        Get a preview of the cost to save an omni object using the session's banker.

        Args:
            omni: The omni object to save
            incremental: Whether to save only dirty fields

        Returns:
            Negotiation result with preview, or None if no banker available
        """
        # Determine fields to save
        if incremental and hasattr(omni, 'get_dirty_fields'):
            fields = list(omni.get_dirty_fields().keys())
            action = "save_object"
        else:
            fields = list(omni.__class__._omni_all_fields) if hasattr(
                omni, '__class__') else []
            action = "save_object"

        params = {"fields": fields, "omni_id": getattr(
            omni, '_omni_id', 'unknown')}

        # Use session's banker for negotiation
        return self.session.negotiate_transaction(action, params)

    async def save_omni_with_cost(self, omni: Any, incremental: bool = True,
                                  selected_cost: Optional[int] = None,
                                  show_preview: bool = True) -> Dict[str, Any]:
        """
        Save an omni object with cost negotiation and preview through session's banker.

        Args:
            omni: The omni object to save
            incremental: Whether to save only dirty fields
            selected_cost: The selected cost option (for package deals)
            show_preview: Whether to show the preview before proceeding

        Returns:
            Dictionary with save result and cost information
        """
        # Determine action parameters
        if incremental and hasattr(omni, 'get_dirty_fields'):
            fields = list(omni.get_dirty_fields().keys())
        else:
            fields = list(omni.__class__._omni_all_fields) if hasattr(
                omni, '__class__') else []

        params = {"fields": fields, "omni_id": getattr(
            omni, '_omni_id', 'unknown')}

        # Get cost estimate first
        estimate = self.session.get_cost_estimate("save_object", params)

        if not estimate:
            # No cost base - proceed with regular save
            success = await omni.save_to_storage(incremental)
            return {
                "success": success,
                "dust_charged": 0,
                "message": "Saved without cost (no cost base loaded)"
            }

        # Get negotiation with preview if requested
        if show_preview:
            negotiation = self.session.negotiate_transaction(
                "save_object", params)
            if negotiation and negotiation.get("preview"):
                print("=== Storage Operation Preview ===")
                # Format the preview (in a real app, you'd use the format function)
                preview = negotiation["preview"]
                print(f"Action: save_object")
                print(f"Fields: {len(fields)} fields")
                print(f"Cost base: {negotiation['cost_base']}")
                print(f"Estimated cost: {estimate['dust_cost']} dust")
                print(
                    f"Current balance: {self.session.get_dust_balance()} dust")
                print()

        # Determine cost to use
        cost = selected_cost or estimate.get("dust_cost")

        if cost is None:
            return {
                "success": False,
                "dust_charged": 0,
                "message": "Unable to determine cost for save operation"
            }

        # Check if session can afford it
        if not self.session.can_afford(cost):
            return {
                "success": False,
                "dust_charged": 0,
                "message": f"Insufficient dust. Need {cost}, have {self.session.get_dust_balance()}"
            }

        # Commit transaction through session's banker
        tx_result = self.session.commit_transaction(
            "save_object", params, cost)

        if tx_result["success"]:
            # Perform the actual save
            success = await omni.save_to_storage(incremental)

            if success:
                return {
                    "success": True,
                    "dust_charged": tx_result["dust_charged"],
                    "message": f"Successfully saved and charged {tx_result['dust_charged']} dust",
                    "transaction_id": tx_result.get("transaction_id")
                }
            else:
                # Refund if save failed (would need to implement refund in banker)
                return {
                    "success": False,
                    "dust_charged": tx_result["dust_charged"],
                    "message": "Save failed after dust was charged (refund needed)"
                }
        else:
            return {
                "success": False,
                "dust_charged": 0,
                "message": tx_result["message"]
            }

    def get_load_preview(self, omni_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a preview of the cost to load an omni object using the session's banker.

        Args:
            omni_id: ID of the omni to load

        Returns:
            Negotiation result with preview, or None if no banker available
        """
        params = {"omni_id": omni_id}
        return self.session.negotiate_transaction("load_object", params)


# Convenience functions for easy integration

def create_storage_manager(session: Session) -> StorageOperationsManager:
    """
    Create a storage operations manager for a session.

    Args:
        session: User session with banker agents

    Returns:
        Configured StorageOperationsManager
    """
    return StorageOperationsManager(session)


async def save_with_preview(omni: Any, session: Session, incremental: bool = True) -> Dict[str, Any]:
    """
    Convenience function to save an omni with cost preview using session's banker.

    Args:
        omni: Omni object to save
        session: User session with banker agents
        incremental: Whether to save incrementally

    Returns:
        Save result
    """
    manager = create_storage_manager(session)
    return await manager.save_omni_with_cost(omni, incremental)
