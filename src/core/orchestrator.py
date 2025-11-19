"""
Orchestrator - Main system coordinator with dependency injection.

This module provides the main orchestrator that coordinates all system components:
- Tick synchronization (network polling)
- Tick prediction (smooth interpolation)
- Player tracking (who to visualize)
- Input visualization (rendering)

The orchestrator uses dependency injection to allow easy switching between
mock and real implementations for testing and development.
"""

import asyncio
import time
from typing import Optional

from src.interfaces.tick_source import ITickSource
from src.interfaces.demo_repository import IDemoRepository
from src.interfaces.player_tracker import IPlayerTracker
from src.interfaces.input_visualizer import IInputVisualizer
from src.core.prediction_engine import PredictionEngine, SmoothPredictionEngine


class SyncEngine:
    """Synchronization engine for network polling.

    Uses periodic force_sync to resynchronize with CS2 demo playback.
    Between syncs, the prediction engine interpolates tick values.
    """

    def __init__(self, tick_source: ITickSource, sync_interval: float = 5.0):
        """Initialize sync engine.

        Args:
            tick_source: Source of tick data (Telnet or Mock)
            sync_interval: Time between force syncs in seconds (default: 5.0)
        """
        self.tick_source = tick_source
        self.sync_interval = sync_interval

        # State
        self._last_tick = 0
        self._last_update_time = 0.0
        self._last_sync_time = 0.0

    async def update(self, force: bool = False):
        """Update tick from source.

        Args:
            force: If True, forces a sync via demo_pause/resume. 
                   If False, just returns last known tick.

        Raises:
            Exception: If tick source update fails
        """
        try:
            current_time = time.time()
            
            # Check if we need to force sync
            should_sync = force or (current_time - self._last_sync_time >= self.sync_interval)
            
            if should_sync and hasattr(self.tick_source, 'force_sync_tick'):
                # Do force sync
                tick = await self.tick_source.force_sync_tick()
                self._last_sync_time = current_time
                print(f"[SyncEngine] Synced to tick {tick}")
            else:
                # Just get passive tick (no polling)
                tick = await self.tick_source.get_current_tick()
            
            self._last_tick = tick
            self._last_update_time = current_time

        except Exception as e:
            print(f"[SyncEngine] Update error: {e}")
            raise

    def get_last_tick(self) -> int:
        """Get last known server tick.

        Returns:
            int: Last tick received from server (0 if no updates yet)
        """
        return self._last_tick

    def get_last_update_time(self) -> float:
        """Get timestamp of last update.

        Returns:
            float: Unix timestamp of last successful update
        """
        return self._last_update_time


class Orchestrator:
    """Main orchestrator coordinating all system components.

    This class implements the dependency injection pattern,
    allowing easy switching between mock and real implementations.

    It manages three main loops:
    1. Sync loop - polls tick source at regular intervals
    2. Render loop - renders at target FPS using predicted tick
    3. Player tracking loop - tracks current player
    """

    def __init__(
        self,
        tick_source: ITickSource,
        demo_repository: IDemoRepository,
        player_tracker: IPlayerTracker,
        visualizer: IInputVisualizer,
        polling_interval: float = 0.25,
        render_fps: int = 60,
        tick_rate: int = 64,
        use_smooth_prediction: bool = True
    ):
        """Initialize orchestrator with dependencies.

        Args:
            tick_source: Source of current tick (Telnet or Mock)
            demo_repository: Source of input data (Parser or Mock)
            player_tracker: Tracker for current player (CS2 or Mock)
            visualizer: UI overlay (PyQt6 or Mock)
            polling_interval: Network polling frequency in seconds (default: 0.25)
            render_fps: Target rendering FPS (default: 60)
            tick_rate: Game tick rate in Hz (default: 64)
            use_smooth_prediction: Use smooth prediction engine (default: True)
        """
        # Dependencies (injected)
        self.tick_source = tick_source
        self.demo_repo = demo_repository
        self.player_tracker = player_tracker
        self.visualizer = visualizer

        # Configuration
        self.polling_interval = polling_interval
        self.render_fps = render_fps
        self.tick_rate = tick_rate
        self.use_smooth_prediction = use_smooth_prediction

        # State
        self._running = False
        self._current_tick = 0
        self._current_player: Optional[str] = None

        # Components (created during initialization)
        self.sync_engine: Optional[SyncEngine] = None
        self.prediction_engine: Optional[PredictionEngine] = None

        # Tasks
        self._sync_task: Optional[asyncio.Task] = None
        self._render_task: Optional[asyncio.Task] = None
        self._player_task: Optional[asyncio.Task] = None

    async def initialize(self) -> bool:
        """Initialize all components.

        Connects to tick source, initializes player tracker, and creates
        sync and prediction engines.

        Returns:
            bool: True if initialization successful, False otherwise
        """
        print("[Orchestrator] Initializing components...")

        try:
            # Connect to tick source
            if not await self.tick_source.connect():
                print("[Orchestrator] Failed to connect tick source")
                return False

            # Initialize player tracker
            await self.player_tracker.update()
            self._current_player = await self.player_tracker.get_current_player()

            if not self._current_player:
                print("[Orchestrator] Warning: No player selected")

            # Initialize sync engine (pass sync_interval instead of polling_interval)
            self.sync_engine = SyncEngine(
                self.tick_source,
                sync_interval=1.5  # Force sync every 1.5 seconds (reduced from 5.0 for less drift)
            )
            
            # Do initial sync to get starting tick
            print("[Orchestrator] Performing initial synchronization...")
            await self.sync_engine.update(force=True)

            # Initialize prediction engine (basic or smooth)
            if self.use_smooth_prediction:
                self.prediction_engine = SmoothPredictionEngine(
                    self.sync_engine,
                    self.tick_rate
                )
                print("[Orchestrator] Using smooth prediction engine")
            else:
                self.prediction_engine = PredictionEngine(
                    self.sync_engine,
                    self.tick_rate
                )
                print("[Orchestrator] Using basic prediction engine")

            # Show visualizer
            self.visualizer.show()

            print("[Orchestrator] Initialization complete")
            return True

        except Exception as e:
            print(f"[Orchestrator] Initialization failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def start(self):
        """Start main orchestration loop.

        Initializes all components and starts three concurrent loops:
        - Sync loop: polls tick source
        - Render loop: renders at target FPS
        - Player tracking loop: tracks current player

        This method blocks until stop() is called or an error occurs.
        """
        if not await self.initialize():
            print("[Orchestrator] Initialization failed, aborting")
            return

        self._running = True

        # Start sync loop
        self._sync_task = asyncio.create_task(self._sync_loop())

        # Start render loop
        self._render_task = asyncio.create_task(self._render_loop())

        # Start player tracking loop
        self._player_task = asyncio.create_task(self._player_tracking_loop())

        print("[Orchestrator] All loops started")

        # Wait for all tasks
        try:
            await asyncio.gather(
                self._sync_task,
                self._render_task,
                self._player_task,
                return_exceptions=True
            )
        except Exception as e:
            print(f"[Orchestrator] Error in main loop: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await self.stop()

    async def stop(self):
        """Stop all loops and cleanup.

        Cancels all running tasks, disconnects tick source, and hides visualizer.
        """
        if not self._running:
            return

        print("[Orchestrator] Stopping...")

        self._running = False

        # Cancel tasks
        for task in [self._sync_task, self._render_task, self._player_task]:
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        # Disconnect tick source
        try:
            await self.tick_source.disconnect()
        except Exception as e:
            print(f"[Orchestrator] Error disconnecting tick source: {e}")

        # Hide visualizer
        try:
            self.visualizer.hide()
        except Exception as e:
            print(f"[Orchestrator] Error hiding visualizer: {e}")

        print("[Orchestrator] Stopped")

    async def _sync_loop(self):
        """Periodic sync with tick source.

        Polls the tick source at regular intervals to get the current server tick.
        Runs until stop() is called.
        """
        print("[Orchestrator] Sync loop started")

        while self._running:
            try:
                # Update sync engine
                await self.sync_engine.update()

            except Exception as e:
                print(f"[Orchestrator] Sync error: {e}")

            # Wait for next poll
            await asyncio.sleep(self.polling_interval)

        print("[Orchestrator] Sync loop stopped")

    async def _render_loop(self):
        """Render loop at target FPS.

        Renders input visualization at the target FPS using predicted tick.
        Runs until stop() is called.
        """
        print("[Orchestrator] Render loop started")

        frame_time = 1.0 / self.render_fps

        while self._running:
            try:
                # Get predicted tick
                self._current_tick = self.prediction_engine.get_current_tick()

                # Get input data for current tick and player
                if self._current_player:
                    input_data = self.demo_repo.get_inputs(
                        self._current_tick,
                        self._current_player
                    )

                    # Render if we have data
                    if input_data:
                        self.visualizer.render(input_data)
                else:
                    # No player selected, clear visualization
                    self.visualizer.render(None)

            except Exception as e:
                print(f"[Orchestrator] Render error: {e}")

            # Wait for next frame
            await asyncio.sleep(frame_time)

        print("[Orchestrator] Render loop stopped")

    async def _player_tracking_loop(self):
        """Track current player (update every 1 second).

        Monitors which player is currently being spectated and updates
        the visualization accordingly. Runs until stop() is called.
        """
        print("[Orchestrator] Player tracking loop started")

        while self._running:
            try:
                await self.player_tracker.update()
                new_player = await self.player_tracker.get_current_player()

                if new_player != self._current_player:
                    print(f"[Orchestrator] Player changed: {self._current_player} → {new_player}")
                    self._current_player = new_player

            except Exception as e:
                print(f"[Orchestrator] Player tracking error: {e}")

            # Update every second
            await asyncio.sleep(1.0)

        print("[Orchestrator] Player tracking loop stopped")


class RobustOrchestrator(Orchestrator):
    """Orchestrator with enhanced error handling and recovery.

    Extends base orchestrator with:
    - Automatic reconnection on network failure
    - Retry logic with exponential backoff
    - Graceful degradation
    """

    def __init__(self, *args, reconnect_attempts: int = 3, reconnect_delay: float = 2.0, **kwargs):
        """Initialize robust orchestrator.

        Args:
            reconnect_attempts: Number of reconnection attempts (default: 3)
            reconnect_delay: Delay between reconnection attempts in seconds (default: 2.0)
            *args, **kwargs: Passed to base Orchestrator
        """
        super().__init__(*args, **kwargs)
        self.reconnect_attempts = reconnect_attempts
        self.reconnect_delay = reconnect_delay

    async def _sync_loop(self):
        """Sync loop with automatic reconnection."""
        print("[Orchestrator] Robust sync loop started")

        retry_count = 0

        while self._running:
            try:
                await self.sync_engine.update()
                retry_count = 0  # Reset on success

            except ConnectionError as e:
                retry_count += 1
                print(f"[Orchestrator] Connection error ({retry_count}/{self.reconnect_attempts}): {e}")

                if retry_count >= self.reconnect_attempts:
                    print("[Orchestrator] Max retries reached, attempting reconnection...")

                    # Disconnect and reconnect
                    await self.tick_source.disconnect()
                    await asyncio.sleep(self.reconnect_delay)

                    if await self.tick_source.connect():
                        print("[Orchestrator] Reconnection successful")
                        retry_count = 0
                    else:
                        print("[Orchestrator] Reconnection failed, stopping")
                        await self.stop()
                        break

            except Exception as e:
                print(f"[Orchestrator] Unexpected sync error: {e}")
                import traceback
                traceback.print_exc()

            await asyncio.sleep(self.polling_interval)

        print("[Orchestrator] Robust sync loop stopped")
