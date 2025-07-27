# Copyright (c) 2025 Scott Russell
# SPDX-License-Identifier: MIT

"""
LRU Cache implementation for in-memory storage.
"""

from typing import Any, Dict, Optional, List


class LRUCache:
    """
    Least Recently Used cache implementation.
    
    Provides O(1) get/put operations with automatic eviction
    when max_items is exceeded.
    """
    
    class Node:
        def __init__(self, key: str, value: Any):
            self.key = key
            self.value = value
            self.prev = None
            self.next = None
    
    def __init__(self, max_items: int):
        self.max_items = max_items
        self.cache: Dict[str, 'LRUCache.Node'] = {}
        
        # Create dummy head and tail nodes for easier manipulation
        self.head = self.Node("", None)
        self.tail = self.Node("", None)
        self.head.next = self.tail
        self.tail.prev = self.head
    
    def _add_node(self, node: 'LRUCache.Node'):
        """Add node right after head"""
        node.prev = self.head
        node.next = self.head.next
        self.head.next.prev = node
        self.head.next = node
    
    def _remove_node(self, node: 'LRUCache.Node'):
        """Remove an existing node from linked list"""
        prev_node = node.prev
        new_node = node.next
        prev_node.next = new_node
        new_node.prev = prev_node
    
    def _move_to_head(self, node: 'LRUCache.Node'):
        """Move node to head (mark as recently used)"""
        self._remove_node(node)
        self._add_node(node)
    
    def _pop_tail(self) -> 'LRUCache.Node':
        """Remove last node (least recently used)"""
        last_node = self.tail.prev
        self._remove_node(last_node)
        return last_node
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value by key, marking as recently used.
        
        Args:
            key: Cache key
            
        Returns:
            Value if found, None otherwise
        """
        node = self.cache.get(key)
        if not node:
            return None
        
        # Move to head (mark as recently used)
        self._move_to_head(node)
        return node.value
    
    def put(self, key: str, value: Any):
        """
        Store a key-value pair in the cache.
        
        Args:
            key: Cache key
            value: Value to store
        """
        # Handle zero capacity case
        if self.max_items == 0:
            return
            
        node = self.cache.get(key)
        
        if node:
            # Update existing node
            node.value = value
            self._move_to_head(node)
        else:
            # Add new node
            new_node = self.Node(key, value)
            
            if len(self.cache) >= self.max_items:
                # Remove least recently used
                tail = self._pop_tail()
                del self.cache[tail.key]
            
            self.cache[key] = new_node
            self._add_node(new_node)
    
    def delete(self, key: str) -> bool:
        """
        Delete key from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if key existed, False otherwise
        """
        node = self.cache.get(key)
        if not node:
            return False
        
        self._remove_node(node)
        del self.cache[key]
        return True
    
    def clear(self):
        """Clear all items from cache"""
        self.cache.clear()
        self.head.next = self.tail
        self.tail.prev = self.head
    
    def keys(self) -> List[str]:
        """Get all keys in cache (most recent first)"""
        keys = []
        current = self.head.next
        while current != self.tail:
            keys.append(current.key)
            current = current.next
        return keys
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            "current_items": len(self.cache),
            "max_items": self.max_items,
            "usage_percent": (len(self.cache) / self.max_items) * 100 if self.max_items > 0 else 0
        }
