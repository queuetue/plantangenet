"""
Comdec System - Compositor/Decoder Communication Framework

This module provides a codec system for communicating with compositors in their language,
commonly monodirectional. Codecs consume compositor outputs and transform them into
various formats or destinations (files, streams, displays, etc).
"""

from typing import Any, Dict, Optional, List
from plantangenet.core import ComponentRegistryMixin
from .base import BaseComdec
from .snapshotter import SnapshotterComdec
from .logger import LoggerComdec
from .streaming import StreamingComdec


class ComdecManager(ComponentRegistryMixin):
    """Manager for multiple comdecs attached to a compositor."""

    def __init__(self):
        super().__init__()
        self.active = True

    def add_comdec(self, comdec: BaseComdec):
        """Add a comdec to this manager."""
        self.add_component(comdec)

    def remove_comdec(self, comdec_name: str) -> bool:
        """Remove a comdec by name."""
        comdec = self.get_component(comdec_name)
        if comdec:
            self.remove_component(comdec)
            return True
        return False

    @property
    def comdecs(self) -> List[BaseComdec]:
        """Get all comdecs as a list for backward compatibility."""
        return [c for c in self.get_components_by_type(BaseComdec) if isinstance(c, BaseComdec)]

    async def broadcast_frame(self, frame: Any, metadata: Optional[Dict[str, Any]] = None):
        if not self.active:
            return
        for comdec in self.comdecs:
            try:
                await comdec.consume(frame, metadata)
            except Exception as e:
                comdec.add_error(f"Error consuming frame: {e}")
                print(f"Error in comdec {comdec.name}: {e}")

    async def initialize_all(self):
        for comdec in self.comdecs:
            try:
                await comdec.initialize()
            except Exception as e:
                print(f"Error initializing comdec {comdec.name}: {e}")

    async def finalize_all(self):
        for comdec in self.comdecs:
            try:
                await comdec.finalize()
            except Exception as e:
                print(f"Error finalizing comdec {comdec.name}: {e}")

    def get_all_stats(self) -> Dict[str, Any]:
        return {
            'active': self.active,
            'comdec_count': len(self.comdecs),
            'comdecs': [comdec.get_stats() for comdec in self.comdecs]
        }

    def stop(self):
        self.active = False


__all__ = [
    "ComdecManager",
    "SnapshotterComdec",
    "LoggerComdec",
    "StreamingComdec",
]
