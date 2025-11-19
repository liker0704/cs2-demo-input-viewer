"""
Smart Tick Synchronization with Speed Detection.

This module provides advanced tick synchronization that:
- Calculates playback speed from tick history
- Accurately detects pause vs slow playback
- Uses demo_marktick (passive, no choppy playback)
- Provides speed-aware prediction
"""

import time
import logging
from typing import Optional, List, Tuple
from collections import deque

logger = logging.getLogger(__name__)


class TickMeasurement:
    """Single tick measurement with timestamp."""

    def __init__(self, tick: int, timestamp: float):
        self.tick = tick
        self.timestamp = timestamp

    def __repr__(self):
        return f"TickMeasurement(tick={self.tick}, time={self.timestamp:.3f})"


class SmartTickSync:
    """Smart tick synchronization with speed detection.

    This class tracks tick history over time and calculates:
    - Current playback speed (0.25x, 0.5x, 1.0x, 2.0x, etc.)
    - Pause state (accurately distinguishes from slow speed)
    - Predicted current tick using speed-aware interpolation

    It uses demo_marktick command which is passive (doesn't pause demo).
    """

    def __init__(
        self,
        tick_source,
        tick_rate: int = 64,
        history_size: int = 10,
        pause_threshold: int = 3,
        speed_calculation_window: int = 5
    ):
        """Initialize smart tick sync.

        Args:
            tick_source: Source of tick data (telnet client with demo_marktick)
            tick_rate: Game tick rate in Hz (default: 64)
            history_size: Number of measurements to keep in history (default: 10)
            pause_threshold: Number of identical ticks to consider paused (default: 3)
            speed_calculation_window: Number of measurements for speed calc (default: 5)
        """
        self.tick_source = tick_source
        self.tick_rate = tick_rate
        self.history_size = history_size
        self.pause_threshold = pause_threshold
        self.speed_calculation_window = speed_calculation_window

        # Tick history: recent measurements
        self._history: deque[TickMeasurement] = deque(maxlen=history_size)

        # Current state
        self._current_speed = 1.0  # Playback speed multiplier
        self._is_paused = False
        self._last_tick = 0
        self._last_update_time = 0.0

        logger.info(f"[SmartTickSync] Initialized (tick_rate={tick_rate}Hz, "
                   f"history={history_size}, pause_threshold={pause_threshold})")

    async def update(self) -> bool:
        """Update tick from source and recalculate speed.

        Returns:
            bool: True if update successful, False otherwise
        """
        try:
            # Get tick from source (demo_marktick - passive, no pause)
            tick = await self.tick_source.get_current_tick()
            current_time = time.time()

            # Add to history
            measurement = TickMeasurement(tick, current_time)
            self._history.append(measurement)

            logger.debug(f"[SmartTickSync] Measured: tick={tick} at t={current_time:.3f}")

            # Update state
            self._last_tick = tick
            self._last_update_time = current_time

            # Recalculate speed and pause state
            self._recalculate_speed()
            self._detect_pause()

            return True

        except Exception as e:
            logger.error(f"[SmartTickSync] Update error: {e}", exc_info=True)
            return False

    def _recalculate_speed(self):
        """Recalculate playback speed from tick history.

        Speed is calculated as:
        speed = (tick_diff / time_diff) / tick_rate

        We use linear regression over the last N measurements for stability.

        Edge cases handled:
        - Tick jumps (Shift+F2 goto): Discard measurements with sudden large jumps
        - Outliers: Discard speed measurements far from recent average
        """
        if len(self._history) < 2:
            # Not enough data
            self._current_speed = 1.0
            return

        # Use last N measurements for speed calculation
        window_size = min(self.speed_calculation_window, len(self._history))
        recent = list(self._history)[-window_size:]

        # Calculate average speed over window
        # Use oldest and newest measurement for stability
        oldest = recent[0]
        newest = recent[-1]

        tick_diff = newest.tick - oldest.tick
        time_diff = newest.timestamp - oldest.timestamp

        # Avoid division by zero
        if time_diff < 0.01:
            # Too short time interval, keep previous speed
            logger.debug(f"[SmartTickSync] Time diff too small ({time_diff:.3f}s), keeping speed={self._current_speed:.2f}x")
            return

        # Edge Case 1: Detect tick jumps (Shift+F2 goto)
        # If tick_diff is way larger than expected, likely a jump
        if len(self._history) >= 3:
            expected_diff = self.tick_rate * time_diff * self._current_speed
            if abs(tick_diff) > abs(expected_diff) * 5:
                logger.warning(f"[SmartTickSync] Tick jump detected: {tick_diff} ticks "
                              f"(expected ~{expected_diff:.0f}), discarding measurement")
                # Remove the newest measurement that caused the jump
                self._history.pop()
                return

        # Calculate tick rate (ticks per second)
        measured_tick_rate = tick_diff / time_diff

        # Calculate speed multiplier
        speed = measured_tick_rate / self.tick_rate

        # Clamp to reasonable range (0.05x - 5.0x)
        speed = max(0.05, min(5.0, speed))

        # Edge Case 2: Outlier detection
        # If speed differs too much from current average, it might be an outlier
        if self._is_outlier(speed, threshold=0.5):
            logger.warning(f"[SmartTickSync] Outlier detected: {speed:.2f}x "
                          f"(current avg: {self._current_speed:.2f}x), discarding")
            return

        # Smooth speed changes (exponential moving average)
        alpha = 0.3  # Smoothing factor
        self._current_speed = alpha * speed + (1 - alpha) * self._current_speed

        logger.debug(f"[SmartTickSync] Speed calculation: "
                    f"tick_diff={tick_diff}, time_diff={time_diff:.3f}s, "
                    f"measured_rate={measured_tick_rate:.1f} tps, "
                    f"speed={speed:.2f}x, smoothed={self._current_speed:.2f}x")

    def _is_outlier(self, speed: float, threshold: float = 0.5) -> bool:
        """Check if speed measurement is an outlier.

        An outlier is a measurement that differs significantly from the
        current average, which might indicate measurement error or
        temporary glitch.

        Args:
            speed: Speed measurement to check
            threshold: Maximum allowed deviation (default: 0.5x)

        Returns:
            bool: True if outlier, False otherwise
        """
        # Need at least some history to compare
        if len(self._history) < 3:
            return False

        # Calculate deviation from current speed
        deviation = abs(speed - self._current_speed)

        # If deviation exceeds threshold, it's an outlier
        return deviation > threshold

    def _detect_pause(self):
        """Detect if demo is paused.

        Demo is paused if:
        1. Last N ticks are identical AND > 0
        2. Time has passed between measurements (not just no updates)

        This distinguishes pause from:
        - Demo not loaded (tick=0)
        - Very slow playback (ticks still change, just slowly)
        """
        if len(self._history) < self.pause_threshold:
            self._is_paused = False
            return

        # Get last N measurements
        recent = list(self._history)[-self.pause_threshold:]

        # Check if all ticks are identical
        ticks = [m.tick for m in recent]
        all_same = len(set(ticks)) == 1
        tick_value = ticks[0]

        # Check time has passed
        time_diff = recent[-1].timestamp - recent[0].timestamp

        # Pause detection logic:
        # - All ticks same AND tick > 0 AND time passed
        if all_same and tick_value > 0 and time_diff > 0.1:
            if not self._is_paused:
                logger.warning(f"[SmartTickSync] PAUSE DETECTED: {self.pause_threshold} identical ticks "
                              f"({tick_value}) over {time_diff:.2f}s")
            self._is_paused = True
        else:
            if self._is_paused:
                logger.info(f"[SmartTickSync] RESUME DETECTED: ticks changing again")
            self._is_paused = False

        # Special case: tick=0 means demo not loaded
        if tick_value == 0:
            logger.debug(f"[SmartTickSync] Tick is 0 (demo not loaded), not paused")
            self._is_paused = False

    def get_current_speed(self) -> float:
        """Get current playback speed multiplier.

        Returns:
            float: Speed multiplier (0.25, 0.5, 1.0, 2.0, etc.)
        """
        return self._current_speed

    def is_paused(self) -> bool:
        """Check if demo is currently paused.

        Returns:
            bool: True if paused, False if playing
        """
        return self._is_paused

    def get_last_tick(self) -> int:
        """Get last known tick.

        Returns:
            int: Last tick from source (file tick from demo_marktick)
        """
        return self._last_tick

    def get_last_update_time(self) -> float:
        """Get timestamp of last update.

        Returns:
            float: Unix timestamp of last update
        """
        return self._last_update_time

    def predict_current_tick(self) -> int:
        """Predict current tick using speed-aware interpolation.

        This method predicts the current tick by:
        1. Taking last known tick from source
        2. Calculating time elapsed since last update
        3. Predicting ticks elapsed using current speed
        4. Returning predicted tick

        If paused, returns last known tick (no prediction).

        Returns:
            int: Predicted current tick
        """
        # If paused, return last known tick
        if self._is_paused:
            logger.debug(f"[SmartTickSync] Demo paused, returning last tick: {self._last_tick}")
            return self._last_tick

        # If no data yet, return 0
        if self._last_tick == 0:
            logger.debug(f"[SmartTickSync] No data yet (tick=0)")
            return 0

        # Calculate time elapsed since last update
        time_elapsed = time.time() - self._last_update_time

        # Predict ticks elapsed using current speed
        # ticks_per_second = tick_rate * speed
        ticks_per_second = self.tick_rate * self._current_speed
        ticks_elapsed = int(time_elapsed * ticks_per_second)

        # Calculate predicted tick
        predicted_tick = self._last_tick + ticks_elapsed

        logger.debug(f"[SmartTickSync] Prediction: last={self._last_tick}, "
                    f"elapsed={time_elapsed:.3f}s, speed={self._current_speed:.2f}x, "
                    f"predicted={predicted_tick}")

        return predicted_tick

    def get_status_info(self) -> dict:
        """Get detailed status information for debugging.

        Returns:
            dict: Status information including speed, pause state, history
        """
        return {
            "current_speed": self._current_speed,
            "is_paused": self._is_paused,
            "last_tick": self._last_tick,
            "last_update_time": self._last_update_time,
            "history_size": len(self._history),
            "history": [
                {"tick": m.tick, "time": m.timestamp}
                for m in self._history
            ]
        }
