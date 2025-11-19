"""
Core Layer - Central orchestration and system coordination.

This module provides the core logic for the CS2 Input Visualizer:

1. **Orchestrator**: Main system coordinator with dependency injection
   - Coordinates tick sync, prediction, player tracking, and rendering
   - Manages three concurrent loops (sync, render, player tracking)
   - Supports both basic and robust implementations

2. **Prediction Engine**: Tick prediction for smooth interpolation
   - Predicts intermediate ticks between network polls
   - Supports basic and smooth (jump/pause detection) variants
   - Handles drift correction and demo playback anomalies

3. **Sync Engine**: Network polling coordination
   - Polls tick source at regular intervals
   - Tracks last known tick and update time
   - Used by prediction engine for interpolation

4. **Configuration**: Application configuration management
   - Type-safe configuration via dataclass
   - JSON file loading/saving
   - Validation and default values

Usage:
    Basic usage with dependency injection:

    >>> from src.core import Orchestrator, AppConfig, load_config
    >>> from src.mocks.tick_source import MockTickSource
    >>> from src.mocks.demo_repository import MockDemoRepository
    >>> from src.mocks.player_tracker import MockPlayerTracker
    >>> from src.ui.overlay import CS2InputOverlay
    >>>
    >>> # Load configuration
    >>> config = load_config("config.json")
    >>>
    >>> # Create components
    >>> tick_source = MockTickSource()
    >>> demo_repo = MockDemoRepository()
    >>> player_tracker = MockPlayerTracker()
    >>> visualizer = CS2InputOverlay()
    >>>
    >>> # Create orchestrator
    >>> orchestrator = Orchestrator(
    ...     tick_source=tick_source,
    ...     demo_repository=demo_repo,
    ...     player_tracker=player_tracker,
    ...     visualizer=visualizer,
    ...     polling_interval=config.polling_interval,
    ...     render_fps=config.render_fps
    ... )
    >>>
    >>> # Run
    >>> await orchestrator.start()

For production use with enhanced error handling:

    >>> from src.core import RobustOrchestrator
    >>>
    >>> orchestrator = RobustOrchestrator(
    ...     tick_source=tick_source,
    ...     demo_repository=demo_repo,
    ...     player_tracker=player_tracker,
    ...     visualizer=visualizer,
    ...     polling_interval=config.polling_interval,
    ...     render_fps=config.render_fps,
    ...     reconnect_attempts=3,
    ...     reconnect_delay=2.0
    ... )
"""

from src.core.config import (
    AppConfig,
    load_config,
    save_config,
    create_default_config,
    validate_config,
)

from src.core.orchestrator import (
    Orchestrator,
    RobustOrchestrator,
    SyncEngine,
)

from src.core.prediction_engine import (
    PredictionEngine,
    SmoothPredictionEngine,
)

from src.core.factory import (
    create_dev_app,
    create_prod_app,
    validate_production_config,
)

__all__ = [
    # Configuration
    "AppConfig",
    "load_config",
    "save_config",
    "create_default_config",
    "validate_config",

    # Orchestration
    "Orchestrator",
    "RobustOrchestrator",
    "SyncEngine",

    # Prediction
    "PredictionEngine",
    "SmoothPredictionEngine",

    # Factory
    "create_dev_app",
    "create_prod_app",
    "validate_production_config",
]

__version__ = "0.1.0"
__author__ = "CS2 Input Visualizer Team"
