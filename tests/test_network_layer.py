#!/usr/bin/env python3
"""Test script for network layer components.

This script demonstrates basic usage of the network layer without
requiring a live CS2 connection. It uses mock implementations to
simulate the behavior.
"""

import asyncio
import sys

# Add src to path
sys.path.insert(0, 'src')

from network import (
    CS2TelnetClient,
    RobustTelnetClient,
    SyncEngine,
    PredictionEngine,
    ManualPlayerTracker,
)


async def test_telnet_client():
    """Test telnet client connection (will fail without CS2)."""
    print("\n=== Testing CS2TelnetClient ===")
    client = CS2TelnetClient()

    print(f"Attempting connection to {client.host}:{client.port}...")
    connected = await client.connect()

    if connected:
        print("✓ Connected to CS2!")
        tick = await client.get_current_tick()
        print(f"✓ Current tick: {tick}")

        demo_info = await client.get_demo_info()
        print(f"✓ Demo info: {demo_info}")

        await client.disconnect()
    else:
        print("✗ Connection failed (CS2 not running with -netconport)")


async def test_robust_telnet_client():
    """Test robust telnet client with retry logic."""
    print("\n=== Testing RobustTelnetClient ===")
    client = RobustTelnetClient(max_retries=2, retry_delay=0.5)

    print(f"Attempting connection with retry...")
    connected = await client.connect_with_retry()

    if connected:
        print("✓ Connected with retry!")
        await client.disconnect()
    else:
        print("✗ Connection failed after retries")


async def test_sync_engine():
    """Test sync engine with mock tick source."""
    print("\n=== Testing SyncEngine ===")

    # Use mock tick source
    from mocks.tick_source import MockTickSource

    mock_tick = MockTickSource(start_tick=1000, tick_rate=64)
    await mock_tick.connect()

    sync = SyncEngine(mock_tick, polling_interval=0.5)
    await sync.start()

    print("✓ Sync engine started")

    # Wait for a few sync cycles
    for i in range(5):
        await asyncio.sleep(0.2)
        predicted = sync.get_predicted_tick()
        synced = sync.get_last_synced_tick()
        drift = sync.get_drift()

        print(f"  Cycle {i+1}: Predicted={predicted}, Synced={synced}, Drift={drift:.3f}s")

    await sync.stop()
    await mock_tick.disconnect()
    print("✓ Sync engine stopped")


async def test_prediction_engine():
    """Test prediction engine with drift correction."""
    print("\n=== Testing PredictionEngine ===")

    from mocks.tick_source import MockTickSource

    mock_tick = MockTickSource(start_tick=5000, tick_rate=64)
    await mock_tick.connect()

    sync = SyncEngine(mock_tick, polling_interval=0.5)
    prediction = PredictionEngine(sync, max_drift_ticks=10)

    await sync.start()
    print("✓ Prediction engine started")

    # Normal operation
    for i in range(3):
        await asyncio.sleep(0.2)
        tick = prediction.get_corrected_tick()
        drift_info = prediction.get_drift_info()
        print(f"  Tick {i+1}: {tick} (drift: {drift_info['tick_drift']} ticks)")

    # Simulate a jump (user pressed Shift+F2) by creating a new mock
    print("\n  Simulating tick jump...")
    await sync.stop()
    await mock_tick.disconnect()

    # Create new mock at different tick
    mock_tick = MockTickSource(start_tick=10000, tick_rate=64)
    await mock_tick.connect()
    sync = SyncEngine(mock_tick, polling_interval=0.5)
    prediction = PredictionEngine(sync, max_drift_ticks=10)
    await sync.start()
    await asyncio.sleep(0.6)  # Wait for sync

    tick = prediction.get_corrected_tick()
    drift_info = prediction.get_drift_info()
    print(f"  After jump: {tick} (corrected: {drift_info['drift_corrected']})")

    await sync.stop()
    await mock_tick.disconnect()
    print("✓ Prediction engine test complete")


async def test_player_tracker():
    """Test player tracker."""
    print("\n=== Testing ManualPlayerTracker ===")

    tracker = ManualPlayerTracker()

    # Initially no player
    player = await tracker.get_current_player()
    print(f"Initial player: {player}")
    print(f"Has player: {tracker.has_player()}")

    # Set player
    tracker.set_player("STEAM_1:0:123456789")
    player = await tracker.get_current_player()
    print(f"✓ Set player: {player}")
    print(f"✓ Has player: {tracker.has_player()}")

    # Clear player
    tracker.clear_player()
    player = await tracker.get_current_player()
    print(f"✓ Cleared player: {player}")
    print(f"✓ Has player: {tracker.has_player()}")


async def main():
    """Run all tests."""
    print("CS2 Input Visualizer - Network Layer Test")
    print("=" * 50)

    # Test player tracker (always works)
    await test_player_tracker()

    # Test sync and prediction (uses mock)
    await test_sync_engine()
    await test_prediction_engine()

    # Test telnet clients (requires CS2)
    print("\nNote: Next tests require CS2 running with -netconport 2121")
    await test_telnet_client()
    await test_robust_telnet_client()

    print("\n" + "=" * 50)
    print("All tests complete!")


if __name__ == "__main__":
    asyncio.run(main())
