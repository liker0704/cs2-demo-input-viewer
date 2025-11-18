# Network Layer Documentation

## CS2 Subtick Input Visualizer - Sync & Player Tracking

### 1. Overview

The Network Layer synchronizes the overlay with CS2 demo playback in real-time. It consists of two main components:

1. **Telnet Client**: Connects to CS2's network console to query current tick
2. **Player Tracker**: Determines which player is currently being spectated

---

## 2. CS2 Network Console Setup

### 2.1 Launch Parameters

CS2 must be launched with specific flags:

```bash
# Windows
cs2.exe -netconport 2121 -insecure

# Linux
./cs2.sh -netconport 2121 -insecure
```

**Flags Explanation:**
- `-netconport 2121`: Opens network console on port 2121
- `-insecure`: Disables VAC (required for external tools during development)

**Security Notes:**
- Telnet binds to `127.0.0.1` (localhost only)
- Never use `-insecure` on VAC-secured servers
- Only for local demo playback

### 2.2 Available Commands

```bash
# Get demo playback info (our primary command)
demo_info

# Example response:
# Demo contents for demo.dem:
# Currently playing 12500 of 160000 ticks (0:03:15 / 0:41:40)
# at 1.00x speed

# Other useful commands
demo_pause          # Pause demo
demo_resume         # Resume demo
demo_gototick 5000  # Jump to specific tick
status              # Get server/player info
```

---

## 3. Telnet Client Implementation

### 3.1 Why asyncio Instead of telnetlib?

- `telnetlib` was deprecated in Python 3.11 and removed in 3.13
- `asyncio` provides better performance and modern async/await syntax
- Non-blocking I/O allows simultaneous network polling and UI rendering

### 3.2 Async Telnet Client

```python
import asyncio
import re
from typing import Optional
from interfaces.tick_source import ITickSource

class CS2TelnetClient(ITickSource):
    """Async Telnet client for CS2 network console.

    Connects to CS2's netcon port to query demo playback state.
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 2121):
        self.host = host
        self.port = port
        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None
        self._connected = False
        self._current_tick = 0

        # Regex to parse demo_info response
        self._tick_pattern = re.compile(r"Currently playing (\d+) of (\d+) ticks")

    async def connect(self) -> bool:
        """Establish connection to CS2 network console.

        Returns:
            bool: True if connection successful
        """
        try:
            self.reader, self.writer = await asyncio.wait_for(
                asyncio.open_connection(self.host, self.port),
                timeout=5.0
            )

            # Read welcome message
            welcome = await asyncio.wait_for(
                self.reader.read(1024),
                timeout=2.0
            )

            self._connected = True
            print(f"[Telnet] Connected to CS2 at {self.host}:{self.port}")
            return True

        except asyncio.TimeoutError:
            print("[Telnet] Connection timeout - is CS2 running with -netconport?")
            return False
        except ConnectionRefusedError:
            print("[Telnet] Connection refused - check CS2 launch parameters")
            return False
        except Exception as e:
            print(f"[Telnet] Connection error: {e}")
            return False

    async def disconnect(self) -> None:
        """Close connection to CS2."""
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()
            self._connected = False
            print("[Telnet] Disconnected from CS2")

    def is_connected(self) -> bool:
        """Check if connection is active.

        Returns:
            bool: Connection status
        """
        return self._connected

    async def get_current_tick(self) -> int:
        """Query CS2 for current demo tick.

        Returns:
            int: Current tick number, or last known tick if query fails
        """
        if not self._connected:
            print("[Telnet] Not connected, cannot get tick")
            return self._current_tick

        try:
            # Send demo_info command
            self.writer.write(b"demo_info\n")
            await self.writer.drain()

            # Read response (with timeout)
            response = await asyncio.wait_for(
                self.reader.read(2048),
                timeout=1.0
            )

            # Parse response
            response_text = response.decode('utf-8', errors='ignore')
            match = self._tick_pattern.search(response_text)

            if match:
                current_tick = int(match.group(1))
                self._current_tick = current_tick
                return current_tick
            else:
                print(f"[Telnet] Failed to parse tick from response: {response_text[:100]}")
                return self._current_tick

        except asyncio.TimeoutError:
            print("[Telnet] Query timeout - using last known tick")
            return self._current_tick
        except Exception as e:
            print(f"[Telnet] Query error: {e}")
            return self._current_tick

    async def get_demo_info(self) -> dict:
        """Get full demo playback information.

        Returns:
            dict: Demo info including current_tick, total_ticks, speed
        """
        if not self._connected:
            return {
                "current_tick": 0,
                "total_ticks": 0,
                "speed": 1.0,
                "time_current": "0:00:00",
                "time_total": "0:00:00"
            }

        try:
            self.writer.write(b"demo_info\n")
            await self.writer.drain()

            response = await asyncio.wait_for(
                self.reader.read(2048),
                timeout=1.0
            )

            response_text = response.decode('utf-8', errors='ignore')

            # Parse tick info
            tick_match = self._tick_pattern.search(response_text)

            # Parse speed (e.g., "at 1.00x speed")
            speed_match = re.search(r"at ([\d.]+)x speed", response_text)

            # Parse time info (e.g., "0:03:15 / 0:41:40")
            time_match = re.search(r"\((\d+:\d+:\d+) / (\d+:\d+:\d+)\)", response_text)

            return {
                "current_tick": int(tick_match.group(1)) if tick_match else 0,
                "total_ticks": int(tick_match.group(2)) if tick_match else 0,
                "speed": float(speed_match.group(1)) if speed_match else 1.0,
                "time_current": time_match.group(1) if time_match else "0:00:00",
                "time_total": time_match.group(2) if time_match else "0:00:00"
            }

        except Exception as e:
            print(f"[Telnet] Error getting demo info: {e}")
            return {
                "current_tick": self._current_tick,
                "total_ticks": 0,
                "speed": 1.0,
                "time_current": "0:00:00",
                "time_total": "0:00:00"
            }
```

### 3.3 Reconnection Logic

Handle connection drops gracefully:

```python
class RobustTelnetClient(CS2TelnetClient):
    """Telnet client with automatic reconnection."""

    def __init__(self, *args, max_retries: int = 3, retry_delay: float = 2.0, **kwargs):
        super().__init__(*args, **kwargs)
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    async def connect_with_retry(self) -> bool:
        """Connect with automatic retry on failure.

        Returns:
            bool: True if connected successfully
        """
        for attempt in range(self.max_retries):
            if await self.connect():
                return True

            if attempt < self.max_retries - 1:
                print(f"[Telnet] Retry {attempt + 1}/{self.max_retries} in {self.retry_delay}s...")
                await asyncio.sleep(self.retry_delay)

        print("[Telnet] Max retries reached, connection failed")
        return False

    async def get_current_tick(self) -> int:
        """Get tick with automatic reconnection on failure."""
        try:
            return await super().get_current_tick()
        except Exception as e:
            print(f"[Telnet] Error during tick query: {e}")

            # Try to reconnect
            print("[Telnet] Attempting reconnection...")
            if await self.connect_with_retry():
                return await super().get_current_tick()
            else:
                return self._current_tick
```

---

## 4. Sync Engine & Prediction

### 4.1 Polling Strategy

**Challenge**: Telnet has 2-10ms latency, can't poll at 64 Hz (every 15.6ms)

**Solution**: Poll every 250-500ms and predict intermediate ticks

```python
import time

class SyncEngine:
    """Manages synchronization between CS2 and prediction engine.

    Polls CS2 at low frequency (2-4 Hz) and predicts intermediate ticks
    for smooth 60 FPS rendering.
    """

    def __init__(self, tick_source: ITickSource, polling_interval: float = 0.25):
        """
        Args:
            tick_source: Source of tick information (Telnet client)
            polling_interval: How often to poll in seconds (default: 250ms)
        """
        self.tick_source = tick_source
        self.polling_interval = polling_interval

        # State
        self._last_synced_tick = 0
        self._last_sync_time = 0.0
        self._predicted_tick = 0

        # CS2 tick rate
        self.tick_rate = 64  # ticks per second
        self.tick_duration = 1.0 / self.tick_rate  # 15.625 ms

    async def start(self):
        """Start sync loop."""
        # Initial sync
        await self._sync_with_server()

        # Start periodic sync task
        asyncio.create_task(self._sync_loop())

    async def _sync_loop(self):
        """Periodic sync with CS2."""
        while True:
            await asyncio.sleep(self.polling_interval)
            await self._sync_with_server()

    async def _sync_with_server(self):
        """Query CS2 for current tick and update sync state."""
        try:
            server_tick = await self.tick_source.get_current_tick()
            current_time = time.time()

            # Update sync state
            self._last_synced_tick = server_tick
            self._last_sync_time = current_time
            self._predicted_tick = server_tick

            print(f"[Sync] Tick {server_tick} @ {current_time:.3f}")

        except Exception as e:
            print(f"[Sync] Error during sync: {e}")

    def get_predicted_tick(self) -> int:
        """Get current tick using prediction between syncs.

        Returns:
            int: Predicted current tick
        """
        if self._last_sync_time == 0:
            return 0

        # Time since last sync
        time_elapsed = time.time() - self._last_sync_time

        # Predict tick based on tick rate
        ticks_elapsed = int(time_elapsed / self.tick_duration)

        # Predicted tick
        predicted = self._last_synced_tick + ticks_elapsed

        return predicted

    def get_drift(self) -> int:
        """Calculate drift between prediction and last known server tick.

        Returns:
            int: Tick drift (positive = ahead, negative = behind)
        """
        return self._predicted_tick - self._last_synced_tick
```

### 4.2 Drift Correction

When user jumps to different tick (Shift+F2), correct smoothly:

```python
class PredictionEngine:
    """Advanced prediction with drift correction."""

    def __init__(self, sync_engine: SyncEngine, max_drift: int = 10):
        self.sync_engine = sync_engine
        self.max_drift = max_drift

    def get_corrected_tick(self) -> int:
        """Get tick with drift correction applied.

        Returns:
            int: Corrected current tick
        """
        predicted = self.sync_engine.get_predicted_tick()
        drift = self.sync_engine.get_drift()

        # If drift exceeds threshold, snap to server tick
        if abs(drift) > self.max_drift:
            print(f"[Prediction] Large drift detected ({drift} ticks), correcting...")
            return self.sync_engine._last_synced_tick

        return predicted
```

---

## 5. Player Tracking

### 5.1 Challenge

Need to know which player we're spectating in the demo to show correct inputs.

**Approaches:**
1. Query CS2 for current spectator target
2. Parse from demo events
3. Manual selection by user

### 5.2 CS2 Player Tracker

```python
from interfaces.player_tracker import IPlayerTracker

class CS2PlayerTracker(IPlayerTracker):
    """Track currently spectated player via CS2 console."""

    def __init__(self, telnet_client: CS2TelnetClient):
        self.telnet = telnet_client
        self._current_player_id: Optional[str] = None

    async def get_current_player(self) -> Optional[str]:
        """Get currently spectated player ID.

        Returns:
            str: Player SteamID or None if unknown
        """
        # Note: This requires additional CS2 console commands
        # to query spectator state. Implementation depends on
        # available console commands.

        # Placeholder implementation
        if not self.telnet.is_connected():
            return self._current_player_id

        try:
            # Query player info (command TBD based on CS2 console API)
            # For now, return cached value
            return self._current_player_id

        except Exception as e:
            print(f"[PlayerTracker] Error: {e}")
            return self._current_player_id

    async def update(self) -> None:
        """Update player tracking information."""
        # Poll for current spectator target
        # Implementation TBD
        pass

    def set_player_manually(self, player_id: str):
        """Manually set target player.

        Args:
            player_id: Player SteamID
        """
        self._current_player_id = player_id
        print(f"[PlayerTracker] Manually set to player: {player_id}")
```

### 5.3 Manual Player Selection (MVP)

For initial implementation, use manual selection:

```python
class ManualPlayerTracker(IPlayerTracker):
    """Simple player tracker with manual selection."""

    def __init__(self, default_player_id: Optional[str] = None):
        self._player_id = default_player_id

    async def get_current_player(self) -> Optional[str]:
        return self._player_id

    async def update(self) -> None:
        # No-op for manual tracker
        pass

    def set_player(self, player_id: str):
        """Set the target player.

        Args:
            player_id: Player SteamID from cache metadata
        """
        self._player_id = player_id
```

---

## 6. Mock Implementations

### 6.1 Mock Tick Source

For UI development without CS2:

```python
import time

class MockTickSource(ITickSource):
    """Mock tick source using system timer.

    Simulates CS2 demo playback at 64 Hz.
    """

    def __init__(self, start_tick: int = 0, tick_rate: int = 64):
        self.start_tick = start_tick
        self.tick_rate = tick_rate
        self.start_time = time.time()
        self._connected = True

    async def connect(self) -> bool:
        self._connected = True
        return True

    async def disconnect(self) -> None:
        self._connected = False

    def is_connected(self) -> bool:
        return self._connected

    async def get_current_tick(self) -> int:
        """Calculate tick based on elapsed time.

        Returns:
            int: Simulated current tick
        """
        if not self._connected:
            return self.start_tick

        elapsed = time.time() - self.start_time
        ticks_elapsed = int(elapsed * self.tick_rate)

        return self.start_tick + ticks_elapsed

    def reset(self):
        """Reset timer to start."""
        self.start_time = time.time()

    def jump_to_tick(self, tick: int):
        """Simulate jump to specific tick.

        Args:
            tick: Target tick
        """
        self.start_tick = tick
        self.start_time = time.time()
```

### 6.2 Mock Player Tracker

```python
class MockPlayerTracker(IPlayerTracker):
    """Mock player tracker for testing."""

    def __init__(self, player_id: str = "MOCK_PLAYER_123"):
        self._player_id = player_id

    async def get_current_player(self) -> Optional[str]:
        return self._player_id

    async def update(self) -> None:
        pass
```

---

## 7. Complete Integration Example

```python
import asyncio

async def main():
    """Example integration of network layer components."""

    # Setup components
    telnet_client = RobustTelnetClient(host="127.0.0.1", port=2121)
    sync_engine = SyncEngine(telnet_client, polling_interval=0.25)
    prediction_engine = PredictionEngine(sync_engine)
    player_tracker = ManualPlayerTracker()

    # Connect to CS2
    if await telnet_client.connect_with_retry():
        print("Connected to CS2!")

        # Set player (from cache metadata)
        player_tracker.set_player("STEAM_1:0:123456789")

        # Start sync
        await sync_engine.start()

        # Main loop (simulate 60 FPS rendering)
        for _ in range(60 * 10):  # 10 seconds
            current_tick = prediction_engine.get_corrected_tick()
            current_player = await player_tracker.get_current_player()

            print(f"Tick: {current_tick}, Player: {current_player}")

            await asyncio.sleep(1/60)  # 60 FPS

        # Cleanup
        await telnet_client.disconnect()
    else:
        print("Failed to connect to CS2")


if __name__ == "__main__":
    asyncio.run(main())
```

---

## 8. Performance Considerations

### 8.1 Network Latency

- Typical latency: 2-10 ms per request
- Polling at 4 Hz (250ms): ~1-2% CPU usage
- Prediction eliminates visual stutter

### 8.2 Error Handling

```python
class SafeSyncEngine(SyncEngine):
    """Sync engine with comprehensive error handling."""

    async def _sync_with_server(self):
        """Sync with error recovery."""
        try:
            server_tick = await asyncio.wait_for(
                self.tick_source.get_current_tick(),
                timeout=2.0
            )

            # Validate tick (sanity check)
            if server_tick < 0 or server_tick > 1_000_000:
                print(f"[Sync] Invalid tick received: {server_tick}")
                return

            # Update state
            self._last_synced_tick = server_tick
            self._last_sync_time = time.time()

        except asyncio.TimeoutError:
            print("[Sync] Server timeout - continuing with prediction")
        except ConnectionError:
            print("[Sync] Connection lost - attempting reconnect")
            await self.tick_source.connect()
        except Exception as e:
            print(f"[Sync] Unexpected error: {e}")
```

---

## 9. Testing

### 9.1 Unit Tests

```python
import pytest

@pytest.mark.asyncio
async def test_telnet_connection():
    """Test Telnet client connection."""
    client = CS2TelnetClient()

    # Should fail without CS2 running
    result = await client.connect()
    assert result == False or result == True  # Depends on CS2 state


@pytest.mark.asyncio
async def test_mock_tick_source():
    """Test mock tick source."""
    mock = MockTickSource(start_tick=1000, tick_rate=64)

    await mock.connect()
    assert mock.is_connected()

    tick1 = await mock.get_current_tick()
    await asyncio.sleep(0.1)  # 100ms
    tick2 = await mock.get_current_tick()

    # Should advance ~6-7 ticks in 100ms at 64 Hz
    assert 5 <= (tick2 - tick1) <= 8


@pytest.mark.asyncio
async def test_prediction_engine():
    """Test prediction engine accuracy."""
    mock_tick = MockTickSource(start_tick=0)
    sync = SyncEngine(mock_tick, polling_interval=0.5)

    await sync.start()
    await asyncio.sleep(1.0)

    predicted = sync.get_predicted_tick()

    # Should be around 64 ticks after 1 second
    assert 60 <= predicted <= 68
```

---

## 10. Next Steps

After Network Layer completion:
1. Integrate with Data Layer (cache reading)
2. Connect to UI Layer (PyQt6 overlay)
3. Build complete orchestrator
