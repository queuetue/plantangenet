# Copyright (c) 2025 Scott Russell
# SPDX-License-Identifier: MIT

"""
Core storage management system.

Provides in-memory caching with configurable backend synchronization,
audit logging, change notifications, and relationship tracking.
"""

import asyncio
import time
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Callable

from ..mixins.omni_storage import OmniStorageMixin
from .backends import StorageBackend
from .cache import LRUCache
from .audit import AuditLogger
from .relationships import RelationshipManager
from .policy_cache import PolicyCache
from .versioning import VersionManager
from .notifications import ChangeNotifier


class SyncStrategy(Enum):
    """Synchronization strategies for managed storage"""
    WRITE_THROUGH = "write_through"  # Immediate sync on writes
    WRITE_BACK = "write_back"       # Periodic sync of dirty data
    READ_THROUGH = "read_through"   # Load from backend on cache miss
    READ_AHEAD = "read_ahead"       # Preload related data


class ManagedStorage(OmniStorageMixin):
    """
    Managed storage system with in-memory cache and backend synchronization.
    
    Features:
    - LRU cache with configurable size
    - Multiple backend support
    - Configurable sync strategies
    - Audit logging
    - Change notifications
    - Relationship tracking
    - Policy decision caching
    - Version management
    """

    def __init__(
        self,
        max_memory_items: int = 10000,
        sync_strategy: SyncStrategy = SyncStrategy.WRITE_BACK,
        sync_interval: float = 30.0,
        max_versions_per_omni: int = 10,
        audit_enabled: bool = True
    ):
        # Core components
        self._cache = LRUCache(max_items=max_memory_items)
        self._audit = AuditLogger(enabled=audit_enabled)
        self._relationships = RelationshipManager()
        self._policy_cache = PolicyCache()
        self._versions = VersionManager(max_versions_per_omni=max_versions_per_omni)
        self._notifier = ChangeNotifier()
        
        # Backend management
        self._backends: Dict[str, StorageBackend] = {}
        self._primary_backend: Optional[str] = None
        self._sync_strategy = sync_strategy
        self._sync_interval = sync_interval
        self._sync_task: Optional[asyncio.Task] = None
        
        # Dirty tracking for write-back strategy
        self._dirty_items: Set[str] = set()
        
        # Start background sync if needed
        if sync_strategy == SyncStrategy.WRITE_BACK:
            self._start_sync_task()

    def add_backend(self, name: str, backend: StorageBackend, is_primary: bool = False):
        """
        Add a storage backend.
        
        Args:
            name: Unique name for the backend
            backend: Backend implementation
            is_primary: Whether this should be the primary backend
        """
        self._backends[name] = backend
        if is_primary or not self._primary_backend:
            self._primary_backend = name

    def add_change_callback(self, callback: Callable):
        """Add callback for change notifications"""
        self._notifier.add_callback(callback)

    def _start_sync_task(self):
        """Start background sync task"""
        if self._sync_task:
            self._sync_task.cancel()
        self._sync_task = asyncio.create_task(self._background_sync())

    async def _background_sync(self):
        """Background task for periodic synchronization"""
        while True:
            try:
                await asyncio.sleep(self._sync_interval)
                await self._sync_dirty_items()
            except asyncio.CancelledError:
                break
            except Exception as e:
                if hasattr(self, 'logger'):
                    self.logger.error(f"Background sync error: {e}")

    async def _sync_dirty_items(self):
        """Sync all dirty items to primary backend"""
        if not self._dirty_items or not self._primary_backend:
            return

        backend = self._backends.get(self._primary_backend)
        if not backend:
            return

        dirty_copy = set(self._dirty_items)
        for omni_id in dirty_copy:
            try:
                data = self._cache.get(omni_id)
                if data is not None:
                    # Filter out metadata fields before syncing to backends
                    filtered_data = {k: v for k, v in data.items() if not k.startswith('_')}
                    await backend.store_data(omni_id, filtered_data)
                    self._dirty_items.discard(omni_id)
                    
                    # Log sync audit
                    await self._audit.log(
                        omni_id=omni_id,
                        action="sync_to_backend",
                        context={"backend": self._primary_backend}
                    )
            except Exception as e:
                if hasattr(self, 'logger'):
                    self.logger.error(f"Failed to sync {omni_id}: {e}")

    async def _load_from_backend(self, omni_id: str) -> Optional[Dict[str, Any]]:
        """Load data from primary backend"""
        if not self._primary_backend:
            return None

        backend = self._backends.get(self._primary_backend)
        if not backend:
            return None

        try:
            data = await backend.load_data(omni_id)
            if data:
                self._cache.put(omni_id, data)
            return data
        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.error(f"Failed to load {omni_id} from backend: {e}")
            return None

    async def _sync_to_backends(self, omni_id: str, data: Dict[str, Any]):
        """Sync data to backends based on strategy"""
        # Filter out metadata fields before syncing to backends
        filtered_data = {k: v for k, v in data.items() if not k.startswith('_')}
        
        if self._sync_strategy == SyncStrategy.WRITE_THROUGH:
            # Immediate sync to all backends
            for name, backend in self._backends.items():
                try:
                    await backend.store_data(omni_id, filtered_data)
                except Exception as e:
                    if hasattr(self, 'logger'):
                        self.logger.error(f"Failed to sync to {name}: {e}")
        elif self._sync_strategy == SyncStrategy.WRITE_BACK:
            # Mark as dirty for later sync
            self._dirty_items.add(omni_id)

    # OmniStorageMixin implementation

    async def store_omni_structured(
        self,
        omni_id: str,
        fields: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        identity_id: Optional[str] = None
    ) -> bool:
        """Store omni fields in structured way"""
        try:
            # Get existing data or create new
            existing_data = self._cache.get(omni_id) or {}
            old_data = existing_data.copy()
            
            # Update with new fields
            existing_data.update(fields)
            
            # Add identity and timestamp
            if identity_id:
                existing_data["_identity_id"] = identity_id
            existing_data["_updated_at"] = time.time()
            
            # Store in cache
            self._cache.put(omni_id, existing_data)
            
            # Sync to backends
            await self._sync_to_backends(omni_id, existing_data)
            
            # Log audit
            await self._audit.log(
                omni_id=omni_id,
                action="store_structured",
                identity_id=identity_id,
                context={"field_count": len(fields)}
            )
            
            # Notify changes
            for field_name, new_value in fields.items():
                old_value = old_data.get(field_name)
                if old_value != new_value:
                    await self._notifier.notify_change(
                        omni_id, field_name, old_value, new_value, identity_id
                    )
            
            return True
            
        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.error(f"Failed to store omni {omni_id}: {e}")
            return False

    async def load_omni_structured(
        self,
        omni_id: str,
        field_names: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """Load omni fields from structured storage"""
        try:
            # Check cache first
            data = self._cache.get(omni_id)
            
            if data is None:
                # Load from backend if cache miss
                if self._sync_strategy in [SyncStrategy.READ_THROUGH, SyncStrategy.READ_AHEAD]:
                    data = await self._load_from_backend(omni_id)
                    if not data:
                        return None
                else:
                    return None
            
            # Filter fields if requested
            if field_names:
                return {k: data.get(k) for k in field_names if k in data}
            
            return data.copy()
            
        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.error(f"Failed to load omni {omni_id}: {e}")
            return None

    async def update_omni_fields(
        self,
        omni_id: str,
        dirty_fields: Dict[str, Any],
        identity_id: Optional[str] = None
    ) -> bool:
        """Update only dirty fields"""
        try:
            # Get existing data
            existing_data = self._cache.get(omni_id)
            if existing_data is None:
                # Try to load from backend
                existing_data = await self._load_from_backend(omni_id)
                if not existing_data:
                    existing_data = {}
            
            old_data = existing_data.copy()
            
            # Update fields
            existing_data.update(dirty_fields)
            existing_data["_updated_at"] = time.time()
            
            # Store in cache
            self._cache.put(omni_id, existing_data)
            
            # Sync to backends
            await self._sync_to_backends(omni_id, existing_data)
            
            # Log audit entries for each changed field
            for field_name, new_value in dirty_fields.items():
                old_value = old_data.get(field_name)
                await self._audit.log(
                    omni_id=omni_id,
                    action="write",
                    field_name=field_name,
                    old_value=old_value,
                    new_value=new_value,
                    identity_id=identity_id
                )
                
                # Notify changes
                await self._notifier.notify_change(
                    omni_id, field_name, old_value, new_value, identity_id
                )
            
            return True
            
        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.error(f"Failed to update omni {omni_id} fields: {e}")
            return False

    async def store_omni_version(
        self,
        omni_id: str,
        version_data: Any,
        timestamp: Optional[float] = None,
        version_id: Optional[str] = None
    ) -> str:
        """Store omni version, using provided version_id or generating one"""
        try:
            # Store version in memory, allow explicit version_id override
            vid = await self._versions.store_version(
                omni_id, version_data, timestamp, version_id=version_id
            )
            
            # Store to primary backend if configured
            if self._primary_backend:
                backend = self._backends.get(self._primary_backend)
                if backend:
                    await backend.store_version(omni_id, vid, version_data)
            
            return vid
            
        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.error(f"Failed to store version for omni {omni_id}: {e}")
            return ""

    async def load_omni_version(
        self,
        omni_id: str,
        version_id: Optional[str] = None
    ) -> Optional[Any]:
        """Load omni version"""
        try:
            # Check memory first
            data = await self._versions.load_version(omni_id, version_id)
            if data is not None:
                return data
            
            # Try backend
            if self._primary_backend:
                backend = self._backends.get(self._primary_backend)
                if backend:
                    return await backend.load_version(omni_id, version_id)
            
            return None
            
        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.error(f"Failed to load version for omni {omni_id}: {e}")
            return None

    async def list_omni_versions(
        self,
        omni_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """List available versions"""
        try:
            # Check memory first
            versions = await self._versions.list_versions(omni_id, limit)
            if versions:
                return versions
            
            # Try backend
            if self._primary_backend:
                backend = self._backends.get(self._primary_backend)
                if backend:
                    return await backend.list_versions(omni_id)
            
            return []
            
        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.error(f"Failed to list versions for omni {omni_id}: {e}")
            return []

    async def add_omni_relationship(
        self,
        parent_id: str,
        child_id: str,
        relationship_type: str = "child"
    ) -> bool:
        """Add relationship between omnis"""
        return await self._relationships.add_relationship(parent_id, child_id, relationship_type)

    async def remove_omni_relationship(
        self,
        parent_id: str,
        child_id: str,
        relationship_type: str = "child"
    ) -> bool:
        """Remove relationship between omnis"""
        return await self._relationships.remove_relationship(parent_id, child_id, relationship_type)

    async def get_omni_relationships(
        self,
        omni_id: str,
        relationship_type: str = "child",
        reverse: bool = False
    ) -> List[str]:
        """Get relationships for an omni"""
        return await self._relationships.get_relationships(omni_id, relationship_type, reverse)

    async def cache_policy_decision(
        self,
        identity_id: str,
        action: str,
        resource: str,
        decision: bool,
        reason: str,
        ttl: int = 300
    ) -> bool:
        """Cache policy decision"""
        return await self._policy_cache.cache_decision(identity_id, action, resource, decision, reason, ttl)

    async def get_cached_policy_decision(
        self,
        identity_id: str,
        action: str,
        resource: str
    ) -> Optional[Dict[str, Any]]:
        """Get cached policy decision"""
        return await self._policy_cache.get_decision(identity_id, action, resource)

    async def publish_omni_change(
        self,
        omni_id: str,
        field_name: str,
        old_value: Any,
        new_value: Any,
        identity_id: Optional[str] = None
    ) -> bool:
        """Publish change notification"""
        await self._notifier.notify_change(omni_id, field_name, old_value, new_value, identity_id)
        return True

    async def log_omni_audit(
        self,
        omni_id: str,
        action: str,
        field_name: Optional[str] = None,
        old_value: Any = None,
        new_value: Any = None,
        identity_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Log audit entry"""
        return await self._audit.log(omni_id, action, field_name, old_value, new_value, identity_id, context)
    
    async def check_health(self) -> Dict[str, Any]:
        """Check health of all configured backends"""
        status_map: Dict[str, bool] = {}
        for name, backend in self._backends.items():
            try:
                status_map[name] = await backend.health_check()
            except Exception:
                status_map[name] = False
        overall = 'healthy' if all(status_map.values()) else 'unhealthy'
        return {'status': overall, 'backends': status_map}
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get storage statistics for cache and backends"""
        stats: Dict[str, Any] = {}
        # Cache stats
        cache_stats = self._cache.get_stats()
        cache_stats['size'] = len(self._cache.cache)  # Add size field
        stats['cache'] = cache_stats
        # Backend names
        stats['backends'] = list(self._backends.keys())
        return stats

    async def get_omni_audit_log(
        self,
        omni_id: str,
        limit: int = 100,
        since: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get audit log"""
        return await self._audit.get_log(omni_id, limit, since)

    async def atomic_omni_update(
        self,
        omni_id: str,
        updates: Dict[str, Any],
        conditions: Optional[Dict[str, Any]] = None,
        identity_id: Optional[str] = None
    ) -> bool:
        """Perform atomic update with conditions"""
        try:
            # Load current data
            current_data = await self.load_omni_structured(omni_id)
            if not current_data and conditions:
                return False
            
            # Check conditions
            if conditions:
                for field, expected_value in conditions.items():
                    current_value = current_data.get(field) if current_data else None
                    if current_value != expected_value:
                        if hasattr(self, 'logger'):
                            self.logger.warning(f"Atomic update condition failed for field {field}")
                        return False
            
            # Apply updates
            return await self.update_omni_fields(omni_id, updates, identity_id)
            
        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.error(f"Failed atomic update for omni {omni_id}: {e}")
            return False

    # Utility methods

    async def flush_to_backends(self):
        """Force flush all dirty items to backends"""
        await self._sync_dirty_items()

    async def preload_omni(self, omni_id: str) -> bool:
        """Preload omni from backend to memory"""
        if self._cache.get(omni_id) is None:
            data = await self._load_from_backend(omni_id)
            return data is not None
        return True

    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory usage statistics"""
        return {
            "cache_stats": self._cache.get_stats(),
            "dirty_items": len(self._dirty_items),
            "relationship_stats": self._relationships.get_stats(),
            "policy_cache_stats": self._policy_cache.get_stats(),
            "version_stats": self._versions.get_stats(),
            "audit_stats": self._audit.get_stats()
        }

    async def cleanup(self):
        """Cleanup resources"""
        # Cancel sync task
        if self._sync_task:
            self._sync_task.cancel()
            try:
                await self._sync_task
            except asyncio.CancelledError:
                pass
        
        # Final sync
        await self._sync_dirty_items()
        
        # Cleanup backends
        for backend in self._backends.values():
            await backend.cleanup()
        
        # Cleanup components
        await self._audit.cleanup()
        await self._notifier.cleanup()
    
    async def initialize(self):
        """Initialize the storage system"""
        # Start the background sync task if using write-back strategy
        if self._sync_strategy == SyncStrategy.WRITE_BACK:
            self._start_sync_task()

    @property
    def notifications(self):
        """Access to the notification system"""
        return self._notifier