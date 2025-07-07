import pytest
import numpy as np
from plantangenet.compositor.fb_types import (
    FBCompositor,
    SoftwareFBCompositor,
    ImmediateModeFBCompositor,
    DearImGuiCompositor
)


def test_fbcompositor_basic_pixel_operations():
    """Test basic pixel operations on framebuffer."""
    fb = SoftwareFBCompositor(width=100, height=100, channels=4)

    # Test initial state
    assert fb.framebuffer.shape == (100, 100, 4)
    assert fb.get_pixel(0, 0) == (0, 0, 0, 0)

    # Test set/get pixel
    fb.set_pixel(10, 10, (255, 128, 64, 255))
    assert fb.get_pixel(10, 10) == (255, 128, 64, 255)

    # Test bounds checking
    fb.set_pixel(-1, -1, (255, 0, 0, 255))  # Should not crash
    fb.set_pixel(200, 200, (255, 0, 0, 255))  # Should not crash
    assert fb.get_pixel(-1, -1) == (0, 0, 0, 0)  # Out of bounds


def test_fbcompositor_clear_and_rect():
    """Test clear and rectangle drawing operations."""
    fb = SoftwareFBCompositor(width=50, height=50, channels=4)

    # Test clear
    fb.clear((255, 0, 0, 255))  # Red
    assert fb.get_pixel(25, 25) == (255, 0, 0, 255)
    assert fb.get_pixel(0, 0) == (255, 0, 0, 255)

    # Test rectangle drawing
    fb.draw_rect(10, 10, 20, 20, (0, 255, 0, 255))  # Green rect
    assert fb.get_pixel(15, 15) == (0, 255, 0, 255)  # Inside rect
    assert fb.get_pixel(5, 5) == (255, 0, 0, 255)   # Outside rect (still red)
    assert fb.get_pixel(35, 35) == (255, 0, 0, 255)  # Outside rect


def test_fbcompositor_transform_with_numpy_array():
    """Test transform method with numpy array input."""
    fb = SoftwareFBCompositor(width=10, height=10, channels=4)

    # Create test pattern
    test_pattern = np.ones((10, 10, 4), dtype=np.uint8) * 128
    test_pattern[5, 5] = [255, 255, 255, 255]  # White pixel in center

    # Transform with the pattern
    result = fb.transform(test_pattern)

    # Verify the pattern was applied
    assert fb.get_pixel(5, 5) == (255, 255, 255, 255)
    assert fb.get_pixel(0, 0) == (128, 128, 128, 128)
    assert isinstance(result, np.ndarray)


def test_software_fbcompositor_present():
    """Test software framebuffer presentation."""
    fb = SoftwareFBCompositor(width=20, height=20, channels=4)
    fb.set_pixel(10, 10, (255, 0, 0, 255))

    # Present should return a copy of the framebuffer
    presented = fb.present()
    assert isinstance(presented, np.ndarray)
    assert presented.shape == (20, 20, 4)
    assert tuple(presented[10, 10]) == (255, 0, 0, 255)

    # Verify it's a copy (modifying presented shouldn't affect original)
    presented[10, 10] = [0, 255, 0, 255]
    assert fb.get_pixel(10, 10) == (255, 0, 0, 255)  # Original unchanged


def test_immediate_mode_fbcompositor_basic():
    """Test immediate mode UI compositor basics."""
    fb = ImmediateModeFBCompositor(width=200, height=150, channels=4)

    # Test frame lifecycle
    fb.begin_frame()
    assert len(fb.widgets) == 0
    assert fb.get_pixel(0, 0) == (50, 50, 50, 255)  # Dark gray background

    # Test button creation
    clicked = fb.button("Test Button", 10, 10, 80, 25)
    assert not clicked  # No click event yet
    assert len(fb.widgets) == 1
    assert fb.widgets[0]["label"] == "Test Button"

    fb.end_frame()


def test_immediate_mode_button_interaction():
    """Test immediate mode button click interaction."""
    fb = ImmediateModeFBCompositor(width=200, height=150, channels=4)

    fb.begin_frame()

    # First frame: no interaction
    clicked = fb.button("Click Me", 50, 50)
    assert not clicked

    # Simulate button click event
    events = [{"type": "button_click", "id": "button_0"}]
    redraw_needed = fb.handle_events(events)
    assert redraw_needed

    # Next frame: button should report clicked
    fb.begin_frame()
    clicked = fb.button("Click Me", 50, 50)
    assert clicked  # Button was clicked!

    fb.end_frame()


def test_immediate_mode_mouse_tracking():
    """Test immediate mode mouse position tracking."""
    fb = ImmediateModeFBCompositor(width=200, height=150, channels=4)

    # Simulate mouse move event
    events = [{"type": "mouse_move", "x": 100, "y": 75}]
    redraw_needed = fb.handle_events(events)
    assert redraw_needed
    assert fb.ui_state["mouse_pos"] == (100, 75)


def test_dear_imgui_compositor_extension():
    """Test Dear ImGui compositor as extension of immediate mode."""
    fb = DearImGuiCompositor(width=300, height=200, channels=4)

    fb.begin_frame()
    clicked = fb.button("ImGui Button", 20, 20)
    fb.end_frame()

    # Present should include ImGui-specific data
    result = fb.present()
    assert "framebuffer" in result
    assert "ui_state" in result
    assert "widgets" in result
    assert "imgui_backend" in result
    assert result["imgui_backend"] == "software"


def test_fbcompositor_compose_method():
    """Test the compose method returns framebuffer copy."""
    fb = SoftwareFBCompositor(width=30, height=30, channels=4)
    fb.set_pixel(15, 15, (255, 255, 0, 255))  # Yellow

    composed = fb.compose()
    assert isinstance(composed, np.ndarray)
    assert composed.shape == (30, 30, 4)
    assert tuple(composed[15, 15]) == (255, 255, 0, 255)

    # Verify it's a copy
    composed[15, 15] = [0, 0, 255, 255]  # Blue
    assert fb.get_pixel(15, 15) == (255, 255, 0, 255)  # Original still yellow


def test_fbcompositor_event_transform():
    """Test transform method with event list input."""
    fb = ImmediateModeFBCompositor(width=100, height=100, channels=4)

    # Transform with events
    events = [{"type": "button_click", "id": "test_button"}]
    result = fb.transform(events)

    # Should call handle_events and present
    assert "framebuffer" in result
    assert fb.ui_state.get("test_button") == True


if __name__ == "__main__":
    # Run basic tests manually
    test_fbcompositor_basic_pixel_operations()
    test_fbcompositor_clear_and_rect()
    test_software_fbcompositor_present()
    test_immediate_mode_fbcompositor_basic()
    test_immediate_mode_button_interaction()
    test_dear_imgui_compositor_extension()
    print("✅ All framebuffer compositor tests passed!")
