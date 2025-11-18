"""Interface definitions for CS2 Input Visualizer.

This package contains abstract base classes that define the contracts
for various components of the application.
"""

from .tick_source import ITickSource
from .player_tracker import IPlayerTracker

__all__ = ["ITickSource", "IPlayerTracker"]
