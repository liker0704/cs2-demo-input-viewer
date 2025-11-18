#!/usr/bin/env python3
"""Example demonstrating how to use the mock implementations.

This script shows how to use MockTickSource, MockDemoRepository, and
MockPlayerTracker together to simulate a complete CS2 input visualization
system without requiring a real CS2 connection or demo file.

Usage:
    python examples/mock_usage_example.py
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mocks import MockTickSource, MockDemoRepository, MockPlayerTracker


async def simulate_demo_playback():
    """Simulate demo playback using mock implementations."""
    
    print("=== CS2 Input Visualizer - Mock Mode ===\n")
    
    # Initialize components
    print("1. Initializing components...")
    tick_source = MockTickSource(start_tick=1000, tick_rate=64)
    demo_repo = MockDemoRepository()
    player_tracker = MockPlayerTracker()
    
    # Connect tick source
    print("2. Connecting to mock tick source...")
    connected = await tick_source.connect()
    print(f"   Connected: {connected}")
    
    # Load demo cache
    print("3. Loading demo cache...")
    cache_path = Path(__file__).parent.parent / "data" / "sample_cache.json"
    loaded = demo_repo.load_demo(str(cache_path))
    print(f"   Loaded: {loaded}")
    
    if loaded:
        player_id = demo_repo.get_default_player()
        tick_range = demo_repo.get_tick_range()
        print(f"   Player: {player_id}")
        print(f"   Tick range: {tick_range}")
    else:
        print("   Using empty cache (demo file not found)")
        player_id = demo_repo.get_default_player()
    
    # Update player tracker
    print("4. Updating player tracker...")
    await player_tracker.update()
    current_player = await player_tracker.get_current_player()
    print(f"   Current player: {current_player}")
    
    # Simulate playback
    print("\n5. Simulating demo playback (5 seconds)...")
    print("   Format: [Tick] -> Keys: [...] Mouse: [...]\n")
    
    for i in range(50):  # 50 iterations at 10 Hz = 5 seconds
        current_tick = await tick_source.get_current_tick()
        inputs = demo_repo.get_inputs(current_tick, player_id)
        
        if inputs:
            keys_str = ", ".join(inputs.keys) if inputs.keys else "None"
            mouse_str = ", ".join(inputs.mouse) if inputs.mouse else "None"
            print(f"   [Tick {current_tick}] -> Keys: [{keys_str}] Mouse: [{mouse_str}]")
        else:
            # Only print every 10th tick when no input to reduce spam
            if i % 10 == 0:
                print(f"   [Tick {current_tick}] -> No input data")
        
        await asyncio.sleep(0.1)  # 10 Hz update rate
    
    # Cleanup
    print("\n6. Cleaning up...")
    await tick_source.disconnect()
    print("   Disconnected from tick source")
    
    print("\n=== Demo playback simulation complete ===")


if __name__ == "__main__":
    asyncio.run(simulate_demo_playback())
