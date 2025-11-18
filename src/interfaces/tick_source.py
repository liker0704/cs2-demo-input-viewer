"""Interface for tick synchronization sources.

This module defines the abstract interface for components that provide
tick synchronization for demo playback. Implementations might include
GSI (Game State Integration) servers or mock tick generators.
"""

from abc import ABC, abstractmethod


class ITickSource(ABC):
    """Interface for tick synchronization sources.

    A tick source provides the current game tick for synchronizing
    input visualization with demo playback or live gameplay.
    """

    @abstractmethod
    async def connect(self) -> bool:
        """Establish connection to the tick source.

        Returns:
            bool: True if connection was successful, False otherwise.
        """
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the tick source.

        Cleanly closes the connection and releases any resources.
        """
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """Check if currently connected to the tick source.

        Returns:
            bool: True if connected, False otherwise.
        """
        pass

    @abstractmethod
    async def get_current_tick(self) -> int:
        """Get the current tick number from the source.

        Returns:
            int: The current game tick number.

        Raises:
            ConnectionError: If not connected to the tick source.
        """
        pass
