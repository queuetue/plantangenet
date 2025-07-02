__version__ = "0.1.0"
import os
import re
from .agent import Agent
from .buoy import Buoy
from .cursor import Cursor
from .drift import Drift
from .gyre import Gyre
from .logger import Logger
from .message import Message
from .session import Session
from .shard import Shard
from .utilities import (
    smtpe_from_stamp,
    midi_time_from_stamp,
    samples_from_stamp,
    tick_count_from_stamp,
    beat_count_from_stamp,
    conductor_time_from_stamp
)
from .mixins import (
    TimebaseMixin,
    HeartbeatMixin,
    TopicsMixin,
    OceanMixinBase,
    FramesMixin,
    HeartbeatMixin,
    LuckMixin,
    NatsMixin,
    PolicyMixin,
    RedisMixin,
    RoxMixin,
    StorageMixin,
    TimebaseMixin,
    TransportMixin,
    OmniMixin,
)

from .collector import (
    TimeSeriesCollector,
    AxisFrame,
    MultiAxisFrame
)

from .policy import (
    Vanilla,
    Identity,
    Statement,
    Role
)

from .coordinators import (
    AxisCoordinator,
    MultiAxisCoordinator,
    TemporalCoordinator,
    TemporalMultiAxisCoordinator
)

from .omni import (
    OmniMeta,
    Observable,
    PersistedBase,
    Omni,
    persist,
    watch
)

from .topics import (
    TopicsWrapper,
    on_topic,
)


NATS_URLS = re.split(
    r"[;,\s]+", os.getenv("NATS_URLS", "nats://localhost:4222")
    .strip().lower()) or ["nats://localhost:4222"]

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

GLOBAL_LOGGER = Logger()


def get_logger() -> Logger:
    """Get the global logger instance."""
    return GLOBAL_LOGGER


__all__ = [
    "__version__",
    "Agent",
    "Buoy",
    "Cursor",
    "Drift",
    "Gyre",
    "Logger",
    "Message",
    "Session",
    "Shard",
    "smtpe_from_stamp",
    "midi_time_from_stamp",
    "samples_from_stamp",
    "tick_count_from_stamp",
    "beat_count_from_stamp",
    "conductor_time_from_stamp",
    "TimebaseMixin",
    "HeartbeatMixin",
    "TopicsMixin",
    "OceanMixinBase",
    "FramesMixin",
    "LuckMixin",
    "NatsMixin",
    "PolicyMixin",
    "RedisMixin",
    "RoxMixin",
    "StorageMixin",
    "TimebaseMixin",
    "TransportMixin",
    "OmniMixin",
    "TimeSeriesCollector",
    "AxisFrame",
    "MultiAxisFrame",
    "Vanilla",
    "Identity",
    "Statement",
    "Role",
    "AxisCoordinator",
    "MultiAxisCoordinator",
    "TemporalCoordinator",
    "TemporalMultiAxisCoordinator",
    "OmniMeta",
    "Observable",
    "PersistedBase",
    "Omni",
    "persist",
    "watch",
    "TopicsWrapper",
    "on_topic",
    "get_logger",
    "NATS_URLS",
    "REDIS_URL",
]
