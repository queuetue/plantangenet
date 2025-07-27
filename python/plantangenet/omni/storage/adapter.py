# Copyright (c) 2025 Scott Russell
# SPDX-License-Identifier: MIT

"""
Simple storage adapter providing key-value interface over ManagedStorage.
"""

from typing import Any, Dict, List, Optional, Callable
from .core import ManagedStorage


class SimpleStorageAdapter:
    """
    Adapter providing simple key-value storage interface over ManagedStorage.
    
    This adapter bridges the gap between test expectations and the full
    OmniStorageMixin implementation, providing clean method signatures
    and proper event handling.
    """
    
    def __init__(self, managed_storage: ManagedStorage):
        self._storage = managed_storage
    
    # Delegate core setup methods
    def add_backend(self, name: str, backend, is_primary: bool = False):
        """Add a storage backend"""
        return self._storage.add_backend(name, backend, is_primary)
    
    async def initialize(self):
        """Initialize the storage system"""
        return await self._storage.initialize()
    
    async def cleanup(self):
        """Cleanup resources"""
        return await self._storage.cleanup()
    
    # Simple key-value interface
    async def store_data(self, key: str, data: dict) -> bool:
        """Store data with data_changed event notification"""
        try:
            # Capture old data for event
            old_data = await self.load_data(key)
            # Store new data using omni structured storage
            await self._storage.store_omni_structured(key, data)
            # Trigger named event for data change
            await self._storage.notifications.trigger_event('data_changed', key, old_data, data)
            return True
        except Exception:
            return False
    
    async def load_data(self, key: str) -> Optional[dict]:
        """Load data"""
        data = await self._storage.load_omni_structured(key)
        if data:
            # Filter out metadata fields for clean interface
            return {k: v for k, v in data.items() if not k.startswith('_')}
        return data
    
    async def delete_data(self, key: str) -> bool:
        """Delete data"""
        try:
            # Clear from cache
            self._storage._cache.delete(key)
            # Remove from backends
            for backend in self._storage._backends.values():
                try:
                    await backend.delete_data(key)
                except Exception:
                    pass  # Continue with other backends
            return True
        except Exception:
            return False
    
    def list_keys(self, prefix: str = "") -> List[str]:
        """List all keys currently in cache"""
        keys = list(self._storage._cache.keys())
        if prefix:
            keys = [k for k in keys if k.startswith(prefix)]
        return keys
    
    # Version management with proper signature
    async def store_version(self, key: str, version_id: str, data: any) -> bool:
        """Store version with explicit version_id"""
        try:
            result = await self._storage.store_omni_version(
                key, data, version_id=version_id
            )
            return bool(result)
        except Exception:
            return False
    
    async def load_version(self, key: str, version_id: str = None) -> any:
        """Load specific version or latest"""
        return await self._storage.load_omni_version(key, version_id)
    
    async def list_versions(self, key: str) -> list:
        """List available versions in chronological order (oldest first)"""
        versions = await self._storage.list_omni_versions(key)
        # Reverse to get chronological order (oldest first) for test compatibility
        return list(reversed(versions))
    
    # Relationship management
    async def store_relationship(self, subj: str, rel: str, obj: str) -> bool:
        """Store relationship between objects"""
        return await self._storage.add_omni_relationship(subj, obj, rel)
    
    async def get_related(self, omni_id: str, rel_type: str, reverse: bool = False) -> list:
        """Get related objects"""
        return await self._storage.get_omni_relationships(omni_id, rel_type, reverse)
    
    async def remove_relationship(self, subj: str, rel: str, obj: str) -> bool:
        """Remove relationship"""
        return await self._storage.remove_omni_relationship(subj, obj, rel)
    
    # Policy cache
    async def cache_policy_decision(self, identity: str, action: str, resource: str, 
                                   decision: bool, reason: str, ttl: int = 300) -> bool:
        """Cache policy decision"""
        return await self._storage.cache_policy_decision(
            identity, action, resource, decision, reason, ttl
        )
    
    async def get_cached_policy(self, identity: str, action: str, resource: str):
        """Get cached policy decision"""
        return await self._storage.get_cached_policy_decision(identity, action, resource)
    
    # Health and statistics
    async def check_health(self) -> Dict[str, Any]:
        """Check health of all backends"""
        return await self._storage.check_health()
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get storage statistics"""
        return await self._storage.get_statistics()
    
    # Notification management
    @property
    def notifications(self):
        """Access to notification system"""
        return self._storage.notifications
    
    def add_change_callback(self, callback: Callable):
        """Add change notification callback"""
        return self._storage.add_change_callback(callback)
