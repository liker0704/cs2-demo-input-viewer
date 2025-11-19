"""Layout definitions for CS2 Input Visualizer UI components.

This module defines layout parameters and position calculations for keyboard and mouse
visualization components in the PyQt6 overlay.
"""

from PyQt6.QtGui import QColor
from typing import Tuple, Dict, Optional


class KeyboardLayout:
    """Layout parameters for keyboard block visualization.

    Defines dimensions, spacing, and visual styling for keyboard keys.
    """

    # Base dimensions (in pixels)
    W = 40          # Key width
    H = 40          # Key height
    Gx = 4          # Horizontal gap
    Gy = 4          # Vertical gap

    # Origin point (top-left of ~ key)
    KX0 = 20
    KY0 = 20

    # Row offsets (left shift for each row)
    S = int(0.4 * W)        # Row 1 shift (~16px)
    S2 = int(S + 0.3 * W)   # Row 2 shift (~28px)
    S3 = int(S2 + 0.2 * W)  # Row 3 shift (~36px)

    # Special key dimensions
    SPACE_WIDTH = int(3 * W)  # Space bar width

    # Visual style
    OUTLINE_WIDTH = 2
    OUTLINE_COLOR = QColor(0, 0, 0)        # Black
    FILL_COLOR = QColor(0, 0, 0, 0)        # Transparent
    ACTIVE_COLOR = QColor(255, 0, 0, 200)  # Red semi-transparent
    TEXT_COLOR = QColor(0, 0, 0)


class KeyPosition:
    """Calculate exact positions for each keyboard key.

    Computes (x, y, width, height) coordinates for all keys in the keyboard
    layout based on KeyboardLayout parameters.
    """

    def __init__(self, layout: KeyboardLayout):
        """Initialize key position calculator.

        Args:
            layout: KeyboardLayout instance with dimension parameters
        """
        self.layout = layout
        self.positions = self._calculate_positions()

    def _calculate_positions(self) -> Dict[str, Tuple[int, int, int, int]]:
        """Calculate (x, y, width, height) for each key.

        Computes positions for all keys in the keyboard layout, accounting
        for row staggering and special key sizes (SHIFT, SPACE).

        Returns:
            Dictionary mapping key_name to (x, y, width, height) tuple
        """
        L = self.layout
        positions = {}

        # Row 0: ~, 1, 2, 3, 4, 5
        y0 = L.KY0
        row0_keys = ["~", "1", "2", "3", "4", "5"]
        for i, key in enumerate(row0_keys):
            x = L.KX0 + i * (L.W + L.Gx)
            positions[key] = (x, y0, L.W, L.H)

        # Row 1: TAB, Q, W, E, R, T
        y1 = L.KY0 + L.H + L.Gy
        row1_keys = ["TAB", "Q", "W", "E", "R", "T"]
        for i, key in enumerate(row1_keys):
            x = L.KX0 - L.S + i * (L.W + L.Gx)
            positions[key] = (x, y1, L.W, L.H)

        # Row 2: A, S, D, F, G
        y2 = y1 + L.H + L.Gy
        row2_keys = ["A", "S", "D", "F", "G"]
        for i, key in enumerate(row2_keys):
            x = L.KX0 - L.S2 + i * (L.W + L.Gx)
            positions[key] = (x, y2, L.W, L.H)

        # Row 3: SHIFT (vertical), Z, X, C, V, B
        y3 = y2 + L.H + L.Gy

        # SHIFT: vertical key (rotated 90°)
        shift_x = L.KX0 - L.S3
        positions["SHIFT"] = (shift_x, y3, L.H, L.W)  # Note: swapped W and H

        # Z, X, C, V, B (start after SHIFT)
        row3_keys = ["Z", "X", "C", "V", "B"]
        for i, key in enumerate(row3_keys):
            x = shift_x + L.H + L.Gx + i * (L.W + L.Gx)
            positions[key] = (x, y3, L.W, L.H)

        # Row 4: CTRL, ALT, SPACE
        y4 = y3 + L.H + L.Gy
        ctrl_x = L.KX0 - L.S3
        alt_x = ctrl_x + L.W + L.Gx
        space_x = alt_x + L.W + L.Gx

        positions["CTRL"] = (ctrl_x, y4, L.W, L.H)
        positions["ALT"] = (alt_x, y4, L.W, L.H)
        positions["SPACE"] = (space_x, y4, L.SPACE_WIDTH, L.H)

        return positions

    def get(self, key: str) -> Optional[Tuple[int, int, int, int]]:
        """Get position for specific key.

        Args:
            key: Key name (e.g., "W", "SPACE")

        Returns:
            Tuple of (x, y, width, height) or None if key not found
        """
        return self.positions.get(key.upper())


class MouseLayout:
    """Layout parameters for mouse visualization.

    Defines dimensions, spacing, and visual styling for mouse components
    including buttons, wheel, body, and side buttons.
    """

    # Position relative to keyboard
    # DM = distance from keyboard right edge to mouse left edge
    DM = 80

    # Mouse dimensions
    WM = 80         # Total mouse width
    HM1 = 60        # Upper block height (buttons)
    HM2 = 100       # Lower block height (body)

    # Button widths (upper block)
    LMB_WIDTH = int(0.4 * WM)      # Left button
    MWHEEL_WIDTH = int(0.2 * WM)   # Wheel area
    RMB_WIDTH = int(0.4 * WM)      # Right button

    # Side button dimensions
    SIDE_WIDTH = int(0.3 * WM)
    SIDE_HEIGHT = 20
    SIDE_GAP = 4

    # Visual style
    OUTLINE_WIDTH = 2
    OUTLINE_COLOR = QColor(0, 0, 0)        # Black
    FILL_COLOR = QColor(0, 0, 0, 0)        # Transparent
    ACTIVE_COLOR = QColor(255, 0, 0, 200)  # Red semi-transparent
    TEXT_COLOR = QColor(0, 0, 0)

    @classmethod
    def get_origin(cls, keyboard_right: int) -> Tuple[int, int]:
        """Calculate mouse origin based on keyboard position.

        Args:
            keyboard_right: Right edge X coordinate of keyboard

        Returns:
            Tuple of (mouse_x, mouse_y) coordinates
        """
        mouse_x = keyboard_right + cls.DM
        mouse_y = KeyboardLayout.KY0  # Align with keyboard top
        return mouse_x, mouse_y


class MousePosition:
    """Calculate positions for mouse components.

    Computes exact (x, y, width, height) coordinates for all mouse visualization
    components including buttons, wheel, body, and side buttons.
    """

    def __init__(self, layout: MouseLayout, origin_x: int, origin_y: int):
        """Initialize mouse position calculator.

        Args:
            layout: MouseLayout instance with dimension parameters
            origin_x: X coordinate of mouse origin (top-left)
            origin_y: Y coordinate of mouse origin (top-left)
        """
        self.layout = layout
        self.origin_x = origin_x
        self.origin_y = origin_y
        self.positions = self._calculate_positions()

    def _calculate_positions(self) -> Dict[str, Tuple[int, int, int, int]]:
        """Calculate positions for all mouse components.

        Computes positions for:
        - LMB: Left mouse button
        - RMB: Right mouse button
        - MWHEEL: Mouse wheel area
        - BODY: Mouse body (lower section)
        - SIDE_UP: Upper side button (M4)
        - SIDE_DOWN: Lower side button (M5)

        Returns:
            Dictionary mapping component names to (x, y, width, height) tuples
        """
        L = self.layout
        ox, oy = self.origin_x, self.origin_y
        positions = {}

        # Upper block - buttons
        y_buttons = oy

        # Left button
        positions["LMB"] = (ox, y_buttons, L.LMB_WIDTH, L.HM1)

        # Wheel area
        wheel_x = ox + L.LMB_WIDTH
        positions["MWHEEL"] = (wheel_x, y_buttons, L.MWHEEL_WIDTH, L.HM1)

        # Right button
        rmb_x = wheel_x + L.MWHEEL_WIDTH
        positions["RMB"] = (rmb_x, y_buttons, L.RMB_WIDTH, L.HM1)

        # Lower block - body
        y_body = oy + L.HM1
        positions["BODY"] = (ox, y_body, L.WM, L.HM2)

        # Side buttons (on left side of body)
        side_x = ox - L.SIDE_WIDTH
        side_y_center = y_body + L.HM2 // 2

        # Upper side button
        side_y1 = side_y_center - L.SIDE_HEIGHT - L.SIDE_GAP // 2
        positions["SIDE_UP"] = (side_x, side_y1, L.SIDE_WIDTH, L.SIDE_HEIGHT)

        # Lower side button
        side_y2 = side_y_center + L.SIDE_GAP // 2
        positions["SIDE_DOWN"] = (side_x, side_y2, L.SIDE_WIDTH, L.SIDE_HEIGHT)

        return positions

    def get(self, component: str) -> Optional[Tuple[int, int, int, int]]:
        """Get position for a specific mouse component.

        Args:
            component: Component name (e.g., "LMB", "SIDE_UP")

        Returns:
            Tuple of (x, y, width, height) or None if component not found
        """
        return self.positions.get(component)
