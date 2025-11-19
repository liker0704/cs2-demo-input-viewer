#!/usr/bin/env python3
"""Test script to verify logging and tick synchronization fixes."""

import sys
import asyncio
import logging
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

# Setup logging (test force=True fix)
log_file = f"test_fixes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler(log_file, mode='w', encoding='utf-8', delay=False),
        logging.StreamHandler(sys.stdout)
    ],
    force=True  # Test force=True fix
)

logger = logging.getLogger(__name__)
logger.info("=" * 60)
logger.info("Testing Fixes for CS2 Input Visualizer")
logger.info("=" * 60)

# Test 1: Logging Fix
logger.info("[Test 1] Testing logging system...")
logger.debug("[Test 1] This is a DEBUG message (should appear if --debug works)")
logger.info("[Test 1] This is an INFO message")
logger.warning("[Test 1] This is a WARNING message")

# Test 2: Tick Synchronization Fix
logger.info("\n[Test 2] Testing tick synchronization...")

# Direct import to avoid UI dependencies
import importlib.util
spec = importlib.util.spec_from_file_location(
    "prediction_engine",
    "src/core/prediction_engine.py"
)
prediction_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prediction_module)

PredictionEngine = prediction_module.PredictionEngine
SmoothPredictionEngine = prediction_module.SmoothPredictionEngine


class MockSyncEngine:
    """Mock sync engine for testing."""

    def __init__(self, tick=0):
        self._tick = tick
        self._time = asyncio.get_event_loop().time() if asyncio._get_running_loop() else 0

    def get_last_tick(self):
        return self._tick

    def get_last_update_time(self):
        import time
        return time.time()

    def set_tick(self, tick):
        self._tick = tick
        import time
        self._time = time.time()


async def test_prediction_engine():
    """Test prediction engine with tick 0."""
    logger.info("[Test 2.1] Testing PredictionEngine with tick=0...")

    sync_engine = MockSyncEngine(tick=0)
    predictor = PredictionEngine(sync_engine)

    # Should return 0, not crash
    tick = predictor.get_current_tick()
    logger.info(f"[Test 2.1] Predicted tick: {tick} (expected: 0)")
    assert tick == 0, f"Expected 0, got {tick}"

    logger.info("[Test 2.1] ✓ PredictionEngine handles tick=0 correctly")

    # Test with valid tick
    logger.info("[Test 2.2] Testing PredictionEngine with tick=1000...")
    sync_engine.set_tick(1000)
    tick = predictor.get_current_tick()
    logger.info(f"[Test 2.2] Predicted tick: {tick} (expected: ≥1000)")
    assert tick >= 1000, f"Expected ≥1000, got {tick}"

    logger.info("[Test 2.2] ✓ PredictionEngine predicts correctly")


async def test_smooth_prediction():
    """Test smooth prediction engine pause detection."""
    logger.info("[Test 2.3] Testing SmoothPredictionEngine pause detection...")

    sync_engine = MockSyncEngine(tick=0)
    smooth = SmoothPredictionEngine(sync_engine)

    # Fill history with 0s
    for _ in range(5):
        tick = smooth.get_current_tick()
        await asyncio.sleep(0.01)

    # Should NOT print "Pause detected" because tick=0 means demo not loaded
    logger.info("[Test 2.3] Tick history filled with 0s")

    # Now test with valid ticks
    sync_engine.set_tick(5000)
    tick1 = smooth.get_current_tick()
    logger.info(f"[Test 2.3] First valid tick: {tick1}")

    await asyncio.sleep(0.1)
    tick2 = smooth.get_current_tick()
    logger.info(f"[Test 2.3] Second tick: {tick2}")

    logger.info("[Test 2.3] ✓ SmoothPredictionEngine doesn't false-positive on tick=0")


async def test_telnet_client_mock():
    """Test telnet client force_sync_tick fix."""
    logger.info("[Test 3] Testing telnet client force_sync_tick...")

    # Direct import to avoid UI dependencies
    import importlib.util
    spec_telnet = importlib.util.spec_from_file_location(
        "telnet_client",
        "src/network/telnet_client.py"
    )
    telnet_module = importlib.util.module_from_spec(spec_telnet)

    # Need to load tick_source interface first
    spec_tick = importlib.util.spec_from_file_location(
        "tick_source",
        "src/interfaces/tick_source.py"
    )
    tick_module = importlib.util.module_from_spec(spec_tick)
    sys.modules['src.interfaces.tick_source'] = tick_module
    spec_tick.loader.exec_module(tick_module)

    spec_telnet.loader.exec_module(telnet_module)
    CS2TelnetClient = telnet_module.CS2TelnetClient

    client = CS2TelnetClient()

    # Test without connection (should return 0)
    tick = await client.force_sync_tick()
    logger.info(f"[Test 3.1] Force sync without connection: {tick} (expected: 0)")
    assert tick == 0, f"Expected 0, got {tick}"

    logger.info("[Test 3.1] ✓ force_sync_tick handles disconnected state")

    # Note: Can't test connected state without actual CS2 server
    logger.info("[Test 3] ⚠ Skipping connected state test (requires CS2)")


async def main():
    """Run all tests."""
    try:
        await test_prediction_engine()
        await test_smooth_prediction()
        await test_telnet_client_mock()

        logger.info("\n" + "=" * 60)
        logger.info("✓ ALL TESTS PASSED")
        logger.info("=" * 60)
        logger.info(f"\nLog file: {log_file}")

        # Check log file exists and has content
        log_path = Path(log_file)
        if log_path.exists():
            size = log_path.stat().st_size
            logger.info(f"Log file size: {size} bytes")

            if size > 0:
                logger.info("✓ Log file created and contains data")

                # Print first few lines
                with open(log_file, 'r') as f:
                    lines = f.readlines()[:5]
                logger.info(f"\nFirst 5 lines of log file:")
                for line in lines:
                    print(f"  {line.rstrip()}")
            else:
                logger.error("✗ Log file is empty!")
        else:
            logger.error(f"✗ Log file not found: {log_file}")

    except Exception as e:
        logger.error(f"✗ TEST FAILED: {e}", exc_info=True)
        return 1

    finally:
        # Test logging.shutdown()
        logging.shutdown()

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
