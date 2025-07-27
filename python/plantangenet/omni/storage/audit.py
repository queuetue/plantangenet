# Copyright (c) 2025 Scott Russell
# SPDX-License-Identifier: MIT

"""
Audit logging system for tracking storage operations.
"""

import time
from datetime import datetime
from typing import Any, Dict, List, Optional


class AuditLogger:
    """
    In-memory audit logging system.
    
    Tracks all storage operations with timestamps, identity information,
    and change details for compliance and debugging purposes.
    """
    
    def __init__(self, enabled: bool = True, max_entries_per_omni: int = 1000):
        self.enabled = enabled
        self.max_entries_per_omni = max_entries_per_omni
        self._audit_log: Dict[str, List[Dict[str, Any]]] = {}
    
    async def log(
        self,
        omni_id: str,
        action: str,
        field_name: Optional[str] = None,
        old_value: Any = None,
        new_value: Any = None,
        identity_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Log an audit entry.
        
        Args:
            omni_id: ID of the omni being operated on
            action: Action being performed (e.g., "write", "delete", "sync")
            field_name: Optional field name being changed
            old_value: Previous value (for updates)
            new_value: New value (for updates)
            identity_id: ID of identity performing the action
            context: Additional context information
            
        Returns:
            Audit entry ID
        """
        if not self.enabled:
            return ""
        
        timestamp = time.time()
        audit_entry = {
            "timestamp": timestamp,
            "action": action,
            "identity_id": identity_id,
        }
        
        if field_name:
            audit_entry["field"] = field_name
        if old_value is not None:
            audit_entry["old_value"] = old_value
        if new_value is not None:
            audit_entry["new_value"] = new_value
        if context:
            audit_entry["context"] = context
        
        # Add to log
        if omni_id not in self._audit_log:
            self._audit_log[omni_id] = []
        
        self._audit_log[omni_id].append(audit_entry)
        
        # Trim log if too large
        if len(self._audit_log[omni_id]) > self.max_entries_per_omni:
            self._audit_log[omni_id] = self._audit_log[omni_id][-self.max_entries_per_omni:]
        
        return f"audit_{int(timestamp * 1000)}"
    
    async def get_log(
        self,
        omni_id: str,
        limit: int = 100,
        since: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Get audit log entries for an omni.
        
        Args:
            omni_id: ID of the omni
            limit: Maximum number of entries to return
            since: Optional datetime to filter entries after
            
        Returns:
            List of audit entries (most recent first)
        """
        if not self.enabled or omni_id not in self._audit_log:
            return []
        
        entries = self._audit_log[omni_id]
        
        # Filter by date if provided
        if since:
            since_timestamp = since.timestamp()
            entries = [e for e in entries if e["timestamp"] >= since_timestamp]
        
        # Return most recent entries
        return entries[-limit:]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get audit system statistics"""
        total_entries = sum(len(entries) for entries in self._audit_log.values())
        return {
            "enabled": self.enabled,
            "omnis_with_audit": len(self._audit_log),
            "total_entries": total_entries,
            "max_entries_per_omni": self.max_entries_per_omni
        }
    
    async def cleanup(self):
        """Cleanup audit resources"""
        # Could implement log archival here
        pass
    
    def clear_log(self, omni_id: str):
        """Clear audit log for a specific omni"""
        if omni_id in self._audit_log:
            del self._audit_log[omni_id]
    
    def clear_all_logs(self):
        """Clear all audit logs"""
        self._audit_log.clear()
