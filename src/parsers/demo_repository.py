"""Demo repository implementation using cached data.

This module provides an implementation of IDemoRepository that loads
preprocessed cache files for fast input data access.
"""

from pathlib import Path
from typing import Optional
from ..interfaces.demo_repository import IDemoRepository
from ..domain.models import InputData
from .cache_manager import CacheManager


class CachedDemoRepository(IDemoRepository):
    """Repository for demo data backed by preprocessed cache files.

    Loads cache files created by the ETL pipeline and provides fast
    access to player input data by tick number.

    Attributes:
        cache_manager: CacheManager for loading cache files
        cache_data: Currently loaded cache data
        player_id: ID of the player whose inputs are loaded
    """

    def __init__(self):
        """Initialize the cached demo repository."""
        self.cache_manager = CacheManager()
        self.cache_data: Optional[dict] = None
        self.player_id: Optional[str] = None

    def load_demo(self, cache_path: str) -> bool:
        """Load a preprocessed cache file.

        Args:
            cache_path: Path to cache file (.json or .msgpack)

        Returns:
            True if loaded successfully, False otherwise
        """
        try:
            self.cache_data = self.cache_manager.load_cache(cache_path)

            if self.cache_data is None:
                return False

            # Extract player ID from metadata
            meta = self.cache_data.get("meta", {})
            self.player_id = meta.get("player_id", "unknown")

            print(f"[DemoRepository] Loaded cache for player: {self.player_id}")
            return True

        except Exception as e:
            print(f"[DemoRepository] Error loading cache: {e}")
            self.cache_data = None
            self.player_id = None
            return False

    def get_inputs(self, tick: int, player_id: str) -> Optional[InputData]:
        """Get player inputs for a specific tick.

        Args:
            tick: Game tick number
            player_id: Player identifier (must match loaded cache)

        Returns:
            InputData object if inputs exist for that tick, None otherwise
        """
        if self.cache_data is None:
            return None

        # Check if player ID matches
        if player_id != self.player_id:
            return None

        # Get inputs for tick
        inputs = self.cache_data.get("inputs", {})
        tick_data = inputs.get(str(tick))

        if tick_data is None:
            return None

        # Convert to InputData object
        return InputData(
            tick=tick,
            keys=tick_data.get("keys", []),
            mouse=tick_data.get("mouse", []),
            subtick=tick_data.get("subtick", {})
        )

    def get_tick_range(self) -> tuple[int, int]:
        """Get the valid tick range for the loaded demo.

        Returns:
            Tuple of (min_tick, max_tick)

        Raises:
            RuntimeError: If no demo is loaded
        """
        if self.cache_data is None:
            raise RuntimeError("No demo loaded")

        meta = self.cache_data.get("meta", {})
        tick_range = meta.get("tick_range", [0, 0])

        return (tick_range[0], tick_range[1])

    def get_default_player(self) -> str:
        """Get the player ID from the loaded cache.

        Returns:
            Player ID string

        Raises:
            RuntimeError: If no demo is loaded
        """
        if self.cache_data is None or self.player_id is None:
            raise RuntimeError("No demo loaded")

        return self.player_id

    def get_metadata(self) -> dict:
        """Get metadata from loaded cache.

        Returns:
            Dictionary with demo metadata
        """
        if self.cache_data is None:
            return {}

        return self.cache_data.get("meta", {})
