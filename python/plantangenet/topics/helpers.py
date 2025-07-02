from .wrapper import TopicsWrapper
from typing import Any, Callable, Optional, Union


def on_topic(
    topic: str,
    mod: int = 1,
    cooldown: Optional[float] = None,
    jitter: Optional[float] = None,
    predicate: Optional[Callable[[Any], bool]] = None,
    debounce: Optional[float] = None,
    once: bool = False,
    changed: Union[bool, Callable[[Any], Any]] = False,
    rate_limit: Optional[float] = None,
):
    return TopicsWrapper(
        topic,
        mod=mod,
        cooldown=cooldown,
        jitter=jitter,
        predicate=predicate,
        debounce=debounce,
        once=once,
        changed=changed,
        rate_limit=rate_limit,
    )
