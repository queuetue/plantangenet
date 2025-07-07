import time
import yaml
import json
import numpy as np
from typing import Any, Dict, Optional
from .base import BaseComdec


class StreamingComdec(BaseComdec):
    """
    Streaming codec for sending compositions (frames, results, etc) over a wire-friendly protocol.
    Can handle partials, chunked data, or custom serialization for real-time consumers.
    """

    def __init__(self, stream_handler, format: str = "yaml", **config):
        super().__init__("streaming", **config)
        self.stream_handler = stream_handler
        self.format = format.lower()

    async def consume(self, frame: Any, metadata: Optional[Dict[str, Any]] = None) -> bool:
        try:
            import collections.abc
            self.frame_count += 1
            self.stats['frames_consumed'] += 1
            self.stats['last_frame_time'] = time.time()
            # If frame is a dict (stats), stream as YAML or JSON
            if isinstance(frame, dict):
                if self.format == "json":
                    payload = json.dumps(frame, indent=2).encode('utf-8')
                else:
                    payload = yaml.safe_dump(
                        frame, sort_keys=False).encode('utf-8')
            else:
                payload = self.serialize(frame, metadata)
            if callable(self.stream_handler):
                result = self.stream_handler(payload)
                if isinstance(result, collections.abc.Awaitable):
                    await result
            return True
        except Exception as e:
            self.stats['errors'] += 1
            print(f"StreamingComdec error: {e}")
            return False

    def serialize(self, frame: Any, metadata: Optional[Dict[str, Any]] = None) -> bytes:
        if isinstance(frame, np.ndarray):
            frame_data = frame.tolist()
        else:
            frame_data = frame
        payload = {
            'frame': frame_data,
            'metadata': metadata or {},
            'frame_count': self.frame_count
        }
        if self.format == "json":
            return json.dumps(payload, indent=2).encode('utf-8')
        else:
            return yaml.safe_dump(payload, sort_keys=False).encode('utf-8')
