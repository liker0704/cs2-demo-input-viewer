"""
Prediction Engine - Tick prediction for smooth interpolation.

This module provides tick prediction engines that interpolate between
network polls to provide smooth 60 FPS visualization despite polling
at only 2-4 Hz.

CS2 runs at 64 Hz (one tick every 15.625ms).
We poll network at 2-4 Hz (every 250-500ms).
The prediction engine predicts intermediate ticks for smooth visualization.
"""

import time
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from src.core.orchestrator import SyncEngine


class PredictionEngine:
    """Tick prediction engine for smooth interpolation between syncs.

    This engine predicts the current game tick based on:
    1. Last known server tick (from network poll)
    2. Time elapsed since last poll
    3. Known tick rate (64 Hz for CS2)

    It includes drift correction to handle:
    - Network latency variance
    - Clock drift between client/server
    - Demo playback speed changes
    """

    def __init__(self, sync_engine: 'SyncEngine', tick_rate: int = 64):
        """Initialize prediction engine.

        Args:
            sync_engine: Sync engine providing server tick updates
            tick_rate: Game tick rate in ticks per second (default: 64 for CS2)
        """
        self.sync_engine = sync_engine
        self.tick_rate = tick_rate
        self.tick_duration = 1.0 / tick_rate  # 15.625ms for 64 Hz

        # Prediction state
        self._predicted_tick = 0
        self._last_update_time = time.time()

    def get_current_tick(self) -> int:
        """Get current tick using prediction.

        Calculates predicted tick based on:
        - Last known server tick from sync engine
        - Time elapsed since last server update
        - Tick rate (ticks per second)

        Returns:
            int: Predicted current tick
        """
        # Get last known server tick
        server_tick = self.sync_engine.get_last_tick()

        if server_tick == 0:
            import logging
            logger = logging.getLogger(__name__)
            logger.debug("[Prediction] Server tick is 0, demo not loaded yet")
            return 0

        # Time since last server update
        server_time = self.sync_engine.get_last_update_time()
        time_elapsed = time.time() - server_time

        # Predict ticks elapsed
        ticks_elapsed = int(time_elapsed / self.tick_duration)

        # Calculate predicted tick
        predicted = server_tick + ticks_elapsed

        # Apply drift correction
        predicted = self._apply_drift_correction(predicted, server_tick)

        self._predicted_tick = predicted

        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f"[Prediction] server={server_tick}, elapsed={time_elapsed:.3f}s, "
                    f"predicted={predicted}, drift={predicted-server_tick}")

        return predicted

    def _apply_drift_correction(
        self,
        predicted: int,
        server_tick: int,
        max_drift: int = 10
    ) -> int:
        """Apply drift correction to prevent excessive prediction error.

        If the predicted tick drifts too far from the server tick,
        snap back to the server tick. This handles:
        - Demo pause/resume
        - Network hiccups
        - Playback speed changes

        Args:
            predicted: Predicted tick value
            server_tick: Last known server tick
            max_drift: Maximum allowed drift in ticks before snapping (default: 10)

        Returns:
            int: Corrected tick value
        """
        drift = abs(predicted - server_tick)

        if drift > max_drift:
            # Large drift detected, snap to server tick
            print(f"[Prediction] Large drift ({drift} ticks), snapping to server")
            return server_tick

        return predicted

    def get_drift(self) -> int:
        """Get current drift between prediction and server.

        Returns:
            int: Tick drift (positive = ahead of server, negative = behind)
        """
        server_tick = self.sync_engine.get_last_tick()
        return self._predicted_tick - server_tick

    def reset(self):
        """Reset prediction state.

        Useful when demo is reloaded or connection is reset.
        """
        self._predicted_tick = 0
        self._last_update_time = time.time()


class SmoothPredictionEngine(PredictionEngine):
    """Advanced prediction engine with smoothing for jumps and pauses.

    Extends basic prediction with:
    1. Jump detection - handles Shift+F2 demo seeking
    2. Pause detection - detects when demo is paused
    3. Smoothing window - averages recent ticks for stability
    """

    def __init__(self, sync_engine: 'SyncEngine', tick_rate: int = 64, smoothing_window: int = 5):
        """Initialize smooth prediction engine.

        Args:
            sync_engine: Sync engine providing server tick updates
            tick_rate: Game tick rate in ticks per second (default: 64)
            smoothing_window: Number of recent ticks to track (default: 5)
        """
        super().__init__(sync_engine, tick_rate)
        self.smoothing_window = smoothing_window
        self._tick_history: list[int] = []  # Recent tick measurements

    def get_current_tick(self) -> int:
        """Get smoothed predicted tick.

        Applies smoothing and detects anomalies like jumps and pauses.

        Returns:
            int: Smoothed predicted tick
        """
        # Get base prediction
        predicted = super().get_current_tick()

        # Add to history
        self._tick_history.append(predicted)

        # Keep only recent history
        if len(self._tick_history) > self.smoothing_window:
            self._tick_history.pop(0)

        # Detect jump (user pressed Shift+F2 to jump to tick)
        if len(self._tick_history) >= 2:
            jump_size = abs(self._tick_history[-1] - self._tick_history[-2])

            if jump_size > 100:  # Large jump detected (>100 ticks = ~1.5 seconds)
                print(f"[Prediction] Jump detected ({jump_size} ticks)")
                # Clear history and accept new tick
                self._tick_history = [predicted]
                return predicted

        # Detect pause
        if self._is_paused():
            print("[Prediction] Pause detected")
            return self._tick_history[-1] if self._tick_history else 0

        return predicted

    def _is_paused(self) -> bool:
        """Detect if demo is paused.

        A demo is considered paused if the last 3 ticks are identical AND > 0.
        (Tick 0 means demo not loaded, not paused)

        Returns:
            bool: True if demo appears to be paused
        """
        if len(self._tick_history) < 3:
            return False

        # If last 3 ticks are identical, likely paused
        recent = self._tick_history[-3:]
        all_same = len(set(recent)) == 1

        # Don't consider tick=0 as "paused" (it means demo not loaded yet)
        if all_same and recent[0] == 0:
            import logging
            logger = logging.getLogger(__name__)
            logger.debug(f"[Prediction] Tick history all 0s (demo not loaded), not paused: {recent}")
            return False

        if all_same:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"[Prediction] Pause detected - last 3 ticks identical: {recent}")

        return all_same

    def reset(self):
        """Reset prediction state and history."""
        super().reset()
        self._tick_history = []
