import sys
from PyQt6.QtWidgets import QApplication
from src.ui.overlay import CS2InputOverlay
from src.domain.models import InputData

app = QApplication(sys.argv)

# Create overlay
overlay = CS2InputOverlay()

# Make sure it's visible
overlay.show()
overlay.raise_()
overlay.activateWindow()

# Print window info
print(f"Overlay created!")
print(f"Position: ({overlay.x()}, {overlay.y()})")
print(f"Size: {overlay.width()}x{overlay.height()}")
print(f"Visible: {overlay.isVisible()}")
print(f"Window flags: {overlay.windowFlags()}")
print(f"Opacity: {overlay.windowOpacity()}")

# Set some test input to make it visible
test_input = InputData(
    tick=1000,
    subtick=0,
    keys=['W', 'A', 'SPACE'],
    mouse=['MOUSE1']
)

overlay.render(test_input)

print("\nOverlay should be visible at top-left corner with W, A, SPACE, and MOUSE1 pressed")
print("Press Ctrl+C to exit")

sys.exit(app.exec())
