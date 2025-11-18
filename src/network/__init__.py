"""Network layer for CS2 demo synchronization.

This module provides components for synchronizing the input visualizer
with CS2 demo playback through the network console (netcon).

Main components:
- CS2TelnetClient: Connects to CS2's netcon port to query tick information
- RobustTelnetClient: Telnet client with automatic reconnection
- SyncEngine: Manages periodic tick polling and prediction
- PredictionEngine: Provides tick prediction with drift correction
- SafeSyncEngine: Sync engine with comprehensive error handling
- CS2PlayerTracker: Tracks which player's inputs to visualize
- ManualPlayerTracker: Simple manual player selection for testing

Example usage:
    >>> import asyncio
    >>> from network import RobustTelnetClient, SyncEngine, CS2PlayerTracker
    >>>
    >>> async def main():
    ...     # Setup components
    ...     telnet = RobustTelnetClient()
    ...     sync = SyncEngine(telnet)
    ...     tracker = CS2PlayerTracker()
    ...
    ...     # Connect and start
    ...     if await telnet.connect_with_retry():
    ...         tracker.set_player("STEAM_1:0:123456789")
    ...         await sync.start()
    ...
    ...         # Use in render loop
    ...         tick = sync.get_predicted_tick()
    ...         player = await tracker.get_current_player()
    ...
    ...         await telnet.disconnect()
    >>>
    >>> asyncio.run(main())
"""

from network.telnet_client import (
    CS2TelnetClient,
    RobustTelnetClient,
)

from network.sync_engine import (
    SyncEngine,
    PredictionEngine,
    SafeSyncEngine,
)

from network.player_tracker import (
    CS2PlayerTracker,
    AutoPlayerTracker,
    ManualPlayerTracker,
    DefaultPlayerTracker,
)


__all__ = [
    # Telnet clients
    "CS2TelnetClient",
    "RobustTelnetClient",
    # Sync engines
    "SyncEngine",
    "PredictionEngine",
    "SafeSyncEngine",
    # Player trackers
    "CS2PlayerTracker",
    "AutoPlayerTracker",
    "ManualPlayerTracker",
    "DefaultPlayerTracker",
]
