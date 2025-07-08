import numpy as np
from typing import Dict, Any, Tuple
from plantangenet.compositor.base import BaseCompositor
from plantangenet.comdec.manager import ComdecManager
from plantangenet.game.widgets import Widget, WidgetDashboard
from fastapi import FastAPI, Response, HTTPException
from fastapi.responses import StreamingResponse
import io
from PIL import Image


class CompositorWidgetDashboard(BaseCompositor):
    def __init__(self, width: int = 800, height: int = 600, dpi: int = 72):
        super().__init__()
        self.width = width
        self.height = height
        self.dpi = dpi
        self.framebuffer = np.zeros((height, width, 3), dtype=np.uint8)
        self.widgets: Dict[str, Widget] = {}
        self.layout_direction = "horizontal"
        self.padding = 10
        self.widget_size = (120, 80)
        self.comdec_manager = ComdecManager()
        self.frame_count = 0
        self.last_render_time = 0
        self.colors = {
            'background': (30, 30, 30),
            'player_idle': (100, 150, 100),
            'player_playing': (255, 255, 100),
            'player_winner': (100, 255, 100),
            'text': (255, 255, 255),
            'border': (128, 128, 128)
        }

    def clear(self):
        self.framebuffer[:, :] = self.colors['background']

    def add_widget(self, name: str, widget: Widget, participant=None, style=None):
        if participant is not None:
            widget.participant = participant
        if style is not None:
            widget.style = style
        self.widgets[name] = widget

    def render(self):
        self.clear()
        # Render widgets (placeholder: just fill rectangles and text)
        for widget in self.widgets.values():
            x, y, w, h = widget.x, widget.y, widget.width, widget.height
            color = widget.color
            self.framebuffer[y:y+h, x:x+w] = color
        self.frame_count += 1
        self.last_render_time = 0  # Placeholder
        return self.framebuffer

    def compose(self, *args, **kwargs):
        """Produce a composed output (framebuffer)."""
        return self.render()

    def transform(self, data, **kwargs):
        """No-op transform for now."""
        return data

    def add_comdec(self, comdec):
        self.comdec_manager.add_comdec(comdec)

    async def initialize_comdecs(self):
        await self.comdec_manager.initialize_all()

    def start_streaming(self):
        self.comdec_manager.active = True


class BreakoutWidgetDashboard(WidgetDashboard):
    """Concrete dashboard for Breakout, implements compose and transform."""

    def compose(self, *args, **kwargs):
        # Compose widgets for the dashboard (could be a no-op or custom logic)
        return self.widgets

    def transform(self, data=None, **kwargs):
        # Transform dashboard state for rendering (could be a no-op or custom logic)
        return data

    def add_comdec(self, comdec):
        # Optional: delegate to a comdec_manager if present, or just no-op
        if hasattr(self, 'comdec_manager'):
            self.comdec_manager.add_comdec(comdec)
        # else: no-op

    def initialize_comdecs(self):
        # Optional: delegate to a comdec_manager if present, or just no-op
        if hasattr(self, 'comdec_manager'):
            return self.comdec_manager.initialize_all()
        return None

    def start_streaming(self):
        # Optional: delegate to a comdec_manager if present, or just no-op
        if hasattr(self, 'comdec_manager'):
            self.comdec_manager.active = True
        # else: no-op

    def get_fastapi_app(self):
        app = FastAPI()

        @app.get("/")
        def root():
            # Render the main framebuffer as an image
            img = self.render_main_framebuffer()
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            buf.seek(0)
            return StreamingResponse(buf, media_type="image/png")

        @app.get("/asset/{object_id}")
        def asset(object_id: str):
            # Render the default asset for the addressed object
            img = self.render_asset(object_id)
            if img is None:
                raise HTTPException(status_code=404, detail="Asset not found")
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            buf.seek(0)
            return StreamingResponse(buf, media_type="image/png")

        return app

    def render_main_framebuffer(self):
        # Render the main dashboard framebuffer as a PIL Image
        arr = self.render() if hasattr(self, 'render') else None
        if arr is None:
            arr = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        return Image.fromarray(arr.astype('uint8'), 'RGB')

    def render_asset(self, object_id):
        # Render the default asset for the addressed object as a PIL Image
        widget = self.widgets.get(object_id)
        if widget is None:
            return None
        # Create an image for just this widget
        arr = np.zeros((widget.height, widget.width, 3), dtype=np.uint8)
        arr[:, :] = widget.color if hasattr(
            widget, 'color') else (128, 128, 128)
        return Image.fromarray(arr.astype('uint8'), 'RGB')
