# Copyright (c) 2025 Scott Russell
# SPDX-License-Identifier: MIT

"""
PlantangeNet Omni Storage System

A modular storage system for omni objects with:
- In-memory caching with configurable eviction
- Multiple backend adapters (Redis, Registry, ConfigMap)
- Configurable sync strategies
- Audit logging and change notifications
- Version management and relationships
- Policy decision caching

To add a new storage adapter:
1. Inherit from backends.StorageBackend
2. Implement all abstract methods
3. Register with ManagedStorage via add_backend()

Example:
    from plantangenet.omni.storage import ManagedStorage, SyncStrategy
    from plantangenet.omni.storage.backends import RedisBackend
    
    storage = ManagedStorage(sync_strategy=SyncStrategy.WRITE_BACK)
    redis_backend = RedisBackend(redis_client, "omni")
    storage.add_backend("redis", redis_backend, is_primary=True)
"""

from .core import ManagedStorage, SyncStrategy
from .adapter import SimpleStorageAdapter
from .backends import StorageBackend
from .adapters.redis_adapter import RedisStorageAdapter
from .adapters.registry_adapter import RegistryStorageAdapter
from .adapters.configmap_adapter import ConfigMapStorageAdapter

__all__ = [
    "ManagedStorage",
    "SimpleStorageAdapter",
    "SyncStrategy", 
    "StorageBackend",
    "RedisStorageAdapter",
    "RegistryStorageAdapter", 
    "ConfigMapStorageAdapter"
]
