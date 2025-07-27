# Copyright (c) 2025 Scott Russell
# SPDX-License-Identifier: MIT

"""
Change notification system for storage events.
"""

import asyncio
import time
from typing import Any, Callable, Dict, List


class ChangeNotifier:
    """
    Manages change notifications for storage events.
    
    Supports both synchronous and asynchronous callbacks
    for responding to data changes in real-time.
    """
    
    def __init__(self):
        # Callbacks for field-level change notifications
        self._callbacks: List[Callable] = []
        # Callbacks for specific named events (e.g., data_changed)
        self._event_callbacks: Dict[str, List[Callable]] = {}
    
    def add_callback(self, event_type_or_callback, callback=None):
        """
        Add a change notification callback.
        
        Args:
            event_type_or_callback: Either event type string or callback function
            callback: Callback function if first param is event type
                     Will receive a change_data dict with:
                     - omni_id: ID of changed omni
                     - field: Field that changed
                     - old_value: Previous value
                     - new_value: New value
                     - identity_id: ID of identity making change
                     - timestamp: Unix timestamp of change
        """
        if callback is None:
            # Single parameter - it's a field-level callback
            self._callbacks.append(event_type_or_callback)
        else:
            # Two parameters - register for a specific event type
            event_type = event_type_or_callback
            self._event_callbacks.setdefault(event_type, []).append(callback)
    
    def remove_callback(self, callback: Callable) -> bool:
        """
        Remove a change notification callback.
        
        Args:
            callback: Callback function to remove
            
        Returns:
            True if callback was found and removed
        """
        try:
            self._callbacks.remove(callback)
            return True
        except ValueError:
            return False
    
    async def notify_change(
        self,
        omni_id: str,
        field_name: str,
        old_value: Any,
        new_value: Any,
        identity_id: str = None
    ):
        """
        Notify all callbacks of a change.
        
        Args:
            omni_id: ID of the omni that changed
            field_name: Name of the field that changed
            old_value: Previous value
            new_value: New value
            identity_id: ID of identity making the change
        """
        if not self._callbacks:
            return
        
        change_data = {
            "omni_id": omni_id,
            "field": field_name,
            "old_value": old_value,
            "new_value": new_value,
            "identity_id": identity_id,
            "timestamp": time.time()
        }
        
        # Call all callbacks
        for callback in self._callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(change_data)
                else:
                    callback(change_data)
            except Exception as e:
                # Log error but don't stop other callbacks
                if hasattr(self, 'logger'):
                    self.logger.error(f"Change callback error: {e}")
    
    def clear_callbacks(self):
        """Remove all callbacks"""
        self._callbacks.clear()
    
    def get_callback_count(self) -> int:
        """Get number of registered callbacks"""
        return len(self._callbacks)
    
    async def cleanup(self):
        """Cleanup notification resources"""
        # Clear all callbacks
        self._callbacks.clear()
        self._event_callbacks.clear()
    
    async def trigger_event(self, event_type: str, *args):
        """
        Trigger callbacks registered for a named event type.
        """
        callbacks = self._event_callbacks.get(event_type, [])
        for callback in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(*args)
                else:
                    callback(*args)
            except Exception as e:
                if hasattr(self, 'logger'):
                    self.logger.error(f"Event callback error: {e}")


class ChangeBuffer:
    """
    Buffers changes for batch notification.
    
    Useful for reducing notification overhead when many
    changes happen in quick succession.
    """
    
    def __init__(self, notifier: ChangeNotifier, buffer_time: float = 0.1):
        self.notifier = notifier
        self.buffer_time = buffer_time
        self._buffer: List[Dict[str, Any]] = []
        self._flush_task: asyncio.Task = None
        self._batch_callbacks: List[Callable] = []
    
    async def add_change(
        self,
        omni_id: str,
        field_name: str,
        old_value: Any,
        new_value: Any,
        identity_id: str = None
    ):
        """
        Add a change to the buffer.
        
        Args:
            omni_id: ID of the omni that changed
            field_name: Name of the field that changed
            old_value: Previous value
            new_value: New value
            identity_id: ID of identity making the change
        """
        change_data = {
            "omni_id": omni_id,
            "field": field_name,
            "old_value": old_value,
            "new_value": new_value,
            "identity_id": identity_id,
            "timestamp": time.time()
        }
        
        self._buffer.append(change_data)
        
        # Schedule flush if not already scheduled
        if not self._flush_task or self._flush_task.done():
            self._flush_task = asyncio.create_task(self._delayed_flush())
    
    async def _delayed_flush(self):
        """Flush buffer after delay"""
        await asyncio.sleep(self.buffer_time)
        await self.flush()
    
    async def flush(self):
        """Immediately flush all buffered changes"""
        if not self._buffer:
            return
        
        # Send all changes as one batch to batch callbacks
        changes_copy = self._buffer.copy()
        
        for callback in self._batch_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(changes_copy)
                else:
                    callback(changes_copy)
            except Exception as e:
                if hasattr(self, 'logger'):
                    self.logger.error(f"Batch callback error: {e}")
        
        # Also send individual notifications through the notifier
        for change in self._buffer:
            await self.notifier.notify_change(
                change["omni_id"],
                change["field"],
                change["old_value"],
                change["new_value"],
                change["identity_id"]
            )
        
        # Clear buffer
        self._buffer.clear()
    
    async def cleanup(self):
        """Cleanup buffer resources"""
        if self._flush_task and not self._flush_task.done():
            self._flush_task.cancel()
        await self.flush()  # Final flush
        self._buffer.clear()
    
    def add_batch_callback(self, callback):
        """Add a callback for batch notifications"""
        self._batch_callbacks.append(callback)
    
    def clear(self):
        """Clear all buffered changes"""
        self._buffer.clear()
    
    def get_stats(self):
        """Get buffer statistics"""
        stats = {
            "buffered_changes": len(self._buffer),
            "buffer_time": self.buffer_time
        }
        
        if self._buffer:
            oldest_timestamp = min(change["timestamp"] for change in self._buffer)
            stats["oldest_change_age"] = time.time() - oldest_timestamp
        else:
            stats["oldest_change_age"] = 0
            
        return stats
