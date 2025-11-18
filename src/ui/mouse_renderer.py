"""Mouse renderer for CS2 Input Visualizer.

This module provides the MouseRenderer class for visualizing mouse button states
in the PyQt6 overlay, including left/right buttons, mouse wheel, and side buttons.
"""

from typing import List, Set
from PyQt6.QtGui import QPainter, QPen, QFont, QColor
from PyQt6.QtCore import Qt

from .layouts import MouseLayout, MousePosition


class MouseRenderer:
    """Renders mouse visualization with interactive button states.

    Displays a graphical representation of a mouse with clickable components:
    - LMB (left mouse button)
    - RMB (right mouse button)
    - MWHEEL (mouse wheel)
    - BODY (mouse body - non-interactive)
    - SIDE_UP (upper side button - M4)
    - SIDE_DOWN (lower side button - M5)

    Active buttons are highlighted with a red fill, while inactive buttons
    show only an outline.
    """

    def __init__(self, layout: MouseLayout, origin_x: int, origin_y: int):
        """Initialize mouse renderer.

        Args:
            layout: MouseLayout instance with dimension and style parameters
            origin_x: X coordinate of mouse origin (top-left corner)
            origin_y: Y coordinate of mouse origin (top-left corner)
        """
        self.layout = layout
        self.positions = MousePosition(layout, origin_x, origin_y)
        self.active_buttons: Set[str] = set()

    def set_active_buttons(self, buttons: List[str]) -> None:
        """Update which mouse buttons are currently pressed.

        Maps CS2 button names (MOUSE1-5) to internal component names and
        updates the active button set for rendering.

        Mapping:
        - MOUSE1 -> LMB (left mouse button)
        - MOUSE2 -> RMB (right mouse button)
        - MOUSE3 -> MWHEEL (mouse wheel click)
        - MOUSE4 -> SIDE_UP (upper side button, M4)
        - MOUSE5 -> SIDE_DOWN (lower side button, M5)

        Args:
            buttons: List of button names from CS2 input data (e.g., ["MOUSE1", "MOUSE2"])
        """
        # Map CS2 button names to component names
        button_map = {
            "MOUSE1": "LMB",
            "MOUSE2": "RMB",
            "MOUSE3": "MWHEEL",
            "MOUSE4": "SIDE_UP",
            "MOUSE5": "SIDE_DOWN"
        }

        # Convert button list to set of component names
        self.active_buttons = set(button_map.get(btn, btn) for btn in buttons)

    def render(self, painter: QPainter) -> None:
        """Render complete mouse visualization.

        Draws all mouse components with appropriate active/inactive states.
        Special handling:
        - BODY is always inactive (outline only)
        - MWHEEL gets a vertical line indicator in the center
        - Side buttons display "M4" and "M5" labels

        Args:
            painter: QPainter instance for drawing
        """
        L = self.layout

        # Render each component
        for component, (x, y, w, h) in self.positions.positions.items():
            if component == "BODY":
                # Body is not interactive, just outline
                self._draw_component(painter, component, x, y, w, h, False)
            else:
                # Buttons can be active
                is_active = component in self.active_buttons
                self._draw_component(painter, component, x, y, w, h, is_active)

        # Draw wheel indicator (vertical line in center)
        self._draw_wheel_indicator(painter)

    def _draw_component(
        self,
        painter: QPainter,
        name: str,
        x: int,
        y: int,
        w: int,
        h: int,
        active: bool
    ) -> None:
        """Draw a single mouse component.

        Args:
            painter: QPainter instance for drawing
            name: Component name (e.g., "LMB", "SIDE_UP")
            x: X coordinate of component
            y: Y coordinate of component
            w: Width of component
            h: Height of component
            active: Whether the button is currently pressed
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

        # Draw component rectangle
        painter.drawRect(x, y, w, h)

        # Draw labels for side buttons
        if name.startswith("SIDE"):
            self._draw_side_button_label(painter, name, x, y, w, h)

    def _draw_wheel_indicator(self, painter: QPainter) -> None:
        """Draw vertical line indicator in mouse wheel center.

        Args:
            painter: QPainter instance for drawing
        """
        wheel_pos = self.positions.get("MWHEEL")
        if wheel_pos:
            wx, wy, ww, wh = wheel_pos

            # Draw thin vertical line in center
            painter.setPen(QPen(QColor(0, 0, 0), 1))
            center_x = wx + ww // 2
            painter.drawLine(center_x, wy + 5, center_x, wy + wh - 5)

    def _draw_side_button_label(
        self,
        painter: QPainter,
        name: str,
        x: int,
        y: int,
        w: int,
        h: int
    ) -> None:
        """Draw label text for side buttons (M4/M5).

        Args:
            painter: QPainter instance for drawing
            name: Component name ("SIDE_UP" or "SIDE_DOWN")
            x: X coordinate of button
            y: Y coordinate of button
            w: Width of button
            h: Height of button
        """
        L = self.layout

        # Set text style
        painter.setPen(L.TEXT_COLOR)
        painter.setFont(QFont("Arial", 8))

        # Determine label based on component name
        label = "M4" if name == "SIDE_UP" else "M5"

        # Draw centered text
        painter.drawText(x, y, w, h, Qt.AlignmentFlag.AlignCenter, label)
