# Plantangenet Memory and Compositing Architecture

## Introduction

Plantangenet is a policy-bound system for recording, organizing, summarizing, and remembering time-indexed, multi-dimensional data.

It is built for flexible, lossy, economically-aware memory that models real-world observation:

> Not everything is remembered equally. What we attend to stays. What we ignore fades.

---

## Design Goals

* Store raw, high-resolution data temporarily.
* Allow selective, degraded, long-term memory of important regions.
* Enable clients to direct system attention and pay for retention.
* Provide multiple views of the same underlying data for different use cases.
* Keep the core modular, composable, and domain-agnostic.

---

## Core Concepts

### AxisFrame

* The atomic unit of data.
* Represents a single measurement along a single axis at one moment in time.
* Example:

```json
{
  "tick": 42,
  "axis_name": "temperature",
  "position": 23.5,
  "impulse_data": {
    "pressure": 1013,
    "humidity": 45
  }
}
```

* Encodes domain-specific features.
* Can be converted into tensor-compatible data for ML or analysis.

---

### MultiAxisFrame

* A complete snapshot at a single time tick.

* Contains all relevant AxisFrames.

* Represents the system's full state at a tick.

* Supports:

  * Composition into flat dictionaries.
  * Coordination metadata.
  * Marking "dirty" axes for efficient updates.

* All raw data is stored in this format in short-term memory.

---

### TimeSeriesCollector

* Holds a rolling collection of MultiAxisFrames over time.

* Provides efficient time-indexed access.

* Supports:

  * Collecting new AxisFrames.
  * Retrieving frames over windows.
  * Tracking "dirty" (updated) frames for efficient processing.
  * Trimming history to maintain memory limits.

* The source of truth for recent, high-resolution data.

---

## Client Cursors

> Focus is expensive.

Cursors define regions of interest in the time/axis space:

* Axes: which dimensions matter.

* Tick range: the time window of interest.

* Owner: the client/agent that owns this observation.

* Dynamic or static: moves over time or stays fixed.

* Update policy: logic for when a new observation is "interesting."

* Cursors track attention in the system.

* They are the economic signal of value:

  * Clients pay (e.g. in Dust) to register Cursors.
  * Memory allocation is guided by these signals.

* Memory is not uniform. It is shaped by what clients choose to observe.

---

## Turns

* A Turn is a collated batch of frames over time.

* Rather than operating on single ticks, system-level logic processes turns:

  * Collation
  * Summarization
  * Degradation

* Turns are the unit of work for long-term memory.

* When a Turn is emitted, it triggers memory processes like Membry.

---

## Views

> How do we see this data?

Compositors transform raw MultiAxisFrames into views:

* Tensors for ML training.

* 2D buffers for UIs or dashboards.

* Summaries for logging or alerts.

* Degraded representations for memory.

* Heatmaps of regions of activity.

* A view is any meaningful projection of the data.

* Views are defined by CompositionRules:

  * Feature selection.
  * Precision reduction.
  * Axis filtering.
  * Noise injection.
  * Aggregation.

* Rules are composable and pluggable.

---

## Compositors

* The View Factory of the system.

* Holds a pipeline of CompositionRules.

* Applies them to produce:

  * Single-frame views.
  * Windows over time.
  * Batch tensors.

* Compositors are lenses:

> They decide what a client sees.

* Compositors are used:

  * For client-facing introspection.
  * For memory degradation.
  * For analytics.

* Degradation is just a view. Membry uses Compositors to store simplified versions of raw frames.

---

## Membry

> Memory that fades, simplifies, and forgets.

Membry is the long-term, lossy memory store of the system.

* It persists selected views of frames in an external store (e.g. Redis).

* Uses TTL (time-to-live) to model fading memory.

* Supports region-aware, attention-guided retention:

  * Frames in hot regions (as defined by Cursors) get longer TTL.
  * Unused frames fade faster.

* Memory is expensive:

  * Clients pay (with Dust) to keep regions alive.
  * Higher payment → longer TTL, less degradation.
  * Cheaper regions → faster decay, greater simplification.

* Clients shape memory by buying attention.

---

## Economic Model (Dust)

* Observation isn’t free.

* Clients spend Dust to:

  * Register Cursors.
  * Control TTL of stored frames.
  * Influence degradation level.

* Memory is a market:

  * High-value regions get more precise, longer-lasting memory.
  * Low-value regions degrade or vanish.

* Memory is not uniform. It is shaped by demand.

---

## Flow Example

1. Client pays Dust to introspect region:

```python
cursor = Cursor(
  axes=["volume", "temperature"],
  tick_range=(1000, 1100),
  owner="client_42",
  metadata={"dust_budget": 10}
)
membry.register_cursor(cursor)
```

2. Collector continues recording raw MultiAxisFrames.

3. System emits Turn:

* Collects relevant frames.
* Collates into batch.

4. Membry triggers:

* Finds overlapping Cursors.
* Computes TTL and degradation level (based on Dust).
* Invokes Compositor to degrade data appropriately.
* Stores simplified view in Redis with calculated TTL.

5. Clients later retrieve:

* High-paying regions → high-resolution, long-lived memory.
* Low-paying regions → fuzzy, short-lived memory.
* Cold regions → forgotten entirely.

---

## Key Interfaces

* Collector:

  * `.collect_axis_data()`
  * `.get_time_window()`
  * `.get_axis_history()`

* Compositor:

  * `.compose_frame()`
  * `.compose_window()`
  * Holds pipeline of CompositionRules

* Cursor:

  * Defines attention region
  * Can be static or dynamic
  * Controls Dust budget

* MembryMixin:

  * `.register_cursor()`
  * `.remember_turn()`
  * `.load_frame()`
  * Computes TTL based on attention

* External Store (e.g. Redis):

  * Holds degraded frames
  * TTL models natural forgetting

---

## Design Summary

* Plantangenet models real-world observation:

  * High-resolution, short-term recording.
  * Long-term, lossy, demand-driven memory.
  * Economic model for memory allocation.
  * Pluggable, modular views via Compositors.
  * Regions of interest tracked via Cursors.

---

## Philosophy

> Memory is valuable. Observation costs.
> Attention shapes what is kept.
> Unused regions fade away.
> The system remembers what matters.

---

## Next Steps

* Implement Cursor registration with Dust accounting.
* Define Turn collation process.
* Build MembryMixin with:

  * Attention-aware TTL strategy.
  * Integration with Compositor for degradation.
  * External store persistence.
* Define domain-specific Compositors.
* Expose friendly, domain-level APIs hiding axes/ticks from users.

## Contributing

If you're extending Plantangenet:

* Don't break separation of concerns:

  * Collector = raw truth
  * Compositor = view generator
  * Membry = memory policy
  * Cursor = attention declaration

* Keep domain adapters clean: Expose domain concepts, not raw axes.

---
Copyright (c) 1998-2025 Scott Russell
SPDX-License-Identifier: MIT 