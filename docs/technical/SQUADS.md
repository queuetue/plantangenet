# The Squad Concept in Plantangenet

## Overview

The `Squad` abstraction in Plantangenet provides a unified, extensible pattern for group-based management of objects within a session or distributed agent system. It is designed to support modular, testable, and composable management of agents, updatables, and other participants, and serves as the foundation for more specialized managers (such as `VanillaSquad`, `ChocolateSquad`, and others).

## Motivation

Traditional agent systems often have ad-hoc or tightly-coupled management of agents, bankers, and other session participants. The `Squad` pattern unifies these under a common protocol, enabling:
- Consistent group management (add, remove, query, difference)
- Extensible update and transform logic
- Easy composition and subclassing for domain-specific needs
- Improved testability and modularity

## Core API

A `Squad` (or subclass) typically provides:
- `add(group: str, obj: Any)`: Add an object to a named group
- `remove(group: str, obj: Any)`: Remove an object from a group
- `get(group: str) -> List[Any]`: Retrieve all objects in a group
- `all() -> dict`: Get all groups and their members
- `difference(group_a: str, group_b: str) -> list`: Objects in group_a but not in group_b
- `query(group: str, predicate: Callable[[Any], bool]) -> list`: Filter group by predicate
- `transform(group: str, data: Any, frame: Any) -> Any`: Optional, for data transformation

## Specializations

- **VanillaSquad**: Basic group manager, no update loop
- **ChocolateSquad**: Adds an async `update()` method, which updates all objects in the `updatables` group (if they have an `update` method)
- **StrawberrySquad**: (If present) May add hierarchical or parent-manager logic

## Example Usage

```python
from plantangenet.squads.vanilla import VanillaSquad
from plantangenet.squads.chocolate import ChocolateSquad

squad = VanillaSquad(name="my_squad")
squad.add('agents', agent1)
squad.add('agents', agent2)
agents = squad.get('agents')

choco = ChocolateSquad(name="choco")
choco.add('updatables', agent1)
choco.add('updatables', agent2)
await choco.update()  # Calls update() on all updatables
```

## Testing

The squads system is designed for easy testing. See `python/tests/test_squads.py` for examples covering group management and update logic.

## When to Use

Use the `Squad` pattern whenever you need to manage collections of agents, updatables, or other session participants in a modular, extensible, and testable way. Subclass or compose as needed for your domain.
