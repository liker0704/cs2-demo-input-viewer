"""UI layer for CS2 Input Visualizer.

This package provides PyQt6-based visualization components for displaying
CS2 player inputs in a transparent overlay window.

Main Components:
- CS2InputOverlay: Main overlay window
- KeyboardRenderer: Renders keyboard visualization
- MouseRenderer: Renders mouse visualization
- Layout classes: Define dimensions and positions for UI components
"""

from .overlay import CS2InputOverlay
from .keyboard_renderer import KeyboardRenderer
from .mouse_renderer import MouseRenderer
from .layouts import KeyboardLayout, MouseLayout, KeyPosition, MousePosition

__all__ = [
    "CS2InputOverlay",
    "KeyboardRenderer",
    "MouseRenderer",
    "KeyboardLayout",
    "MouseLayout",
    "KeyPosition",
    "MousePosition",
]
