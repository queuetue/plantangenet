# Copyright (c) 2025 Scott Russell
# SPDX-License-Identifier: MIT

"""
Policy decision caching system.
"""

import time
from typing import Any, Dict, Optional


class PolicyCache:
    """
    Caches policy decisions to avoid repeated expensive policy evaluations.
    
    Supports TTL-based expiration and automatic cleanup of expired entries.
    """
    
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._ttl: Dict[str, float] = {}
    
    def _make_key(self, identity_id: str, action: str, resource: str) -> str:
        """Create cache key from policy parameters"""
        return f"{identity_id}:{action}:{resource}"
    
    async def cache_decision(
        self,
        identity_id: str,
        action: str,
        resource: str,
        decision: bool,
        reason: str,
        ttl: int = 300
    ) -> bool:
        """
        Cache a policy decision.
        
        Args:
            identity_id: ID of the identity making the request
            action: Action being attempted
            resource: Resource being accessed
            decision: Whether access is allowed
            reason: Reason for the decision
            ttl: Time to live in seconds
            
        Returns:
            True if successful
        """
        try:
            cache_key = self._make_key(identity_id, action, resource)
            
            self._cache[cache_key] = {
                "decision": decision,
                "reason": reason,
                "cached_at": time.time(),
                "identity_id": identity_id,
                "action": action,
                "resource": resource
            }
            
            self._ttl[cache_key] = time.time() + ttl
            return True
            
        except Exception:
            return False
    
    async def get_decision(
        self,
        identity_id: str,
        action: str,
        resource: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached policy decision.
        
        Args:
            identity_id: ID of the identity making the request
            action: Action being attempted
            resource: Resource being accessed
            
        Returns:
            Cached decision dictionary or None if not found/expired
        """
        try:
            cache_key = self._make_key(identity_id, action, resource)
            
            # Check if key exists
            if cache_key not in self._cache:
                return None
            
            # Check TTL
            if cache_key in self._ttl:
                if time.time() > self._ttl[cache_key]:
                    # Expired - remove from cache
                    self._cache.pop(cache_key, None)
                    self._ttl.pop(cache_key, None)
                    return None
            
            return self._cache[cache_key]
            
        except Exception:
            return None
    
    def cleanup_expired(self):
        """Remove all expired entries from cache"""
        current_time = time.time()
        expired_keys = [
            key for key, expiry_time in self._ttl.items()
            if current_time > expiry_time
        ]
        
        for key in expired_keys:
            self._cache.pop(key, None)
            self._ttl.pop(key, None)
    
    def clear_cache(self):
        """Clear all cached decisions"""
        self._cache.clear()
        self._ttl.clear()
    
    def clear_for_identity(self, identity_id: str):
        """Clear all cached decisions for a specific identity"""
        keys_to_remove = [
            key for key, decision in self._cache.items()
            if decision.get("identity_id") == identity_id
        ]
        
        for key in keys_to_remove:
            self._cache.pop(key, None)
            self._ttl.pop(key, None)
    
    def clear_for_resource(self, resource: str):
        """Clear all cached decisions for a specific resource"""
        keys_to_remove = [
            key for key, decision in self._cache.items()
            if decision.get("resource") == resource
        ]
        
        for key in keys_to_remove:
            self._cache.pop(key, None)
            self._ttl.pop(key, None)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        # Clean up expired entries first
        self.cleanup_expired()
        
        current_time = time.time()
        decisions_by_result = {"allow": 0, "deny": 0}
        ttl_remaining = []
        
        for key, decision in self._cache.items():
            if decision.get("decision"):
                decisions_by_result["allow"] += 1
            else:
                decisions_by_result["deny"] += 1
                
            # Calculate TTL remaining
            if key in self._ttl:
                remaining = self._ttl[key] - current_time
                if remaining > 0:
                    ttl_remaining.append(remaining)
        
        avg_ttl = sum(ttl_remaining) / len(ttl_remaining) if ttl_remaining else 0
        
        return {
            "total_entries": len(self._cache),
            "total_cached_decisions": len(self._cache),
            "decisions_by_result": decisions_by_result,
            "unique_identities": len(set(
                decision.get("identity_id") for decision in self._cache.values()
            )),
            "unique_resources": len(set(
                decision.get("resource") for decision in self._cache.values()
            )),
            "avg_ttl_remaining": avg_ttl
        }
