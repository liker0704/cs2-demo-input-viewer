import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

app = QApplication(sys.argv)

# Create a simple overlay window
window = QMainWindow()
window.setWindowTitle("Overlay Test")
window.setWindowFlags(
    Qt.WindowType.FramelessWindowHint |
    Qt.WindowType.WindowStaysOnTopHint |
    Qt.WindowType.Tool
)
window.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
window.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

# Add a visible label
label = QLabel("OVERLAY TEST - If you see this, overlay works!", window)
label.setStyleSheet("""
    QLabel {
        background-color: rgba(255, 0, 0, 200);
        color: white;
        padding: 20px;
        font-size: 24px;
        border: 3px solid yellow;
    }
""")
label.setFont(QFont("Arial", 24, QFont.Weight.Bold))
label.adjustSize()

# Position at top-left
window.setGeometry(100, 100, 800, 200)
label.setGeometry(0, 0, 800, 200)

window.show()

print("Overlay window created!")
print(f"Position: {window.x()}, {window.y()}")
print(f"Size: {window.width()}x{window.height()}")
print("Press Ctrl+C to close")

sys.exit(app.exec())
