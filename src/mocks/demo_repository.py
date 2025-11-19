"""Mock demo repository implementation for testing and development.

This module provides a JSON cache-based mock repository that loads
pre-parsed demo data for UI development and testing.
"""

import json
import sys
from pathlib import Path
from typing import Optional, Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from interfaces.demo_repository import IDemoRepository
from domain.models import InputData


class MockDemoRepository(IDemoRepository):
    """Mock demo repository that loads data from JSON cache files.

    This implementation loads pre-parsed demo data from a JSON cache file,
    allowing UI development and testing without requiring real demo parsing
    or the demoparser2 library.

    Cache File Format:
        {
            "metadata": {
                "player_id": "76561198012345678",
                "player_name": "PlayerName",
                "tick_range": [0, 100000],
                "tick_rate": 64
            },
            "inputs": {
                "1000": {
                    "tick": 1000,
                    "keys": ["W", "A"],
                    "mouse": ["MOUSE1"],
                    "subtick": {"W": 0.0, "A": 0.3, "MOUSE1": 0.5}
                },
                ...
            }
        }

    Attributes:
        cache_data: Loaded cache data dictionary
        player_id: Default player ID from cache metadata
        tick_range: Valid tick range from cache metadata
        _loaded: Flag indicating if demo is loaded

    Example:
        >>> repo = MockDemoRepository()
        >>> repo.load_demo("cache.json")
        >>> data = repo.get_inputs(1000, "76561198012345678")
        >>> print(data.keys)  # ["W", "A"]
    """

    def __init__(self):
        """Initialize mock demo repository with empty state."""
        self.cache_data: Dict[str, Any] = {}
        self.player_id: str = ""
        self.tick_range: tuple[int, int] = (0, 0)
        self._loaded: bool = False

    def load_demo(self, demo_path: str) -> bool:
        """Load demo data from JSON cache file.

        Attempts to load and parse a JSON cache file. If the file doesn't
        exist or is invalid, initializes with empty data and logs a warning.

        Args:
            demo_path: Path to JSON cache file (can be relative or absolute)

        Returns:
            bool: True if loaded successfully, False if file not found
                  or parsing failed (still initializes with defaults)

        Example:
            >>> repo = MockDemoRepository()
            >>> success = repo.load_demo("data/cache.json")
            >>> if not success:
            ...     print("Using empty cache")
        """
        cache_path = Path(demo_path)

        # Handle missing file gracefully
        if not cache_path.exists():
            print(f"Warning: Cache file not found: {demo_path}")
            print("Initializing with empty mock data")
            self._initialize_empty_cache()
            return False

        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                self.cache_data = json.load(f)

            # Extract metadata
            metadata = self.cache_data.get("metadata", {})
            self.player_id = metadata.get("player_id", "MOCK_PLAYER")
            tick_range_list = metadata.get("tick_range", [0, 10000])
            self.tick_range = (tick_range_list[0], tick_range_list[1])

            self._loaded = True
            return True

        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in cache file: {e}")
            self._initialize_empty_cache()
            return False

        except Exception as e:
            print(f"Error loading cache file: {e}")
            self._initialize_empty_cache()
            return False

    def _initialize_empty_cache(self) -> None:
        """Initialize repository with empty/default data.

        Used when cache file is missing or invalid. Creates a minimal
        working state for testing.
        """
        self.cache_data = {
            "metadata": {
                "player_id": "MOCK_PLAYER_123",
                "player_name": "MockPlayer",
                "tick_range": [0, 10000],
                "tick_rate": 64
            },
            "inputs": {}
        }
        self.player_id = "MOCK_PLAYER_123"
        self.tick_range = (0, 10000)
        self._loaded = True

    def get_inputs(self, tick: int, player_id: str) -> Optional[InputData]:
        """Get input data for a specific tick and player.

        Retrieves input data from the loaded cache. Returns None if
        no data exists for the given tick.

        Args:
            tick: Tick number to retrieve
            player_id: Player identifier (currently not used in mock,
                      assumes single player data)

        Returns:
            InputData object if found, None otherwise

        Example:
            >>> repo = MockDemoRepository()
            >>> repo.load_demo("cache.json")
            >>> inputs = repo.get_inputs(1500, "PLAYER_ID")
            >>> if inputs:
            ...     print(f"Keys pressed: {inputs.keys}")
        """
        if not self._loaded:
            return None

        inputs_dict = self.cache_data.get("inputs", {})
        tick_str = str(tick)

        if tick_str not in inputs_dict:
            return None

        tick_data = inputs_dict[tick_str]

        # Convert dict to InputData object
        return InputData(
            tick=tick_data.get("tick", tick),
            keys=tick_data.get("keys", []),
            mouse=tick_data.get("mouse", []),
            subtick=tick_data.get("subtick", {}),
            timestamp=tick_data.get("timestamp")
        )

    def get_tick_range(self) -> tuple[int, int]:
        """Get the range of available ticks in the loaded demo.

        Returns:
            tuple: (min_tick, max_tick) from cache metadata

        Raises:
            RuntimeError: If no demo is currently loaded

        Example:
            >>> repo = MockDemoRepository()
            >>> repo.load_demo("cache.json")
            >>> min_tick, max_tick = repo.get_tick_range()
            >>> print(f"Demo has {max_tick - min_tick} ticks")
        """
        if not self._loaded:
            raise RuntimeError("No demo loaded. Call load_demo() first.")

        return self.tick_range

    def get_default_player(self) -> str:
        """Get the default player identifier from cache metadata.

        Returns the player ID that was extracted during demo parsing.
        Useful for automatically selecting which player to visualize.

        Returns:
            str: Default player identifier (SteamID)

        Raises:
            RuntimeError: If no demo is currently loaded

        Example:
            >>> repo = MockDemoRepository()
            >>> repo.load_demo("cache.json")
            >>> player = repo.get_default_player()
            >>> print(f"Tracking player: {player}")
        """
        if not self._loaded:
            raise RuntimeError("No demo loaded. Call load_demo() first.")

        return self.player_id
