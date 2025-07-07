from abc import ABC, abstractmethod
from typing import Any, Dict, List, Tuple, Optional
import numpy as np
from plantangenet.compositor.base import BaseCompositor
from plantangenet.comdec.comdec import ComdecManager


class FBCompositor(BaseCompositor):
    """Base class for all framebuffer compositors (UI, graphics, etc)."""

    def __init__(self, width: int = 800, height: int = 600, channels: int = 4):
        super().__init__()
        self.width = width
        self.height = height
        self.channels = channels  # RGBA = 4, RGB = 3, etc.
        self.framebuffer = np.zeros((height, width, channels), dtype=np.uint8)
        # Comdec integration
        self.comdec_manager = ComdecManager()
        self.frame_count = 0
        self.last_present_time = 0

    def add_comdec(self, comdec):
        self.comdec_manager.add_comdec(comdec)

    async def broadcast_frame(self, frame=None, metadata=None):
        if frame is None:
            frame = self.framebuffer.copy()
        if metadata is None:
            metadata = {'frame_count': self.frame_count,
                        'timestamp': self.last_present_time}
        await self.comdec_manager.broadcast_frame(frame, metadata)

    @abstractmethod
    def present(self, framebuffer: Optional[np.ndarray] = None, **kwargs) -> Any:
        """Present the framebuffer to the display or UI layer."""
        pass

    @abstractmethod
    def handle_events(self, events: List[Any], **kwargs) -> bool:
        """Handle input/events and update framebuffer state. Returns True if redraw needed."""
        pass

    def transform(self, data, **kwargs):
        """Default: update framebuffer with new data and present."""
        if isinstance(data, np.ndarray):
            self.framebuffer = data
        elif isinstance(data, list):  # events
            self.handle_events(data, **kwargs)
        return self.present(**kwargs)

    def compose(self, *args, **kwargs):
        """Default: return current framebuffer state."""
        return self.framebuffer.copy()

    def clear(self, color: Tuple[int, int, int, int] = (0, 0, 0, 255)):
        """Clear framebuffer to specified color."""
        self.framebuffer[:, :] = color

    def set_pixel(self, x: int, y: int, color: Tuple[int, int, int, int]):
        """Set a single pixel."""
        if 0 <= x < self.width and 0 <= y < self.height:
            self.framebuffer[y, x] = color

    def get_pixel(self, x: int, y: int) -> Tuple[int, int, int, int]:
        """Get a single pixel."""
        if 0 <= x < self.width and 0 <= y < self.height:
            return tuple(self.framebuffer[y, x])
        return (0, 0, 0, 0)

    def draw_rect(self, x: int, y: int, w: int, h: int, color: Tuple[int, int, int, int]):
        """Draw a filled rectangle."""
        x1, y1 = max(0, x), max(0, y)
        x2, y2 = min(self.width, x + w), min(self.height, y + h)
        if x1 < x2 and y1 < y2:
            self.framebuffer[y1:y2, x1:x2] = color


class SoftwareFBCompositor(FBCompositor):
    """Software-rendered framebuffer compositor."""

    def present(self, framebuffer: Optional[np.ndarray] = None, **kwargs) -> np.ndarray:
        """Present by returning the framebuffer (software rendering)."""
        fb = framebuffer if framebuffer is not None else self.framebuffer
        return fb.copy()

    def handle_events(self, events: List[Any], **kwargs) -> bool:
        """Handle events for software rendering (stub)."""
        return len(events) > 0


class ImmediateModeFBCompositor(FBCompositor):
    """Immediate mode UI framebuffer compositor."""

    def __init__(self, width: int = 800, height: int = 600, channels: int = 4):
        super().__init__(width, height, channels)
        self.ui_state = {}
        self.widgets = []

    def present(self, framebuffer: Optional[np.ndarray] = None, **kwargs) -> Dict[str, Any]:
        """Present immediate mode UI state."""
        return {
            "framebuffer": framebuffer if framebuffer is not None else self.framebuffer.copy(),
            "ui_state": self.ui_state.copy(),
            "widgets": self.widgets.copy()
        }

    def handle_events(self, events: List[Any], **kwargs) -> bool:
        """Handle immediate mode UI events."""
        redraw_needed = False
        for event in events:
            if event.get("type") == "button_click":
                button_id = event.get("id", "")
                # Store click state using the full button ID
                self.ui_state[button_id] = True
                redraw_needed = True
            elif event.get("type") == "mouse_move":
                self.ui_state["mouse_pos"] = (
                    event.get("x", 0), event.get("y", 0))
                redraw_needed = True
        return redraw_needed

    def begin_frame(self):
        """Begin immediate mode frame."""
        self.widgets.clear()
        self.clear((50, 50, 50, 255))  # Dark gray background

    def button(self, label: str, x: int, y: int, w: int = 100, h: int = 30) -> bool:
        """Draw immediate mode button and return if clicked."""
        button_id = f"button_{len(self.widgets)}"
        self.widgets.append({"type": "button", "label": label,
                            "x": x, "y": y, "w": w, "h": h, "id": button_id})

        # Draw button
        color = (100, 100, 100, 255) if not self.ui_state.get(
            button_id, False) else (150, 150, 150, 255)
        self.draw_rect(x, y, w, h, color)

        # Check if clicked and reset state
        clicked = self.ui_state.get(button_id, False)
        if clicked:
            self.ui_state[button_id] = False  # Reset click state immediately
        return clicked

    def end_frame(self):
        """End immediate mode frame."""
        pass


class DearImGuiCompositor(ImmediateModeFBCompositor):
    """Dear ImGui-style compositor (stub for future integration)."""

    def present(self, framebuffer: Optional[np.ndarray] = None, **kwargs) -> Dict[str, Any]:
        """Present Dear ImGui interface."""
        result = super().present(framebuffer, **kwargs)
        # Future: could be OpenGL, Vulkan, etc.
        result["imgui_backend"] = "software"
        return result
