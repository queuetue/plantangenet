__version__ = "0.1.0"
import os
import re
from plantangenet.agents.agent import Agent
from plantangenet.agents.gyre import Gyre
from plantangenet.agents.float import Float
from .cursor import Cursor
from .logger import Logger
from .message import Message
from .session import Session
from .helpers.time import (
    smtpe_from_stamp,
    midi_time_from_stamp,
    samples_from_stamp,
    tick_count_from_stamp,
    beat_count_from_stamp,
    conductor_time_from_stamp
)
from .collector import (
    TimeSeriesCollector,
    AxisFrame,
    MultiAxisFrame
)
from .policy import (
    Policy,
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
from .omni.mixins import (
    TimebaseMixin,
    HeartbeatMixin,
    TopicsMixin,
    OmniMixin,
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
    "Cursor",
    "Gyre",
    "Logger",
    "Message",
    "Session",
    "Float",
    "smtpe_from_stamp",
    "midi_time_from_stamp",
    "samples_from_stamp",
    "tick_count_from_stamp",
    "beat_count_from_stamp",
    "conductor_time_from_stamp",
    "TimebaseMixin",
    "HeartbeatMixin",
    "TopicsMixin",
    "OmniMixin",
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
    "Policy",
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
