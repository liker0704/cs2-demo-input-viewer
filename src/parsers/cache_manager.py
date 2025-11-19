"""Cache Manager for CS2 Input Visualizer.

This module provides functionality for loading, saving, and optimizing cache files
containing player input data extracted from CS2 demo files. Supports multiple formats
including JSON (development) and MessagePack (production).

Cache Structure:
    {
        "meta": {
            "demo_file": "match.dem",
            "player_id": "STEAM_1:0:123456789",
            "player_name": "player",
            "tick_range": [0, 160000],
            "tick_rate": 64
        },
        "inputs": {
            "100": {
                "keys": ["W", "A"],
                "mouse": ["MOUSE1"],
                "subtick": {
                    "W": 0.0,
                    "A": 0.2,
                    "MOUSE1": 0.5
                }
            }
        }
    }

Example:
    >>> manager = CacheManager()
    >>> cache = manager.load_cache("demo_cache.json")
    >>> optimized = manager.optimize_cache(cache)
    >>> manager.save_cache(optimized, "demo_cache_optimized.msgpack")
"""

import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, List
import os

# Optional MessagePack support
try:
    import msgpack
    MSGPACK_AVAILABLE = True
except ImportError:
    MSGPACK_AVAILABLE = False

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CacheError(Exception):
    """Base exception for cache operations."""
    pass


class CacheFormatError(CacheError):
    """Raised when cache format is invalid or corrupted."""
    pass


class CacheNotFoundError(CacheError):
    """Raised when cache file is not found."""
    pass


class CacheManager:
    """Manager for loading, saving, and optimizing CS2 input cache files.

    Attributes:
        cache: Currently loaded cache data (dict or None)
        format_handlers: Dictionary mapping format names to handler functions
    """

    SUPPORTED_FORMATS = ['json', 'msgpack']
    FORMAT_EXTENSIONS = {
        '.json': 'json',
        '.msgpack': 'msgpack',
        '.msgpk': 'msgpack',
        '.mpk': 'msgpack'
    }

    def __init__(self):
        """Initialize the cache manager."""
        self.cache: Optional[Dict[str, Any]] = None
        self._setup_format_handlers()

    def _setup_format_handlers(self):
        """Setup format-specific save/load handlers."""
        self.format_handlers = {
            'json': {
                'save': self._save_json,
                'load': self._load_json
            }
        }

        if MSGPACK_AVAILABLE:
            self.format_handlers['msgpack'] = {
                'save': self._save_msgpack,
                'load': self._load_msgpack
            }

    def _detect_format(self, file_path: str) -> str:
        """Auto-detect format from file extension.

        Args:
            file_path: Path to the cache file

        Returns:
            Format name ('json' or 'msgpack')

        Raises:
            CacheFormatError: If format cannot be determined
        """
        path = Path(file_path)
        ext = path.suffix.lower()

        if ext in self.FORMAT_EXTENSIONS:
            format_name = self.FORMAT_EXTENSIONS[ext]
            if format_name == 'msgpack' and not MSGPACK_AVAILABLE:
                logger.warning(
                    f"MessagePack format detected but msgpack library not installed. "
                    f"Install with: pip install msgpack"
                )
                raise CacheFormatError(
                    f"MessagePack support not available. Install msgpack library."
                )
            return format_name

        # Default to JSON if extension is unknown
        logger.warning(f"Unknown extension '{ext}', defaulting to JSON format")
        return 'json'

    def save_cache(
        self,
        cache_data: Dict[str, Any],
        output_path: str,
        format: str = "auto"
    ) -> bool:
        """Save cache data to file with specified format.

        Args:
            cache_data: Cache dictionary to save
            output_path: Destination file path
            format: Output format ('auto', 'json', or 'msgpack')
                   'auto' detects format from file extension

        Returns:
            True if save was successful, False otherwise

        Raises:
            CacheFormatError: If format is invalid or unsupported
            CacheError: If save operation fails

        Example:
            >>> manager = CacheManager()
            >>> cache = {"meta": {...}, "inputs": {...}}
            >>> manager.save_cache(cache, "output.json")
            True
        """
        try:
            # Validate cache structure before saving
            if not self.validate_cache(cache_data):
                raise CacheFormatError("Invalid cache structure")

            # Determine format
            if format == "auto":
                format = self._detect_format(output_path)
            elif format not in self.SUPPORTED_FORMATS:
                raise CacheFormatError(f"Unsupported format: {format}")

            # Check if format is available
            if format not in self.format_handlers:
                raise CacheFormatError(
                    f"Format '{format}' not available. "
                    f"Install required dependencies."
                )

            # Create output directory if needed
            output_path_obj = Path(output_path)
            output_path_obj.parent.mkdir(parents=True, exist_ok=True)

            # Save using appropriate handler
            save_handler = self.format_handlers[format]['save']
            save_handler(cache_data, output_path)

            file_size = os.path.getsize(output_path)
            logger.info(
                f"Cache saved successfully to {output_path} "
                f"({file_size / 1024:.2f} KB, format: {format})"
            )

            return True

        except Exception as e:
            logger.error(f"Failed to save cache: {e}")
            raise CacheError(f"Save failed: {e}") from e

    def load_cache(self, cache_path: str) -> Optional[Dict[str, Any]]:
        """Load cache from file with automatic format detection.

        Args:
            cache_path: Path to cache file

        Returns:
            Cache dictionary or None if load fails

        Raises:
            CacheNotFoundError: If file does not exist
            CacheFormatError: If file format is invalid
            CacheError: If load operation fails

        Example:
            >>> manager = CacheManager()
            >>> cache = manager.load_cache("demo_cache.json")
            >>> print(cache["meta"]["player_id"])
            STEAM_1:0:123456789
        """
        try:
            # Check if file exists
            if not Path(cache_path).exists():
                raise CacheNotFoundError(f"Cache file not found: {cache_path}")

            # Detect format
            format = self._detect_format(cache_path)

            # Check if format handler is available
            if format not in self.format_handlers:
                raise CacheFormatError(f"No handler for format: {format}")

            # Load using appropriate handler
            load_handler = self.format_handlers[format]['load']
            cache_data = load_handler(cache_path)

            # Validate loaded cache
            if not self.validate_cache(cache_data):
                raise CacheFormatError(
                    f"Loaded cache has invalid structure: {cache_path}"
                )

            # Store in instance
            self.cache = cache_data

            file_size = os.path.getsize(cache_path)
            num_ticks = len(cache_data.get("inputs", {}))
            logger.info(
                f"Cache loaded successfully from {cache_path} "
                f"({file_size / 1024:.2f} KB, {num_ticks} ticks, format: {format})"
            )

            return cache_data

        except (CacheNotFoundError, CacheFormatError):
            raise
        except Exception as e:
            logger.error(f"Failed to load cache: {e}")
            raise CacheError(f"Load failed: {e}") from e

    def _save_json(self, cache_data: Dict[str, Any], output_path: str):
        """Save cache as JSON file.

        Args:
            cache_data: Cache dictionary
            output_path: Destination path
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, indent=2, ensure_ascii=False)

    def _load_json(self, cache_path: str) -> Dict[str, Any]:
        """Load cache from JSON file.

        Args:
            cache_path: Path to JSON file

        Returns:
            Cache dictionary

        Raises:
            CacheFormatError: If JSON is invalid
        """
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise CacheFormatError(f"Invalid JSON format: {e}") from e

    def _save_msgpack(self, cache_data: Dict[str, Any], output_path: str):
        """Save cache as MessagePack file.

        Args:
            cache_data: Cache dictionary
            output_path: Destination path
        """
        with open(output_path, 'wb') as f:
            msgpack.pack(cache_data, f, use_bin_type=True)

    def _load_msgpack(self, cache_path: str) -> Dict[str, Any]:
        """Load cache from MessagePack file.

        Args:
            cache_path: Path to MessagePack file

        Returns:
            Cache dictionary

        Raises:
            CacheFormatError: If MessagePack is invalid
        """
        try:
            with open(cache_path, 'rb') as f:
                return msgpack.unpack(f, raw=False, strict_map_key=False)
        except Exception as e:
            raise CacheFormatError(f"Invalid MessagePack format: {e}") from e

    def optimize_cache(
        self,
        cache: Dict[str, Any],
        remove_duplicates: bool = True,
        sparse_storage: bool = True
    ) -> Dict[str, Any]:
        """Optimize cache by removing redundant data.

        Performs the following optimizations:
        1. Removes consecutive duplicate input states (sparse storage)
        2. Cleans up empty subtick data
        3. Sorts ticks for efficient access

        Args:
            cache: Cache dictionary to optimize
            remove_duplicates: Remove consecutive duplicate states
            sparse_storage: Only keep ticks where inputs change

        Returns:
            Optimized cache dictionary

        Example:
            >>> manager = CacheManager()
            >>> cache = manager.load_cache("demo.json")
            >>> optimized = manager.optimize_cache(cache)
            >>> # Cache reduced from 10000 to 3500 ticks (65% reduction)
        """
        if not self.validate_cache(cache):
            logger.warning("Cache validation failed, skipping optimization")
            return cache

        optimized = {
            "meta": cache["meta"].copy(),
            "inputs": {}
        }

        # Sort ticks numerically
        sorted_ticks = sorted(cache["inputs"].items(), key=lambda x: int(x[0]))

        prev_state = None
        kept_ticks = 0
        removed_ticks = 0

        for tick_str, tick_data in sorted_ticks:
            # Create state signature for comparison
            current_state = self._create_state_signature(tick_data)

            # Check if we should keep this tick
            should_keep = True

            if remove_duplicates and sparse_storage:
                if current_state == prev_state:
                    should_keep = False
                    removed_ticks += 1

            if should_keep:
                # Clean up tick data
                cleaned_data = self._clean_tick_data(tick_data)
                optimized["inputs"][tick_str] = cleaned_data
                prev_state = current_state
                kept_ticks += 1

        original_size = len(cache["inputs"])
        optimized_size = len(optimized["inputs"])
        reduction_pct = 100 * (1 - optimized_size / original_size) if original_size > 0 else 0

        logger.info(
            f"Cache optimized: {original_size} → {optimized_size} ticks "
            f"({reduction_pct:.1f}% reduction)"
        )

        return optimized

    def _create_state_signature(self, tick_data: Dict[str, Any]) -> Tuple:
        """Create hashable signature of tick state for comparison.

        Args:
            tick_data: Tick input data

        Returns:
            Tuple representing the state
        """
        keys = tuple(sorted(tick_data.get("keys", [])))
        mouse = tuple(sorted(tick_data.get("mouse", [])))
        return (keys, mouse)

    def _clean_tick_data(self, tick_data: Dict[str, Any]) -> Dict[str, Any]:
        """Clean up tick data by removing empty or redundant fields.

        Args:
            tick_data: Raw tick data

        Returns:
            Cleaned tick data
        """
        cleaned = {
            "keys": tick_data.get("keys", []),
            "mouse": tick_data.get("mouse", []),
            "subtick": {}
        }

        # Only include subtick data for active keys
        subtick = tick_data.get("subtick", {})
        all_active_keys = set(cleaned["keys"]) | set(cleaned["mouse"])

        for key in all_active_keys:
            if key in subtick:
                cleaned["subtick"][key] = subtick[key]

        return cleaned

    def validate_cache(self, cache: Dict[str, Any]) -> bool:
        """Validate cache structure and integrity.

        Checks:
        - Required top-level keys exist
        - Meta section has required fields
        - Inputs are properly structured
        - Tick numbers are valid

        Args:
            cache: Cache dictionary to validate

        Returns:
            True if cache is valid, False otherwise

        Example:
            >>> manager = CacheManager()
            >>> cache = {"meta": {...}, "inputs": {...}}
            >>> if manager.validate_cache(cache):
            ...     print("Cache is valid")
        """
        try:
            # Check top-level structure
            if not isinstance(cache, dict):
                logger.error("Cache must be a dictionary")
                return False

            if "meta" not in cache or "inputs" not in cache:
                logger.error("Cache missing required keys: 'meta' and 'inputs'")
                return False

            # Validate meta section
            meta = cache["meta"]
            required_meta_fields = ["demo_file", "player_id", "tick_range", "tick_rate"]
            for field in required_meta_fields:
                if field not in meta:
                    logger.error(f"Meta section missing required field: {field}")
                    return False

            # Validate tick_range
            if not isinstance(meta["tick_range"], list) or len(meta["tick_range"]) != 2:
                logger.error("tick_range must be a list of [min, max]")
                return False

            # Validate inputs section
            inputs = cache["inputs"]
            if not isinstance(inputs, dict):
                logger.error("Inputs must be a dictionary")
                return False

            # Validate a sample of tick entries
            sample_size = min(10, len(inputs))
            for tick_str in list(inputs.keys())[:sample_size]:
                # Check tick is numeric string
                try:
                    int(tick_str)
                except ValueError:
                    logger.error(f"Invalid tick key (must be numeric string): {tick_str}")
                    return False

                # Check tick data structure
                tick_data = inputs[tick_str]
                if not isinstance(tick_data, dict):
                    logger.error(f"Tick {tick_str} data must be a dictionary")
                    return False

                required_tick_fields = ["keys", "mouse", "subtick"]
                for field in required_tick_fields:
                    if field not in tick_data:
                        logger.error(f"Tick {tick_str} missing field: {field}")
                        return False

                # Validate field types
                if not isinstance(tick_data["keys"], list):
                    logger.error(f"Tick {tick_str} 'keys' must be a list")
                    return False

                if not isinstance(tick_data["mouse"], list):
                    logger.error(f"Tick {tick_str} 'mouse' must be a list")
                    return False

                if not isinstance(tick_data["subtick"], dict):
                    logger.error(f"Tick {tick_str} 'subtick' must be a dictionary")
                    return False

            logger.debug("Cache validation passed")
            return True

        except Exception as e:
            logger.error(f"Cache validation error: {e}")
            return False

    def get_cache_info(self, cache: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed information about cache contents.

        Args:
            cache: Cache dictionary

        Returns:
            Dictionary with cache statistics and metadata

        Example:
            >>> manager = CacheManager()
            >>> cache = manager.load_cache("demo.json")
            >>> info = manager.get_cache_info(cache)
            >>> print(f"Total ticks: {info['tick_count']}")
            >>> print(f"Duration: {info['duration_seconds']:.1f}s")
        """
        if not self.validate_cache(cache):
            return {"error": "Invalid cache structure"}

        meta = cache["meta"]
        inputs = cache["inputs"]

        # Calculate statistics
        tick_count = len(inputs)
        tick_range = meta["tick_range"]
        tick_rate = meta.get("tick_rate", 64)

        duration_ticks = tick_range[1] - tick_range[0] if tick_count > 0 else 0
        duration_seconds = duration_ticks / tick_rate if tick_rate > 0 else 0

        # Analyze input patterns
        total_keys_pressed = 0
        total_mouse_actions = 0
        unique_keys = set()
        unique_mouse_buttons = set()

        for tick_data in inputs.values():
            keys = tick_data.get("keys", [])
            mouse = tick_data.get("mouse", [])

            total_keys_pressed += len(keys)
            total_mouse_actions += len(mouse)

            unique_keys.update(keys)
            unique_mouse_buttons.update(mouse)

        info = {
            "demo_file": meta.get("demo_file", "unknown"),
            "player_id": meta.get("player_id", "unknown"),
            "player_name": meta.get("player_name", "unknown"),
            "tick_count": tick_count,
            "tick_range": tick_range,
            "tick_rate": tick_rate,
            "duration_seconds": round(duration_seconds, 2),
            "duration_formatted": self._format_duration(duration_seconds),
            "total_keys_pressed": total_keys_pressed,
            "total_mouse_actions": total_mouse_actions,
            "unique_keys": sorted(list(unique_keys)),
            "unique_mouse_buttons": sorted(list(unique_mouse_buttons)),
            "avg_keys_per_tick": round(total_keys_pressed / tick_count, 2) if tick_count > 0 else 0,
            "avg_mouse_per_tick": round(total_mouse_actions / tick_count, 2) if tick_count > 0 else 0,
        }

        return info

    def _format_duration(self, seconds: float) -> str:
        """Format duration in seconds to human-readable string.

        Args:
            seconds: Duration in seconds

        Returns:
            Formatted string (e.g., "5m 30s")
        """
        minutes = int(seconds // 60)
        remaining_seconds = int(seconds % 60)

        if minutes > 0:
            return f"{minutes}m {remaining_seconds}s"
        else:
            return f"{remaining_seconds}s"


# Utility functions

def get_cache_size(cache_path: str) -> int:
    """Get file size of cache in bytes.

    Args:
        cache_path: Path to cache file

    Returns:
        File size in bytes, or -1 if file not found

    Example:
        >>> size_bytes = get_cache_size("demo_cache.json")
        >>> size_mb = size_bytes / (1024 * 1024)
        >>> print(f"Cache size: {size_mb:.2f} MB")
    """
    try:
        return os.path.getsize(cache_path)
    except FileNotFoundError:
        logger.error(f"Cache file not found: {cache_path}")
        return -1


def convert_cache_format(
    input_path: str,
    output_path: str,
    target_format: str = "auto"
) -> bool:
    """Convert cache from one format to another.

    Args:
        input_path: Source cache file path
        output_path: Destination cache file path
        target_format: Target format ('auto', 'json', or 'msgpack')

    Returns:
        True if conversion was successful, False otherwise

    Example:
        >>> # Convert JSON to MessagePack for production
        >>> convert_cache_format("demo.json", "demo.msgpack", "msgpack")
        True

        >>> # Auto-detect from extension
        >>> convert_cache_format("demo.json", "demo.msgpack")
        True
    """
    try:
        manager = CacheManager()

        # Load from source
        logger.info(f"Loading cache from {input_path}")
        cache = manager.load_cache(input_path)

        if cache is None:
            logger.error("Failed to load source cache")
            return False

        # Save to destination
        logger.info(f"Converting to {target_format} format")
        success = manager.save_cache(cache, output_path, format=target_format)

        if success:
            input_size = get_cache_size(input_path)
            output_size = get_cache_size(output_path)
            compression_ratio = (1 - output_size / input_size) * 100 if input_size > 0 else 0

            logger.info(
                f"Conversion complete: {input_size / 1024:.2f} KB → "
                f"{output_size / 1024:.2f} KB "
                f"({compression_ratio:+.1f}% size change)"
            )

        return success

    except Exception as e:
        logger.error(f"Conversion failed: {e}")
        return False


def compare_cache_formats(cache_path_json: str, cache_path_msgpack: str):
    """Compare JSON and MessagePack cache formats for size and performance.

    Args:
        cache_path_json: Path to JSON cache
        cache_path_msgpack: Path to MessagePack cache

    Example:
        >>> compare_cache_formats("demo.json", "demo.msgpack")
        Format Comparison:
        JSON:       1024.50 KB
        MessagePack: 512.25 KB (50.0% smaller)
    """
    json_size = get_cache_size(cache_path_json)
    msgpack_size = get_cache_size(cache_path_msgpack)

    if json_size == -1 or msgpack_size == -1:
        logger.error("One or both cache files not found")
        return

    size_reduction = (1 - msgpack_size / json_size) * 100 if json_size > 0 else 0

    print("\nFormat Comparison:")
    print(f"JSON:        {json_size / 1024:.2f} KB")
    print(f"MessagePack: {msgpack_size / 1024:.2f} KB ({size_reduction:.1f}% smaller)")

    # Test load times
    import time

    manager = CacheManager()

    # JSON load time
    start = time.time()
    manager.load_cache(cache_path_json)
    json_time = time.time() - start

    # MessagePack load time
    start = time.time()
    manager.load_cache(cache_path_msgpack)
    msgpack_time = time.time() - start

    speedup = json_time / msgpack_time if msgpack_time > 0 else 0

    print(f"\nLoad Time Comparison:")
    print(f"JSON:        {json_time * 1000:.2f} ms")
    print(f"MessagePack: {msgpack_time * 1000:.2f} ms ({speedup:.1f}x faster)")


# Example usage and testing
if __name__ == "__main__":
    # Example: Create and use cache manager
    manager = CacheManager()

    # Create sample cache for testing
    sample_cache = {
        "meta": {
            "demo_file": "test_demo.dem",
            "player_id": "STEAM_1:0:123456789",
            "player_name": "TestPlayer",
            "tick_range": [0, 1000],
            "tick_rate": 64
        },
        "inputs": {
            "0": {
                "keys": ["W"],
                "mouse": [],
                "subtick": {"W": 0.0}
            },
            "1": {
                "keys": ["W"],
                "mouse": [],
                "subtick": {"W": 0.0}
            },
            "2": {
                "keys": ["W", "A"],
                "mouse": ["MOUSE1"],
                "subtick": {"W": 0.0, "A": 0.3, "MOUSE1": 0.5}
            }
        }
    }

    # Validate cache
    if manager.validate_cache(sample_cache):
        print("✓ Sample cache is valid")

    # Save as JSON
    manager.save_cache(sample_cache, "test_cache.json", format="json")

    # Load cache
    loaded_cache = manager.load_cache("test_cache.json")

    # Get cache info
    info = manager.get_cache_info(loaded_cache)
    print("\nCache Info:")
    for key, value in info.items():
        print(f"  {key}: {value}")

    # Optimize cache
    optimized = manager.optimize_cache(loaded_cache)

    # Save optimized version
    manager.save_cache(optimized, "test_cache_optimized.json", format="json")

    # Test MessagePack if available
    if MSGPACK_AVAILABLE:
        manager.save_cache(sample_cache, "test_cache.msgpack", format="msgpack")
        compare_cache_formats("test_cache.json", "test_cache.msgpack")
    else:
        print("\nMessagePack not available. Install with: pip install msgpack")
