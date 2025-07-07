#!/usr/bin/env python3
"""
Demonstration of FBCompositor hierarchy with pixel-level testing.
Shows software rendering, immediate mode UI, and pixel verification.
"""

import numpy as np
from plantangenet.compositor.fb_types import (
    SoftwareFBCompositor,
    ImmediateModeFBCompositor,
    DearImGuiCompositor
)
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'python'))


def demo_basic_framebuffer():
    """Demonstrate basic framebuffer operations with pixel verification."""
    print("🖼️  Basic Framebuffer Demo")
    print("=" * 50)

    # Create a small framebuffer for easy visualization
    fb = SoftwareFBCompositor(width=8, height=8, channels=4)

    # Draw a simple pattern
    fb.clear((0, 0, 0, 255))  # Black background
    fb.draw_rect(2, 2, 4, 4, (255, 255, 255, 255))  # White square
    fb.set_pixel(4, 4, (255, 0, 0, 255))  # Red center pixel

    # Present and verify
    presented = fb.present()
    print(f"Framebuffer shape: {presented.shape}")
    print(f"Center pixel (4,4): {tuple(presented[4, 4])}")
    print(f"Corner pixel (0,0): {tuple(presented[0, 0])}")
    print(f"White square pixel (3,3): {tuple(presented[3, 3])}")

    # Verify the pattern
    assert tuple(presented[4, 4]) == (255, 0, 0, 255), "Center should be red"
    assert tuple(presented[0, 0]) == (0, 0, 0, 255), "Corner should be black"
    assert tuple(presented[3, 3]) == (
        255, 255, 255, 255), "Square should be white"

    print("✅ Basic framebuffer operations verified!")
    print()


def demo_immediate_mode_ui():
    """Demonstrate immediate mode UI with button interactions."""
    print("🎮 Immediate Mode UI Demo")
    print("=" * 50)

    fb = ImmediateModeFBCompositor(width=300, height=200, channels=4)

    # Frame 1: Draw initial UI
    fb.begin_frame()
    clicked = fb.button("Start Game", 50, 50, 100, 30)
    score_button = fb.button("High Score", 50, 100, 100, 30)
    fb.end_frame()

    result = fb.present()
    print(f"Frame 1 - Widgets created: {len(result['widgets'])}")
    print(f"Button clicked: {clicked}")
    print(
        f"Framebuffer has {len(np.unique(result['framebuffer']))} unique colors")

    # Simulate button click
    events = [{"type": "button_click", "id": "button_0"}]  # First button
    fb.handle_events(events)

    # Frame 2: Check button click response
    fb.begin_frame()
    clicked = fb.button("Start Game", 50, 50, 100, 30)
    score_button = fb.button("High Score", 50, 100, 100, 30)
    fb.end_frame()

    print(f"Frame 2 - Start Game clicked: {clicked}")
    print(f"Frame 2 - High Score clicked: {score_button}")

    assert clicked == True, "Start Game button should report clicked"
    assert score_button == False, "High Score button should not be clicked"

    print("✅ Immediate mode UI interactions verified!")
    print()


def demo_dear_imgui_extension():
    """Demonstrate Dear ImGui compositor extension."""
    print("🚀 Dear ImGui Extension Demo")
    print("=" * 50)

    fb = DearImGuiCompositor(width=400, height=300, channels=4)

    # Create UI elements
    fb.begin_frame()
    play_clicked = fb.button("Play", 100, 50, 80, 25)
    settings_clicked = fb.button("Settings", 100, 100, 80, 25)
    quit_clicked = fb.button("Quit", 100, 150, 80, 25)
    fb.end_frame()

    # Present and examine the result
    result = fb.present()

    print(f"UI Framework: {result.get('imgui_backend', 'unknown')}")
    print(f"Widgets rendered: {len(result['widgets'])}")
    print(f"UI state keys: {list(result['ui_state'].keys())}")
    print(f"Framebuffer dimensions: {result['framebuffer'].shape}")

    # Verify ImGui-specific features
    assert "imgui_backend" in result, "Should have ImGui backend info"
    assert result["imgui_backend"] == "software", "Should use software backend"
    assert len(result['widgets']) == 3, "Should have 3 buttons"

    print("✅ Dear ImGui extension verified!")
    print()


def demo_unified_transform_interface():
    """Demonstrate unified transform interface across compositor types."""
    print("🔄 Unified Transform Interface Demo")
    print("=" * 50)

    # Create different compositor types
    software_fb = SoftwareFBCompositor(width=50, height=50, channels=4)
    immediate_fb = ImmediateModeFBCompositor(width=50, height=50, channels=4)

    # Test unified transform with different data types

    # 1. Transform with numpy array (framebuffer data)
    test_pattern = np.ones((50, 50, 4), dtype=np.uint8) * 128
    test_pattern[25, 25] = [255, 255, 0, 255]  # Yellow center

    software_result = software_fb.transform(test_pattern)
    assert isinstance(
        software_result, np.ndarray), "Software should return framebuffer"
    assert tuple(software_result[25, 25]) == (
        255, 255, 0, 255), "Yellow pixel preserved"

    # 2. Transform with events (UI interaction)
    events = [{"type": "button_click", "id": "test_button"}]
    ui_result = immediate_fb.transform(events)
    assert isinstance(ui_result, dict), "UI should return state dict"
    assert "framebuffer" in ui_result, "Should contain framebuffer"

    print("✅ Software FB transform: numpy array → numpy array")
    print("✅ Immediate Mode transform: events → UI state dict")
    print("✅ Unified transform interface verified!")
    print()


def demo_pixel_perfect_verification():
    """Demonstrate pixel-perfect verification of rendering operations."""
    print("🔍 Pixel-Perfect Verification Demo")
    print("=" * 50)

    fb = SoftwareFBCompositor(width=16, height=16, channels=4)

    # Create a test pattern
    fb.clear((100, 100, 100, 255))  # Gray background

    # Draw gradient pattern
    for x in range(16):
        intensity = int((x / 15.0) * 255)
        fb.set_pixel(x, 8, (intensity, 0, 255 - intensity, 255))

    # Draw checkerboard in top corner
    for y in range(4):
        for x in range(4):
            if (x + y) % 2 == 0:
                fb.set_pixel(x, y, (255, 255, 255, 255))  # White
            else:
                fb.set_pixel(x, y, (0, 0, 0, 255))  # Black

    # Verify specific pixels
    framebuffer = fb.present()

    # Check gradient
    assert tuple(framebuffer[8, 0]) == (
        0, 0, 255, 255), "Gradient start should be blue"
    assert tuple(framebuffer[8, 15]) == (
        255, 0, 0, 255), "Gradient end should be red"

    # Check checkerboard
    assert tuple(framebuffer[0, 0]) == (
        255, 255, 255, 255), "Checkerboard (0,0) should be white"
    assert tuple(framebuffer[1, 0]) == (
        0, 0, 0, 255), "Checkerboard (1,0) should be black"
    assert tuple(framebuffer[0, 1]) == (
        0, 0, 0, 255), "Checkerboard (0,1) should be black"

    # Check background
    assert tuple(framebuffer[10, 10]) == (
        100, 100, 100, 255), "Background should be gray"

    print("✅ Gradient pattern verified")
    print("✅ Checkerboard pattern verified")
    print("✅ Background color verified")
    print("✅ All pixel operations pixel-perfect!")
    print()


if __name__ == "__main__":
    print("🎨 FBCompositor Pixel-Level Demo")
    print("=" * 60)
    print("Testing framebuffer compositors with pixel verification...")
    print()

    try:
        demo_basic_framebuffer()
        demo_immediate_mode_ui()
        demo_dear_imgui_extension()
        demo_unified_transform_interface()
        demo_pixel_perfect_verification()

        print("🎉 All framebuffer compositor demos completed successfully!")
        print("✨ Ready for real-time immediate mode UI integration!")

    except Exception as e:
        print(f"❌ Demo failed: {e}")
        exit(1)
