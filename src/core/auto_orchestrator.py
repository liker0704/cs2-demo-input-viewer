"""Auto-mode orchestrator for fully automatic CS2 input visualization.

This module provides the AutoOrchestrator which handles:
- Auto-detection of CS2 installation
- Automatic demo monitoring
- Cache validation and rebuilding
- Spectator tracking
- Real-time visualization

The orchestrator runs three concurrent loops:
1. Demo monitoring (500ms) - detects demo loads/switches
2. Spectator tracking (1s) - tracks player changes
3. Render loop (60 FPS) - displays input visualization
"""

import asyncio
from pathlib import Path
from typing import Optional, Union
from PyQt6.QtWidgets import QApplication

from src.utils.cs2_detector import CS2PathDetector
from src.parsers.cache_validator import CacheValidator
from src.parsers.etl_pipeline import DemoETLPipeline
from src.parsers.demo_repository import CachedDemoRepository
from src.network.demo_monitor import DemoMonitor
from src.network.spectator_tracker import SpectatorTracker
from src.network.telnet_client import RobustTelnetClient
from src.ui.overlay import CS2InputOverlay
from src.core.config import AppConfig


class AutoOrchestrator:
    """Fully automatic mode orchestrator.

    Coordinates all components for automatic demo visualization:
    - Detects CS2 path automatically
    - Connects to telnet (netcon)
    - Monitors for demo loads
    - Validates/rebuilds cache automatically
    - Tracks spectator target
    - Shows real-time visualization

    Three concurrent loops run:
    - Demo monitoring: 500ms interval
    - Spectator tracking: 1s interval
    - Render loop: 60 FPS
    """

    def __init__(
        self,
        config: Optional[Union[AppConfig, Path]] = None,
        host: Optional[str] = None,
        port: Optional[int] = None
    ):
        """Initialize auto-orchestrator.

        Args:
            config: Either AppConfig object or Path to cache directory (for backward compatibility)
            host: Telnet host (default: localhost) - ignored if config is AppConfig
            port: Telnet port (default: 2121) - ignored if config is AppConfig
        """
        # Handle different constructor signatures
        if isinstance(config, AppConfig):
            # New signature: AutoOrchestrator(AppConfig())
            self.config = config
            self.cache_dir = Path(config.cache_dir)
            telnet_host = config.cs2_host
            telnet_port = config.cs2_port
        elif isinstance(config, Path):
            # Old signature: AutoOrchestrator(Path("cache"), "host", 2121)
            self.config = None
            self.cache_dir = config
            telnet_host = host or "127.0.0.1"
            telnet_port = port or 2121
        elif config is None:
            # Default: AutoOrchestrator()
            self.config = None
            self.cache_dir = Path("./cache")
            telnet_host = host or "127.0.0.1"
            telnet_port = port or 2121
        else:
            raise TypeError(f"config must be AppConfig or Path, got {type(config)}")

        # Ensure cache directory exists
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Components (initialized in start())
        self.cs2_detector = CS2PathDetector()
        self.cache_validator = CacheValidator(self.cache_dir)
        self.telnet_client = RobustTelnetClient(telnet_host, telnet_port, max_retries=5)
        self.demo_monitor: Optional[DemoMonitor] = None
        self.spectator_tracker: Optional[SpectatorTracker] = None
        self.demo_repository = CachedDemoRepository()
        self.overlay: Optional[CS2InputOverlay] = None

        # State
        self._running = False
        self._current_demo: Optional[Path] = None
        self._current_cache: Optional[Path] = None
        self._current_player: Optional[str] = None
        self._current_tick = 0

        # Tasks
        self._demo_task: Optional[asyncio.Task] = None
        self._spectator_task: Optional[asyncio.Task] = None
        self._render_task: Optional[asyncio.Task] = None

        # Qt application (for overlay)
        self.app: Optional[QApplication] = None

    async def start(self):
        """Main entry point for auto mode.

        Workflow:
        1. Find CS2 installation
        2. Connect to telnet
        3. Initialize Qt overlay
        4. Start monitoring loops
        """
        print("[AutoOrchestrator] Starting auto mode...")

        # Step 1: Find CS2
        print("[AutoOrchestrator] Detecting CS2 installation...")
        cs2_path = self.cs2_detector.find_cs2_path()

        if cs2_path is None:
            print("[AutoOrchestrator] ✗ Failed to detect CS2 installation")
            print("[AutoOrchestrator] Please ensure CS2 is installed via Steam")
            return False

        print(f"[AutoOrchestrator] ✓ Found CS2 at: {cs2_path}")

        # Step 2: Connect to telnet
        print(f"[AutoOrchestrator] Connecting to CS2 telnet ({self.telnet_client.host}:{self.telnet_client.port})...")
        if not await self.telnet_client.connect_with_retry():
            print("[AutoOrchestrator] ✗ Failed to connect to CS2 telnet")
            print("[AutoOrchestrator] Please launch CS2 with: -netconport 2121")
            return False

        print("[AutoOrchestrator] ✓ Connected to CS2 telnet")

        # Step 3: Initialize monitoring components
        self.demo_monitor = DemoMonitor(self.telnet_client)
        self.demo_monitor.set_callback(self._on_demo_loaded)

        self.spectator_tracker = SpectatorTracker(self.telnet_client)
        self.spectator_tracker.set_callback(self._on_spectator_changed)

        # Step 4: Initialize Qt overlay
        print("[AutoOrchestrator] Initializing overlay...")
        if QApplication.instance() is None:
            self.app = QApplication([])
        else:
            self.app = QApplication.instance()

        self.overlay = CS2InputOverlay()
        self.overlay.show()
        print("[AutoOrchestrator] ✓ Overlay ready")

        # Step 5: Start monitoring loops
        self._running = True
        print("[AutoOrchestrator] Starting monitoring loops...")

        self._demo_task = asyncio.create_task(self._demo_monitoring_loop())
        self._spectator_task = asyncio.create_task(self._spectator_tracking_loop())
        self._render_task = asyncio.create_task(self._render_loop())

        print("[AutoOrchestrator] ✓ Auto mode running")
        print("[AutoOrchestrator] Waiting for demo to be loaded in CS2...")

        # Wait for all tasks
        try:
            await asyncio.gather(
                self._demo_task,
                self._spectator_task,
                self._render_task,
                return_exceptions=True
            )
        except Exception as e:
            print(f"[AutoOrchestrator] Error in main loop: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await self.stop()

        return True

    async def stop(self):
        """Graceful shutdown."""
        if not self._running:
            return

        print("[AutoOrchestrator] Shutting down...")
        self._running = False

        # Cancel tasks
        for task in [self._demo_task, self._spectator_task, self._render_task]:
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        # Disconnect telnet
        await self.telnet_client.disconnect()

        # Hide overlay
        if self.overlay:
            self.overlay.hide()

        print("[AutoOrchestrator] Shutdown complete")

    async def _demo_monitoring_loop(self):
        """Monitor for demo load events (500ms interval)."""
        print("[AutoOrchestrator] Demo monitoring loop started")

        while self._running:
            try:
                await self.demo_monitor.update()
            except Exception as e:
                print(f"[AutoOrchestrator] Demo monitor error: {e}")

            await asyncio.sleep(0.5)  # 500ms

        print("[AutoOrchestrator] Demo monitoring loop stopped")

    async def _on_demo_loaded(self, demo_path: Path):
        """Handle new demo loaded event.

        Workflow:
        1. Validate cache
        2. Run ETL if needed (with progress)
        3. Load repository
        4. Extract default player
        """
        print(f"\n[AutoOrchestrator] Demo loaded: {demo_path.name}")
        self._current_demo = demo_path

        # Step 1: Validate cache
        print("[AutoOrchestrator] Checking cache...")
        cache_path = self.cache_validator.get_cache_path(demo_path)

        # Check if cache needs rebuild (invalid or doesn't exist)
        needs_rebuild = not self.cache_validator.is_cache_valid(demo_path)

        if needs_rebuild:
            print("[AutoOrchestrator] Cache invalid or missing, running ETL...")

            # Step 2: Run ETL with progress
            cache_path = await self._run_etl_background(demo_path)

            if cache_path is None:
                print("[AutoOrchestrator] ✗ ETL failed")
                return
        else:
            print(f"[AutoOrchestrator] ✓ Using existing cache: {cache_path.name}")

        # Step 3: Load repository
        print("[AutoOrchestrator] Loading demo data...")
        if not self.demo_repository.load_demo(str(cache_path)):
            print("[AutoOrchestrator] ✗ Failed to load demo repository")
            return

        self._current_cache = cache_path

        # Step 4: Get default player
        try:
            self._current_player = self.demo_repository.get_default_player()
            print(f"[AutoOrchestrator] ✓ Tracking player: {self._current_player}")
        except Exception as e:
            print(f"[AutoOrchestrator] Error getting player: {e}")
            self._current_player = None

    async def _spectator_tracking_loop(self):
        """Monitor spectator target changes (1s interval)."""
        print("[AutoOrchestrator] Spectator tracking loop started")

        while self._running:
            try:
                if self.spectator_tracker:
                    await self.spectator_tracker.update()
            except Exception as e:
                print(f"[AutoOrchestrator] Spectator tracker error: {e}")

            await asyncio.sleep(1.0)  # 1 second

        print("[AutoOrchestrator] Spectator tracking loop stopped")

    async def _on_spectator_changed(self, player_name: str, steam_id: str):
        """Handle spectator target change.

        Args:
            player_name: New player being spectated
            steam_id: Steam ID of the player
        """
        print(f"[AutoOrchestrator] Spectator changed to: {player_name} ({steam_id})")

        # Update current player if steam_id matches loaded data
        if steam_id != "unknown":
            self._current_player = steam_id

    async def _render_loop(self):
        """60 FPS rendering loop."""
        print("[AutoOrchestrator] Render loop started")

        frame_time = 1.0 / 60  # 60 FPS

        while self._running:
            try:
                # Process Qt events
                if self.app:
                    self.app.processEvents()

                # Get current tick from telnet
                self._current_tick = await self.telnet_client.get_current_tick()

                # Render if we have data
                if self._current_player and self._current_demo:
                    input_data = self.demo_repository.get_inputs(
                        self._current_tick,
                        self._current_player
                    )

                    if input_data and self.overlay:
                        self.overlay.update_inputs(input_data)
                    elif self.overlay:
                        # Clear visualization if no input
                        self.overlay.update_inputs(None)

            except Exception as e:
                print(f"[AutoOrchestrator] Render error: {e}")

            await asyncio.sleep(frame_time)

        print("[AutoOrchestrator] Render loop stopped")

    async def _run_etl_background(self, demo_path: Path) -> Optional[Path]:
        """Run ETL pipeline in background with progress reporting.

        Args:
            demo_path: Path to demo file

        Returns:
            Path to generated cache file, or None if failed
        """
        try:
            # Run ETL in executor to avoid blocking
            loop = asyncio.get_event_loop()

            def run_etl():
                pipeline = DemoETLPipeline(
                    demo_path=str(demo_path),
                    output_dir=str(self.cache_dir)
                )
                return pipeline.run(optimize=True, format="json")

            print("[AutoOrchestrator] Running ETL pipeline (this may take a moment)...")
            cache_path_str = await loop.run_in_executor(None, run_etl)

            if cache_path_str:
                print(f"[AutoOrchestrator] ✓ ETL complete: {Path(cache_path_str).name}")
                return Path(cache_path_str)

        except Exception as e:
            print(f"[AutoOrchestrator] ETL error: {e}")
            import traceback
            traceback.print_exc()

        return None


# Main entry point for auto mode
async def run_auto_mode():
    """Run the auto-orchestrator.

    Example:
        >>> import asyncio
        >>> asyncio.run(run_auto_mode())
    """
    orchestrator = AutoOrchestrator()
    await orchestrator.start()


if __name__ == "__main__":
    print("CS2 Input Visualizer - Auto Mode")
    print("=" * 50)
    print()
    print("Requirements:")
    print("1. CS2 must be running")
    print("2. Launch CS2 with: -netconport 2121")
    print("3. Load a demo in CS2")
    print()
    print("Starting auto mode...")
    print()

    asyncio.run(run_auto_mode())
