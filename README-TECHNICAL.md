# Plantangenet Technical Overview

## Introduction

Plantangenet is a framework and event-driven runtime for **building small, bounded, policy-enforced worlds**. It is designed for developers who need **negotiated sharing**, **explicit trust boundaries**, **enforceable policies**, and **ephemeral, attention-shaped memory**.

Plantangenet lets you model **privacy**, **trust**, **negotiation**, and **economic memory** as first-class system features. It is not just an API - it's a system design approach for building "tiny universes" where participants negotiate *what* they reveal, *to whom*, *at what level of detail*, and *for how long*.

---

## Core Concepts

* **Sessions**: Bounded contexts managing identity, policy, lifecycles, and local state. Sessions are the central observable and coordinator for all agents and compositors.
* **Agents**: Policy-enforced actors that embody roles, preferences, and trust boundaries. Agents expose observable state and rendering methods for compositors.
* **Compositors**: Transformations that generate partial, policy-filtered views. Compositors (like dashboards) observe session/agent state and render or export it.
* **Comdecs/Observables**: Output modules (loggers, snapshotters, streamers, dashboards) that subscribe to session or agent state and update outputs in real time.
* **Policies**: Machine-enforced rules governing who can do what, when, and how. Policies are enforced at both the session and agent level.
* **Cursors**: Focus declarations defining regions of interest, shaping memory and data access.
* **Membry**: Attention-shaped, degraded, fading memory with TTL and Dust accounting.
* **Dust**: Internal accounting system for contributions, value exchange, and attention prioritization.

---

## Sessions and Observables

A **Session** is the central trust boundary and observable in Plantangenet. It manages all agents, compositors, and output modules. Observables (comdecs, dashboards, loggers) subscribe to session or agent state and update outputs automatically when state changes.

**Diagram:**

```
+-------------------+
|     Session       |
|-------------------|
|  Agents[]         |
|  Compositors[]    |
|  Policy           |
|  Identity         |
+-------------------+
        |      |         
        v      v         
   [Agent]  [Compositor]   
      |         |         
      v         v         
   (State)   (Render)     
        \     /           
         [Observable]     
         (Comdec, Logger, Dashboard, Streamer)
```

- **Agents** expose state and rendering methods (e.g. `get_widget`, `__render__`).
- **Compositors** (like dashboards) collect and arrange widgets from agents.
- **Observables** (comdecs, loggers, streamers) subscribe to state and update outputs in real time.
- **Session** coordinates all updates, policy checks, and output notifications.

### Example: Dashboard Observable

The WidgetDashboard compositor observes all agents and session state. Each agent provides a `get_widget(asset=...)` method for rendering its widget. The dashboard arranges these widgets and outputs a live framebuffer, which can be streamed (MJPEG), logged, or snapshotted by comdecs.

```python
# Pseudocode
session = Session(...)
dashboard = WidgetDashboard(...)
session.add_compositor("dashboard", dashboard)

# Each agent implements get_widget(asset=...)
class TicTacToePlayer(Agent):
    def get_widget(self, asset="status_widget", **kwargs):
        ...

# Dashboard collects widgets from all agents
for agent in session.agents:
    widget = agent.get_widget(asset="status_widget")
    dashboard.add_widget(agent.id, widget)

# Comdecs observe dashboard output
mjpeg_comdec = MJPEGComdec(port=8080)
dashboard.add_comdec(mjpeg_comdec)
```

### Observables in Action

- **Comdecs**: Log, snapshot, or stream any observable state (agent, session, dashboard).
- **Dashboards**: Render live visualizations of all agents and session state.
- **Extensibility**: Add new observables by implementing the `consume` method and registering with the session or compositor.

---

## Technical Architecture

### Sessions

* Trust boundary and lifecycle manager.
* Manages agents, compositors, and metadata.
* Enforces policies for attached participants.
* Central observable for all state and output.

### Agents

* Actors embodying roles and preferences.
* Expose observable state and rendering methods.
* Enforce policy context during interactions.

### Compositors

* Generate **Views** of data tailored to policy.
* Collect widgets from agents and arrange them for output.
* Support multiple consumer perspectives from shared semantic buffers.

### Comdecs/Observables

* Output modules that subscribe to state and update outputs in real time.
* Examples: LoggerComdec, SnapshotterComdec, MJPEGComdec, WidgetDashboard.

### Policies

* Evaluate permissions using roles and context.
* Support static and negotiated policies.
* Enforce access for all operations.

### Cursors, Membry, Dust

* (See original documentation for advanced memory and economic features.)

---

## Example: TicTacToe Tournament with Observables

See `examples/tictactoe/README.md` and `main.py` for a full working example of sessions, agents, compositors, and observables in action.

---

## Status

Active development. Functional, evolving, and welcoming contributions.

---

## License

© 1998–2025 Scott Russell
SPDX-License-Identifier: MIT
