# Copyright (c) 2025 Scott Russell
# SPDX-License-Identifier: MIT

"""
Storage adapters for different backend systems.
"""

from .redis_adapter import RedisStorageAdapter
from .registry_adapter import RegistryStorageAdapter
from .configmap_adapter import ConfigMapStorageAdapter

__all__ = [
    "RedisStorageAdapter",
    "RegistryStorageAdapter", 
    "ConfigMapStorageAdapter"
]
