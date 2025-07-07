# Referee Abstraction in Plantangenet

## Overview

The referee abstraction in Plantangenet provides a protocol-driven, extensible way to adjudicate the state of a session, contest, or distributed agent system. Referees are responsible for evaluating one or more states and returning a structured result that encodes the outcome, the canonical state, and any additional information.

## Core Concepts

### Judgement
A strongly-typed enumeration of possible outcomes, such as:
- `UNKNOWN`: No clear outcome
- `WIN`, `LOSE`, `DRAW`: Standard contest results
- `CONTEST`, `CHEAT`, `ERROR`: Special or exceptional outcomes

### RefereeState
Encapsulates the information needed for adjudication, including:
- `identities`: The participants involved
- `state`: The current state (as a dict)
- `claims`: Optional assertions or disputes from participants

### AdjudicationResult
A container for the result of adjudication:
- `judgement`: The outcome (from the enum)
- `state`: The canonical or resulting state
- `info`: Optional extra data (logs, explanations, etc.)

### BaseReferee Protocol
Defines the contract for all referees:
- `adjudicate(states: List[dict]) -> AdjudicationResult`

This allows for polymorphic, plug-and-play referee implementations.

## Example: Minimal Referee

```python
from plantangenet.session.referee import BaseReferee, AdjudicationResult, Judgement
from random import choice

class Referee(BaseReferee):
    def adjudicate(self, states: List[dict]) -> AdjudicationResult:
        state = choice(states)
        return AdjudicationResult(
            Judgement.UNKNOWN,
            state,
            info={ "opinion": "random choice" }
        )
```

## When to Use
- To separate contest/session logic from outcome evaluation
- To enable testable, swappable, or pluggable adjudication logic
- For contests, distributed systems, or any scenario where state must be judged

## Extending
- Implement custom logic in your own referee class by subclassing or implementing the protocol
- Add new `Judgement` values as needed for your domain
- Use `info` to provide rich explanations, logs, or metadata

## See Also
- `python/plantangenet/session/referee.py` for the protocol and base types
- Example usage in `examples/breakout/referee.py`
