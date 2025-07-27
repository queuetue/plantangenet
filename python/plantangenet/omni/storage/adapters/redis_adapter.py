# Copyright (c) 2025 Scott Russell
# SPDX-License-Identifier: MIT

"""
Redis storage adapter implementation.

Provides Redis backend support for the managed storage system
using Redis hashes for structured data and sorted sets for versioning.
"""

import json
import pickle
import time
from typing import Any, Dict, List, Optional

import redis.asyncio as Redis

from ..backends import StorageBackend, BackendError, BackendConnectionError


class RedisStorageAdapter(StorageBackend):
    """
    Redis backend adapter for managed storage.
    
    Features:
    - Uses Redis hashes for structured field storage
    - Sorted sets for version management with timestamps
    - Automatic key prefixing for namespace isolation
    - JSON serialization for complex data types
    - Pickle serialization for version data
    
    Example:
        redis_client = Redis.from_url("redis://localhost:6379/0")
        adapter = RedisStorageAdapter(redis_client, key_prefix="plantangenet")
        storage.add_backend("redis", adapter, is_primary=True)
    """
    
    def __init__(self, redis_client: Redis.Redis, key_prefix: str = "omni"):
        """
        Initialize Redis adapter.
        
        Args:
            redis_client: Async Redis client instance
            key_prefix: Prefix for all Redis keys (for namespace isolation)
        """
        self.redis = redis_client
        self.key_prefix = key_prefix
    
    def _key(self, key: str) -> str:
        """Generate prefixed Redis key"""
        return f"{self.key_prefix}:{key}"
    
    def _version_key(self, key: str) -> str:
        """Generate prefixed Redis key for versions"""
        return f"{self.key_prefix}:versions:{key}"
    
    async def store_data(self, key: str, data: Dict[str, Any]) -> bool:
        """
        Store data as Redis hash.
        
        Complex data types (dict, list) are JSON-serialized.
        Simple types are stored as strings.
        """
        try:
            # Prepare data for Redis hash storage
            hash_data = {}
            for field_name, value in data.items():
                if isinstance(value, (dict, list)):
                    hash_data[field_name] = json.dumps(value)
                else:
                    hash_data[field_name] = str(value)
            
            await self.redis.hset(self._key(key), mapping=hash_data)
            return True
            
        except Exception as e:
            raise BackendError(f"Failed to store data in Redis: {e}")
    
    async def load_data(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Load data from Redis hash.
        
        JSON-deserializes complex types, returns simple types as-is.
        """
        try:
            data = await self.redis.hgetall(self._key(key))
            if not data:
                return None
            
            # Convert values back to appropriate types
            result = {}
            for field_name, value in data.items():
                if value is None:
                    continue
                
                # Try JSON parsing first, fall back to string
                try:
                    result[field_name] = json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    result[field_name] = value
            
            return result
            
        except Exception as e:
            raise BackendError(f"Failed to load data from Redis: {e}")
    
    async def delete_data(self, key: str) -> bool:
        """Delete data from Redis"""
        try:
            deleted = await self.redis.delete(self._key(key))
            return deleted > 0
            
        except Exception as e:
            raise BackendError(f"Failed to delete data from Redis: {e}")
    
    async def list_keys(self, prefix: str = "") -> List[str]:
        """
        List keys matching prefix.
        
        Returns keys with the adapter's key prefix removed.
        """
        try:
            pattern = f"{self.key_prefix}:{prefix}*" if prefix else f"{self.key_prefix}:*"
            keys = await self.redis.keys(pattern)
            
            # Remove adapter prefix and return
            prefix_len = len(self.key_prefix) + 1
            return [
                (key.decode() if isinstance(key, bytes) else key)[prefix_len:]
                for key in keys
            ]
            
        except Exception as e:
            raise BackendError(f"Failed to list keys from Redis: {e}")
    
    async def store_version(self, key: str, version_id: str, data: Any) -> bool:
        """
        Store version using Redis sorted set.
        
        Uses current timestamp as score for automatic ordering.
        Limits to last 10 versions per key.
        """
        try:
            timestamp = time.time()
            serialized = pickle.dumps(data)
            
            # Add to sorted set with timestamp as score
            await self.redis.zadd(
                self._version_key(key),
                {serialized: timestamp}
            )
            
            # Keep only last 10 versions (remove older ones)
            await self.redis.zremrangebyrank(self._version_key(key), 0, -11)
            
            return True
            
        except Exception as e:
            raise BackendError(f"Failed to store version in Redis: {e}")
    
    async def load_version(self, key: str, version_id: Optional[str] = None) -> Optional[Any]:
        """
        Load version from Redis sorted set.
        
        If version_id is None, returns the latest version (highest score).
        """
        try:
            # Get latest version (highest score)
            versions = await self.redis.zrevrange(self._version_key(key), 0, 0)
            if not versions:
                return None
            
            return pickle.loads(versions[0])
            
        except Exception as e:
            raise BackendError(f"Failed to load version from Redis: {e}")
    
    async def list_versions(self, key: str) -> List[Dict[str, Any]]:
        """
        List versions from Redis sorted set.
        
        Returns version metadata sorted by timestamp (newest first).
        """
        try:
            # Get all versions with scores (timestamps)
            versions = await self.redis.zrevrange(
                self._version_key(key), 0, -1, withscores=True
            )
            
            return [
                {
                    "version_id": f"v_{int(timestamp * 1000)}",
                    "timestamp": timestamp,
                    "datetime": time.strftime('%Y-%m-%dT%H:%M:%S', time.gmtime(timestamp))
                }
                for _, timestamp in versions
            ]
            
        except Exception as e:
            raise BackendError(f"Failed to list versions from Redis: {e}")
    
    async def health_check(self) -> bool:
        """Check Redis connection health"""
        try:
            await self.redis.ping()
            return True
        except Exception:
            return False
    
    async def cleanup(self):
        """Cleanup Redis connection"""
        try:
            if hasattr(self.redis, 'close'):
                await self.redis.close()
        except Exception:
            pass  # Best effort cleanup
