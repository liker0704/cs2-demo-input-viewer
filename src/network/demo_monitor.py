"""Demo file monitoring for auto-detection of loaded demos.

This module monitors CS2 telnet output to detect when a demo is loaded
or when the user switches to a different demo.
"""

import re
from pathlib import Path
from typing import Optional, Callable, Awaitable
from .telnet_client import CS2TelnetClient


class DemoMonitor:
    """Monitors CS2 for demo load events.

    Uses telnet client's output buffer to detect when a demo is loaded
    by looking for specific console messages.

    Attributes:
        telnet_client: CS2 telnet connection
        current_demo: Currently loaded demo path
        on_demo_loaded: Callback for demo load events
    """

    # Regex patterns for demo detection
    DEMO_LOAD_PATTERN = re.compile(r"Playing demo from (.+\.dem)")
    DEMO_INFO_PATTERN = re.compile(r"Demo contents for (.+\.dem):")

    def __init__(self, telnet_client: CS2TelnetClient, cs2_dir: Optional[Path] = None):
        """Initialize demo monitor.

        Args:
            telnet_client: Connected CS2 telnet client
            cs2_dir: CS2 installation directory (csgo folder) for resolving relative paths
        """
        self.telnet_client = telnet_client
        self.cs2_dir = Path(cs2_dir) if cs2_dir else None
        self.current_demo: Optional[Path] = None
        self.on_demo_loaded: Optional[Callable[[Path], Awaitable[None]]] = None

    async def update(self) -> None:
        """Check for demo load events in telnet buffer."""
        if not self.telnet_client.is_connected():
            return

        # Get buffered console output
        buffer_content = self.telnet_client.get_buffer_content()

        # Check for demo load messages
        demo_path = self._extract_demo_path(buffer_content)

        if demo_path and demo_path != self.current_demo:
            print(f"[DemoMonitor] Detected demo load: {demo_path}")
            self.current_demo = demo_path

            # Trigger callback
            if self.on_demo_loaded:
                await self.on_demo_loaded(demo_path)

    def _extract_demo_path(self, console_output: str) -> Optional[Path]:
        """Extract demo path from console output.

        Args:
            console_output: Console text to search

        Returns:
            Path to demo file if found, None otherwise
        """
        # Try demo_info pattern first
        match = self.DEMO_INFO_PATTERN.search(console_output)
        if match:
            return Path(match.group(1))

        # Try demo load pattern
        match = self.DEMO_LOAD_PATTERN.search(console_output)
        if match:
            return Path(match.group(1))

        return None

    async def get_current_demo(self) -> Optional[Path]:
        """Query CS2 for currently loaded demo.

        Uses demo_info command to get the current demo.

        Returns:
            Path to current demo, or None if no demo is loaded
        """
        try:
            demo_info = await self.telnet_client.get_demo_info()

            # Check buffer for demo name
            buffer = self.telnet_client.get_buffer_content()
            demo_path = self._extract_demo_path(buffer)

            if demo_path:
                self.current_demo = demo_path
                return demo_path

        except Exception as e:
            print(f"[DemoMonitor] Error querying demo: {e}")

        return self.current_demo

    def set_callback(self, callback: Callable[[Path], Awaitable[None]]) -> None:
        """Set callback for demo load events.

        Args:
            callback: Async function called when demo is loaded
        """
        self.on_demo_loaded = callback

    def clear_current(self) -> None:
        """Clear the current demo state."""
        self.current_demo = None

    async def monitor_demo_load(self, callback: Callable[[Path], Awaitable[None]], poll_interval: float = 0.5):
        """Monitor for demo load events continuously.

        Args:
            callback: Async function called when demo is loaded
            poll_interval: Polling interval in seconds (default: 0.5)
        """
        import asyncio
        while True:
            # Check for demo load in telnet buffer
            if hasattr(self.telnet_client, 'reader') and self.telnet_client.reader:
                try:
                    # Read available data (non-blocking)
                    data = await self.telnet_client.reader.read(4096)
                    if data:
                        console_output = data.decode('utf-8', errors='ignore')
                        demo_path = self._extract_demo_path(console_output)

                        if demo_path:
                            # Parse the demo path
                            resolved_path = self._parse_demo_path(str(demo_path))
                            if resolved_path and resolved_path != self.current_demo:
                                self.current_demo = resolved_path
                                await callback(resolved_path)
                except Exception as e:
                    pass  # Ignore read errors

            await asyncio.sleep(poll_interval)

    def _parse_demo_path(self, demo_path_str: str) -> Optional[Path]:
        """Parse demo path from console output.

        Handles both relative and absolute paths. Relative paths are resolved
        against cs2_dir if provided.

        Args:
            demo_path_str: Demo path string from console

        Returns:
            Resolved Path to demo file, or None if cannot be resolved
        """
        demo_path = Path(demo_path_str)

        # If absolute path, return as-is
        if demo_path.is_absolute():
            return demo_path if demo_path.exists() else demo_path

        # If relative path and we have cs2_dir, resolve against it
        if self.cs2_dir:
            resolved = self.cs2_dir / demo_path
            return resolved

        # Otherwise return the path as-is
        return demo_path
