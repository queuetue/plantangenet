# Copyright (c) 1998-2025 Scott Russell
# SPDX-License-Identifier: MIT

import asyncio
import json
import pickle
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Union
import redis.asyncio as Redis

from .omni_storage import OmniStorageMixin
from .redis import RedisMixin


class RedisOmniStorageMixin(RedisMixin, OmniStorageMixin):
    """
    Redis implementation of enhanced omni storage with all advanced features:
    - Structured field storage using Redis hashes
    - Dirty field tracking with incremental updates
    - Versioning using Redis sorted sets
    - Cross-reference tracking with Redis sets
    - Policy decision caching
    - Change notifications via Redis pub/sub
    - Audit logging using Redis streams
    - Atomic operations using Lua scripts
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._lua_scripts = {}

    async def setup_storage(self, urls: list[str]) -> None:
        """Setup Redis storage and load Lua scripts"""
        await super().setup_storage(urls)
        if self._ocean__redis_client:
            await self._load_lua_scripts()

    async def _load_lua_scripts(self):
        """Load Lua scripts for atomic operations"""

        if not self._ocean__redis_client:
            return

        # Atomic field update with policy check script
        atomic_update_script = """
        local omni_key = KEYS[1]
        local conditions = cjson.decode(ARGV[1])
        local updates = cjson.decode(ARGV[2])
        
        -- Check conditions
        for field, expected_value in pairs(conditions) do
            local current_value = redis.call('HGET', omni_key, field)
            if current_value ~= expected_value then
                return {ok = false, reason = 'condition_failed', field = field}
            end
        end
        
        -- Apply updates
        for field, new_value in pairs(updates) do
            redis.call('HSET', omni_key, field, new_value)
        end
        
        return {ok = true}
        """

        # Atomic relationship management script
        relationship_script = """
        local parent_key = KEYS[1]
        local child_key = KEYS[2]
        local operation = ARGV[1]  -- 'add' or 'remove'
        local relationship_type = ARGV[2]
        
        if operation == 'add' then
            redis.call('SADD', parent_key .. ':' .. relationship_type, child_key)
            redis.call('SADD', child_key .. ':parents', parent_key)
        else
            redis.call('SREM', parent_key .. ':' .. relationship_type, child_key)
            redis.call('SREM', child_key .. ':parents', parent_key)
        end
        
        return true
        """

        try:
            self._lua_scripts['atomic_update'] = self._ocean__redis_client.register_script(
                atomic_update_script)
            self._lua_scripts['relationship'] = self._ocean__redis_client.register_script(
                relationship_script)
        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.warning(f"Failed to load Lua scripts: {e}")

    def _omni_key(self, omni_id: str) -> str:
        """Get the Redis key for an omni"""
        return f"{self.storage_root}:omni:{omni_id}"

    def _omni_version_key(self, omni_id: str) -> str:
        """Get the Redis key for omni versions"""
        return f"{self.storage_root}:omni:{omni_id}:versions"

    def _relationship_key(self, omni_id: str, relationship_type: str) -> str:
        """Get the Redis key for omni relationships"""
        return f"{self.storage_root}:omni:{omni_id}:{relationship_type}"

    def _policy_cache_key(self, identity_id: str, action: str, resource: str) -> str:
        """Get the Redis key for policy cache"""
        return f"{self.storage_root}:policy_cache:{identity_id}:{action}:{resource}"

    def _audit_stream_key(self, omni_id: str) -> str:
        """Get the Redis stream key for audit log"""
        return f"{self.storage_root}:audit:{omni_id}"

    async def store_omni_structured(
        self,
        omni_id: str,
        fields: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        identity_id: Optional[str] = None
    ) -> bool:
        """Store omni fields using Redis hash"""
        if not self._ocean__redis_client:
            return False

        try:
            key = self._omni_key(omni_id)

            # Prepare data for hash storage
            hash_data = {}
            for field_name, value in fields.items():
                if isinstance(value, (dict, list)):
                    hash_data[field_name] = json.dumps(value)
                else:
                    hash_data[field_name] = str(value)

            # Add metadata
            if metadata:
                for meta_key, meta_value in metadata.items():
                    hash_data[f"_meta_{meta_key}"] = json.dumps(meta_value) if isinstance(
                        meta_value, (dict, list)) else str(meta_value)

            # Add identity
            if identity_id:
                hash_data["_identity_id"] = identity_id

            # Add timestamp
            hash_data["_updated_at"] = str(time.time())

            # Store in Redis hash
            await self._ocean__redis_client.hset(key, mapping=hash_data)

            # Log audit entry
            await self.log_omni_audit(
                omni_id=omni_id,
                action="store_structured",
                identity_id=identity_id,
                context={"field_count": len(fields)}
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
        """Load omni fields from Redis hash"""
        if not self._ocean__redis_client:
            return None

        try:
            key = self._omni_key(omni_id)

            if field_names:
                # Load specific fields
                values = await self._ocean__redis_client.hmget(key, field_names)
                if not any(values):
                    return None
                result = dict(zip(field_names, values))
            else:
                # Load all fields
                result = await self._ocean__redis_client.hgetall(key)
                if not result:
                    return None

            # Convert values back to appropriate types
            processed_result = {}
            for field_name, value in result.items():
                if value is None:
                    continue

                if field_name.startswith("_meta_") or field_name in ["_identity_id", "_updated_at"]:
                    processed_result[field_name] = value
                else:
                    # Try to parse as JSON, fall back to string
                    try:
                        processed_result[field_name] = json.loads(value)
                    except (json.JSONDecodeError, TypeError):
                        processed_result[field_name] = value

            return processed_result

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
        """Update only dirty fields using Redis HSET"""
        if not self._ocean__redis_client or not dirty_fields:
            return False

        try:
            key = self._omni_key(omni_id)

            # Prepare dirty fields for Redis
            hash_updates = {}
            for field_name, value in dirty_fields.items():
                if isinstance(value, (dict, list)):
                    hash_updates[field_name] = json.dumps(value)
                else:
                    hash_updates[field_name] = str(value)

            # Update timestamp
            hash_updates["_updated_at"] = str(time.time())

            # Perform incremental update
            await self._ocean__redis_client.hset(key, mapping=hash_updates)

            # Log audit entries for each changed field
            for field_name in dirty_fields.keys():
                await self.log_omni_audit(
                    omni_id=omni_id,
                    action="write",
                    field_name=field_name,
                    new_value=dirty_fields[field_name],
                    identity_id=identity_id
                )

            # Publish change notifications
            for field_name, new_value in dirty_fields.items():
                await self.publish_omni_change(
                    omni_id=omni_id,
                    field_name=field_name,
                    old_value=None,  # Would need to track this separately
                    new_value=new_value,
                    identity_id=identity_id
                )

            return True

        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.error(
                    f"Failed to update omni {omni_id} fields: {e}")
            return False

    async def store_omni_version(
        self,
        omni_id: str,
        version_data: Any,
        timestamp: Optional[float] = None
    ) -> str:
        """Store omni version using Redis sorted set"""
        if not self._ocean__redis_client:
            return ""

        try:
            timestamp = timestamp or time.time()
            version_id = f"v_{int(timestamp * 1000)}"  # Millisecond precision

            # Serialize version data
            if isinstance(version_data, bytes):
                serialized_data = version_data
            else:
                serialized_data = pickle.dumps(version_data)

            # Store in sorted set with timestamp as score
            key = self._omni_version_key(omni_id)
            await self._ocean__redis_client.zadd(key, {serialized_data: timestamp})

            # Limit to last 10 versions to prevent unbounded growth
            await self._ocean__redis_client.zremrangebyrank(key, 0, -11)

            return version_id

        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.error(
                    f"Failed to store version for omni {omni_id}: {e}")
            return ""

    async def load_omni_version(
        self,
        omni_id: str,
        version_id: Optional[str] = None
    ) -> Optional[Any]:
        """Load omni version from Redis sorted set"""
        if not self._ocean__redis_client:
            return None

        try:
            key = self._omni_version_key(omni_id)

            if version_id:
                # Load specific version (would need to store version_id -> timestamp mapping)
                # For now, just get latest
                versions = await self._ocean__redis_client.zrevrange(key, 0, 0)
            else:
                # Get latest version
                versions = await self._ocean__redis_client.zrevrange(key, 0, 0)

            if not versions:
                return None

            # Deserialize
            return pickle.loads(versions[0])

        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.error(
                    f"Failed to load version for omni {omni_id}: {e}")
            return None

    async def list_omni_versions(
        self,
        omni_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """List available versions from Redis sorted set"""
        if not self._ocean__redis_client:
            return []

        try:
            key = self._omni_version_key(omni_id)

            # Get versions with scores (timestamps)
            versions = await self._ocean__redis_client.zrevrange(key, 0, limit - 1, withscores=True)

            result = []
            for i, (data, timestamp) in enumerate(versions):
                result.append({
                    "version_id": f"v_{int(timestamp * 1000)}",
                    "timestamp": timestamp,
                    "datetime": datetime.fromtimestamp(timestamp).isoformat(),
                    "index": i
                })

            return result

        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.error(
                    f"Failed to list versions for omni {omni_id}: {e}")
            return []

    async def add_omni_relationship(
        self,
        parent_id: str,
        child_id: str,
        relationship_type: str = "child"
    ) -> bool:
        """Add relationship using Redis sets"""
        if not self._ocean__redis_client:
            return False

        try:
            if 'relationship' in self._lua_scripts:
                # Use atomic Lua script
                parent_key = self._omni_key(parent_id)
                child_key = self._omni_key(child_id)
                await self._lua_scripts['relationship'](
                    keys=[parent_key, child_key],
                    args=['add', relationship_type]
                )
            else:
                # Fall back to individual operations
                parent_rel_key = self._relationship_key(
                    parent_id, relationship_type)
                child_parent_key = self._relationship_key(child_id, "parents")

                await self._ocean__redis_client.sadd(parent_rel_key, child_id)
                await self._ocean__redis_client.sadd(child_parent_key, parent_id)

            return True

        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.error(
                    f"Failed to add relationship {parent_id} -> {child_id}: {e}")
            return False

    async def remove_omni_relationship(
        self,
        parent_id: str,
        child_id: str,
        relationship_type: str = "child"
    ) -> bool:
        """Remove relationship using Redis sets"""
        if not self._ocean__redis_client:
            return False

        try:
            if 'relationship' in self._lua_scripts:
                # Use atomic Lua script
                parent_key = self._omni_key(parent_id)
                child_key = self._omni_key(child_id)
                await self._lua_scripts['relationship'](
                    keys=[parent_key, child_key],
                    args=['remove', relationship_type]
                )
            else:
                # Fall back to individual operations
                parent_rel_key = self._relationship_key(
                    parent_id, relationship_type)
                child_parent_key = self._relationship_key(child_id, "parents")

                await self._ocean__redis_client.srem(parent_rel_key, child_id)
                await self._ocean__redis_client.srem(child_parent_key, parent_id)

            return True

        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.error(
                    f"Failed to remove relationship {parent_id} -> {child_id}: {e}")
            return False

    async def get_omni_relationships(
        self,
        omni_id: str,
        relationship_type: str = "child",
        reverse: bool = False
    ) -> List[str]:
        """Get relationships using Redis sets"""
        if not self._ocean__redis_client:
            return []

        try:
            if reverse:
                # Find omnis that have this omni as a relationship
                key = self._relationship_key(omni_id, "parents")
            else:
                key = self._relationship_key(omni_id, relationship_type)

            members = await self._ocean__redis_client.smembers(key)
            return list(members) if members else []

        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.error(
                    f"Failed to get relationships for omni {omni_id}: {e}")
            return []

    async def cache_policy_decision(
        self,
        identity_id: str,
        action: str,
        resource: str,
        decision: bool,
        reason: str,
        ttl: int = 300
    ) -> bool:
        """Cache policy decision in Redis"""
        if not self._ocean__redis_client:
            return False

        try:
            key = self._policy_cache_key(identity_id, action, resource)
            value = json.dumps({
                "decision": decision,
                "reason": reason,
                "cached_at": time.time()
            })

            await self._ocean__redis_client.setex(key, ttl, value)
            return True

        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.error(f"Failed to cache policy decision: {e}")
            return False

    async def get_cached_policy_decision(
        self,
        identity_id: str,
        action: str,
        resource: str
    ) -> Optional[Dict[str, Any]]:
        """Get cached policy decision from Redis"""
        if not self._ocean__redis_client:
            return None

        try:
            key = self._policy_cache_key(identity_id, action, resource)
            value = await self._ocean__redis_client.get(key)

            if value:
                return json.loads(value)
            return None

        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.error(f"Failed to get cached policy decision: {e}")
            return None

    async def publish_omni_change(
        self,
        omni_id: str,
        field_name: str,
        old_value: Any,
        new_value: Any,
        identity_id: Optional[str] = None
    ) -> bool:
        """Publish change notification via Redis pub/sub"""
        if not self._ocean__redis_client:
            return False

        try:
            channel = f"{self.storage_root}:changes"
            message = json.dumps({
                "omni_id": omni_id,
                "field": field_name,
                "old_value": old_value,
                "new_value": new_value,
                "identity_id": identity_id,
                "timestamp": time.time()
            })

            await self._ocean__redis_client.publish(channel, message)
            return True

        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.error(
                    f"Failed to publish change notification: {e}")
            return False

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
        """Log audit entry using Redis streams"""
        if not self._ocean__redis_client:
            return ""

        try:
            stream_key = self._audit_stream_key(omni_id)

            # Prepare audit data
            audit_data = {
                "action": action,
                "timestamp": str(time.time()),
                "identity_id": identity_id or "",
            }

            if field_name:
                audit_data["field"] = field_name
            if old_value is not None:
                audit_data["old_value"] = json.dumps(old_value) if isinstance(
                    old_value, (dict, list)) else str(old_value)
            if new_value is not None:
                audit_data["new_value"] = json.dumps(new_value) if isinstance(
                    new_value, (dict, list)) else str(new_value)
            if context:
                audit_data["context"] = json.dumps(context)

            # Add to stream
            entry_id = await self._ocean__redis_client.xadd(stream_key, audit_data)

            # Trim stream to last 1000 entries
            await self._ocean__redis_client.xtrim(stream_key, maxlen=1000, approximate=True)

            return entry_id

        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.error(f"Failed to log audit entry: {e}")
            return ""

    async def get_omni_audit_log(
        self,
        omni_id: str,
        limit: int = 100,
        since: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get audit log from Redis streams"""
        if not self._ocean__redis_client:
            return []

        try:
            stream_key = self._audit_stream_key(omni_id)

            # Determine start position
            start = "0"
            if since:
                # Convert datetime to Redis stream ID format
                timestamp_ms = int(since.timestamp() * 1000)
                start = f"{timestamp_ms}-0"

            # Read from stream
            entries = await self._ocean__redis_client.xrevrange(stream_key, max="+", min=start, count=limit)

            result = []
            for entry_id, fields in entries:
                audit_entry = {"id": entry_id}
                for field, value in fields.items():
                    if field in ["old_value", "new_value", "context"] and value:
                        try:
                            audit_entry[field] = json.loads(value)
                        except json.JSONDecodeError:
                            audit_entry[field] = value
                    else:
                        audit_entry[field] = value
                result.append(audit_entry)

            return result

        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.error(
                    f"Failed to get audit log for omni {omni_id}: {e}")
            return []

    async def atomic_omni_update(
        self,
        omni_id: str,
        updates: Dict[str, Any],
        conditions: Optional[Dict[str, Any]] = None,
        identity_id: Optional[str] = None
    ) -> bool:
        """Perform atomic update using Lua script"""
        if not self._ocean__redis_client or not updates:
            return False

        try:
            if 'atomic_update' in self._lua_scripts and conditions:
                # Use Lua script for atomic conditional update
                key = self._omni_key(omni_id)
                result = await self._lua_scripts['atomic_update'](
                    keys=[key],
                    args=[json.dumps(conditions), json.dumps(updates)]
                )

                if result.get('ok'):
                    # Log audit entries
                    for field_name, new_value in updates.items():
                        await self.log_omni_audit(
                            omni_id=omni_id,
                            action="atomic_write",
                            field_name=field_name,
                            new_value=new_value,
                            identity_id=identity_id
                        )
                    return True
                else:
                    if hasattr(self, 'logger'):
                        self.logger.warning(
                            f"Atomic update failed: {result.get('reason')}")
                    return False
            else:
                # Fall back to regular update
                return await self.update_omni_fields(omni_id, updates, identity_id)

        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.error(
                    f"Failed atomic update for omni {omni_id}: {e}")
            return False
