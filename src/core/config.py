"""
Configuration System - Application configuration management.

This module provides a centralized configuration system for the CS2 Input Visualizer.
It supports:
- Loading configuration from JSON files
- Saving configuration to JSON files
- Default values for all settings
- Type-safe configuration access via dataclass
"""

import json
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Optional


@dataclass
class AppConfig:
    """Application configuration.

    This dataclass contains all configurable settings for the application,
    organized by category.
    """

    # Network Settings
    cs2_host: str = "127.0.0.1"
    """CS2 server hostname or IP address"""

    cs2_port: int = 2121
    """CS2 telnet port (default: 2121)"""

    polling_interval: float = 0.25
    """Network polling frequency in seconds (default: 0.25 = 4 Hz)"""

    # Rendering Settings
    render_fps: int = 60
    """Target rendering FPS (default: 60)"""

    overlay_opacity: float = 0.9
    """Overlay window opacity (0.0-1.0, default: 0.9)"""

    # Data Settings
    cache_dir: str = "./cache"
    """Directory for caching parsed demo data"""

    demo_path: Optional[str] = None
    """Path to demo file to load (None = no demo loaded)"""

    # Player Settings
    target_player_id: Optional[str] = None
    """Target player SteamID (None = auto-detect from spectated player)"""

    # Prediction Settings
    max_drift: int = 10
    """Maximum allowed tick drift before snapping (in ticks)"""

    smoothing_window: int = 5
    """Number of ticks to use for smoothing (smooth prediction only)"""

    tick_rate: int = 64
    """Game tick rate in Hz (default: 64 for CS2)"""

    # UI Settings
    overlay_scale: float = 1.0
    """UI scale factor (1.0 = 100%)"""

    overlay_x: int = 100
    """Overlay window X position in pixels"""

    overlay_y: int = 100
    """Overlay window Y position in pixels"""

    overlay_width: int = 700
    """Overlay window width in pixels"""

    overlay_height: int = 300
    """Overlay window height in pixels"""

    # Debug Settings
    debug_mode: bool = False
    """Enable debug mode with verbose logging"""

    show_fps: bool = False
    """Show FPS counter in overlay"""

    show_tick_info: bool = False
    """Show current tick and drift info in overlay"""

    # Advanced Settings
    use_smooth_prediction: bool = True
    """Use smooth prediction engine (handles jumps/pauses)"""

    player_tracking_interval: float = 1.0
    """Player tracking update interval in seconds"""

    reconnect_attempts: int = 3
    """Number of reconnection attempts on network failure"""

    reconnect_delay: float = 2.0
    """Delay between reconnection attempts in seconds"""


def load_config(path: str = "config.json") -> AppConfig:
    """Load configuration from JSON file.

    If the file doesn't exist, returns default configuration.
    If the file exists but some fields are missing, they will use default values.

    Args:
        path: Path to configuration file (default: "config.json")

    Returns:
        AppConfig: Configuration instance with loaded or default values

    Raises:
        json.JSONDecodeError: If file contains invalid JSON
        ValueError: If config file contains invalid values
    """
    config_path = Path(path)

    if not config_path.exists():
        print(f"[Config] No config file at {path}, using defaults")
        return AppConfig()

    try:
        with open(config_path, 'r') as f:
            data = json.load(f)

        # Filter out unknown fields (for forward compatibility)
        valid_fields = {f.name for f in AppConfig.__dataclass_fields__.values()}
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}

        unknown_fields = set(data.keys()) - valid_fields
        if unknown_fields:
            print(f"[Config] Warning: Unknown fields ignored: {unknown_fields}")

        config = AppConfig(**filtered_data)
        print(f"[Config] Loaded configuration from {path}")
        return config

    except json.JSONDecodeError as e:
        print(f"[Config] Error: Invalid JSON in {path}: {e}")
        raise

    except TypeError as e:
        print(f"[Config] Error: Invalid configuration values: {e}")
        raise ValueError(f"Invalid configuration in {path}: {e}") from e


def save_config(config: AppConfig, path: str = "config.json"):
    """Save configuration to JSON file.

    Args:
        config: AppConfig instance to save
        path: Output file path (default: "config.json")

    Raises:
        IOError: If file cannot be written
    """
    try:
        config_path = Path(path)

        # Create parent directory if needed
        config_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert to dict and save
        config_dict = asdict(config)

        with open(config_path, 'w') as f:
            json.dump(config_dict, f, indent=2)

        print(f"[Config] Saved configuration to {path}")

    except IOError as e:
        print(f"[Config] Error: Cannot write to {path}: {e}")
        raise


def create_default_config(path: str = "config.json") -> AppConfig:
    """Create and save a default configuration file.

    Useful for first-time setup or resetting to defaults.

    Args:
        path: Output file path (default: "config.json")

    Returns:
        AppConfig: The default configuration that was saved
    """
    config = AppConfig()
    save_config(config, path)
    print(f"[Config] Created default configuration at {path}")
    return config


def validate_config(config: AppConfig) -> list[str]:
    """Validate configuration values.

    Checks for common issues like invalid ranges, incompatible settings, etc.

    Args:
        config: Configuration to validate

    Returns:
        list[str]: List of validation warnings/errors (empty if valid)
    """
    issues = []

    # Network validation
    if not (1 <= config.cs2_port <= 65535):
        issues.append(f"Invalid cs2_port: {config.cs2_port} (must be 1-65535)")

    if config.polling_interval <= 0:
        issues.append(f"Invalid polling_interval: {config.polling_interval} (must be > 0)")

    if config.polling_interval > 5:
        issues.append(f"Warning: polling_interval {config.polling_interval}s is very high (recommended < 1s)")

    # Rendering validation
    if config.render_fps <= 0:
        issues.append(f"Invalid render_fps: {config.render_fps} (must be > 0)")

    if not (0.0 <= config.overlay_opacity <= 1.0):
        issues.append(f"Invalid overlay_opacity: {config.overlay_opacity} (must be 0.0-1.0)")

    # Prediction validation
    if config.max_drift <= 0:
        issues.append(f"Invalid max_drift: {config.max_drift} (must be > 0)")

    if config.tick_rate <= 0:
        issues.append(f"Invalid tick_rate: {config.tick_rate} (must be > 0)")

    # UI validation
    if config.overlay_scale <= 0:
        issues.append(f"Invalid overlay_scale: {config.overlay_scale} (must be > 0)")

    # Demo file validation
    if config.demo_path:
        demo_path = Path(config.demo_path)
        if not demo_path.exists():
            issues.append(f"Demo file not found: {config.demo_path}")
        elif not demo_path.suffix == '.dem':
            issues.append(f"Warning: Demo file may not be valid (expected .dem extension): {config.demo_path}")

    # Cache directory validation
    cache_path = Path(config.cache_dir)
    if not cache_path.exists():
        issues.append(f"Warning: Cache directory does not exist: {config.cache_dir} (will be created)")

    return issues
