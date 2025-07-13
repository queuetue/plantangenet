from typing import Any, Optional
from .base import BaseSquad


class StorageSquad(BaseSquad):
    """Manages storage operations with integrated banker agent cost negotiation."""

    def __init__(self, session, name: Optional[str] = None):
        super().__init__(name)
        self.session = session

    def generate(self, group: str, omni_type: str, *args, **kwargs):
        """Generate a new storage operation or omni object."""
        operation = {
            "type": omni_type,
            "created_at": kwargs.get("timestamp"),
            "params": kwargs
        }
        self.add(group, operation)
        return operation

    def get_save_preview(self, omni: Any, incremental: bool = True):
        fields = list(omni.get_dirty_fields().keys()) if incremental and hasattr(
            omni, 'get_dirty_fields') else []
        params = {"fields": fields, "omni_id": getattr(
            omni, '_omni_id', 'unknown')}
        return self.session.negotiate_transaction("save_object", params)

    async def save_omni_with_cost(self, omni: Any, incremental: bool = True, selected_cost: Optional[int] = None):
        fields = list(omni.get_dirty_fields().keys()) if incremental and hasattr(
            omni, 'get_dirty_fields') else []
        params = {"fields": fields, "omni_id": getattr(
            omni, '_omni_id', 'unknown')}

        estimate = self.session.get_cost_estimate("save_object", params)
        if not estimate:
            success = await omni.save_to_storage(incremental)
            return {"success": success, "dust_charged": 0, "message": "Saved without cost"}

        cost = selected_cost or estimate.get("dust_cost")
        if not self.session.can_afford(cost):
            return {"success": False, "dust_charged": 0, "message": f"Insufficient dust. Need {cost}"}

        tx_result = self.session.commit_transaction(
            "save_object", params, cost)
        if tx_result["success"]:
            success = await omni.save_to_storage(incremental)
            self.add("completed_saves", {"omni_id": getattr(
                omni, '_omni_id', 'unknown'), "cost": tx_result["dust_charged"]})
            return {"success": success, "dust_charged": tx_result["dust_charged"], "transaction_id": tx_result.get("transaction_id")}
        else:
            return {"success": False, "dust_charged": 0, "message": tx_result["message"]}
