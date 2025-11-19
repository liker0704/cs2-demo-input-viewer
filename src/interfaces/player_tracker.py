"""Interface for tracking the currently active player.

This module defines the abstract interface for components that track
which player's inputs should be visualized, potentially based on
game state or user selection.
"""

from abc import ABC, abstractmethod
from typing import Optional


class IPlayerTracker(ABC):
    """Interface for tracking the currently active player.

    A player tracker determines which player's inputs should be
    displayed based on game state, spectator mode, or user selection.
    """

    @abstractmethod
    async def get_current_player(self) -> Optional[str]:
        """Get the identifier of the currently active player.

        Returns:
            Optional[str]: The player identifier if one is active, None otherwise.
                          Player identifier could be SteamID, username, or other unique ID.
        """
        pass

    @abstractmethod
    async def update(self) -> None:
        """Update the player tracking state.

        This method should be called periodically to refresh the
        current player information from the underlying source
        (e.g., game state, spectator mode changes).
        """
        pass
