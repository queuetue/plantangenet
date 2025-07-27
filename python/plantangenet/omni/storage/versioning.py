# Copyright (c) 2025 Scott Russell
# SPDX-License-Identifier: MIT

"""
Version management system for omni objects.
"""

import time
from datetime import datetime
from typing import Any, Dict, List, Optional


class VersionManager:
    """
    Manages versions of omni objects with automatic cleanup.
    
    Stores versioned snapshots with timestamps and provides
    version listing and retrieval capabilities.
    """
    
    def __init__(self, max_versions_per_omni: int = 10):
        self.max_versions_per_omni = max_versions_per_omni
        self._versions: Dict[str, List[Dict[str, Any]]] = {}
    
    async def store_version(
        self,
        omni_id: str,
        version_data: Any,
        timestamp: Optional[float] = None,
        *,
        version_id: Optional[str] = None
    ) -> str:
        """
        Store a version of an omni.
        
        Args:
            omni_id: ID of the omni
            version_data: Data to version
            timestamp: Optional timestamp (defaults to current time)
            
        Returns:
            Version ID
        """
        timestamp = timestamp or time.time()
        # Use provided version_id or generate one
        if version_id is None:
            version_id_final = f"v_{int(timestamp * 1000)}"
        else:
            version_id_final = version_id
        
        # Create version entry
        version_entry = {
            "version_id": version_id_final,
            "timestamp": timestamp,
            "data": version_data
        }
        
        # Add to version list
        if omni_id not in self._versions:
            self._versions[omni_id] = []
        
        self._versions[omni_id].append(version_entry)
        
        # Sort by timestamp to maintain order
        self._versions[omni_id].sort(key=lambda v: v["timestamp"])
        
        # Limit number of versions
        if len(self._versions[omni_id]) > self.max_versions_per_omni:
            self._versions[omni_id] = self._versions[omni_id][-self.max_versions_per_omni:]
        
        return version_id_final
    
    async def load_version(
        self,
        omni_id: str,
        version_id: Optional[str] = None
    ) -> Optional[Any]:
        """
        Load a specific version or the latest version.
        
        Args:
            omni_id: ID of the omni
            version_id: Specific version ID, or None for latest
            
        Returns:
            Version data or None if not found
        """
        if omni_id not in self._versions:
            return None
        
        versions = self._versions[omni_id]
        if not versions:
            return None
        
        if version_id:
            # Find specific version
            for version in versions:
                if version["version_id"] == version_id:
                    return version["data"]
            return None
        else:
            # Return latest version
            return versions[-1]["data"]
    
    async def list_versions(
        self,
        omni_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        List available versions for an omni.
        
        Args:
            omni_id: ID of the omni
            limit: Maximum number of versions to return
            
        Returns:
            List of version metadata (most recent first)
        """
        if omni_id not in self._versions:
            return []
        
        versions = self._versions[omni_id][-limit:]
        return [
            {
                "version_id": v["version_id"],
                "timestamp": v["timestamp"],
                "datetime": datetime.fromtimestamp(v["timestamp"]).isoformat()
            }
            for v in reversed(versions)  # Most recent first
        ]
    
    def delete_version(self, omni_id: str, version_id: str) -> bool:
        """
        Delete a specific version.
        
        Args:
            omni_id: ID of the omni
            version_id: Version ID to delete
            
        Returns:
            True if version was found and deleted
        """
        if omni_id not in self._versions:
            return False
        
        versions = self._versions[omni_id]
        for i, version in enumerate(versions):
            if version["version_id"] == version_id:
                del versions[i]
                return True
        
        return False
    
    def delete_all_versions(self, omni_id: str):
        """
        Delete all versions for an omni.
        
        Args:
            omni_id: ID of the omni
        """
        if omni_id in self._versions:
            del self._versions[omni_id]
    
    def get_version_count(self, omni_id: str) -> int:
        """
        Get number of versions for an omni.
        
        Args:
            omni_id: ID of the omni
            
        Returns:
            Number of versions
        """
        if omni_id not in self._versions:
            return 0
        return len(self._versions[omni_id])
    
    def get_stats(self) -> Dict[str, Any]:
        """Get version system statistics"""
        total_versions = sum(len(versions) for versions in self._versions.values())
        
        version_counts = {}
        for omni_id, versions in self._versions.items():
            count = len(versions)
            if count not in version_counts:
                version_counts[count] = 0
            version_counts[count] += 1
        
        return {
            "omnis_with_versions": len(self._versions),
            "total_versions": total_versions,
            "max_versions_per_omni": self.max_versions_per_omni,
            "average_versions_per_omni": total_versions / len(self._versions) if self._versions else 0,
            "version_count_distribution": version_counts
        }
    
    def clear_all_versions(self):
        """Clear all versions for all omnis"""
        self._versions.clear()
