"""Sync engine for periodic tick updates and prediction.

This module provides synchronization between CS2 demo playback and the
input visualizer overlay. It polls the tick source at a low frequency
(2-4 Hz) to minimize network overhead while maintaining accurate timing
information.

The sync engine stores the last known server tick and timestamp, allowing
prediction of the current tick between polling intervals.
"""

import asyncio
import time
from typing import Optional

from interfaces.tick_source import ITickSource


class SyncEngine:
    """Manages synchronization between CS2 and the prediction engine.

    Polls the tick source at a configurable interval (default: 250ms) to
    retrieve the current tick. Between polls, the current tick can be
    estimated using the get_predicted_tick() method.

    This approach minimizes network overhead while maintaining smooth
    60 FPS rendering without visual stutter.

    Attributes:
        tick_source: Source of tick information (e.g., telnet client)
        polling_interval: How often to poll in seconds (default: 0.25)
        tick_rate: Game tick rate in Hz (default: 64 for CS2)
    """

    def __init__(
        self,
        tick_source: ITickSource,
        polling_interval: float = 0.25,
        tick_rate: int = 64
    ):
        """Initialize the sync engine.

        Args:
            tick_source: Source of tick information (Telnet client)
            polling_interval: How often to poll in seconds (default: 250ms)
            tick_rate: Game tick rate in Hz (default: 64 for CS2)
        """
        self.tick_source = tick_source
        self.polling_interval = polling_interval
        self.tick_rate = tick_rate

        # Calculated constants
        self.tick_duration = 1.0 / self.tick_rate  # 15.625 ms per tick

        # State
        self._last_synced_tick = 0
        self._last_sync_time = 0.0
        self._running = False
        self._sync_task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        """Start the sync loop.

        Performs an initial sync with the server, then starts a background
        task that periodically polls for tick updates.
        """
        # Initial sync
        await self._sync_with_server()

        # Start periodic sync task
        self._running = True
        self._sync_task = asyncio.create_task(self._sync_loop())
        print(f"[Sync] Started with polling interval: {self.polling_interval * 1000:.0f}ms")

    async def stop(self) -> None:
        """Stop the sync loop.

        Cancels the background sync task and waits for it to finish.
        """
        self._running = False
        if self._sync_task:
            self._sync_task.cancel()
            try:
                await self._sync_task
            except asyncio.CancelledError:
                pass
        print("[Sync] Stopped")

    async def _sync_loop(self) -> None:
        """Periodic sync loop that runs in the background.

        Polls the tick source at the configured interval until stopped.
        """
        while self._running:
            try:
                await asyncio.sleep(self.polling_interval)
                await self._sync_with_server()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[Sync] Error in sync loop: {e}")

    async def _sync_with_server(self) -> None:
        """Query CS2 for current tick and update sync state.

        Retrieves the current tick from the tick source and updates
        the last known tick and timestamp.
        """
        try:
            server_tick = await self.tick_source.get_current_tick()
            current_time = time.time()

            # Update sync state
            self._last_synced_tick = server_tick
            self._last_sync_time = current_time

        except Exception as e:
            print(f"[Sync] Error during sync: {e}")

    def get_last_synced_tick(self) -> int:
        """Get the last tick received from the server.

        Returns:
            int: Last synced tick number
        """
        return self._last_synced_tick

    def get_last_sync_time(self) -> float:
        """Get the timestamp of the last successful sync.

        Returns:
            float: Unix timestamp of last sync
        """
        return self._last_sync_time

    def get_predicted_tick(self) -> int:
        """Get current tick using prediction between syncs.

        Calculates the current tick by adding elapsed ticks since the last
        sync to the last known tick. This provides smooth tick progression
        without constant network queries.

        Returns:
            int: Predicted current tick number
        """
        if self._last_sync_time == 0:
            return 0

        # Time elapsed since last sync
        time_elapsed = time.time() - self._last_sync_time

        # Calculate ticks elapsed based on tick rate
        ticks_elapsed = int(time_elapsed / self.tick_duration)

        # Predicted tick
        predicted = self._last_synced_tick + ticks_elapsed

        return predicted

    def get_drift(self) -> float:
        """Calculate time drift since last sync.

        Returns the time in seconds since the last successful sync with
        the server. This can be used to detect connection issues or
        stale data.

        Returns:
            float: Time drift in seconds
        """
        if self._last_sync_time == 0:
            return 0.0

        return time.time() - self._last_sync_time

    def is_running(self) -> bool:
        """Check if the sync engine is running.

        Returns:
            bool: True if sync loop is active, False otherwise
        """
        return self._running


class PredictionEngine:
    """Advanced prediction engine with drift correction.

    Wraps a SyncEngine to provide tick prediction with automatic correction
    when large drift is detected (e.g., when user jumps to a different
    tick using Shift+F2 in CS2).

    Attributes:
        sync_engine: Underlying sync engine
        max_drift: Maximum allowed drift in ticks before correction
    """

    def __init__(self, sync_engine: SyncEngine, max_drift_ticks: int = 10):
        """Initialize the prediction engine.

        Args:
            sync_engine: Sync engine to use for tick information
            max_drift_ticks: Maximum tick drift before forcing correction
                           (default: 10 ticks ≈ 156ms at 64 Hz)
        """
        self.sync_engine = sync_engine
        self.max_drift_ticks = max_drift_ticks

    def get_corrected_tick(self) -> int:
        """Get tick with drift correction applied.

        Uses prediction for normal playback, but snaps to the last synced
        tick if drift exceeds the threshold. This handles cases where the
        user jumps to a different position in the demo.

        Returns:
            int: Corrected current tick
        """
        predicted = self.sync_engine.get_predicted_tick()
        last_synced = self.sync_engine.get_last_synced_tick()

        # Calculate tick drift
        drift = abs(predicted - last_synced)

        # If drift exceeds threshold, snap to server tick
        if drift > self.max_drift_ticks:
            print(f"[Prediction] Large drift detected ({drift} ticks), correcting...")
            return last_synced

        return predicted

    def get_drift_info(self) -> dict:
        """Get detailed drift information for debugging.

        Returns:
            dict: Dictionary containing:
                - predicted_tick (int): Predicted tick
                - synced_tick (int): Last synced tick
                - tick_drift (int): Difference in ticks
                - time_drift (float): Time since last sync in seconds
                - drift_corrected (bool): Whether drift correction was applied
        """
        predicted = self.sync_engine.get_predicted_tick()
        synced = self.sync_engine.get_last_synced_tick()
        tick_drift = abs(predicted - synced)
        time_drift = self.sync_engine.get_drift()
        corrected = tick_drift > self.max_drift_ticks

        return {
            "predicted_tick": predicted,
            "synced_tick": synced,
            "tick_drift": tick_drift,
            "time_drift": time_drift,
            "drift_corrected": corrected
        }


class SafeSyncEngine(SyncEngine):
    """Sync engine with comprehensive error handling and validation.

    Extends SyncEngine with additional safety checks including:
    - Timeout handling for tick queries
    - Tick value validation (sanity checks)
    - Automatic reconnection on connection loss
    - Connection state monitoring

    This is the recommended implementation for production use.
    """

    def __init__(
        self,
        tick_source: ITickSource,
        polling_interval: float = 0.25,
        tick_rate: int = 64,
        query_timeout: float = 2.0,
        min_valid_tick: int = 0,
        max_valid_tick: int = 1_000_000
    ):
        """Initialize the safe sync engine.

        Args:
            tick_source: Source of tick information
            polling_interval: Polling interval in seconds (default: 0.25)
            tick_rate: Game tick rate in Hz (default: 64)
            query_timeout: Timeout for tick queries in seconds (default: 2.0)
            min_valid_tick: Minimum valid tick value (default: 0)
            max_valid_tick: Maximum valid tick value (default: 1,000,000)
        """
        super().__init__(tick_source, polling_interval, tick_rate)
        self.query_timeout = query_timeout
        self.min_valid_tick = min_valid_tick
        self.max_valid_tick = max_valid_tick

    async def _sync_with_server(self) -> None:
        """Sync with server with comprehensive error handling.

        Includes timeout handling, tick validation, and automatic
        reconnection on connection loss.
        """
        try:
            # Query with timeout
            server_tick = await asyncio.wait_for(
                self.tick_source.get_current_tick(),
                timeout=self.query_timeout
            )

            # Validate tick (sanity check)
            if server_tick < self.min_valid_tick or server_tick > self.max_valid_tick:
                print(f"[Sync] Invalid tick received: {server_tick} (expected {self.min_valid_tick}-{self.max_valid_tick})")
                return

            # Update state
            current_time = time.time()
            self._last_synced_tick = server_tick
            self._last_sync_time = current_time

        except asyncio.TimeoutError:
            print("[Sync] Server timeout - continuing with prediction")
        except ConnectionError as e:
            print(f"[Sync] Connection lost: {e} - attempting reconnect")
            try:
                await self.tick_source.connect()
            except Exception as reconnect_error:
                print(f"[Sync] Reconnection failed: {reconnect_error}")
        except Exception as e:
            print(f"[Sync] Unexpected error: {e}")
