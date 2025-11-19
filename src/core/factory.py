"""Application factory for creating dev and prod orchestrators.

This module provides factory functions that create fully-configured orchestrator
instances with the appropriate dependencies for development or production use.

Development mode uses mock implementations for testing without CS2.
Production mode uses real implementations that connect to CS2.
"""

from pathlib import Path

from src.core.orchestrator import Orchestrator, RobustOrchestrator
from src.core.config import AppConfig
from src.ui.overlay import CS2InputOverlay
from src.mocks.tick_source import MockTickSource
from src.mocks.demo_repository import MockDemoRepository
from src.mocks.player_tracker import MockPlayerTracker
from src.network.telnet_client import CS2TelnetClient, RobustTelnetClient
from src.network.player_tracker import ManualPlayerTracker
from src.parsers.cache_manager import CacheManager


def create_dev_app(config: AppConfig) -> Orchestrator:
    """Create application with mock components for development.

    Uses mock implementations that don't require CS2 to be running.
    Perfect for UI development and testing.

    Args:
        config: Application configuration

    Returns:
        Orchestrator instance configured with mock components

    Example:
        >>> config = AppConfig()
        >>> app = create_dev_app(config)
        >>> # Test without CS2 running
    """
    print("[Factory] Creating DEV application (mocks)")

    # Create mock components
    tick_source = MockTickSource(
        start_tick=0,
        tick_rate=config.tick_rate
    )

    demo_repo = MockDemoRepository()

    # Try to load cache if demo_path is specified
    if config.demo_path:
        cache_path = Path(config.demo_path).with_suffix('.json')
        if cache_path.exists():
            print(f"[Factory] Loading mock cache from {cache_path}")
            demo_repo.load_demo(str(cache_path))
        else:
            print(f"[Factory] No cache found at {cache_path}, using empty mock data")

    player_tracker = MockPlayerTracker(
        player_id=config.target_player_id or "MOCK_PLAYER_123"
    )

    # Create visualizer
    visualizer = CS2InputOverlay()
    visualizer.setWindowOpacity(config.overlay_opacity)
    visualizer.setGeometry(
        config.overlay_x,
        config.overlay_y,
        config.overlay_width,
        config.overlay_height
    )

    # Create orchestrator
    orchestrator = Orchestrator(
        tick_source=tick_source,
        demo_repository=demo_repo,
        player_tracker=player_tracker,
        visualizer=visualizer,
        polling_interval=config.polling_interval,
        render_fps=config.render_fps,
        tick_rate=config.tick_rate,
        use_smooth_prediction=config.use_smooth_prediction
    )

    print("[Factory] Dev application created successfully")
    return orchestrator


def create_prod_app(config: AppConfig) -> Orchestrator:
    """Create application with real components for production.

    Uses real implementations that connect to CS2 and parse demo files.
    Requires CS2 to be running with -netconport flag.

    Args:
        config: Application configuration

    Returns:
        Orchestrator instance configured with real components

    Raises:
        FileNotFoundError: If demo file is not found
        ValueError: If demo file cannot be loaded

    Example:
        >>> config = AppConfig(demo_path="demo.dem")
        >>> app = create_prod_app(config)
        >>> # Connects to CS2 at localhost:2121
    """
    print("[Factory] Creating PROD application (real components)")

    # Create telnet client for CS2 connection
    if config.reconnect_attempts > 1:
        tick_source = RobustTelnetClient(
            host=config.cs2_host,
            port=config.cs2_port,
            max_retries=config.reconnect_attempts,
            retry_delay=config.reconnect_delay
        )
        print(f"[Factory] Using robust telnet client with {config.reconnect_attempts} retries")
    else:
        tick_source = CS2TelnetClient(
            host=config.cs2_host,
            port=config.cs2_port
        )
        print(f"[Factory] Using standard telnet client")

    # Load demo data from cache
    if not config.demo_path:
        raise ValueError("demo_path must be specified in production mode")

    demo_path = Path(config.demo_path)
    if not demo_path.exists():
        raise FileNotFoundError(f"Demo file not found: {config.demo_path}")

    # Determine cache path
    cache_dir = Path(config.cache_dir)
    cache_file = cache_dir / f"{demo_path.stem}_cache.json"

    print(f"[Factory] Loading cache from {cache_file}")

    # Load cache
    cache_manager = CacheManager()

    if not cache_file.exists():
        raise FileNotFoundError(
            f"Cache file not found: {cache_file}\n"
            f"Please run ETL pipeline first:\n"
            f"  python -m src.parsers.etl_pipeline --demo {config.demo_path}"
        )

    cache_data = cache_manager.load_cache(str(cache_file))
    if not cache_data:
        raise ValueError(f"Failed to load cache from {cache_file}")

    # Create demo repository from cache
    demo_repo = MockDemoRepository()  # Uses cache-based repository
    demo_repo.load_demo(str(cache_file))

    # Get player ID from config or cache metadata
    if config.target_player_id:
        player_id = config.target_player_id
        print(f"[Factory] Using configured player: {player_id}")
    else:
        player_id = demo_repo.get_default_player()
        print(f"[Factory] Using auto-detected player: {player_id}")

    # Create player tracker
    player_tracker = ManualPlayerTracker(player_id)

    # Create visualizer
    visualizer = CS2InputOverlay()
    visualizer.setWindowOpacity(config.overlay_opacity)
    visualizer.setGeometry(
        config.overlay_x,
        config.overlay_y,
        config.overlay_width,
        config.overlay_height
    )

    # Create orchestrator (robust if reconnection is enabled)
    if config.reconnect_attempts > 1:
        orchestrator = RobustOrchestrator(
            tick_source=tick_source,
            demo_repository=demo_repo,
            player_tracker=player_tracker,
            visualizer=visualizer,
            polling_interval=config.polling_interval,
            render_fps=config.render_fps,
            tick_rate=config.tick_rate,
            use_smooth_prediction=config.use_smooth_prediction,
            reconnect_attempts=config.reconnect_attempts,
            reconnect_delay=config.reconnect_delay
        )
        print("[Factory] Using robust orchestrator with auto-reconnect")
    else:
        orchestrator = Orchestrator(
            tick_source=tick_source,
            demo_repository=demo_repo,
            player_tracker=player_tracker,
            visualizer=visualizer,
            polling_interval=config.polling_interval,
            render_fps=config.render_fps,
            tick_rate=config.tick_rate,
            use_smooth_prediction=config.use_smooth_prediction
        )
        print("[Factory] Using standard orchestrator")

    print("[Factory] Prod application created successfully")
    return orchestrator


def validate_production_config(config: AppConfig) -> list[str]:
    """Validate configuration for production use.

    Checks that all necessary settings are configured correctly for
    production use with real CS2 connection.

    Args:
        config: Configuration to validate

    Returns:
        List of validation errors (empty if valid)

    Example:
        >>> config = AppConfig()
        >>> errors = validate_production_config(config)
        >>> if errors:
        ...     print("Configuration errors:", errors)
    """
    errors = []

    # Check demo path
    if not config.demo_path:
        errors.append("demo_path is required for production mode")
    elif not Path(config.demo_path).exists():
        errors.append(f"Demo file not found: {config.demo_path}")

    # Check cache directory
    cache_dir = Path(config.cache_dir)
    if not cache_dir.exists():
        errors.append(f"Cache directory not found: {config.cache_dir}")

    # Check CS2 connection settings
    if not (1 <= config.cs2_port <= 65535):
        errors.append(f"Invalid CS2 port: {config.cs2_port}")

    # Check if cache file exists
    if config.demo_path:
        demo_path = Path(config.demo_path)
        cache_file = cache_dir / f"{demo_path.stem}_cache.json"
        if not cache_file.exists():
            errors.append(
                f"Cache file not found: {cache_file}\n"
                f"  Run: python -m src.parsers.etl_pipeline --demo {config.demo_path}"
            )

    return errors
