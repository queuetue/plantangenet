import time
import os
import yaml
import json
import numpy as np
from typing import Any, Dict, Optional
from .base import BaseComdec


class SnapshotterComdec(BaseComdec):
    """Snapshotter codec that saves frames as PNG files or stats as YAML or JSON."""

    def __init__(self, filepath: str = "", output_dir: str = "./snapshots", interval_seconds: float = 1.0,
                 prefix: str = "frame", format: str = "yaml", **config):
        super().__init__("snapshotter", **config)
        self.filepath = filepath  # If set, use this for stats
        self.output_dir = output_dir
        self.interval_seconds = interval_seconds
        self.prefix = prefix
        self.format = format.lower()
        self.last_snapshot_time = 0
        os.makedirs(output_dir, exist_ok=True)

    async def consume(self, frame: Any, metadata: Optional[Dict[str, Any]] = None) -> bool:
        try:
            current_time = time.time()
            self.frame_count += 1
            self.stats['frames_consumed'] += 1
            self.stats['last_frame_time'] = current_time
            # If frame is a dict (stats), write as YAML or JSON
            if isinstance(frame, dict):
                ext = ".json" if self.format == "json" else ".omni.yaml"
                if self.filepath:
                    path = self.filepath
                else:
                    filename = f"{self.prefix}_{self.frame_count:06d}_{int(current_time)}{ext}"
                    path = os.path.join(self.output_dir, filename)
                with open(path, 'w') as f:
                    if self.format == "json":
                        json.dump(frame, f, indent=2)
                    else:
                        yaml.safe_dump(frame, f, sort_keys=False)
                if self.format == "json":
                    self.stats['bytes_processed'] += len(json.dumps(frame))
                else:
                    self.stats['bytes_processed'] += len(yaml.safe_dump(frame))
                return True
            # Otherwise, fallback to image/array logic
            if current_time - self.last_snapshot_time >= self.interval_seconds:
                await self._save_snapshot(frame, metadata, current_time)
                self.last_snapshot_time = current_time
            return True
        except Exception as e:
            self.stats['errors'] += 1
            print(f"SnapshotterComdec error: {e}")
            return False

    async def _save_snapshot(self, frame: Any, metadata: Optional[Dict[str, Any]], timestamp: float):
        try:
            if isinstance(frame, np.ndarray):
                from PIL import Image
                if frame.dtype != np.uint8:
                    frame = (
                        frame * 255).astype(np.uint8) if frame.max() <= 1.0 else frame.astype(np.uint8)
                if len(frame.shape) == 3 and frame.shape[2] == 3:
                    img = Image.fromarray(frame, 'RGB')
                elif len(frame.shape) == 2:
                    img = Image.fromarray(frame, 'L')
                else:
                    print(f"Unsupported frame shape: {frame.shape}")
                    return
                filename = f"{self.prefix}_{self.frame_count:06d}_{int(timestamp)}.png"
                filepath = f"{self.output_dir}/{filename}"
                img.save(filepath)
                print(f"Snapshot saved: {filepath}")
                self.stats['bytes_processed'] += img.size[0] * \
                    img.size[1] * 3
        except Exception as e:
            print(f"Error saving snapshot: {e}")
            self.stats['errors'] += 1
