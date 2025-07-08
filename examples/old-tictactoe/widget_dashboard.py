import numpy as np
from typing import Dict, Any, List, Tuple, Optional
from plantangenet.compositor.base import BaseCompositor
from plantangenet.comdec.manager import ComdecManager
import time


class Widget:
    """Represents a drawable widget on the dashboard."""

    def __init__(self, x: int, y: int, width: int, height: int, color: Tuple[int, int, int] = (255, 255, 255), participant=None, style=None):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.color = color
        self.text = ""
        self.border_color = (128, 128, 128)
        self.text_color = (0, 0, 0)
        self.participant = participant
        self.style = style

    def set_text(self, text: str):
        self.text = text
        return self

    def set_color(self, color: Tuple[int, int, int]):
        self.color = color
        return self

    def set_border_color(self, color: Tuple[int, int, int]):
        self.border_color = color
        return self


class WidgetDashboard(BaseCompositor):
    """
    A framebuffer compositor that draws widgets representing agent states.
    Supports vertical and horizontal layouts for immediate UI rendering.
    Integrates with comdec system for output handling.
    """

    def __init__(self, width: int = 800, height: int = 600, dpi: int = 72):
        super().__init__()
        self.width = width
        self.height = height
        self.dpi = dpi
        self.framebuffer = np.zeros((height, width, 3), dtype=np.uint8)
        self.widgets: Dict[str, Widget] = {}
        self.layout_direction = "horizontal"  # "horizontal" or "vertical"
        self.padding = 10
        self.widget_size = (120, 80)  # default widget size

        # Comdec integration
        self.comdec_manager = ComdecManager()
        self.frame_count = 0
        self.last_render_time = 0

        # Colors for different states
        self.colors = {
            'background': (30, 30, 30),
            'player_idle': (100, 150, 100),
            'player_playing': (255, 255, 100),
            'player_winner': (100, 255, 100),
            'referee_idle': (150, 100, 100),
            'referee_active': (255, 150, 150),
            'text': (255, 255, 255),
            'border': (128, 128, 128)
        }

    def clear(self):
        """Clear the framebuffer to background color."""
        self.framebuffer[:, :] = self.colors['background']

    def add_widget(self, name: str, widget: Widget, participant=None, style=None):
        """Add a widget to the dashboard, optionally associating a participant and style."""
        if participant is not None:
            widget.participant = participant
        if style is not None:
            widget.style = style
        self.widgets[name] = widget

    def remove_widget(self, name: str):
        """Remove a widget from the dashboard."""
        if name in self.widgets:
            del self.widgets[name]

    def auto_layout(self):
        """Automatically layout widgets based on layout_direction."""
        if not self.widgets:
            return

        widget_names = list(self.widgets.keys())
        widget_count = len(widget_names)

        if self.layout_direction == "horizontal":
            # Arrange widgets horizontally
            cols = min(widget_count, self.width //
                       (self.widget_size[0] + self.padding))
            rows = (widget_count + cols - 1) // cols

            for i, name in enumerate(widget_names):
                col = i % cols
                row = i // cols
                x = self.padding + col * (self.widget_size[0] + self.padding)
                y = self.padding + row * (self.widget_size[1] + self.padding)

                widget = self.widgets[name]
                widget.x = x
                widget.y = y
                widget.width = self.widget_size[0]
                widget.height = self.widget_size[1]
        else:
            # Arrange widgets vertically
            rows = min(widget_count, self.height //
                       (self.widget_size[1] + self.padding))
            cols = (widget_count + rows - 1) // rows

            for i, name in enumerate(widget_names):
                row = i % rows
                col = i // rows
                x = self.padding + col * (self.widget_size[0] + self.padding)
                y = self.padding + row * (self.widget_size[1] + self.padding)

                widget = self.widgets[name]
                widget.x = x
                widget.y = y
                widget.width = self.widget_size[0]
                widget.height = self.widget_size[1]

    def draw_widget(self, widget: Widget):
        """Draw a single widget to the framebuffer."""
        # Ensure coordinates are within bounds
        x1 = max(0, widget.x)
        y1 = max(0, widget.y)
        x2 = min(self.width, widget.x + widget.width)
        y2 = min(self.height, widget.y + widget.height)

        if x2 <= x1 or y2 <= y1:
            return  # Widget is outside bounds

        # Fill widget background
        self.framebuffer[y1:y2, x1:x2] = widget.color

        # --- Improved border logic ---
        border_thickness = 3
        # If border_color is not set, use a contrasting color

        def get_contrasting(color):
            # YIQ formula for brightness
            brightness = (color[0]*299 + color[1]*587 + color[2]*114) / 1000
            return (0, 0, 0) if brightness > 128 else (255, 255, 255)
        border_color = widget.border_color if hasattr(
            widget, 'border_color') and widget.border_color else get_contrasting(widget.color)
        # For timestamp and color_drift, use a darker version of their color
        if hasattr(widget, 'text') and widget.text and (widget.text.startswith('Drift') or ':' in widget.text):
            # Darken color by 50%
            border_color = tuple(max(0, int(c*0.5)) for c in widget.color)
        # Draw border (thicker)
        for t in range(border_thickness):
            if y1 + t < self.height:
                self.framebuffer[y1 + t, x1:x2] = border_color  # top
            if y2 - 1 - t >= 0:
                self.framebuffer[y2 - 1 - t, x1:x2] = border_color  # bottom
            if x1 + t < self.width:
                self.framebuffer[y1:y2, x1 + t] = border_color  # left
            if x2 - 1 - t >= 0:
                self.framebuffer[y1:y2, x2 - 1 - t] = border_color  # right

    def draw_widget_timestamp(self, widget: Widget):
        # Digital clock style: black background, bright border, large text
        x1, y1, x2, y2 = widget.x, widget.y, widget.x + \
            widget.width, widget.y + widget.height
        self.framebuffer[y1:y2, x1:x2] = (20, 20, 20)
        border_color = widget.border_color if hasattr(
            widget, 'border_color') else (0, 255, 255)
        for t in range(4):
            self.framebuffer[y1 + t, x1:x2] = border_color
            self.framebuffer[y2 - 1 - t, x1:x2] = border_color
            self.framebuffer[y1:y2, x1 + t] = border_color
            self.framebuffer[y1:y2, x2 - 1 - t] = border_color
        # Large white text
        self.draw_text_simple(widget, font_size=18, bold=True, center=True)

    def draw_widget_color_drift(self, widget: Widget):
        # Gradient fill, colored border, italic text
        x1, y1, x2, y2 = widget.x, widget.y, widget.x + \
            widget.width, widget.y + widget.height
        for i in range(y1, y2):
            ratio = (i - y1) / max(1, y2 - y1 - 1)
            color = tuple(int(c * (1 - ratio) + 30 * ratio)
                          for c in widget.color)
            self.framebuffer[i, x1:x2] = color
        border_color = widget.border_color if hasattr(
            widget, 'border_color') else (255, 0, 128)
        for t in range(3):
            self.framebuffer[y1 + t, x1:x2] = border_color
            self.framebuffer[y2 - 1 - t, x1:x2] = border_color
            self.framebuffer[y1:y2, x1 + t] = border_color
            self.framebuffer[y1:y2, x2 - 1 - t] = border_color
        self.draw_text_simple(widget, font_size=14, italic=True, center=True)

    def draw_widget_referee(self, widget: Widget):
        # Badge style: white background, thick blue border, badge icon
        x1, y1, x2, y2 = widget.x, widget.y, widget.x + \
            widget.width, widget.y + widget.height
        self.framebuffer[y1:y2, x1:x2] = (240, 240, 255)
        border_color = (60, 120, 255)
        for t in range(5):
            self.framebuffer[y1 + t, x1:x2] = border_color
            self.framebuffer[y2 - 1 - t, x1:x2] = border_color
            self.framebuffer[y1:y2, x1 + t] = border_color
            self.framebuffer[y1:y2, x2 - 1 - t] = border_color
        # Draw a simple badge (circle)
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
        r = min(widget.width, widget.height) // 5
        for dx in range(-r, r):
            for dy in range(-r, r):
                if dx*dx + dy*dy < r*r:
                    px, py = cx + dx, cy + dy
                    if 0 <= px < self.width and 0 <= py < self.height:
                        self.framebuffer[py, px] = (60, 120, 255)
        self.draw_text_simple(widget, font_size=12, bold=True, center=True)

    def draw_widget_player(self, widget: Widget):
        # Avatar style: colored circle, thin border, player color
        x1, y1, x2, y2 = widget.x, widget.y, widget.x + \
            widget.width, widget.y + widget.height
        self.framebuffer[y1:y2, x1:x2] = (230, 255, 230)
        border_color = (0, 180, 0)
        for t in range(2):
            self.framebuffer[y1 + t, x1:x2] = border_color
            self.framebuffer[y2 - 1 - t, x1:x2] = border_color
            self.framebuffer[y1:y2, x1 + t] = border_color
            self.framebuffer[y1:y2, x2 - 1 - t] = border_color
        # Draw a filled circle (avatar)
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
        r = min(widget.width, widget.height) // 3
        for dx in range(-r, r):
            for dy in range(-r, r):
                if dx*dx + dy*dy < r*r:
                    px, py = cx + dx, cy + dy
                    if 0 <= px < self.width and 0 <= py < self.height:
                        self.framebuffer[py, px] = (0, 180, 0)
        self.draw_text_simple(widget, font_size=12, center=True)

    def draw_widget_tournament(self, widget: Widget):
        # Trophy style: gold background, thick border, trophy icon
        x1, y1, x2, y2 = widget.x, widget.y, widget.x + \
            widget.width, widget.y + widget.height
        self.framebuffer[y1:y2, x1:x2] = (255, 220, 100)
        border_color = (200, 160, 0)
        for t in range(4):
            self.framebuffer[y1 + t, x1:x2] = border_color
            self.framebuffer[y2 - 1 - t, x1:x2] = border_color
            self.framebuffer[y1:y2, x1 + t] = border_color
            self.framebuffer[y1:y2, x2 - 1 - t] = border_color
        # Draw a simple trophy (rectangle + handles)
        bx, by = (x1 + x2) // 2, y2 - (widget.height // 4)
        for dx in range(-10, 11):
            for dy in range(0, 15):
                px, py = bx + dx, by - dy
                if 0 <= px < self.width and 0 <= py < self.height:
                    self.framebuffer[py, px] = (200, 160, 0)
        # Handles
        for d in range(8):
            if 0 <= bx - 12 - d < self.width and 0 <= by - d < self.height:
                self.framebuffer[by - d, bx - 12 - d] = (200, 160, 0)
            if 0 <= bx + 12 + d < self.width and 0 <= by - d < self.height:
                self.framebuffer[by - d, bx + 12 + d] = (200, 160, 0)
        self.draw_text_simple(widget, font_size=14, bold=True, center=True)

    def draw_text_simple(self, widget: Widget, font_size=12, bold=False, italic=False, center=False):
        # For now, just draw a colored rectangle for each char, but allow font size and centering
        if not widget.text:
            return
        text = widget.text[:10]
        char_width = font_size // 2 + 4
        char_height = font_size + 2
        if center:
            total_width = len(text) * char_width
            start_x = widget.x + (widget.width - total_width) // 2
        else:
            start_x = widget.x + 5
        start_y = widget.y + (widget.height - char_height) // 2
        for i, char in enumerate(text):
            char_x = start_x + (i * char_width)
            char_y = start_y
            char_x2 = min(char_x + char_width - 1, widget.x + widget.width - 1)
            char_y2 = min(char_y + char_height - 1,
                          widget.y + widget.height - 1)
            if char_x < self.width and char_y < self.height and char_x2 >= 0 and char_y2 >= 0:
                color = widget.text_color
                if bold:
                    color = tuple(min(255, c + 80) for c in color)
                if italic and (i % 2 == 1):
                    char_y += 2
                self.framebuffer[char_y:char_y2, char_x:char_x2] = color

    def render(self):
        """Render all widgets to the framebuffer."""
        self.clear()
        self.auto_layout()
        for key, widget in self.widgets.items():
            # If the widget is associated with an agent/participant, delegate rendering
            participant = getattr(widget, 'participant', None)
            style = getattr(widget, 'style', None)
            if participant and hasattr(participant, '__render__'):
                # Use participant's __render__ method, passing style if available
                img = participant.__render__(
                    width=widget.width, height=widget.height, style=style or "default")
                # Paste the rendered image into the framebuffer
                from PIL import Image
                arr = np.array(img)
                x1, y1 = widget.x, widget.y
                x2, y2 = x1 + widget.width, y1 + widget.height
                # Clip to framebuffer bounds
                x2 = min(x2, self.width)
                y2 = min(y2, self.height)
                arr = arr[:y2-y1, :x2-x1]
                self.framebuffer[y1:y2, x1:x2] = arr
            else:
                # Fallback to existing per-type logic for non-agent widgets
                if key == 'timestamp':
                    self.draw_widget_timestamp(widget)
                elif key == 'color_drift':
                    self.draw_widget_color_drift(widget)
                elif key == 'tournament':
                    self.draw_widget_tournament(widget)
                else:
                    self.draw_widget(widget)
        # Schedule async broadcast for next event loop iteration
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(self.broadcast_frame())
        except RuntimeError:
            pass

    def get_framebuffer(self) -> np.ndarray:
        """Get the current framebuffer as a numpy array."""
        return self.framebuffer.copy()

    def transform(self, data: Any, **kwargs) -> Any:
        """Transform method for BaseCompositor interface."""
        # Update widgets based on input data
        if isinstance(data, dict):
            for key, value in data.items():
                if key not in self.widgets:
                    # Create new widget for this data
                    widget = Widget(
                        0, 0, self.widget_size[0], self.widget_size[1])
                    self.add_widget(key, widget)

                widget = self.widgets[key]

                # Update widget based on data type
                if isinstance(value, dict):
                    # Extract common fields
                    if 'text' in value:
                        widget.set_text(str(value['text']))
                    # Set color if provided, otherwise use status
                    if 'color' in value:
                        widget.set_color(value['color'])
                    elif 'status' in value:
                        status = value['status']
                        if status == 'active':
                            widget.set_color((0, 255, 0))  # green
                        elif status == 'idle':
                            widget.set_color((255, 255, 0))  # yellow
                        elif status == 'error':
                            widget.set_color((255, 0, 0))  # red
                        else:
                            widget.set_color((128, 128, 128))  # gray
                    # Set text color if provided
                    if 'text_color' in value:
                        widget.text_color = value['text_color']
                    # Set border color for timestamp and color drift widgets
                    if key in ('timestamp', 'color_drift'):
                        if 'color' in value:
                            widget.set_border_color(value['color'])
                        else:
                            widget.set_border_color(widget.color)
                    # Set main widget background to field color if present
                    if key == 'main' or key == 'field':
                        if 'color' in value:
                            widget.set_color(value['color'])
                else:
                    # Simple string or number
                    widget.set_text(str(value))

        self.render()
        # Schedule async broadcast (will be called later by session)
        return self.get_framebuffer()

    async def transform_async(self, data: Any, **kwargs) -> Any:
        """Async transform method that broadcasts to comdecs."""
        framebuffer = self.transform(data, **kwargs)
        await self.broadcast_frame(framebuffer)
        return framebuffer

    def compose(self, *args, **kwargs) -> Any:
        """Compose method for BaseCompositor interface."""
        # Just render and return the current framebuffer
        self.render()
        return {
            'framebuffer': self.get_framebuffer(),
            'width': self.width,
            'height': self.height,
            'dpi': self.dpi,
            'widget_count': len(self.widgets)
        }

    def save_as_png(self, filename: str):
        """Save the framebuffer as a PNG file (requires Pillow)."""
        try:
            from PIL import Image
            image = Image.fromarray(self.framebuffer, 'RGB')
            image.save(filename)
            return True
        except ImportError:
            print("Pillow not available, cannot save PNG")
            return False

    def update_comdec(self):
        """Update method for comdec integration."""
        current_time = time.time()
        if current_time - self.last_render_time >= 1.0 / 30.0:  # 30 FPS target
            self.last_render_time = current_time

            # Prepare framebuffer for comdec
            comdec_frame = self.get_framebuffer()

            # Send to comdec manager (async call would need await in real usage)
            # For now, we'll handle this in the compose method

            self.frame_count += 1

    def transform_and_update(self, data: Any, **kwargs) -> Any:
        """Transform and update method for BaseCompositor interface with comdec."""
        self.transform(data, **kwargs)
        self.update_comdec()
        return self.get_framebuffer()

    def add_comdec(self, comdec):
        """Add a comdec to this dashboard."""
        self.comdec_manager.add_comdec(comdec)

    async def broadcast_frame(self, frame: Optional[np.ndarray] = None, metadata: Optional[Dict[str, Any]] = None):
        """Broadcast current framebuffer to all comdecs."""
        if frame is None:
            frame = self.get_framebuffer()

        if metadata is None:
            metadata = {
                'frame_count': self.frame_count,
                'timestamp': self.last_render_time,
                'width': self.width,
                'height': self.height,
                'dpi': self.dpi
            }

        await self.comdec_manager.broadcast_frame(frame, metadata)

    async def compose_with_comdec(self, *args, **kwargs) -> Any:
        """Compose and broadcast to comdecs."""
        result = self.compose(*args, **kwargs)
        await self.broadcast_frame()
        return result

    def get_comdec_stats(self) -> Dict[str, Any]:
        """Get statistics from all comdecs."""
        return self.comdec_manager.get_all_stats()

    async def initialize_comdecs(self):
        """Initialize all comdecs."""
        await self.comdec_manager.initialize_all()

    async def finalize_comdecs(self):
        """Finalize all comdecs."""
        await self.comdec_manager.finalize_all()

    async def _periodic_broadcast(self, interval=1/30):
        import asyncio
        while True:
            await self.broadcast_frame()
            await asyncio.sleep(interval)

    def start_streaming(self, interval=1/30):
        """Start periodic broadcasting of the framebuffer for MJPEG streaming."""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(self._periodic_broadcast(interval))
        except RuntimeError:
            pass
