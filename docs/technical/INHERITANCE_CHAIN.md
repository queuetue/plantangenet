# Plantangenet Class Inheritance Chain Documentation

## Overview

The Plantangenet system uses a sophisticated inheritance chain that builds from basic peer functionality up to complex musical coordination systems. This document maps the complete inheritance hierarchy and the responsibilities of each layer.

## Complete Inheritance Chain

### EnhancedConductor Class Hierarchy

```
EnhancedConductor → Omni → Buoy → Shard → [Agent, RedisMixin, NatsMixin, ClusterMixin]
```

## Layer-by-Layer Breakdown

### 1. Agent (Foundation Layer)
**File**: `/python/plantangenet/ocean/base.py`
**Purpose**: Core peer identity and lifecycle management
**Provides**:
- Unique peer ID generation (ULID)
- Logger integration  
- Namespace management
- TTL (time-to-live) handling
- Basic peer lifecycle (setup, update, teardown)
- Disposition management
- Operation caching

### 2. RedisMixin (Storage Layer)
**File**: `/python/plantangenet/ocean/mixins/redis.py`
**Purpose**: Redis-based persistent storage capabilities
**Provides**:
- Key-value storage operations
- Redis connection management
- Data persistence with TTL
- Storage namespace isolation
- Connection pooling

### 3. NatsMixin (Messaging Layer)
**File**: `/python/plantangenet/ocean/mixins/nats.py`  
**Purpose**: NATS-based publish/subscribe messaging
**Provides**:
- **`publish(topic, data)`** - Message publishing
- **`subscribe(topic, callback)`** - Topic subscription
- **`unsubscribe(topic)`** - Subscription removal
- Connection management to NATS server
- Message routing and delivery
- Asynchronous message handling

### 5. Shard (Integration Layer)
**File**: `/python/plantangenet/shard.py`
**Purpose**: Integration of all ocean capabilities into a functional peer
**Provides**:
- Unified initialization of all mixins
- Environment configuration (NATS URLs, Redis settings)
- Default connection parameters
- Mixin coordination and lifecycle management

### 6. Buoy (Time-Aware Layer)
**File**: `/python/plantangenet/buoy.py`
**Purpose**: Time-based event handling and synchronization
**Provides**:
- Clock synchronization and time tracking
- Frame-based updates (`on_frame()`)
- Pulse message handling (`on_pulse()`)
- Origin time tracking and drift management
- Time-based choice and random selection
- Musical timing abstractions

### 7. Omni (Topic-Aware Layer)  
**File**: `/python/plantangenet/omni.py`
**Purpose**: Advanced topic handling with decorators and windowing
**Provides**:
- **`@on_topic`** decorator for automatic message routing
- Cooldown, jitter, and rate limiting on topic handlers
- Message deduplication and debouncing
- Windowing logic for time-based operations
- State publishing and management
- Enhanced topic subscription management

## Serialization Flow

### Message Publishing Chain
```
Omni.publish() (inherited)
    ↓  
Buoy.publish() (inherited)
    ↓
Shard.publish() (inherited) 
    ↓
NatsMixin.publish() (actual implementation)
    ↓
NATS Server
```

### JSON Serialization Requirements

All data passed through `publish()` must be JSON serializable:
- **Primitive types**: `str`, `int`, `float`, `bool`, `None`
- **Collections**: `list`, `dict`, `tuple` (containing JSON-serializable items)
- **NOT serializable**: Class instances, functions, complex objects

## Key Methods by Layer

### Publishing/Messaging (NatsMixin)
- `publish(topic, data)` - Send messages
- `subscribe(topic, callback)` - Listen for messages  
- `unsubscribe(topic)` - Stop listening

### Storage (RedisMixin)
- `get(key)` - Retrieve data
- `set(key, value, ttl)` - Store data
- `delete(key)` - Remove data

### Time Management (Buoy)
- `on_frame()` - Handle time advancement
- `on_pulse(message)` - Process clock signals
- `set_origin(message)` - Initialize timing

### Topic Handling (Omni)
- `@on_topic(topic_name)` - Decorator for handlers
- Advanced message filtering and processing

---
Copyright (c) 1998-2025 Scott Russell
SPDX-License-Identifier: MIT 