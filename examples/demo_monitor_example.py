"""Example usage of DemoMonitor for Phase 6 Auto Mode.

This example demonstrates how to use DemoMonitor to automatically detect
when demos start playing in CS2 and trigger callbacks for auto-loading.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from network.telnet_client import RobustTelnetClient
from network.demo_monitor import DemoMonitor


async def on_demo_detected(demo_path: Path):
    """Callback function triggered when a new demo is detected.

    Args:
        demo_path: Full path to the detected demo file
    """
    print(f"\n{'='*60}")
    print(f"🎬 NEW DEMO DETECTED!")
    print(f"{'='*60}")
    print(f"Demo file: {demo_path}")
    print(f"File exists: {demo_path.exists()}")
    print(f"File size: {demo_path.stat().st_size if demo_path.exists() else 'N/A'} bytes")
    print(f"{'='*60}\n")

    # In a real application, you would:
    # 1. Load the demo data using ETL pipeline
    # 2. Start the visualization overlay
    # 3. Sync with CS2 playback


async def main():
    """Main example demonstrating DemoMonitor usage."""

    # Configuration
    CS2_HOST = "127.0.0.1"
    CS2_PORT = 2121
    CS2_DEMO_DIR = Path.home() / ".local/share/Steam/steamapps/common/Counter-Strike Global Offensive/game/csgo"

    print("DemoMonitor Example - Phase 6 Auto Mode")
    print("="*60)
    print(f"Host: {CS2_HOST}:{CS2_PORT}")
    print(f"Demo directory: {CS2_DEMO_DIR}")
    print("="*60)
    print()

    # Create telnet client with auto-reconnect
    print("[1/3] Creating telnet client...")
    telnet = RobustTelnetClient(
        host=CS2_HOST,
        port=CS2_PORT,
        max_retries=3,
        retry_delay=2.0
    )

    # Connect to CS2
    print("[2/3] Connecting to CS2...")
    if not await telnet.connect_with_retry():
        print("❌ Failed to connect to CS2")
        print("   Make sure CS2 is running with: -netconport 2121 -insecure")
        return

    print("✓ Connected to CS2")
    print()

    # Create demo monitor
    print("[3/3] Starting demo monitor...")
    monitor = DemoMonitor(telnet, CS2_DEMO_DIR)

    try:
        # Start monitoring (this will run until interrupted)
        print("✓ Monitoring active")
        print()
        print("Waiting for demo playback...")
        print("(In CS2, use 'playdemo <filename>' to test)")
        print("(Press Ctrl+C to stop)")
        print()

        # Monitor with 500ms poll interval
        await monitor.monitor_demo_load(
            callback=on_demo_detected,
            poll_interval=0.5
        )

    except KeyboardInterrupt:
        print("\n\nStopping monitor...")
    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        # Cleanup
        await monitor.stop_monitoring()
        await telnet.disconnect()
        print("✓ Disconnected")


if __name__ == "__main__":
    # Run the example
    asyncio.run(main())
