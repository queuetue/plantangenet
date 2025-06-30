__version__ = "0.1.0"
import os
import re
from .logger import Logger
from .buoy import Buoy
from .gyre import Gyre
from .shard import Shard
from .mixins.base import OceanMixinBase
from .mixins.frames import FramesMixin
from .mixins.heartbeat import HeartbeatMixin
from .mixins.luck import LuckMixin
from .mixins.nats import NatsMixin
from .mixins.policy import PolicyMixin
from .mixins.status import watch, Observable
from .mixins.status.mixin import StatusMixin
from .mixins.topics import TopicsMixin, on_topic
from .mixins.heartbeat import HeartbeatMixin
from .mixins.rox import RoxMixin
from .mixins.redis import RedisMixin
from .mixins.transport import TransportMixin
from .mixins.storage import StorageMixin
from .mixins.timebase import TimebaseMixin
from .mixins.turns import TurnMixin

NATS_URLS = re.split(
    r"[;,\s]+", os.getenv("NATS_URLS", "nats://localhost:4222")
    .strip().lower()) or ["nats://localhost:4222"]

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

GLOBAL_LOGGER = Logger()


def get_logger() -> Logger:
    """Get the global logger instance."""
    return GLOBAL_LOGGER


__all__ = [
    "Buoy",
    "Shard",
    "Gyre",
    "OceanMixinBase",
    "FramesMixin",
    "HeartbeatMixin",
    "Logger",
    "NATS_URLS",
    "REDIS_URL",
    "get_logger",
    "on_topic",
    "Observable",
    "LuckMixin",
    "NatsMixin",
    "PolicyMixin",
    "RedisMixin",
    "RoxMixin",
    "watch",
    "StatusMixin",
    "StorageMixin",
    "TimebaseMixin",
    "TopicsMixin",
    "TransportMixin",
    "TurnMixin",
    "__version__",
    "GLOBAL_LOGGER"
]
