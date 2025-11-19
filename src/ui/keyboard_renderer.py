"""Keyboard renderer for CS2 Input Visualizer.

This module provides the KeyboardRenderer class for visualizing keyboard key states
in the PyQt6 overlay, with support for QWERTY layout and special keys.
"""

from typing import List, Set
from PyQt6.QtGui import QPainter, QPen, QFont
from PyQt6.QtCore import Qt

from .layouts import KeyboardLayout, KeyPosition


class KeyboardRenderer:
    """Renders keyboard visualization with interactive key states.

    Displays a graphical QWERTY keyboard layout with keys highlighted when pressed.
    Supports standard keys, modifiers (CTRL, ALT, SHIFT), and special keys (SPACE, TAB).

    Active keys are highlighted with a red fill, while inactive keys show only an outline.
    The SHIFT key is rendered vertically (rotated 90 degrees) to match typical keyboard layout.
    """

    def __init__(self, layout: KeyboardLayout):
        """Initialize keyboard renderer.

        Args:
            layout: KeyboardLayout instance with dimension and style parameters
        """
        self.layout = layout
        self.positions = KeyPosition(layout)
        self.active_keys: Set[str] = set()

    def set_active_keys(self, keys: List[str]) -> None:
        """Update which keys are currently pressed.

        Converts all key names to uppercase for case-insensitive matching.

        Args:
            keys: List of key names from CS2 input data (e.g., ["W", "A", "SPACE"])
        """
        self.active_keys = set(k.upper() for k in keys)

    def render(self, painter: QPainter) -> None:
        """Render all keyboard keys.

        Draws each key with appropriate active/inactive state. The SHIFT key
        receives special handling for vertical orientation.

        Args:
            painter: QPainter instance for drawing
        """
        for key_name, (x, y, w, h) in self.positions.positions.items():
            is_active = key_name in self.active_keys
            self._draw_key(painter, key_name, x, y, w, h, is_active)

    def _draw_key(
        self,
        painter: QPainter,
        name: str,
        x: int,
        y: int,
        w: int,
        h: int,
        active: bool
    ) -> None:
        """Draw individual keyboard key.

        Renders a key with outline, fill (if active), and centered label text.
        Special handling for SHIFT key with 90-degree rotation.

        Args:
            painter: QPainter instance for drawing
            name: Key label (e.g., "W", "SPACE", "SHIFT")
            x: X coordinate of key
            y: Y coordinate of key
            w: Width of key
            h: Height of key
            active: Whether the key is currently pressed
        """
        L = self.layout

        # Set pen for outline
        pen = QPen(L.OUTLINE_COLOR, L.OUTLINE_WIDTH)
        painter.setPen(pen)

        # Set fill color based on active state
        if active:
            painter.setBrush(L.ACTIVE_COLOR)
        else:
            painter.setBrush(L.FILL_COLOR)

        # Draw key rectangle
        painter.drawRect(x, y, w, h)

        # Draw text label
        if name == "SHIFT":
            # Vertical key - draw with rotated text
            self._draw_rotated_text(painter, name, x, y, w, h)
        else:
            # Normal horizontal key
            self._draw_text(painter, name, x, y, w, h)

    def _draw_text(
        self,
        painter: QPainter,
        text: str,
        x: int,
        y: int,
        w: int,
        h: int
    ) -> None:
        """Draw centered text label for normal (horizontal) keys.

        Args:
            painter: QPainter instance for drawing
            text: Text to display
            x: X coordinate of key
            y: Y coordinate of key
            w: Width of key
            h: Height of key
        """
        L = self.layout

        painter.setPen(L.TEXT_COLOR)
        painter.setFont(QFont("Arial", 10))
        painter.drawText(x, y, w, h, Qt.AlignmentFlag.AlignCenter, text)

    def _draw_rotated_text(
        self,
        painter: QPainter,
        text: str,
        x: int,
        y: int,
        w: int,
        h: int
    ) -> None:
        """Draw rotated text label for vertical keys (SHIFT).

        Rotates the painter 90 degrees counter-clockwise to render vertical text.

        Args:
            painter: QPainter instance for drawing
            text: Text to display
            x: X coordinate of key
            y: Y coordinate of key
            w: Width of key (note: for vertical keys this is actually the visual height)
            h: Height of key (note: for vertical keys this is actually the visual width)
        """
        L = self.layout

        # Save painter state before rotation
        painter.save()

        # Move to center of key, rotate, and draw text
        painter.translate(x + w // 2, y + h // 2)
        painter.rotate(-90)

        # Draw text in rotated coordinate system
        painter.setPen(L.TEXT_COLOR)
        painter.setFont(QFont("Arial", 10))
        painter.drawText(-w // 2, -h // 2, w, h, Qt.AlignmentFlag.AlignCenter, text)

        # Restore painter state
        painter.restore()
