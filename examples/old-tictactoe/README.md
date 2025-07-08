# Plantangenet TicTacToe Multi-Agent Tournament Demo

This directory contains a modern, extensible multi-agent TicTacToe tournament system built on the Plantangenet session/compositor/omni architecture. It demonstrates unified agent management, pluggable output systems, policy enforcement, and live dashboard visualization.

## Key Features

- **Session/Omni Architecture:** All agents (referees, players, stats) are managed by a central `Session`, supporting unified state aggregation and policy enforcement.
- **Compositor/Comdec/Observable System:** Output is handled by pluggable "comdecs" (codecs/output modules) and compositors (such as dashboards) that observe and transform agent/session state. Observables can subscribe to state changes and render or export them in real time.
- **Policy Enforcement:** Per-game and global policy enforcement via robust, memoizing `LocalPolicy` and session policy delegation.
- **Widget Dashboard:** Live dashboard compositor renders widgets for each agent, stats, and tournament state. Widgets are rendered by each agent's `__render__`/`get_widget` method, supporting asset-based rendering.
- **Extensible Asset System:** Agents can render different widget types (assets) for the dashboard or other consumers, e.g. `status_widget`, with easy extension for new visualizations.
- **Robust Tournament Logic:** Supports both fixed-tournament and batch (infinite play) modes, with automatic player reshuffling and deadlock prevention.
- **Comprehensive Testing:** Includes tests for policy, tournament logic, error handling, and output systems.

## How It Works

- **Agents:**
  - `TicTacToeReferee`: Manages games, enforces policy, recycles players, and coordinates with the session.
  - `TicTacToePlayer`: Simple AI player, tracks its own stats, renders its own widget.
  - `TicTacToeStats`: Aggregates results, provides output to comdecs, and renders a stats widget.
- **Session:**
  - Central manager for all agents and compositors.
  - Aggregates state, enforces policy, and coordinates output.
- **Comdec/Observable System:**
  - Pluggable output modules (comdecs) and compositors (like dashboards) observe agent/session state and render, log, or stream it.
  - Observables can subscribe to state changes and update outputs in real time.
- **Widget Dashboard:**
  - Renders a live visual dashboard of all agents and tournament state, using each agent's `get_widget(asset=...)` method.
  - Supports user-agent-based output formatting and future extensibility.

## Observables and Output

The system uses an **observable pattern**: compositors and comdecs subscribe to session or agent state, and automatically update outputs (logs, dashboards, streams) when state changes. This enables real-time dashboards, live MJPEG streaming, and pluggable output formats with minimal coupling.

## Running the Demo

### Console Mode

To run a quick tournament in the console (no dashboard):

```sh
python3 run_console.py --games 100 --players 6 --refs 2
```

- `--games N`: Number of games to play (default: 100)
- `--players M`: Number of players (default: 4)
- `--refs R`: Number of referees (default: 2)
- `--benchmark`: Enable benchmark mode (runs as fast as possible)

### Visual Dashboard Mode

To run with a live dashboard (MJPEG stream, snapshots, etc):

```sh
python3 main.py --dashboard --players 6 --refs 2 --time 30
```

- Open [http://localhost:8080/](http://localhost:8080/) in your browser or VLC to view the live dashboard.
- Snapshots are saved to `./tictactoe_snapshots/`.
- All widgets (players, referees, stats, tournament) are rendered live and updated every second.

### Tournament vs Batch Mode

- `--tournament`: Run a fixed set of games, then stop.
- Default (no `--tournament`): Batch mode, runs indefinitely (or until `--time` is reached).

## Extending the System

- **Add New Widget Types:**
  - Implement new assets in each agent's `get_widget(asset=...)` and `__render__` methods.
  - Update the dashboard to request and display new widget types.
- **Add New Comdecs/Observables:**
  - Implement a new comdec or compositor in `plantangenet/comdec/` and register it with the session or dashboard.
- **Policy/Activity:**
  - Extend or replace the policy system for more complex permissioning or activity types.

## File Overview

- `main.py`: Main entry point for dashboard/tournament mode.
- `run_console.py`: Minimal CLI runner for console-only tournaments.
- `referee.py`, `player.py`, `stats.py`: Agent implementations.
- `widget_dashboard.py`: Dashboard compositor and widget logic.
- `game.py`, `local_policy.py`, `tictactoe_types.py`: Game and policy logic.
- `policy.py`: Example permissive policy and identity.

## Requirements

- Python 3.8+
- `Pillow`, `numpy`, and other dependencies in `requirements.txt`

## License

MIT License. Copyright (c) 1998-2025 Scott Russell
