"""Main PyQt6 overlay window for CS2 Input Visualizer.

This module provides the CS2InputOverlay class which creates a transparent,
click-through window that displays real-time keyboard and mouse input visualization
on top of CS2 gameplay.
"""

from typing import Optional
from PyQt6.QtWidgets import QMainWindow
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPainter

from src.domain.models import InputData
from .layouts import KeyboardLayout, MouseLayout, KeyPosition
from .keyboard_renderer import KeyboardRenderer
from .mouse_renderer import MouseRenderer


class CS2InputOverlay(QMainWindow):
    """Main overlay window for CS2 input visualization.

    Creates a transparent, frameless, always-on-top window that displays keyboard
    and mouse input states. The window is click-through to avoid interfering with
    gameplay, and renders at 60 FPS by default.

    The overlay consists of two main components:
    - Keyboard visualization: QWERTY layout with active key highlighting
    - Mouse visualization: Mouse body with button states (LMB, RMB, wheel, side buttons)

    Window properties:
    - Transparent background (WA_TranslucentBackground)
    - Always on top (WindowStaysOnTopHint)
    - Frameless (FramelessWindowHint)
    - Click-through (WA_TransparentForMouseEvents)
    - Tool window (excludes from taskbar)

    Example:
        >>> from PyQt6.QtWidgets import QApplication
        >>> import sys
        >>> app = QApplication(sys.argv)
        >>> overlay = CS2InputOverlay()
        >>> overlay.show()
        >>> # Update with input data
        >>> input_data = InputData(tick=100, keys=["W", "A"], mouse=["MOUSE1"], subtick={})
        >>> overlay.update_inputs(input_data)
        >>> sys.exit(app.exec())
    """

    def __init__(self):
        """Initialize the CS2 input overlay window.

        Sets up the window configuration, creates keyboard and mouse renderers,
        calculates layout positions, and starts the render loop at 60 FPS.
        """
        super().__init__()

        # Layout configurations
        self.keyboard_layout = KeyboardLayout()
        self.mouse_layout = MouseLayout()

        # Calculate mouse position relative to keyboard
        # Find the rightmost edge of the keyboard layout
        keyboard_positions = KeyPosition(self.keyboard_layout)
        max_x = max(x + w for x, y, w, h in keyboard_positions.positions.values())

        # Position mouse with DM offset from keyboard
        mouse_x, mouse_y = self.mouse_layout.get_origin(max_x)

        # Initialize renderers
        self.keyboard_renderer = KeyboardRenderer(self.keyboard_layout)
        self.mouse_renderer = MouseRenderer(self.mouse_layout, mouse_x, mouse_y)

        # Current input state
        self.current_input_data: Optional[InputData] = None

        # Render timer (initialized in start_rendering)
        self.render_timer: Optional[QTimer] = None

        # Setup window configuration and start rendering
        self._setup_window()
        self.start_rendering(fps=60)

    def _setup_window(self) -> None:
        """Configure window flags and attributes for transparent overlay.

        Sets up the window to be:
        - Frameless (no title bar or borders)
        - Always on top of other windows
        - Transparent background
        - Click-through (mouse events pass through to windows below)
        - Tool window (excluded from taskbar)
        - Hardware accelerated rendering
        """
        # Window flags for overlay behavior
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |      # No title bar/borders
            Qt.WindowType.WindowStaysOnTopHint |     # Always on top
            Qt.WindowType.Tool                       # Exclude from taskbar
        )

        # Transparency and click-through attributes
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        # Hardware acceleration hints
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, False)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)

        # Set window size and position
        # Position at (50, 50) with size to contain keyboard + mouse + margins
        self.setGeometry(50, 50, 700, 300)

        # Set window title (not visible but useful for debugging/window management)
        self.setWindowTitle("CS2 Input Overlay")

    def update_inputs(self, input_data: InputData) -> None:
        """Update displayed inputs with new data.

        Updates both keyboard and mouse renderers with the current input state
        and triggers a window repaint to show the changes.

        Args:
            input_data: InputData object containing current tick's input state
                       (keyboard keys, mouse buttons, subtick timing)
        """
        self.current_input_data = input_data

        if input_data:
            # Update keyboard renderer with active keys
            self.keyboard_renderer.set_active_keys(input_data.keys)

            # Update mouse renderer with active buttons
            self.mouse_renderer.set_active_buttons(input_data.mouse)

        # Trigger repaint to show updated input states
        self.update()

    def paintEvent(self, event) -> None:
        """Render the overlay visualization.

        Called automatically by Qt when the window needs to be repainted
        (either from update() calls or the render timer). Draws both keyboard
        and mouse visualizations with antialiasing enabled.

        Args:
            event: QPaintEvent (provided by Qt, contains paint region info)
        """
        painter = QPainter(self)

        # Enable antialiasing for smooth lines and shapes
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Render keyboard visualization
        self.keyboard_renderer.render(painter)

        # Render mouse visualization
        self.mouse_renderer.render(painter)

    def start_rendering(self, fps: int = 60) -> None:
        """Start the render loop at specified frame rate.

        Creates a QTimer that triggers window repaints at the specified FPS.
        Higher FPS provides smoother visualization but uses more CPU.

        Args:
            fps: Target frames per second (default: 60)
                 Common values: 30 (low CPU), 60 (smooth), 120 (very smooth)
        """
        self.render_timer = QTimer()
        self.render_timer.timeout.connect(self.update)  # Trigger repaint on timeout
        interval_ms = 1000 // fps  # Convert FPS to milliseconds
        self.render_timer.start(interval_ms)

    def stop_rendering(self) -> None:
        """Stop the render loop.

        Stops the render timer to pause overlay updates. The overlay will
        remain visible but won't refresh until start_rendering() is called again.
        """
        if self.render_timer:
            self.render_timer.stop()
