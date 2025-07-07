import time
import yaml
import json
import numpy as np
from typing import Any, Dict, Optional
from .base import BaseComdec


class LoggerComdec(BaseComdec):
    """Logger codec that logs frame metadata and stats as YAML or JSON."""

    def __init__(self, log_stream=None, log_level: str = "INFO", format: str = "yaml", **config):
        super().__init__("logger", **config)
        self.log_level = log_level
        self.log_stream = log_stream  # If set, write logs here
        self.format = format.lower()

    async def consume(self, frame: Any, metadata: Optional[Dict[str, Any]] = None) -> bool:
        try:
            self.frame_count += 1
            self.stats['frames_consumed'] += 1
            self.stats['last_frame_time'] = time.time()
            # If frame is a dict (stats), log as YAML or JSON
            if isinstance(frame, dict):
                if self.format == "json":
                    log_line = json.dumps(frame, indent=2)
                else:
                    log_line = yaml.safe_dump(frame, sort_keys=False)
                if self.log_stream:
                    self.log_stream.write(log_line + "\n")
                else:
                    print(f"[LoggerComdec] {log_line}")
                return True
            # Otherwise, fallback to image/array logic
            frame_info = {
                'frame_count': self.frame_count,
                'frame_type': type(frame).__name__,
                'timestamp': time.time()
            }
            if isinstance(frame, np.ndarray):
                frame_info.update({
                    'shape': frame.shape,
                    'dtype': str(frame.dtype),
                    'size_bytes': frame.nbytes
                })
                self.stats['bytes_processed'] += frame.nbytes
            if metadata:
                frame_info['metadata'] = metadata
            if self.log_level == "DEBUG":
                print(f"[LoggerComdec] Frame {self.frame_count}: {frame_info}")
            elif self.frame_count % 10 == 0:
                print(
                    f"[LoggerComdec] Processed {self.frame_count} frames, latest: {frame_info}")
            return True
        except Exception as e:
            self.stats['errors'] += 1
            print(f"LoggerComdec error: {e}")
            return False
