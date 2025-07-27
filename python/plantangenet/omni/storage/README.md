# PlantangeNet Omni Storage System

A modular, high-performance storage abstraction layer for PlantangeNet with pluggable backends, intelligent caching, and comprehensive audit capabilities.

## Overview

The omni storage system provides a unified interface for data persistence with support for multiple storage backends, intelligent caching, relationship tracking, versioning, and audit logging.

### Key Features

- **Multi-backend support**: Redis, Docker Registry, Kubernetes ConfigMaps
- **Intelligent caching**: LRU cache with configurable eviction policies
- **Audit logging**: Comprehensive change tracking with retention policies
- **Relationship management**: Bidirectional relationship tracking with cleanup
- **Policy caching**: TTL-based caching for authorization decisions
- **Versioning**: Automatic version management with cleanup
- **Change notifications**: Sync and async callback system
- **Health monitoring**: Backend health checks and statistics

## Quick Start

```python
from plantangenet.omni.storage import ManagedStorage
from plantangenet.omni.storage.adapters import RedisStorageAdapter

# Create storage with Redis backend
adapter = RedisStorageAdapter(url='redis://localhost:6379')
storage = ManagedStorage()
storage.add_backend('redis', adapter)

# Store and retrieve data
await storage.store_data('user:123', {'name': 'Alice', 'role': 'admin'})
user_data = await storage.load_data('user:123')
```

## Architecture

```
ManagedStorage (Core)
├── Cache (LRU)
├── Audit (Change tracking)
├── Relationships (Bidirectional links)
├── Policy Cache (TTL-based)
├── Versioning (History management)
├── Notifications (Change callbacks)
└── Backends
    ├── Redis Adapter
    ├── Registry Adapter
    └── ConfigMap Adapter
```

## Components

### Core Storage (`core.py`)
The main orchestrator that coordinates all components and backends.

```python
storage = ManagedStorage(
    sync_strategy='write_through',  # or 'write_behind', 'write_around'
    cache_size=10000,
    default_ttl=3600
)
```

### Backends (`backends.py`)
Abstract interface for storage backends with error handling and health checks.

```python
class StorageBackend:
    async def store_data(self, key: str, data: Dict[str, Any]) -> bool
    async def load_data(self, key: str) -> Optional[Dict[str, Any]]
    async def delete_data(self, key: str) -> bool
    async def health_check(self) -> bool
```

### Cache (`cache.py`)
High-performance LRU cache with O(1) operations.

```python
# Configure cache
storage.cache.configure(
    max_size=5000,
    eviction_callback=lambda key, data: print(f"Evicted {key}")
)

# Manual cache operations
await storage.cache.put('key', data)
data = await storage.cache.get('key')
```

### Audit (`audit.py`)
Comprehensive change tracking with configurable retention.

```python
# Configure audit
storage.audit.configure(
    retention_seconds=86400,  # 24 hours
    include_data_snapshots=True,
    max_entries_per_key=100
)

# Get audit trail
trail = await storage.get_audit_trail('user:123')
for entry in trail:
    print(f"{entry['timestamp']}: {entry['operation']} by {entry['identity']}")
```

### Relationships (`relationships.py`)
Bidirectional relationship tracking with automatic cleanup.

```python
# Store relationships
await storage.store_relationship('user:123', 'member_of', 'group:admin')
await storage.store_relationship('group:admin', 'contains', 'user:123')

# Query relationships
groups = await storage.get_related('user:123', 'member_of')
members = await storage.get_related('group:admin', 'contains')
```

### Policy Cache (`policy_cache.py`)
TTL-based caching for authorization decisions.

```python
# Configure policy cache
storage.policy_cache.configure(
    default_ttl=1800,  # 30 minutes
    max_entries=10000
)

# Cache policy decision
await storage.cache_policy_decision('user:123', 'read', 'resource:abc', True)
allowed = await storage.get_cached_policy('user:123', 'read', 'resource:abc')
```

### Versioning (`versioning.py`)
Automatic version management with configurable limits.

```python
# Configure versioning
storage.versioning.configure(
    max_versions_per_key=25,
    cleanup_interval=3600
)

# Store version
await storage.store_version('config', 'v1.2.3', config_data)

# Load versions
versions = await storage.list_versions('config')
latest = await storage.load_version('config')  # Latest version
specific = await storage.load_version('config', 'v1.2.3')
```

### Notifications (`notifications.py`)
Flexible callback system for change notifications.

```python
# Add sync callback
def on_user_changed(key, old_data, new_data):
    print(f"User {key} updated")

storage.notifications.add_callback('data_changed', on_user_changed)

# Add async callback
async def on_relationship_changed(subject, predicate, obj, operation):
    await send_notification(f"Relationship {operation}: {subject} {predicate} {obj}")

storage.notifications.add_async_callback('relationship_changed', on_relationship_changed)
```

## Storage Adapters

### Redis Adapter (`adapters/redis_adapter.py`)
High-performance Redis backend using hashes and sorted sets.

```python
from plantangenet.omni.storage.adapters import RedisStorageAdapter

adapter = RedisStorageAdapter(
    url='redis://localhost:6379',
    db=0,
    max_connections=20,
    key_prefix='plantangenet:'
)
storage.add_backend('redis', adapter, priority=1)
```

Features:
- Connection pooling
- Atomic operations
- Efficient relationship storage using sorted sets
- Version storage with automatic expiration

### Registry Adapter (`adapters/registry_adapter.py`)
Docker Registry v2 API backend using blob storage.

```python
from plantangenet.omni.storage.adapters import RegistryStorageAdapter

adapter = RegistryStorageAdapter(
    registry_url='http://localhost:5000',
    repository='plantangenet/storage',
    username='admin',
    password='secret'
)
storage.add_backend('registry', adapter, priority=2)
```

Features:
- OCI-compliant blob storage
- Authentication support
- Chunked uploads for large data
- Content deduplication

### ConfigMap Adapter (`adapters/configmap_adapter.py`)
Kubernetes ConfigMap backend with DNS-1123 name compliance.

```python
from plantangenet.omni.storage.adapters import ConfigMapStorageAdapter

adapter = ConfigMapStorageAdapter(
    namespace='plantangenet'
)
storage.add_backend('configmap', adapter, priority=3)
```

Features:
- Automatic name sanitization
- JSON serialization
- Label-based querying
- In-cluster and external config support

## Advanced Usage

### Multi-Backend Configuration
```python
# Primary: Redis (fastest)
redis_adapter = RedisStorageAdapter(url='redis://localhost:6379')
storage.add_backend('redis', redis_adapter, priority=1)

# Secondary: Registry (durable)
registry_adapter = RegistryStorageAdapter(
    registry_url='http://registry:5000',
    repository='plantangenet/backup'
)
storage.add_backend('registry', registry_adapter, priority=2)

# Tertiary: ConfigMap (Kubernetes-native)
configmap_adapter = ConfigMapStorageAdapter(namespace='plantangenet')
storage.add_backend('configmap', configmap_adapter, priority=3)
```

### Custom Sync Strategies
```python
async def custom_sync_strategy(storage, key, data):
    """Store in Redis immediately, queue for Registry backup"""
    # Immediate storage
    await storage.backends['redis'].store_data(key, data)
    
    # Queue for background backup
    await storage.queue_backup('registry', key, data)

storage.set_sync_strategy('custom', custom_sync_strategy)
```

### Health Monitoring
```python
# Check overall health
health = await storage.check_health()
print(f"Storage health: {health['status']}")

# Get detailed statistics
stats = await storage.get_statistics()
print(f"Cache hit ratio: {stats['cache']['hit_ratio']:.2%}")
print(f"Active backends: {len(stats['backends'])}")
```

### Error Handling
```python
from plantangenet.omni.storage.backends import BackendError, BackendConnectionError

try:
    await storage.store_data('key', data)
except BackendConnectionError:
    # All backends unavailable
    await storage.enable_offline_mode()
except BackendError as e:
    # Specific backend error
    logger.error(f"Storage error: {e}")
```

## Performance Tuning

### Cache Configuration
```python
# Optimize for read-heavy workloads
storage.cache.configure(
    max_size=50000,  # Larger cache
    eviction_policy='lru',
    preload_keys=['critical:*']
)
```

### Batch Operations
```python
# Store multiple items efficiently
batch_data = {
    'user:1': {'name': 'Alice'},
    'user:2': {'name': 'Bob'},
    'user:3': {'name': 'Charlie'}
}
await storage.store_batch(batch_data)
```

### Background Sync
```python
# Use write-behind for better write performance
storage.set_sync_strategy('write_behind', interval=30)
```

## Monitoring and Observability

### Metrics Collection
```python
# Built-in metrics
metrics = await storage.get_metrics()
print(f"Operations/sec: {metrics['ops_per_second']}")
print(f"Error rate: {metrics['error_rate']:.2%}")
```

### Custom Instrumentation
```python
import time

async def timing_callback(operation, key, duration):
    print(f"{operation} on {key} took {duration:.3f}s")

storage.add_instrumentation_callback(timing_callback)
```

## Testing

### Unit Tests
```python
import pytest
from plantangenet.omni.storage import ManagedStorage
from plantangenet.omni.storage.adapters import RedisStorageAdapter

@pytest.fixture
async def storage():
    adapter = RedisStorageAdapter(url='redis://localhost:6380')  # Test Redis
    storage = ManagedStorage()
    storage.add_backend('redis', adapter)
    yield storage
    await storage.cleanup()

async def test_basic_operations(storage):
    # Test store/load cycle
    test_data = {'name': 'test', 'value': 42}
    success = await storage.store_data('test-key', test_data)
    assert success
    
    loaded = await storage.load_data('test-key')
    assert loaded == test_data
```

### Integration Tests
```python
async def test_multi_backend_failover():
    # Set up backends with one that will fail
    failing_adapter = FailingRedisAdapter()
    working_adapter = RedisStorageAdapter()
    
    storage = ManagedStorage()
    storage.add_backend('primary', failing_adapter, priority=1)
    storage.add_backend('backup', working_adapter, priority=2)
    
    # Should automatically failover to backup
    success = await storage.store_data('test', {'data': 'value'})
    assert success
```

## Migration

See [MIGRATION.md](MIGRATION.md) for detailed migration instructions from the old `ManagedOmniStorageMixin` system.

## Contributing

### Adding New Adapters

1. Implement the `StorageBackend` interface
2. Add comprehensive error handling
3. Include health check implementation
4. Add adapter to `adapters/__init__.py`
5. Write tests and documentation

Example skeleton:
```python
from ..backends import StorageBackend, BackendError

class MyStorageAdapter(StorageBackend):
    async def store_data(self, key: str, data: Dict[str, Any]) -> bool:
        try:
            # Implementation here
            return True
        except Exception as e:
            raise BackendError(f"Failed to store: {e}")
    
    # Implement other required methods...
```

### Development Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests/storage/

# Run with coverage
pytest --cov=plantangenet.omni.storage tests/storage/
```

## License

MIT License - see LICENSE.md for details.

## Support

- Documentation: See individual module docstrings
- Issues: GitHub issue tracker
- Migration help: See MIGRATION.md
