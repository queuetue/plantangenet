from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class BaseComdec(ABC):
    """Base class for all comdecs (compositor/decoder codecs)."""

    def __init__(self, name: str, **config):
        self.name = name
        self.config = config
        self.frame_count = 0
        self.last_consume_time = None
        self.stats = {
            'frames_consumed': 0,
            'bytes_processed': 0,
            'errors': 0,
            'last_frame_time': None
        }

    @abstractmethod
    async def consume(self, frame: Any, metadata: Optional[Dict[str, Any]] = None) -> bool:
        pass

    async def initialize(self) -> bool:
        return True

    async def finalize(self) -> bool:
        return True

    def get_stats(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'config': self.config,
            'frame_count': self.frame_count,
            **self.stats
        }
