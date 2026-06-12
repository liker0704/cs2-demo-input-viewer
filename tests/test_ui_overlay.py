#!/usr/bin/env python3
"""
Test script for CS2 Input Visualizer UI Layer

Tests the overlay with mock data from MockDemoRepository.
"""

import sys
import asyncio
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

# Add src to path
sys.path.insert(0, '/home/user/cs2-demo-input-viewer')

from src.ui import CS2InputOverlay
from src.mocks import MockTickSource, MockDemoRepository, MockPlayerTracker
from src.domain.models import InputData


async def test_ui_with_mocks():
    """Test UI with mock data sources."""

    print("=" * 60)
    print("CS2 Input Visualizer - UI Test")
    print("=" * 60)

    # Create Qt application
    app = QApplication(sys.argv)

    # Create overlay
    print("\n[1] Creating overlay window...")
    overlay = CS2InputOverlay()
    overlay.show()
    print("    ✓ Overlay created and shown")

    # Initialize mocks
    print("\n[2] Initializing mock components...")
    tick_source = MockTickSource(start_tick=0, tick_rate=64)
    demo_repo = MockDemoRepository()
    player_tracker = MockPlayerTracker(player_id="MOCK_PLAYER_123")

    await tick_source.connect()
    demo_repo.load_demo("data/sample_cache.json")
    print("    ✓ Mocks initialized")

    # Test with sample input data
    print("\n[3] Testing with sample inputs...")

    # Test case 1: W + A
    test_data_1 = InputData(
        tick=100,
        keys=["W", "A"],
        mouse=[],
        subtick={"W": 0.0, "A": 0.2}
    )
    overlay.update_inputs(test_data_1)
    print(f"    ✓ Test 1: W + A rendered")

    await asyncio.sleep(1.5)

    # Test case 2: W + D + SPACE + MOUSE1
    test_data_2 = InputData(
        tick=164,
        keys=["W", "D", "SPACE"],
        mouse=["MOUSE1"],
        subtick={"W": 0.0, "D": 0.0, "SPACE": 0.5, "MOUSE1": 0.3}
    )
    overlay.update_inputs(test_data_2)
    print(f"    ✓ Test 2: W + D + SPACE + MOUSE1 rendered")

    await asyncio.sleep(1.5)

    # Test case 3: CTRL + SHIFT + MOUSE2
    test_data_3 = InputData(
        tick=228,
        keys=["CTRL", "SHIFT"],
        mouse=["MOUSE2"],
        subtick={"CTRL": 0.0, "SHIFT": 0.1, "MOUSE2": 0.4}
    )
    overlay.update_inputs(test_data_3)
    print(f"    ✓ Test 3: CTRL + SHIFT + MOUSE2 rendered")

    await asyncio.sleep(1.5)

    # Test case 4: Complex input
    test_data_4 = InputData(
        tick=292,
        keys=["W", "A", "CTRL", "R"],
        mouse=["MOUSE1"],
        subtick={"W": 0.0, "A": 0.1, "CTRL": 0.0, "R": 0.6, "MOUSE1": 0.2}
    )
    overlay.update_inputs(test_data_4)
    print(f"    ✓ Test 4: W + A + CTRL + R + MOUSE1 rendered")

    await asyncio.sleep(1.5)

    # Test case 5: All clear
    test_data_5 = InputData(
        tick=356,
        keys=[],
        mouse=[],
        subtick={}
    )
    overlay.update_inputs(test_data_5)
    print(f"    ✓ Test 5: All keys released")

    print("\n[4] Running continuous simulation...")
    print("    Simulating gameplay with mock tick source...")
    print("    Press Ctrl+C to stop")

    # Simulation loop
    current_tick = 0

    def update_from_demo():
        nonlocal current_tick

        # Get player ID
        player_id = "MOCK_PLAYER_123"

        # Get inputs for current tick
        inputs = demo_repo.get_inputs(current_tick, player_id)

        if inputs:
            overlay.update_inputs(inputs)

        current_tick += 1

        # Loop back if we reach the end
        tick_range = demo_repo.get_tick_range()
        if current_tick > tick_range[1]:
            current_tick = tick_range[0]

    # Setup timer for continuous updates (64 Hz)
    update_timer = QTimer()
    update_timer.timeout.connect(update_from_demo)
    update_timer.start(16)  # ~60 FPS (close to 64 Hz)

    # Run Qt event loop
    try:
        sys.exit(app.exec())
    except KeyboardInterrupt:
        print("\n\n[5] Stopping...")
        overlay.stop_rendering()
        update_timer.stop()
        await tick_source.disconnect()
        print("    ✓ Cleaned up")


def main():
    """Main entry point."""
    try:
        asyncio.run(test_ui_with_mocks())
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
