"""Mock player tracker implementation for testing and development.

This module provides a mock player tracker that returns a configurable
player ID without requiring a real game connection.
"""

import sys
from pathlib import Path
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from interfaces.player_tracker import IPlayerTracker


class MockPlayerTracker(IPlayerTracker):
    """Mock player tracker returning configurable player information.

    This implementation returns a pre-configured player ID, making it
    ideal for UI development and testing without a real game connection.

    Attributes:
        player_id: The Steam ID to return (default: test player)
        _updated: Flag tracking if update has been called

    Example:
        >>> tracker = MockPlayerTracker(player_id="76561198012345678")
        >>> await tracker.update()
        >>> player = await tracker.get_current_player()
        >>> print(f"Current player: {player}")
    """

    def __init__(self, player_id: str = "76561198000000001"):
        """Initialize mock player tracker.

        Args:
            player_id: Steam ID to return as current player (default: test ID)
        """
        self.player_id = player_id
        self._updated = False

    async def get_current_player(self) -> Optional[str]:
        """Get the configured player ID.

        Returns:
            Optional[str]: The configured Steam ID, or None if never updated
        """
        if not self._updated:
            return None
        return self.player_id

    async def update(self) -> None:
        """Mark tracker as updated.

        In a real implementation, this would poll the game state.
        For the mock, we just mark it as updated.
        """
        self._updated = True

    def set_player(self, player_id: Optional[str]) -> None:
        """Set the current player ID for testing.

        Args:
            player_id: New Steam ID to return, or None to simulate no player
        """
        self.player_id = player_id
        if player_id is not None:
            self._updated = True
        else:
            self._updated = False
