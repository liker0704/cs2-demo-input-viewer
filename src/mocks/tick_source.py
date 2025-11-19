"""Mock tick source implementation for testing and development.

This module provides a timer-based mock tick source that simulates
CS2 demo playback without requiring a real game connection.
"""

import time
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from interfaces.tick_source import ITickSource


class MockTickSource(ITickSource):
    """Mock tick source using system timer to simulate tick progression.

    This implementation simulates CS2's tick progression using the system clock,
    making it ideal for UI development and testing without a real game connection.

    The tick counter progresses at the configured tick rate (default 64 Hz),
    starting from a configurable start tick.

    Attributes:
        start_tick: Initial tick number when timer starts
        tick_rate: Ticks per second (e.g., 64 for CS2 servers)
        start_time: Unix timestamp when connection was established
        _connected: Current connection state

    Example:
        >>> source = MockTickSource(start_tick=1000, tick_rate=64)
        >>> await source.connect()
        >>> tick = await source.get_current_tick()
        >>> print(f"Current tick: {tick}")
    """

    def __init__(self, start_tick: int = 0, tick_rate: int = 64):
        """Initialize mock tick source.

        Args:
            start_tick: Starting tick number (default: 0)
            tick_rate: Ticks per second, matching server tickrate (default: 64)
        """
        self.start_tick = start_tick
        self.tick_rate = tick_rate
        self.start_time: float = 0.0
        self._connected: bool = False

    async def connect(self) -> bool:
        """Establish mock connection and start timer.

        Records the current system time as the reference point for
        tick calculations.

        Returns:
            bool: Always returns True for mock connection
        """
        self.start_time = time.time()
        self._connected = True
        return True

    async def disconnect(self) -> None:
        """Disconnect from mock tick source.

        Resets the connection state and timer.
        """
        self._connected = False
        self.start_time = 0.0

    def is_connected(self) -> bool:
        """Check if mock connection is active.

        Returns:
            bool: Current connection state
        """
        return self._connected

    async def get_current_tick(self) -> int:
        """Get current tick based on elapsed time.

        Calculates the current tick by measuring elapsed time since
        connection and multiplying by tick rate.

        Formula:
            current_tick = start_tick + (elapsed_seconds * tick_rate)

        Returns:
            int: Current tick number

        Raises:
            ConnectionError: If not connected (start_time not set)

        Example:
            If connected at time T=0 with start_tick=1000 and tick_rate=64:
            - At T=1.0s: returns 1064 (1000 + 1*64)
            - At T=2.0s: returns 1128 (1000 + 2*64)
        """
        if not self._connected:
            raise ConnectionError("Not connected to mock tick source")

        elapsed_time = time.time() - self.start_time
        ticks_elapsed = int(elapsed_time * self.tick_rate)
        return self.start_tick + ticks_elapsed
