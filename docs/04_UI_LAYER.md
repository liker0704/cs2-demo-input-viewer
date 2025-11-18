# UI Layer Documentation

## CS2 Subtick Input Visualizer - PyQt6 Overlay

### 1. Overview

The UI Layer renders a transparent overlay on top of CS2 that visualizes player inputs in real-time. Built with PyQt6 for hardware acceleration and modern styling.

**Visual Style**: Transparent background with black wireframe outlines, highlighting on key press.

---

## 2. PyQt6 Overlay Setup

### 2.1 Window Configuration

```python
from PyQt6.QtWidgets import QMainWindow, QWidget
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPainter, QColor, QPen, QFont

class InputOverlay(QMainWindow):
    """Main overlay window for input visualization."""

    def __init__(self):
        super().__init__()
        self._setup_window()

    def _setup_window(self):
        """Configure window for transparent overlay."""

        # Window flags for overlay behavior
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |          # No title bar/borders
            Qt.WindowType.WindowStaysOnTopHint |         # Always on top
            Qt.WindowType.Tool                           # Exclude from taskbar
        )

        # Transparency and click-through
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        # Optional: Allow dragging (disable click-through temporarily)
        # self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)

        # Set initial size and position
        self.setGeometry(100, 100, 600, 300)  # x, y, width, height

        # Set window title (not visible with FramelessWindowHint, but useful for debugging)
        self.setWindowTitle("CS2 Input Overlay")

        # Hardware acceleration
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, False)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
```

### 2.2 Rendering Setup

```python
    def paintEvent(self, event):
        """Main paint event for rendering overlay."""
        painter = QPainter(self)

        # Enable antialiasing for smooth lines
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Render keyboard block
        self._render_keyboard(painter)

        # Render mouse block
        self._render_mouse(painter)

    def _render_keyboard(self, painter: QPainter):
        """Render keyboard visualization."""
        # Implementation in section 3

    def _render_mouse(self, painter: QPainter):
        """Render mouse visualization."""
        # Implementation in section 4
```

### 2.3 Update Loop

```python
    def start_rendering(self, fps: int = 60):
        """Start render loop at specified FPS.

        Args:
            fps: Target frames per second
        """
        self.render_timer = QTimer()
        self.render_timer.timeout.connect(self.update)  # Trigger repaint
        self.render_timer.start(1000 // fps)  # Interval in ms

    def stop_rendering(self):
        """Stop render loop."""
        if hasattr(self, 'render_timer'):
            self.render_timer.stop()
```

---

## 3. Keyboard Block Layout

### 3.1 Layout Parameters

```python
class KeyboardLayout:
    """Layout parameters for keyboard block."""

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
```

### 3.2 Key Positions

```python
class KeyPosition:
    """Calculate exact positions for each key."""

    def __init__(self, layout: KeyboardLayout):
        self.layout = layout
        self.positions = self._calculate_positions()

    def _calculate_positions(self) -> dict:
        """Calculate (x, y, width, height) for each key.

        Returns:
            dict: {key_name: (x, y, w, h)}
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

    def get(self, key: str) -> tuple:
        """Get position for specific key.

        Args:
            key: Key name (e.g., "W", "SPACE")

        Returns:
            tuple: (x, y, width, height) or None if not found
        """
        return self.positions.get(key.upper())
```

### 3.3 Keyboard Rendering

```python
class KeyboardRenderer:
    """Renders keyboard visualization."""

    def __init__(self, layout: KeyboardLayout):
        self.layout = layout
        self.positions = KeyPosition(layout)
        self.active_keys = set()  # Currently pressed keys

    def set_active_keys(self, keys: list):
        """Update which keys are currently pressed.

        Args:
            keys: List of key names (e.g., ["W", "A", "SPACE"])
        """
        self.active_keys = set(k.upper() for k in keys)

    def render(self, painter: QPainter):
        """Render all keyboard keys.

        Args:
            painter: QPainter instance
        """
        for key_name, (x, y, w, h) in self.positions.positions.items():
            is_active = key_name in self.active_keys
            self._draw_key(painter, key_name, x, y, w, h, is_active)

    def _draw_key(self, painter: QPainter, name: str, x: int, y: int,
                  w: int, h: int, active: bool):
        """Draw individual key.

        Args:
            painter: QPainter instance
            name: Key label
            x, y: Position
            w, h: Dimensions
            active: Whether key is pressed
        """
        L = self.layout

        # Set pen for outline
        pen = QPen(L.OUTLINE_COLOR, L.OUTLINE_WIDTH)
        painter.setPen(pen)

        # Set fill color
        if active:
            painter.setBrush(L.ACTIVE_COLOR)
        else:
            painter.setBrush(L.FILL_COLOR)

        # Draw key rectangle
        if name == "SHIFT":
            # Vertical key - draw with text rotated
            painter.drawRect(x, y, w, h)

            # Draw rotated text
            painter.save()
            painter.translate(x + w // 2, y + h // 2)
            painter.rotate(-90)
            painter.setPen(L.TEXT_COLOR)
            painter.setFont(QFont("Arial", 10))
            painter.drawText(-w // 2, -h // 2, w, h,
                           Qt.AlignmentFlag.AlignCenter, name)
            painter.restore()
        else:
            # Normal horizontal key
            painter.drawRect(x, y, w, h)

            # Draw text
            painter.setPen(L.TEXT_COLOR)
            painter.setFont(QFont("Arial", 10))
            painter.drawText(x, y, w, h,
                           Qt.AlignmentFlag.AlignCenter, name)
```

---

## 4. Mouse Block Layout

### 4.1 Mouse Parameters

```python
class MouseLayout:
    """Layout parameters for mouse visualization."""

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

    # Position (calculated from keyboard)
    @classmethod
    def get_origin(cls, keyboard_right: int) -> tuple:
        """Calculate mouse origin based on keyboard position.

        Args:
            keyboard_right: Right edge X coordinate of keyboard

        Returns:
            tuple: (mouse_x, mouse_y)
        """
        mouse_x = keyboard_right + cls.DM
        mouse_y = KeyboardLayout.KY0  # Align with keyboard top
        return mouse_x, mouse_y
```

### 4.2 Mouse Component Positions

```python
class MousePosition:
    """Calculate positions for mouse components."""

    def __init__(self, layout: MouseLayout, origin_x: int, origin_y: int):
        self.layout = layout
        self.origin_x = origin_x
        self.origin_y = origin_y
        self.positions = self._calculate_positions()

    def _calculate_positions(self) -> dict:
        """Calculate positions for all mouse components.

        Returns:
            dict: {component_name: (x, y, w, h)}
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

    def get(self, component: str) -> tuple:
        """Get position for mouse component.

        Args:
            component: Component name (e.g., "LMB", "SIDE_UP")

        Returns:
            tuple: (x, y, width, height)
        """
        return self.positions.get(component)
```

### 4.3 Mouse Rendering

```python
class MouseRenderer:
    """Renders mouse visualization."""

    def __init__(self, layout: MouseLayout, origin_x: int, origin_y: int):
        self.layout = layout
        self.positions = MousePosition(layout, origin_x, origin_y)
        self.active_buttons = set()

    def set_active_buttons(self, buttons: list):
        """Update which mouse buttons are pressed.

        Args:
            buttons: List of button names (e.g., ["MOUSE1", "MOUSE2"])
        """
        # Map button names to components
        button_map = {
            "MOUSE1": "LMB",
            "MOUSE2": "RMB",
            "MOUSE3": "MWHEEL",
            "MOUSE4": "SIDE_UP",
            "MOUSE5": "SIDE_DOWN"
        }

        self.active_buttons = set()
        for btn in buttons:
            if btn in button_map:
                self.active_buttons.add(button_map[btn])

    def render(self, painter: QPainter):
        """Render mouse visualization.

        Args:
            painter: QPainter instance
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
        wheel_pos = self.positions.get("MWHEEL")
        if wheel_pos:
            wx, wy, ww, wh = wheel_pos
            painter.setPen(QPen(QColor(0, 0, 0), 1))
            center_x = wx + ww // 2
            painter.drawLine(center_x, wy + 5, center_x, wy + wh - 5)

    def _draw_component(self, painter: QPainter, name: str,
                       x: int, y: int, w: int, h: int, active: bool):
        """Draw mouse component.

        Args:
            painter: QPainter instance
            name: Component name
            x, y: Position
            w, h: Dimensions
            active: Whether button is pressed
        """
        # Set pen for outline
        pen = QPen(QColor(0, 0, 0), 2)
        painter.setPen(pen)

        # Set fill color
        if active:
            painter.setBrush(QColor(255, 0, 0, 200))  # Red when active
        else:
            painter.setBrush(QColor(0, 0, 0, 0))  # Transparent

        # Draw component
        painter.drawRect(x, y, w, h)

        # Draw label for side buttons
        if name.startswith("SIDE"):
            painter.setPen(QColor(0, 0, 0))
            painter.setFont(QFont("Arial", 8))
            label = "M4" if name == "SIDE_UP" else "M5"
            painter.drawText(x, y, w, h,
                           Qt.AlignmentFlag.AlignCenter, label)
```

---

## 5. Complete Overlay Integration

### 5.1 Main Overlay Class

```python
class CS2InputOverlay(QMainWindow):
    """Complete input overlay with keyboard and mouse."""

    def __init__(self):
        super().__init__()

        # Layouts
        self.keyboard_layout = KeyboardLayout()
        self.mouse_layout = MouseLayout()

        # Calculate mouse position
        # Find rightmost keyboard key
        keyboard_positions = KeyPosition(self.keyboard_layout)
        max_x = max(x + w for x, y, w, h in keyboard_positions.positions.values())
        mouse_x, mouse_y = self.mouse_layout.get_origin(max_x)

        # Renderers
        self.keyboard_renderer = KeyboardRenderer(self.keyboard_layout)
        self.mouse_renderer = MouseRenderer(self.mouse_layout, mouse_x, mouse_y)

        # Input state
        self.current_input_data = None

        # Setup window
        self._setup_window()
        self.start_rendering(fps=60)

    def _setup_window(self):
        """Configure overlay window."""
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        # Set size to contain all elements
        self.setGeometry(50, 50, 700, 300)

    def update_inputs(self, input_data):
        """Update displayed inputs.

        Args:
            input_data: InputData object from domain layer
        """
        self.current_input_data = input_data

        if input_data:
            # Update keyboard
            self.keyboard_renderer.set_active_keys(input_data.keys)

            # Update mouse
            self.mouse_renderer.set_active_buttons(input_data.mouse)

        # Trigger repaint
        self.update()

    def paintEvent(self, event):
        """Render overlay."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Render keyboard
        self.keyboard_renderer.render(painter)

        # Render mouse
        self.mouse_renderer.render(painter)

    def start_rendering(self, fps: int = 60):
        """Start render loop."""
        self.render_timer = QTimer()
        self.render_timer.timeout.connect(self.update)
        self.render_timer.start(1000 // fps)
```

### 5.2 Data Model Integration

```python
from dataclasses import dataclass
from typing import List

@dataclass
class InputData:
    """Input data model from domain layer."""
    keys: List[str]        # ["W", "A", "SPACE"]
    mouse: List[str]       # ["MOUSE1"]
    subtick: dict         # {"W": 0.0, "MOUSE1": 0.5}
    tick: int             # Current tick number


# Example usage in main loop
def render_loop(overlay: CS2InputOverlay, demo_repo, current_tick: int, player_id: str):
    """Example render loop integration.

    Args:
        overlay: CS2InputOverlay instance
        demo_repo: IDemoRepository instance
        current_tick: Current tick from prediction engine
        player_id: Current player ID from tracker
    """
    # Fetch input data from repository
    input_data = demo_repo.get_inputs(current_tick, player_id)

    # Update overlay
    overlay.update_inputs(input_data)
```

---

## 6. Advanced Features

### 6.1 Configurable Position

```python
class DraggableOverlay(CS2InputOverlay):
    """Overlay with drag support."""

    def __init__(self):
        super().__init__()
        self.dragging = False
        self.drag_position = None
        self.lock_position = False

    def toggle_lock(self):
        """Toggle position lock (enable/disable dragging)."""
        self.lock_position = not self.lock_position

        if self.lock_position:
            # Enable click-through
            self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        else:
            # Disable click-through to allow dragging
            self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)

    def mousePressEvent(self, event):
        """Handle mouse press for dragging."""
        if not self.lock_position and event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        """Handle mouse move for dragging."""
        if self.dragging:
            self.move(event.globalPosition().toPoint() - self.drag_position)

    def mouseReleaseEvent(self, event):
        """Handle mouse release."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = False
```

### 6.2 Opacity Control

```python
    def set_opacity(self, opacity: float):
        """Set overlay opacity.

        Args:
            opacity: 0.0 (transparent) to 1.0 (opaque)
        """
        self.setWindowOpacity(opacity)
```

### 6.3 Scaling

```python
class ScalableOverlay(CS2InputOverlay):
    """Overlay with scale support."""

    def __init__(self, scale: float = 1.0):
        self.scale = scale
        super().__init__()

    def set_scale(self, scale: float):
        """Change overlay scale.

        Args:
            scale: Scale factor (e.g., 1.5 for 150%)
        """
        self.scale = scale

        # Update layout dimensions
        self.keyboard_layout.W = int(40 * scale)
        self.keyboard_layout.H = int(40 * scale)
        self.keyboard_layout.Gx = int(4 * scale)
        self.keyboard_layout.Gy = int(4 * scale)

        # Recalculate positions
        # ... (recreate renderers with new layout)

        # Resize window
        new_width = int(700 * scale)
        new_height = int(300 * scale)
        self.resize(new_width, new_height)
```

---

## 7. Performance Optimization

### 7.1 Dirty Rectangle Rendering

```python
class OptimizedOverlay(CS2InputOverlay):
    """Overlay with optimized rendering."""

    def __init__(self):
        super().__init__()
        self.dirty_regions = []

    def update_inputs(self, input_data):
        """Update with dirty region tracking."""
        if input_data and self.current_input_data:
            # Find changed keys
            old_keys = set(self.current_input_data.keys)
            new_keys = set(input_data.keys)
            changed_keys = old_keys.symmetric_difference(new_keys)

            # Mark dirty regions
            for key in changed_keys:
                pos = self.keyboard_renderer.positions.get(key)
                if pos:
                    self.dirty_regions.append(pos)

        super().update_inputs(input_data)

    def paintEvent(self, event):
        """Optimized paint with dirty regions."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if self.dirty_regions:
            # Only repaint dirty regions
            for x, y, w, h in self.dirty_regions:
                painter.setClipRect(x-5, y-5, w+10, h+10)
                self.keyboard_renderer.render(painter)
            self.dirty_regions.clear()
        else:
            # Full repaint
            self.keyboard_renderer.render(painter)
            self.mouse_renderer.render(painter)
```

---

## 8. Testing

### 8.1 UI Test with Mock Data

```python
import sys
from PyQt6.QtWidgets import QApplication

def test_ui():
    """Test UI with mock data."""
    app = QApplication(sys.argv)

    # Create overlay
    overlay = CS2InputOverlay()
    overlay.show()

    # Simulate input changes
    import time
    test_inputs = [
        InputData(keys=["W"], mouse=[], subtick={}, tick=0),
        InputData(keys=["W", "A"], mouse=[], subtick={}, tick=64),
        InputData(keys=["W", "A"], mouse=["MOUSE1"], subtick={}, tick=128),
        InputData(keys=["W", "D", "SPACE"], mouse=["MOUSE1"], subtick={}, tick=192),
    ]

    def cycle_inputs(index=[0]):
        overlay.update_inputs(test_inputs[index[0] % len(test_inputs)])
        index[0] += 1

    # Change inputs every second
    timer = QTimer()
    timer.timeout.connect(cycle_inputs)
    timer.start(1000)

    sys.exit(app.exec())

if __name__ == "__main__":
    test_ui()
```

---

## 9. Next Steps

After UI Layer completion:
1. Integrate with Core Logic (orchestrator)
2. Connect to Network Layer (sync engine)
3. Connect to Data Layer (cache repository)
4. Build complete application
