# Copyright (c) 2025 Scott Russell
# SPDX-License-Identifier: MIT

"""
Storage backend interface and base classes.

All storage adapters must implement the StorageBackend interface.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class StorageBackend(ABC):
    """
    Abstract base class for storage backends.
    
    All storage adapters must implement these methods to work with ManagedStorage.
    The backend is responsible for:
    - Persisting data in its specific format/protocol
    - Handling connection management and error recovery
    - Serializing/deserializing data appropriately
    """
    
    @abstractmethod
    async def store_data(self, key: str, data: Dict[str, Any]) -> bool:
        """
        Store data to backend.
        
        Args:
            key: Unique identifier for the data
            data: Dictionary containing the data to store
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def load_data(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Load data from backend.
        
        Args:
            key: Unique identifier for the data
            
        Returns:
            Dictionary containing the data, or None if not found
        """
        pass
    
    @abstractmethod
    async def delete_data(self, key: str) -> bool:
        """
        Delete data from backend.
        
        Args:
            key: Unique identifier for the data
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def list_keys(self, prefix: str = "") -> List[str]:
        """
        List available keys with optional prefix filter.
        
        Args:
            prefix: Optional prefix to filter keys
            
        Returns:
            List of keys matching the prefix
        """
        pass
    
    @abstractmethod
    async def store_version(self, key: str, version_id: str, data: Any) -> bool:
        """
        Store versioned data.
        
        Args:
            key: Base key for the data
            version_id: Unique version identifier
            data: Version data to store
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def load_version(self, key: str, version_id: Optional[str] = None) -> Optional[Any]:
        """
        Load versioned data.
        
        Args:
            key: Base key for the data
            version_id: Specific version to load, or None for latest
            
        Returns:
            Version data, or None if not found
        """
        pass
    
    @abstractmethod
    async def list_versions(self, key: str) -> List[Dict[str, Any]]:
        """
        List available versions for a key.
        
        Args:
            key: Base key for the data
            
        Returns:
            List of version metadata dictionaries with keys:
            - version_id: Unique version identifier
            - timestamp: Unix timestamp
            - datetime: ISO format datetime string
        """
        pass
    
    async def health_check(self) -> bool:
        """
        Check if backend is healthy and reachable.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            # Default implementation - try to list keys
            await self.list_keys("")
            return True
        except Exception:
            return False
    
    async def cleanup(self):
        """
        Cleanup backend resources.
        
        Called when the storage system is shutting down.
        Override to close connections, clear caches, etc.
        """
        pass


class BackendError(Exception):
    """Base exception for backend errors"""
    pass


class BackendConnectionError(BackendError):
    """Backend connection/network error"""
    pass


class BackendStorageError(BackendError):
    """Backend storage/persistence error"""
    pass


class BackendNotFoundError(BackendError):
    """Requested data not found in backend"""
    pass
