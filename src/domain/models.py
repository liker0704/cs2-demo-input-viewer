"""Domain models for CS2 Input Visualizer.

This module contains the core data structures used throughout the application
to represent player inputs, player information, and demo file metadata.
"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class InputData:
    """Player input state for a single tick.

    Represents all input actions (keyboard, mouse) that occurred during
    a specific game tick, including subtick timing information.

    Attributes:
        tick: The game tick number when this input occurred
        keys: List of keyboard keys pressed (e.g., ["W", "A", "SPACE"])
        mouse: List of mouse buttons pressed (e.g., ["MOUSE1"])
        subtick: Dictionary mapping input actions to their subtick timing (0.0-1.0)
        timestamp: Optional Unix timestamp when this input occurred
        playback_speed: Optional playback speed multiplier (0.25x, 0.5x, 1.0x, 2.0x, etc.)
                        Used for speed-aware visualization timing
    """
    tick: int
    keys: List[str]
    mouse: List[str]
    subtick: dict
    timestamp: Optional[float] = None
    playback_speed: Optional[float] = 1.0  # Default to 1.0x (normal speed)


@dataclass
class PlayerInfo:
    """Player identification information.

    Contains information to identify a specific player in a CS2 demo file.

    Attributes:
        steam_id: Player's Steam ID (unique identifier)
        name: Player's display name
        entity_id: Optional in-game entity ID for the player
    """
    steam_id: str
    name: str
    entity_id: Optional[int] = None


@dataclass
class DemoMetadata:
    """Demo file metadata.

    Contains metadata about a CS2 demo file including timing information
    and player identification.

    Attributes:
        file_path: Full path to the demo file
        player_id: Steam ID of the player being tracked
        player_name: Display name of the player being tracked
        tick_range: Tuple of (start_tick, end_tick) for the demo
        tick_rate: Server tick rate (e.g., 64 or 128 ticks per second)
        duration_seconds: Total duration of the demo in seconds
    """
    file_path: str
    player_id: str
    player_name: str
    tick_range: tuple[int, int]
    tick_rate: int
    duration_seconds: float
