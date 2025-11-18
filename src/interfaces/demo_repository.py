"""Interface for demo file data access.

This module defines the abstract interface for components that load
and provide access to CS2 demo file data, particularly player inputs.
"""

from abc import ABC, abstractmethod
from typing import Optional

from domain.models import InputData


class IDemoRepository(ABC):
    """Interface for demo file data access.

    A demo repository handles loading demo files and retrieving
    player input data for specific ticks.
    """

    @abstractmethod
    def load_demo(self, demo_path: str) -> bool:
        """Load a CS2 demo file from the specified path.

        Args:
            demo_path: Absolute or relative path to the demo file.

        Returns:
            bool: True if demo was loaded successfully, False otherwise.
        """
        pass

    @abstractmethod
    def get_inputs(self, tick: int, player_id: str) -> Optional[InputData]:
        """Get player inputs for a specific tick.

        Args:
            tick: The game tick number to retrieve inputs for.
            player_id: Identifier for the player (e.g., SteamID or name).

        Returns:
            Optional[InputData]: The input data if available, None otherwise.
        """
        pass

    @abstractmethod
    def get_tick_range(self) -> tuple[int, int]:
        """Get the valid tick range for the loaded demo.

        Returns:
            tuple[int, int]: A tuple of (min_tick, max_tick) for the demo.

        Raises:
            RuntimeError: If no demo is currently loaded.
        """
        pass

    @abstractmethod
    def get_default_player(self) -> str:
        """Get the default player identifier for the demo.

        This typically returns the POV (point of view) player or
        the first player found in the demo.

        Returns:
            str: The default player identifier.

        Raises:
            RuntimeError: If no demo is currently loaded.
        """
        pass
