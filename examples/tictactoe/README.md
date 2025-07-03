# TicTacToe Multi-Agent Tournament Example

This example demonstrates how to build a modern, session-centric multi-agent simulation using the Plantangenet `SessionApp` pattern. It is designed as a teaching tool for:

- **Agent orchestration and lifecycle management**
- **Periodic async tasks and event loops**
- **Message-passing and agent coordination**
- **Economic simulation and resource accounting**
- **Best practices for scalable, testable agent systems**

## What This Example Does

- **Simulates a tournament of Tic Tac Toe games** between multiple autonomous player agents.
- **A referee agent** matches players, manages game state, and enforces rules.
- **Players are recycled** after each game, so the tournament runs continuously.
- **A scoreboard** is maintained and printed periodically, showing games played and wins per agent.
- **Economic transactions** ("dust") are simulated for each completed game.
- **Graceful shutdown** is handled automatically after a configurable runtime.

## Architecture

- `main.py`: Main entry point. Sets up the session, agents, periodic tasks, and runs the event loop.
- **Agents**: All agents inherit from Plantangenet's `Agent` base class.
  - `TicTacToePlayer`: Makes moves, tracks stats, and participates in games.
  - `TicTacToeReferee`: Manages matchmaking, game state, and scoring.
  - `TicTacToeStats`: (Optional) Collects and reports statistics.
- **SessionApp**: Orchestrates agent updates, periodic tasks, and shutdown.

## How to Run

```sh
python examples/tictactoe/main.py
```

## Customization & Experimentation

- **Number of players**: Set `NUM_PLAYERS` env var or edit `num_players` in `main.py`.
- **Reporting interval**: Set `REPORTING_INTERVAL` env var or edit `reporting_interval`.
- **Max runtime**: Set `max_runtime` in `SessionApp` (default: 10 seconds).
- **Agent logic**: Try modifying the `TicTacToePlayer` or `TicTacToeReferee` classes to experiment with strategies, communication, or learning.
- **Economic simulation**: See how dust transactions are handled and try integrating with a real ledger or message bus.

## Learning Goals

- Understand how to structure a multi-agent system using async Python and Plantangenet's orchestration tools.
- Learn how to register, update, and coordinate agents in a session-centric architecture.
- See how to implement periodic reporting, resource management, and graceful shutdown.
- Use this as a template for more complex simulations, games, or distributed agent systems.

---

**Explore, modify, and extend!** This example is meant to be a playground for learning and prototyping with Plantangenet's modern orchestration patterns.
