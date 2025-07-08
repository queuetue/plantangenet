import numpy as np
from typing import Dict, Any, Tuple
from plantangenet.compositor.base import BaseCompositor
from plantangenet.comdec.manager import ComdecManager


class Widget:
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

    def remove_widget(self, name: str):
        if name in self.widgets:
            del self.widgets[name]

    def get_widget(self, name: str):
        return self.widgets.get(name)

    def all_widgets(self):
        return self.widgets.values()
