# Copyright (c) 2025 Scott Russell
# SPDX-License-Identifier: MIT

"""
Example usage of the new modular Omni Storage system with multiple backends.

This example demonstrates:
1. Setting up managed storage with Redis, Registry, and ConfigMap backends
2. Configuring different sync strategies and components
3. Working with in-memory operations and background sync
4. Monitoring and statistics
5. Advanced features like versioning, relationships, and audit logging
"""

import asyncio
import json
import time
from datetime import datetime
import logging

# Import the new modular storage system
from plantangenet.omni.storage import ManagedStorage
from plantangenet.omni.storage.adapters import (
    RedisStorageAdapter, 
    RegistryStorageAdapter, 
    ConfigMapStorageAdapter
)


class ExampleOmniManager:
    """Example implementation showing new modular storage usage"""
    
    def __init__(self):
        # Create the new modular storage system
        self.storage = ManagedStorage(
            sync_strategy='write_behind',  # Background sync for demo
            cache_size=1000
        )
        self.logger = self._setup_logger()
        self._setup_notifications()
    
    def _setup_logger(self):
        logger = logging.getLogger("omni_manager")
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger
    
    def _setup_notifications(self):
        """Setup change notification callbacks"""
        
        def sync_change_handler(key, old_data, new_data):
            """Synchronous change handler"""
            print(f"SYNC Change: {key} updated")
        
        async def async_change_handler(key, old_data, new_data):
            """Asynchronous change handler"""
            print(f"ASYNC Change: {key} changed")
            # Could trigger additional processing here
        
        self.storage.notifications.add_callback('data_changed', sync_change_handler)
        self.storage.notifications.add_async_callback('data_changed', async_change_handler)


async def setup_redis_backend(manager: ExampleOmniManager):
    """Setup Redis backend"""
    try:
        adapter = RedisStorageAdapter(url="redis://localhost:6379/0")
        # Test connection
        if await adapter.health_check():
            manager.storage.add_backend('redis', adapter, priority=1)
            print("✓ Redis backend configured")
            return True
        else:
            print("✗ Redis backend health check failed")
            return False
    except Exception as e:
        print(f"✗ Redis backend failed: {e}")
        return False


async def setup_registry_backend(manager: ExampleOmniManager):
    """Setup Docker Registry backend"""
    try:
        adapter = RegistryStorageAdapter(
            registry_url="http://localhost:5000", 
            repository="plantangenet/omni"
        )
        if await adapter.health_check():
            manager.storage.add_backend('registry', adapter, priority=2)
            print("✓ Registry backend configured")
            return True
        else:
            print("✗ Registry backend health check failed")
            return False
    except Exception as e:
        print(f"✗ Registry backend failed: {e}")
        return False


async def setup_configmap_backend(manager: ExampleOmniManager):
    """Setup Kubernetes ConfigMap backend"""
    try:
        adapter = ConfigMapStorageAdapter(namespace="plantangenet")
        if await adapter.health_check():
            manager.storage.add_backend('configmap', adapter, priority=3)
            print("✓ ConfigMap backend configured")
            return True
        else:
            print("✗ ConfigMap backend health check failed")
            return False
    except Exception as e:
        print(f"✗ ConfigMap backend failed: {e}")
        return False


async def demonstrate_basic_operations(manager: ExampleOmniManager):
    """Demonstrate basic storage operations"""
    print("\n=== Basic Operations ===")
    
    # Store some data
    omni_id = "demo-agent-001"
    fields = {
        "name": "Demo Agent",
        "type": "autonomous",
        "status": "active",
        "capabilities": ["sensing", "planning", "acting"],
        "metadata": {
            "created_at": time.time(),
            "version": "1.0.0"
        }
    }
    
    success = await manager.storage.store_data(omni_id, fields)
    print(f"Store result: {success}")
    
    # Load the data
    loaded_data = await manager.storage.load_data(omni_id)
    print(f"Loaded data keys: {list(loaded_data.keys()) if loaded_data else 'None'}")
    
    # Update some fields (simulate partial update)
    updates = {
        "status": "busy",
        "current_task": "exploration",
        "last_update": time.time()
    }
    
    # Merge updates with existing data
    if loaded_data:
        loaded_data.update(updates)
        update_success = await manager.storage.store_data(omni_id, loaded_data)
        print(f"Update result: {update_success}")
    
    # Load updated data
    updated_data = await manager.storage.load_data(omni_id)
    print(f"Updated status: {updated_data.get('status') if updated_data else 'None'}")
    print(f"Current task: {updated_data.get('current_task') if updated_data else 'None'}")


async def demonstrate_versioning(manager: ExampleOmniManager):
    """Demonstrate versioning capabilities"""
    print("\n=== Versioning ===")
    
    omni_id = "versioned-agent-001"
    
    # Create initial version
    initial_data = {"version": "1.0", "config": {"param1": 100}}
    version_1 = await manager.storage.store_version(omni_id, "v1.0", initial_data)
    print(f"Version 1 stored: {version_1}")
    
    # Create updated version
    updated_data = {"version": "1.1", "config": {"param1": 150, "param2": "new"}}
    version_2 = await manager.storage.store_version(omni_id, "v1.1", updated_data)
    print(f"Version 2 stored: {version_2}")
    
    # List versions
    versions = await manager.storage.list_versions(omni_id)
    print(f"Available versions: {len(versions)}")
    for v in versions:
        print(f"  - {v['version_id']} at {v['datetime']}")
    
    # Load specific version
    loaded_version = await manager.storage.load_version(omni_id, "v1.0")
    print(f"Loaded version 1.0: {loaded_version}")
    
    # Load latest version
    latest_version = await manager.storage.load_version(omni_id)
    print(f"Latest version: {latest_version}")


async def demonstrate_relationships(manager: ExampleOmniManager):
    """Demonstrate relationship tracking"""
    print("\n=== Relationships ===")
    
    # Create parent-child relationships
    parent_id = "supervisor-001"
    child_ids = ["worker-001", "worker-002", "worker-003"]
    
    for child_id in child_ids:
        await manager.storage.store_relationship(parent_id, "manages", child_id)
        print(f"Added relationship: {parent_id} manages {child_id}")
    
    # Get children
    children = await manager.storage.get_related(parent_id, "manages")
    print(f"Supervisor manages: {children}")
    
    # Get parents (reverse relationship)
    parents = await manager.storage.get_related("worker-001", "managed_by")
    print(f"Worker-001 reports to: {parents}")
    
    # Remove a relationship
    await manager.storage.remove_relationship(parent_id, "manages", "worker-002")
    updated_children = await manager.storage.get_related(parent_id, "manages")
    print(f"Updated children: {updated_children}")
    
    # Demonstrate different relationship types
    await manager.storage.store_relationship("worker-001", "collaborates_with", "worker-003")
    collaborators = await manager.storage.get_related("worker-001", "collaborates_with")
    print(f"Worker-001 collaborates with: {collaborators}")


async def demonstrate_policy_cache(manager: ExampleOmniManager):
    """Demonstrate policy decision caching"""
    print("\n=== Policy Cache ===")
    
    # Cache some policy decisions
    await manager.storage.cache_policy_decision(
        identity_id="agent-001",
        action="read",
        resource="/sensors/temperature",
        decision=True,
        reason="Agent has sensor access role",
        ttl=60
    )
    
    await manager.storage.cache_policy_decision(
        identity_id="agent-001",
        action="write",
        resource="/actuators/motor",
        decision=False,
        reason="Agent lacks actuator control role",
        ttl=60
    )
    
    # Retrieve cached decisions
    read_decision = await manager.storage.get_cached_policy(
        "agent-001", "read", "/sensors/temperature"
    )
    print(f"Read decision: {read_decision}")
    
    write_decision = await manager.storage.get_cached_policy(
        "agent-001", "write", "/actuators/motor"
    )
    print(f"Write decision: {write_decision}")
    
    # Demonstrate TTL expiration simulation
    print("Waiting for TTL to demonstrate expiration...")
    await asyncio.sleep(2)  # Short wait for demo
    
    # Check cache statistics
    cache_stats = await manager.storage.get_statistics()
    print(f"Policy cache stats: {cache_stats.get('policy_cache', {})}")


async def demonstrate_audit_log(manager: ExampleOmniManager):
    """Demonstrate audit logging"""
    print("\n=== Audit Log ===")
    
    omni_id = "audited-agent-001"
    
    # Perform some operations that generate audit entries
    await manager.storage.store_data(
        omni_id,
        {"name": "Audited Agent", "status": "active"}
    )
    
    # Update with audit context
    await manager.storage.store_data(
        omni_id,
        {"name": "Audited Agent", "status": "maintenance"}
    )
    
    # Add custom audit entry
    await manager.storage.log_audit(
        key=omni_id,
        action="manual_intervention",
        context={"reason": "Scheduled maintenance"},
        identity_id="maintenance-team"
    )
    
    # Retrieve audit log
    audit_entries = await manager.storage.get_audit_trail(omni_id, limit=10)
    print(f"Audit entries: {len(audit_entries)}")
    for entry in audit_entries:
        timestamp = datetime.fromtimestamp(entry['timestamp']).isoformat()
        print(f"  - {entry['action']} by {entry.get('identity_id', 'unknown')} at {timestamp}")
        if 'context' in entry:
            print(f"    Context: {entry['context']}")
    
    # Demonstrate audit filtering
    recent_entries = await manager.storage.get_audit_trail(
        omni_id, 
        since=datetime.now().timestamp() - 60  # Last minute
    )
    print(f"Recent audit entries (last minute): {len(recent_entries)}")


async def demonstrate_atomic_operations(manager: ExampleOmniManager):
    """Demonstrate atomic operations and advanced features"""
    print("\n=== Atomic Operations & Advanced Features ===")
    
    omni_id = "atomic-test-001"
    
    # Store initial data
    initial_data = {"counter": 0, "status": "ready", "owner": "system"}
    await manager.storage.store_data(omni_id, initial_data)
    
    # Demonstrate cache operations
    cache_hit = await manager.storage.cache.get(omni_id)
    print(f"Cache hit: {cache_hit is not None}")
    
    # Store additional data for cache demonstration
    await manager.storage.cache.put(f"{omni_id}-cache-test", {"cached": True})
    cached_data = await manager.storage.cache.get(f"{omni_id}-cache-test")
    print(f"Manual cache operation: {cached_data}")
    
    # Demonstrate notifications
    def change_callback(key, old_data, new_data):
        print(f"Notification: {key} changed from {old_data} to {new_data}")
    
    manager.storage.notifications.add_callback('data_changed', change_callback)
    
    # Update data to trigger notification
    updated_data = initial_data.copy()
    updated_data.update({"counter": 1, "status": "processing"})
    await manager.storage.store_data(omni_id, updated_data)
    
    # Check final state
    final_state = await manager.storage.load_data(omni_id)
    print(f"Final state: {final_state}")


async def demonstrate_cache_features(manager: ExampleOmniManager):
    """Demonstrate advanced cache features"""
    print("\n=== Cache Features ===")
    
    # Configure cache with custom settings
    manager.storage.cache.configure(
        max_size=100,
        eviction_callback=lambda key, data: print(f"Evicted: {key}")
    )
    
    # Fill cache with test data
    for i in range(5):
        test_key = f"cache-test-{i}"
        test_data = {"index": i, "data": f"test-data-{i}"}
        await manager.storage.cache.put(test_key, test_data)
    
    # Check cache statistics
    stats = await manager.storage.get_statistics()
    cache_stats = stats.get('cache', {})
    print(f"Cache size: {cache_stats.get('size', 0)}")
    print(f"Cache hit ratio: {cache_stats.get('hit_ratio', 0):.2%}")
    
    # Test cache operations
    hit = await manager.storage.cache.get("cache-test-0")
    miss = await manager.storage.cache.get("non-existent-key")
    print(f"Cache hit result: {hit is not None}")
    print(f"Cache miss result: {miss is None}")


async def monitor_system(manager: ExampleOmniManager):
    """Monitor system statistics"""
    print("\n=== System Statistics ===")
    
    # Get comprehensive statistics
    stats = await manager.storage.get_statistics()
    
    print("Storage Statistics:")
    for component, data in stats.items():
        print(f"  {component}:")
        if isinstance(data, dict):
            for key, value in data.items():
                print(f"    {key}: {value}")
        else:
            print(f"    {data}")
    
    # Check backend health
    health = await manager.storage.check_health()
    print(f"\nOverall health: {health['status']}")
    
    if 'backends' in health:
        print("Backend health:")
        for backend_name, backend_health in health['backends'].items():
            status = "✓" if backend_health else "✗"
            print(f"  {status} {backend_name}")
    
    # Force sync demonstration
    print("\nForcing sync to backends...")
    try:
        await manager.storage.sync_all()
        print("Sync completed successfully")
    except Exception as e:
        print(f"Sync error: {e}")


def setup_change_notifications(manager: ExampleOmniManager):
    """Setup additional change notification callbacks"""
    
    def relationship_callback(subject, predicate, obj, operation):
        """Handle relationship changes"""
        print(f"Relationship {operation}: {subject} {predicate} {obj}")
    
    def audit_callback(key, action, context):
        """Handle audit events"""
        print(f"Audit: {action} on {key}")
    
    manager.storage.notifications.add_callback('relationship_changed', relationship_callback)
    manager.storage.notifications.add_callback('audit_logged', audit_callback)


async def main():
    """Main demonstration function"""
    print("PlantangeNet Modular Omni Storage Demo")
    print("=====================================")
    
    # Create manager with new modular storage system
    manager = ExampleOmniManager()
    
    # Configure storage components
    manager.storage.cache.configure(max_size=1000)
    manager.storage.audit.configure(retention_seconds=3600)
    manager.storage.policy_cache.configure(default_ttl=300)
    manager.storage.versioning.configure(max_versions_per_key=10)
    
    # Setup additional change notifications
    setup_change_notifications(manager)
    
    # Setup backends (in order of preference)
    backends_setup = []
    backends_setup.append(await setup_redis_backend(manager))
    backends_setup.append(await setup_registry_backend(manager))
    backends_setup.append(await setup_configmap_backend(manager))
    
    if not any(backends_setup):
        print("No backends available! Demo will run in memory-only mode.")
    else:
        print(f"Successfully configured {sum(backends_setup)} backend(s)")
    
    try:
        # Run demonstrations
        await demonstrate_basic_operations(manager)
        await demonstrate_versioning(manager)
        await demonstrate_relationships(manager)
        await demonstrate_policy_cache(manager)
        await demonstrate_audit_log(manager)
        await demonstrate_atomic_operations(manager)
        await demonstrate_cache_features(manager)
        await monitor_system(manager)
        
        # Wait for background sync cycles
        print("\nWaiting for background sync cycles...")
        await asyncio.sleep(15)
        
        # Final statistics
        await monitor_system(manager)
        
    finally:
        # Cleanup
        print("\nCleaning up...")
        await manager.storage.cleanup()
        print("Demo complete!")


if __name__ == "__main__":
    asyncio.run(main())
