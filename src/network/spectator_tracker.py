"""Spectator target tracking for auto-detection of viewed player.

This module monitors console output to detect which player the user
is currently spectating during demo playback.
"""

import re
from typing import Optional, Callable, Awaitable, Tuple
from .telnet_client import CS2TelnetClient


class SpectatorTracker:
    """Tracks which player is currently being spectated.

    Monitors console output for spectator change messages to detect
    when the user switches between players during demo playback.

    Attributes:
        telnet_client: CS2 telnet connection
        current_player: Currently spectated player (name, steam_id)
        on_spectator_changed: Callback for spectator change events
    """

    # Regex patterns for spectator detection
    # Examples:
    # "Spectating: PlayerName"
    # "Now spectating: PlayerName (STEAM_1:0:123456)"
    SPECTATOR_PATTERN = re.compile(r"[Ss]pectating:?\s+(.+?)(?:\s+\(([^)]+)\))?$")

    def __init__(self, telnet_client: CS2TelnetClient):
        """Initialize spectator tracker.

        Args:
            telnet_client: Connected CS2 telnet client
        """
        self.telnet_client = telnet_client
        self.current_player: Optional[Tuple[str, str]] = None  # (name, steam_id)
        self.on_spectator_changed: Optional[Callable[[str, str], Awaitable[None]]] = None

    async def update(self) -> None:
        """Check for spectator change events in telnet buffer."""
        if not self.telnet_client.is_connected():
            return

        # Get buffered console output
        buffer_content = self.telnet_client.get_buffer_content()

        # Check for spectator messages
        player_info = self._extract_spectator_info(buffer_content)

        if player_info and player_info != self.current_player:
            player_name, steam_id = player_info
            print(f"[SpectatorTracker] Detected spectator change: {player_name}")
            self.current_player = player_info

            # Trigger callback
            if self.on_spectator_changed:
                await self.on_spectator_changed(player_name, steam_id)

    def _extract_spectator_info(self, console_output: str) -> Optional[Tuple[str, str]]:
        """Extract spectator player info from console output.

        Args:
            console_output: Console text to search

        Returns:
            Tuple of (player_name, steam_id) if found, None otherwise
        """
        # Search for spectator patterns in recent lines
        lines = console_output.splitlines()

        # Check last few lines (most recent)
        for line in reversed(lines[-10:]):
            match = self.SPECTATOR_PATTERN.search(line)
            if match:
                player_name = match.group(1).strip()
                steam_id = match.group(2) if match.group(2) else "unknown"
                return (player_name, steam_id)

        return None

    async def get_current_player(self) -> Optional[Tuple[str, str]]:
        """Get the currently spectated player.

        Returns:
            Tuple of (player_name, steam_id) or None
        """
        # Try to update from buffer
        await self.update()
        return self.current_player

    def set_callback(self, callback: Callable[[str, str], Awaitable[None]]) -> None:
        """Set callback for spectator change events.

        Args:
            callback: Async function called when spectator target changes
                     Receives (player_name, steam_id) as arguments
        """
        self.on_spectator_changed = callback

    def set_player(self, player_name: str, steam_id: str) -> None:
        """Manually set the spectated player.

        Args:
            player_name: Player display name
            steam_id: Player Steam ID
        """
        self.current_player = (player_name, steam_id)
        print(f"[SpectatorTracker] Manually set player: {player_name}")

    def clear_current(self) -> None:
        """Clear the current spectator state."""
        self.current_player = None

    async def get_current_target(self) -> Optional[str]:
        """Get the current spectator target player name.

        Returns:
            Player name if spectating someone, None otherwise
        """
        # Send status command to get current spectator info
        if hasattr(self.telnet_client, 'writer') and self.telnet_client.writer:
            try:
                self.telnet_client.writer.write(b"status\n")
                await self.telnet_client.writer.drain()

                # Read response
                if hasattr(self.telnet_client, 'reader') and self.telnet_client.reader:
                    data = await self.telnet_client.reader.read(4096)
                    if data:
                        status_output = data.decode('utf-8', errors='ignore')
                        return self._parse_status_output(status_output)
            except Exception:
                pass

        return None

    async def track_spectator_changes(self, callback: Callable[[str], Awaitable[None]], poll_interval: float = 1.0):
        """Track spectator target changes continuously.

        Args:
            callback: Async function called when spectator target changes (receives player name)
            poll_interval: Polling interval in seconds (default: 1.0)
        """
        import asyncio
        last_target = None

        while True:
            try:
                # Check for spectator info in telnet buffer
                if hasattr(self.telnet_client, 'reader') and self.telnet_client.reader:
                    data = await self.telnet_client.reader.read(4096)
                    if data:
                        console_output = data.decode('utf-8', errors='ignore')
                        current_target = self._parse_status_output(console_output)

                        if current_target and current_target != last_target:
                            last_target = current_target
                            await callback(current_target)
            except Exception:
                pass

            await asyncio.sleep(poll_interval)

    def _parse_status_output(self, status_text: str) -> Optional[str]:
        """Parse status command output to extract spectator target.

        Args:
            status_text: Output from 'status' console command

        Returns:
            Player name being spectated, or None if not spectating
        """
        # Look for "Spectating: PlayerName" pattern
        match = self.SPECTATOR_PATTERN.search(status_text)
        if match:
            return match.group(1).strip()

        return None

    def _build_player_mapping(self, status_text: str) -> dict:
        """Build mapping of player names to Steam IDs from status output.

        Args:
            status_text: Output from 'status' console command

        Returns:
            Dictionary mapping player names to Steam IDs
        """
        player_mapping = {}

        # Parse player list from status output
        # Format: userid "name" uniqueid connected ping
        player_pattern = re.compile(r'^\s*\d+\s+"([^"]+)"\s+(STEAM_[\d:]+)', re.MULTILINE)

        for match in player_pattern.finditer(status_text):
            player_name = match.group(1)
            steam_id = match.group(2)
            player_mapping[player_name] = steam_id

        return player_mapping
