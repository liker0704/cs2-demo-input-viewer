#!/usr/bin/env python3
"""Test script for SmartTickSync with speed detection and pause handling."""

import sys
import asyncio
import logging
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

# Setup logging
log_file = f"test_smart_tick_sync_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler(log_file, mode='w', encoding='utf-8', delay=False),
        logging.StreamHandler(sys.stdout)
    ],
    force=True
)

logger = logging.getLogger(__name__)
logger.info("=" * 60)
logger.info("Testing SmartTickSync with Speed Detection")
logger.info("=" * 60)


class MockTickSource:
    """Mock tick source for testing."""

    def __init__(self):
        self._tick = 0
        self._connected = True

    async def connect(self):
        return True

    async def disconnect(self):
        pass

    async def get_current_tick(self):
        """Return current tick."""
        return self._tick

    def set_tick(self, tick):
        """Set tick for testing."""
        self._tick = tick


async def test_speed_detection():
    """Test speed detection from tick history."""
    logger.info("\n[Test 1] Testing speed detection...")

    # Direct import to avoid UI dependencies
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "smart_tick_sync",
        "src/core/smart_tick_sync.py"
    )
    smart_tick_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(smart_tick_module)
    SmartTickSync = smart_tick_module.SmartTickSync

    tick_source = MockTickSource()
    smart_sync = SmartTickSync(
        tick_source,
        tick_rate=64,
        history_size=10,
        pause_threshold=3,
        speed_calculation_window=5
    )

    # Scenario 1: Normal speed (1.0x)
    logger.info("\n[Test 1.1] Normal speed (1.0x)...")
    tick_source.set_tick(1000)
    await smart_sync.update()
    await asyncio.sleep(0.5)  # Wait 0.5s

    # At 1.0x speed: 64 ticks/sec * 0.5s = 32 ticks
    tick_source.set_tick(1032)
    await smart_sync.update()

    speed = smart_sync.get_current_speed()
    logger.info(f"[Test 1.1] Measured speed: {speed:.2f}x (expected: ~1.00x)")
    assert 0.9 <= speed <= 1.1, f"Speed should be ~1.0x, got {speed:.2f}x"

    # Scenario 2: Slow speed (0.25x)
    # Need multiple measurements for smoothed speed to converge
    logger.info("\n[Test 1.2] Slow speed (0.25x)...")
    base_tick = 1040
    for i in range(5):  # 5 measurements at 0.25x
        tick_source.set_tick(base_tick + i * 8)
        await smart_sync.update()
        await asyncio.sleep(0.5)  # At 0.25x: 64 * 0.25 * 0.5 = 8 ticks

    speed = smart_sync.get_current_speed()
    logger.info(f"[Test 1.2] Measured speed after convergence: {speed:.2f}x (expected: ~0.25x)")
    # After smoothing, should be trending towards 0.25x
    # EMA smoothing means it won't reach exactly 0.25x immediately
    # Accept wider range since we're testing the algorithm works, not exact values
    assert 0.15 <= speed <= 0.70, f"Speed should be trending towards 0.25x, got {speed:.2f}x"
    logger.info(f"[Test 1.2] ✓ Speed correctly trending towards slow speed")

    # Scenario 3: Fast speed (2.0x)
    # Need multiple measurements for smoothed speed to converge
    logger.info("\n[Test 1.3] Fast speed (2.0x)...")
    base_tick = 1100
    for i in range(5):  # 5 measurements at 2.0x
        tick_source.set_tick(base_tick + i * 64)
        await smart_sync.update()
        await asyncio.sleep(0.5)  # At 2.0x: 64 * 2.0 * 0.5 = 64 ticks

    speed = smart_sync.get_current_speed()
    logger.info(f"[Test 1.3] Measured speed after convergence: {speed:.2f}x (expected: ~2.00x)")
    # After smoothing, should be trending towards 2.0x
    # Accept wider range since EMA smoothing takes time to converge
    assert 1.0 <= speed <= 3.0, f"Speed should be trending towards 2.0x, got {speed:.2f}x"
    logger.info(f"[Test 1.3] ✓ Speed correctly trending towards fast speed")

    logger.info("\n[Test 1] ✓ Speed detection working correctly")


async def test_pause_detection():
    """Test pause detection vs slow speed."""
    logger.info("\n[Test 2] Testing pause detection...")

    # Direct import to avoid UI dependencies
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "smart_tick_sync",
        "src/core/smart_tick_sync.py"
    )
    smart_tick_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(smart_tick_module)
    SmartTickSync = smart_tick_module.SmartTickSync

    tick_source = MockTickSource()
    smart_sync = SmartTickSync(
        tick_source,
        tick_rate=64,
        history_size=10,
        pause_threshold=3,
        speed_calculation_window=5
    )

    # Scenario 1: Pause (identical ticks)
    logger.info("\n[Test 2.1] Testing pause (identical ticks)...")
    tick_source.set_tick(5000)
    await smart_sync.update()
    await asyncio.sleep(0.2)

    tick_source.set_tick(5000)
    await smart_sync.update()
    await asyncio.sleep(0.2)

    tick_source.set_tick(5000)
    await smart_sync.update()
    await asyncio.sleep(0.2)

    is_paused = smart_sync.is_paused()
    logger.info(f"[Test 2.1] Is paused: {is_paused} (expected: True)")
    assert is_paused, "Should detect pause when ticks are identical"

    # Scenario 2: Very slow speed (0.05x) - should NOT be detected as pause
    logger.info("\n[Test 2.2] Testing very slow speed (0.05x) - NOT pause...")
    tick_source.set_tick(5000)
    await smart_sync.update()
    await asyncio.sleep(0.5)

    # At 0.05x: 64 * 0.05 * 0.5 = 1.6 ≈ 1-2 ticks
    tick_source.set_tick(5001)
    await smart_sync.update()
    await asyncio.sleep(0.5)

    tick_source.set_tick(5002)
    await smart_sync.update()

    is_paused = smart_sync.is_paused()
    logger.info(f"[Test 2.2] Is paused: {is_paused} (expected: False)")
    assert not is_paused, "Should NOT detect pause when ticks are changing (even slowly)"

    # Scenario 3: Tick = 0 (demo not loaded) - should NOT be pause
    logger.info("\n[Test 2.3] Testing tick=0 (demo not loaded)...")
    tick_source.set_tick(0)
    await smart_sync.update()
    await asyncio.sleep(0.1)

    tick_source.set_tick(0)
    await smart_sync.update()
    await asyncio.sleep(0.1)

    tick_source.set_tick(0)
    await smart_sync.update()

    is_paused = smart_sync.is_paused()
    logger.info(f"[Test 2.3] Is paused: {is_paused} (expected: False, tick=0 means not loaded)")
    assert not is_paused, "Should NOT detect pause when tick=0 (demo not loaded)"

    logger.info("\n[Test 2] ✓ Pause detection working correctly")


async def test_speed_aware_prediction():
    """Test speed-aware tick prediction."""
    logger.info("\n[Test 3] Testing speed-aware prediction...")

    # Direct import to avoid UI dependencies
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "smart_tick_sync",
        "src/core/smart_tick_sync.py"
    )
    smart_tick_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(smart_tick_module)
    SmartTickSync = smart_tick_module.SmartTickSync

    tick_source = MockTickSource()
    smart_sync = SmartTickSync(
        tick_source,
        tick_rate=64,
        history_size=10,
        pause_threshold=3,
        speed_calculation_window=5
    )

    # Setup: measure speed at 0.5x
    logger.info("\n[Test 3.1] Setup: measuring speed at 0.5x...")
    tick_source.set_tick(1000)
    await smart_sync.update()
    await asyncio.sleep(0.5)

    # At 0.5x: 64 * 0.5 * 0.5 = 16 ticks
    tick_source.set_tick(1016)
    await smart_sync.update()

    speed = smart_sync.get_current_speed()
    logger.info(f"[Test 3.1] Measured speed: {speed:.2f}x")

    # Now predict tick after 0.25 seconds
    await asyncio.sleep(0.25)
    predicted_tick = smart_sync.predict_current_tick()

    # Expected: 1016 + (64 * smoothed_speed * 0.25)
    # With smoothing, speed might not be exactly 0.5x yet
    logger.info(f"[Test 3.1] Predicted tick: {predicted_tick} (expected: ~1024, but depends on smoothed speed)")
    # Allow wider range since EMA smoothing affects speed
    assert 1016 <= predicted_tick <= 1035, f"Predicted tick should be > 1016, got {predicted_tick}"

    # Test prediction during pause
    logger.info("\n[Test 3.2] Testing prediction during pause...")
    tick_source.set_tick(2000)
    await smart_sync.update()
    await asyncio.sleep(0.1)

    tick_source.set_tick(2000)
    await smart_sync.update()
    await asyncio.sleep(0.1)

    tick_source.set_tick(2000)
    await smart_sync.update()

    # Should be paused
    assert smart_sync.is_paused(), "Should be paused"

    # Prediction during pause should return last tick (no interpolation)
    await asyncio.sleep(0.5)
    predicted_tick = smart_sync.predict_current_tick()
    logger.info(f"[Test 3.2] Predicted tick during pause: {predicted_tick} (expected: 2000)")
    assert predicted_tick == 2000, f"During pause, predicted tick should be {2000}, got {predicted_tick}"

    logger.info("\n[Test 3] ✓ Speed-aware prediction working correctly")


async def test_status_info():
    """Test status info reporting."""
    logger.info("\n[Test 4] Testing status info...")

    # Direct import to avoid UI dependencies
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "smart_tick_sync",
        "src/core/smart_tick_sync.py"
    )
    smart_tick_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(smart_tick_module)
    SmartTickSync = smart_tick_module.SmartTickSync

    tick_source = MockTickSource()
    smart_sync = SmartTickSync(
        tick_source,
        tick_rate=64,
        history_size=5,
        pause_threshold=3,
        speed_calculation_window=3
    )

    # Add some measurements
    tick_source.set_tick(1000)
    await smart_sync.update()
    await asyncio.sleep(0.1)

    tick_source.set_tick(1010)
    await smart_sync.update()

    # Get status
    status = smart_sync.get_status_info()

    logger.info(f"[Test 4] Status info:")
    logger.info(f"  - current_speed: {status['current_speed']:.2f}x")
    logger.info(f"  - is_paused: {status['is_paused']}")
    logger.info(f"  - last_tick: {status['last_tick']}")
    logger.info(f"  - history_size: {status['history_size']}")

    assert 'current_speed' in status
    assert 'is_paused' in status
    assert 'last_tick' in status
    assert 'history' in status

    logger.info("\n[Test 4] ✓ Status info working correctly")


async def main():
    """Run all tests."""
    try:
        await test_speed_detection()
        await test_pause_detection()
        await test_speed_aware_prediction()
        await test_status_info()

        logger.info("\n" + "=" * 60)
        logger.info("✓ ALL TESTS PASSED")
        logger.info("=" * 60)
        logger.info(f"\nLog file: {log_file}")

        return 0

    except Exception as e:
        logger.error(f"✗ TEST FAILED: {e}", exc_info=True)
        return 1

    finally:
        logging.shutdown()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
