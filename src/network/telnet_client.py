"""Asyncio-based telnet client for CS2 network console.

This module provides an implementation of ITickSource that connects to CS2's
network console (netcon) to query demo playback state in real-time.

The client connects to CS2's netcon port (default: 2121) and uses the
'demo_info' command to retrieve the current tick number during demo playback.
"""

import asyncio
import re
from typing import Optional

from ..interfaces.tick_source import ITickSource


class CS2TelnetClient(ITickSource):
    """Async telnet client for CS2 network console.

    Connects to CS2's netcon port to query demo playback state. CS2 must be
    launched with the -netconport flag:

        cs2.exe -netconport 2121 -insecure

    The client sends 'demo_info' commands and parses the response to extract
    the current tick number.

    Example response:
        Demo contents for demo.dem:
        Currently playing 12500 of 160000 ticks (0:03:15 / 0:41:40)
        at 1.00x speed

    Attributes:
        host: Hostname or IP address (default: 127.0.0.1)
        port: Network console port (default: 2121)
        reader: AsyncIO stream reader for receiving data
        writer: AsyncIO stream writer for sending commands
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 2121):
        """Initialize the telnet client.

        Args:
            host: CS2 server hostname/IP (default: localhost)
            port: Network console port (default: 2121)
        """
        self.host = host
        self.port = port
        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None
        self._connected = False
        self._current_tick = 0

        # Output buffering for monitoring console output
        self.output_buffer: list[str] = []
        self.buffer_size = 100  # Keep last 100 lines

        # Regex pattern to parse demo_info response
        # Matches: "Currently playing 12500 of 160000 ticks"
        self._tick_pattern = re.compile(r"Currently playing (\d+) of \d+ ticks")

    async def connect(self) -> bool:
        """Establish connection to CS2 network console.

        Attempts to connect to the CS2 netcon port with a 5-second timeout.
        Reads the welcome message after connecting.

        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            # Open connection with timeout
            self.reader, self.writer = await asyncio.wait_for(
                asyncio.open_connection(self.host, self.port),
                timeout=5.0
            )

            # Read welcome message (CS2 sends initial prompt)
            # Note: CS2 might not send a welcome message immediately, so we handle timeout
            try:
                welcome = await asyncio.wait_for(
                    self.reader.read(1024),
                    timeout=2.0
                )
                print(f"[Telnet] Received welcome: {repr(welcome.decode('utf-8', errors='ignore'))}")
            except asyncio.TimeoutError:
                print("[Telnet] No welcome message received (timeout), but connected.")

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
        """Close connection to CS2 network console.

        Cleanly closes the writer stream and waits for it to close.
        """
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()
            self._connected = False
            print("[Telnet] Disconnected from CS2")

    def is_connected(self) -> bool:
        """Check if connection is active.

        Returns:
            bool: True if connected to CS2, False otherwise
        """
        return self._connected

    async def get_current_tick(self) -> int:
        """Get current demo playback tick (passive).

        This method NEVER actively polls CS2. It only returns the last known tick
        that was synced via force_sync_tick(). The prediction engine will interpolate
        between sync points.

        Returns:
            int: Last known tick from most recent sync
        """
        return self._current_tick

    async def force_sync_tick(self) -> int:
        """Force synchronization using get_demo_info().

        This should be used sparingly, only when we need to resync
        (e.g., after connection loss or large drift).

        Uses get_demo_info() which is PASSIVE (no pause/resume) and reliable.

        Returns:
            int: Current tick number from forced sync
        """
        if not self._connected:
            print("[Telnet] Not connected, cannot force sync")
            return self._current_tick

        try:
            import logging
            logger = logging.getLogger(__name__)
            logger.info("[Telnet] Force syncing tick via demo_info...")

            # Use get_demo_info() - passive, reliable, no freeze
            demo_info = await self.get_demo_info()
            current_tick = demo_info["current_tick"]

            # Validate tick > 0 before updating
            if current_tick > 0:
                self._current_tick = current_tick
                logger.info(f"[Telnet] Force sync successful: tick {current_tick} (speed: {demo_info['speed']}x)")
                print(f"[Telnet] Force sync successful: tick {current_tick}")
                return current_tick
            else:
                logger.warning(f"[Telnet] Force sync got invalid tick: {current_tick} (keeping previous: {self._current_tick})")
                print(f"[Telnet] Force sync got tick 0 (demo not playing?), keeping previous tick: {self._current_tick}")
                return self._current_tick

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"[Telnet] Force sync error: {e}", exc_info=True)
            print(f"[Telnet] Force sync error: {e}")
            import traceback
            traceback.print_exc()
            return self._current_tick

    async def _read_with_buffer(self, size: int) -> bytes:
        """Read from stream and accumulate in buffer.

        Args:
            size: Number of bytes to read

        Returns:
            bytes: Data read from stream
        """
        data = await self.reader.read(size)

        # Decode and add to buffer
        try:
            text = data.decode('utf-8', errors='ignore')
            lines = text.splitlines()

            for line in lines:
                if line.strip():  # Only add non-empty lines
                    self.output_buffer.append(line)

            # Maintain buffer size limit
            if len(self.output_buffer) > self.buffer_size:
                self.output_buffer = self.output_buffer[-self.buffer_size:]
        except Exception:
            pass  # Ignore buffer errors

        return data

    def get_buffer_content(self) -> str:
        """Get accumulated output from buffer.

        Returns:
            str: Concatenated buffer content with newlines
        """
        return '\n'.join(self.output_buffer)

    def clear_buffer(self) -> None:
        """Clear the output buffer."""
        self.output_buffer.clear()

    async def get_demo_info(self) -> dict:
        """Get full demo playback information.

        Sends 'demo_info' command and parses the complete response including
        current tick, total ticks, playback speed, and timestamps.

        Returns:
            dict: Dictionary containing:
                - current_tick (int): Current playback tick
                - total_ticks (int): Total ticks in demo
                - speed (float): Playback speed multiplier
                - time_current (str): Current time in HH:MM:SS format
                - time_total (str): Total time in HH:MM:SS format
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
            # Send demo_info command
            self.writer.write(b"demo_info\n")
            await self.writer.drain()

            # Read response with timeout
            response = await asyncio.wait_for(
                self.reader.read(2048),
                timeout=1.0
            )

            response_text = response.decode('utf-8', errors='ignore')

            # Parse tick info: "Currently playing 12500 of 160000 ticks"
            tick_match = self._tick_pattern.search(response_text)

            # Parse total ticks
            total_match = re.search(r"Currently playing \d+ of (\d+) ticks", response_text)

            # Parse speed: "at 1.00x speed"
            speed_match = re.search(r"at ([\d.]+)x speed", response_text)

            # Parse time info: "(0:03:15 / 0:41:40)"
            time_match = re.search(r"\((\d+:\d+:\d+) / (\d+:\d+:\d+)\)", response_text)

            return {
                "current_tick": int(tick_match.group(1)) if tick_match else 0,
                "total_ticks": int(total_match.group(1)) if total_match else 0,
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


class RobustTelnetClient(CS2TelnetClient):
    """Telnet client with automatic reconnection and exponential backoff.

    Extends CS2TelnetClient with retry logic for connecting and recovering
    from connection failures. Uses exponential backoff to avoid overwhelming
    the server during connection attempts.

    Attributes:
        max_retries: Maximum number of connection attempts
        retry_delay: Initial delay between retries (seconds)
        max_retry_delay: Maximum delay between retries (seconds)
    """

    def __init__(
        self,
        *args,
        max_retries: int = 3,
        retry_delay: float = 2.0,
        max_retry_delay: float = 10.0,
        **kwargs
    ):
        """Initialize robust telnet client.

        Args:
            max_retries: Maximum connection retry attempts (default: 3)
            retry_delay: Initial retry delay in seconds (default: 2.0)
            max_retry_delay: Maximum retry delay in seconds (default: 10.0)
            *args: Positional arguments for CS2TelnetClient
            **kwargs: Keyword arguments for CS2TelnetClient
        """
        super().__init__(*args, **kwargs)
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.max_retry_delay = max_retry_delay

    async def connect_with_retry(self) -> bool:
        """Connect with automatic retry and exponential backoff.

        Attempts to connect up to max_retries times, with exponentially
        increasing delays between attempts.

        Returns:
            bool: True if connected successfully, False otherwise
        """
        current_delay = self.retry_delay

        for attempt in range(self.max_retries):
            if await self.connect():
                return True

            if attempt < self.max_retries - 1:
                print(f"[Telnet] Retry {attempt + 1}/{self.max_retries} in {current_delay:.1f}s...")
                await asyncio.sleep(current_delay)

                # Exponential backoff
                current_delay = min(current_delay * 2, self.max_retry_delay)

        print("[Telnet] Max retries reached, connection failed")
        return False

    async def get_current_tick(self) -> int:
        """Get tick with automatic reconnection on failure.

        Attempts to query the current tick. If the connection is lost,
        automatically attempts to reconnect before retrying the query.

        Returns:
            int: Current tick number, or last known tick if reconnection fails
        """
        # First, try normal query
        if self._connected:
            try:
                return await super().get_current_tick()
            except Exception as e:
                print(f"[Telnet] Error during tick query: {e}")
                self._connected = False

        # If not connected or query failed, try to reconnect
        if not self._connected:
            print("[Telnet] Attempting reconnection...")
            if await self.connect_with_retry():
                try:
                    return await super().get_current_tick()
                except Exception:
                    pass

        # Return last known tick if all else fails
        return self._current_tick
