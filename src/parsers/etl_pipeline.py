"""Complete ETL Pipeline for CS2 Input Visualizer.

This module implements a full Extract-Transform-Load pipeline for processing
CS2 demo files (.dem) into optimized cache files for real-time input visualization.

Pipeline Stages:
1. Extract: Parse .dem files using demoparser2 to extract input events
2. Transform: Decode button masks, process subtick data, filter by player
3. Load: Save processed data to optimized cache format

Usage:
    pipeline = DemoETLPipeline("path/to/demo.dem")
    cache_path = pipeline.run(player_id="STEAM_1:0:123456")
"""

import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from collections import Counter

from .button_decoder import decode_buttons, ButtonPress
from .cache_manager import CacheManager
from ..domain.models import DemoMetadata

# Configure logging
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('[%(levelname)s] %(message)s'))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# Try to import demoparser2 with graceful fallback
try:
    from demoparser2 import DemoParser
    HAS_DEMOPARSER = True
except ImportError:
    logger.warning(
        "demoparser2 not installed. ETL will not work with real demos. "
        "Install with: pip install demoparser2"
    )
    DemoParser = None
    HAS_DEMOPARSER = False


class DemoETLPipeline:
    """Complete ETL pipeline for demo processing.

    Extracts player input data from CS2 demo files, transforms it into
    a structured format with decoded buttons and subtick timing, and
    loads it into an optimized cache for real-time playback.

    Attributes:
        demo_path: Path to the input .dem file
        output_dir: Directory where cache files will be saved
        cache_manager: CacheManager instance for saving caches
    """

    def __init__(self, demo_path: str, output_dir: str = "./cache"):
        """Initialize the ETL pipeline.

        Args:
            demo_path: Path to the .dem demo file
            output_dir: Directory to save cache files (default: "./cache")

        Raises:
            FileNotFoundError: If demo file doesn't exist
        """
        self.demo_path = Path(demo_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        if not self.demo_path.exists():
            raise FileNotFoundError(f"Demo file not found: {self.demo_path}")

        self.cache_manager = CacheManager()
        logger.info(f"Initialized ETL pipeline for: {self.demo_path.name}")

    def run(
        self,
        player_id: Optional[str] = None,
        optimize: bool = True,
        format: str = "json"
    ) -> str:
        """Run complete ETL pipeline.

        Args:
            player_id: Target player SteamID (None for auto-detect)
            optimize: Whether to optimize cache by removing duplicate entries
            format: Output format ("json", "msgpack", or "sqlite")

        Returns:
            Path to generated cache file

        Raises:
            RuntimeError: If demoparser2 is not installed
            ValueError: If demo parsing fails
        """
        logger.info("=" * 60)
        logger.info(f"Starting ETL pipeline for: {self.demo_path.name}")
        logger.info("=" * 60)

        # EXTRACT
        logger.info("Phase 1/3: Extracting data from demo file...")
        raw_data = self._extract()
        logger.info(f"✓ Extracted {len(raw_data)} input events")

        # TRANSFORM
        logger.info("Phase 2/3: Transforming data...")
        cache_data = self._transform(raw_data, player_id)
        logger.info(
            f"✓ Transformed data for player {cache_data['meta']['player_id']}"
        )
        logger.info(
            f"  Tick range: {cache_data['meta']['tick_range'][0]} - "
            f"{cache_data['meta']['tick_range'][1]}"
        )
        logger.info(f"  Total ticks with input: {len(cache_data['inputs'])}")

        # Optimize if requested
        if optimize:
            logger.info("Optimizing cache...")
            cache_data = self.cache_manager.optimize_cache(cache_data)

        # LOAD
        logger.info("Phase 3/3: Loading to cache...")
        cache_path = self._load(cache_data, format)
        logger.info(f"✓ Cache saved to: {cache_path}")

        logger.info("=" * 60)
        logger.info("ETL pipeline completed successfully!")
        logger.info("=" * 60)

        return cache_path

    def _extract(self) -> list:
        """Extract phase: Parse demo file using demoparser2.

        Returns:
            List of input events with raw data

        Raises:
            RuntimeError: If demoparser2 is not installed
            ValueError: If demo parsing fails
        """
        if not HAS_DEMOPARSER:
            raise RuntimeError(
                "demoparser2 is required for demo parsing. "
                "Install with: pip install demoparser2"
            )

        try:
            logger.info(f"Parsing demo file: {self.demo_path}")
            parser = DemoParser(str(self.demo_path))

            # Define required fields for extraction
            fields = [
                "m_nButtonDownMaskPrev",  # Button bitmask
                "subtick_moves",          # Subtick timing data
                "m_steamID",              # Player identification
                "tick",                   # Tick number
                "name",                   # Player name (optional)
            ]

            # Parse player input events
            logger.info("Parsing player input events...")
            df = parser.parse_event(
                "player_input",
                player=["m_steamID", "name"],
                other=["m_nButtonDownMaskPrev", "subtick_moves", "tick"]
            )

            # Convert DataFrame to list of dicts
            if hasattr(df, 'to_dict'):
                # pandas DataFrame
                events = df.to_dict('records')
            elif isinstance(df, list):
                # Already a list
                events = df
            else:
                # Try to convert to list
                events = list(df)

            logger.info(f"Successfully parsed {len(events)} input events")
            return events

        except Exception as e:
            logger.error(f"Failed to parse demo file: {e}")
            raise ValueError(f"Demo parsing failed: {e}")

    def _transform(
        self,
        raw_data: list,
        player_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Transform phase: Decode buttons and process subtick data.

        Args:
            raw_data: Raw input events from extraction phase
            player_id: Target player SteamID (None for auto-detect)

        Returns:
            Transformed cache data dictionary

        Raises:
            ValueError: If no valid player data found
        """
        # Auto-detect player if not specified
        if player_id is None:
            player_id = self._detect_player(raw_data)
            logger.info(f"Auto-detected player: {player_id}")

        # Filter events for target player
        player_events = [
            event for event in raw_data
            if event.get('m_steamID') == player_id
        ]

        if not player_events:
            raise ValueError(
                f"No input events found for player: {player_id}. "
                f"Available players: {self._get_available_players(raw_data)}"
            )

        logger.info(f"Processing {len(player_events)} events for player {player_id}")

        # Get player name
        player_name = "Unknown"
        for event in player_events:
            if event.get('name'):
                player_name = event['name']
                break

        # Build cache structure
        ticks = [event.get('tick', 0) for event in player_events]
        tick_min = int(min(ticks)) if ticks else 0
        tick_max = int(max(ticks)) if ticks else 0

        cache = {
            "meta": {
                "demo_file": self.demo_path.name,
                "player_id": player_id,
                "player_name": player_name,
                "tick_range": [tick_min, tick_max],
                "tick_rate": 64,  # CS2 default tick rate
                "total_events": len(player_events)
            },
            "inputs": {}
        }

        # Transform each event
        logger.info("Decoding button masks and processing subtick data...")
        processed_count = 0

        for event in player_events:
            tick = int(event.get('tick', 0))
            mask = int(event.get('m_nButtonDownMaskPrev', 0))
            subtick_moves = event.get('subtick_moves', None)

            # Handle None or invalid subtick_moves
            if subtick_moves is None or not isinstance(subtick_moves, list):
                subtick_moves = []

            # Decode button mask into button presses
            button_presses = decode_buttons(mask, subtick_moves)

            # Separate keyboard and mouse inputs
            keyboard_keys = []
            mouse_keys = []
            subtick_data = {}

            for btn in button_presses:
                if 'Mouse' in btn.key:
                    mouse_keys.append(btn.key)
                else:
                    keyboard_keys.append(btn.key)

                # Store subtick timing
                if btn.subtick_offset > 0:
                    subtick_data[btn.key] = btn.subtick_offset

            # Only store ticks with actual input
            if keyboard_keys or mouse_keys:
                cache["inputs"][str(tick)] = {
                    "keys": keyboard_keys,
                    "mouse": mouse_keys,
                    "subtick": subtick_data
                }
                processed_count += 1

        logger.info(f"Processed {processed_count} ticks with active inputs")

        return cache

    def _load(self, cache_data: Dict[str, Any], format: str = "json") -> str:
        """Load phase: Save cache to disk.

        Args:
            cache_data: Transformed cache data
            format: Output format ("json", "msgpack", or "sqlite")

        Returns:
            Path to saved cache file
        """
        # Generate cache filename from demo name
        demo_name = self.demo_path.stem
        player_id = cache_data['meta']['player_id'].replace(':', '_')

        # Determine file extension based on format
        extensions = {
            "json": ".json",
            "msgpack": ".msgpack",
            "sqlite": ".db"
        }
        ext = extensions.get(format, ".json")
        cache_path = self.output_dir / f"{demo_name}_{player_id}_cache{ext}"

        # Save using cache manager
        self.cache_manager.save_cache(
            cache_data,
            str(cache_path),
            format=format
        )

        return str(cache_path)

    def _detect_player(self, raw_data: list) -> str:
        """Auto-detect the most frequent player in the demo.

        Args:
            raw_data: List of input events

        Returns:
            Steam ID of the most frequent player

        Raises:
            ValueError: If no valid player IDs found
        """
        logger.info("Auto-detecting player...")

        # Count occurrences of each player
        player_counts = Counter()
        for event in raw_data:
            steam_id = event.get('m_steamID')
            if steam_id:
                player_counts[steam_id] += 1

        if not player_counts:
            raise ValueError("No player IDs found in demo data")

        # Get most frequent player
        most_common_player = player_counts.most_common(1)[0][0]

        logger.info(
            f"Found {len(player_counts)} unique players. "
            f"Most active: {most_common_player} "
            f"({player_counts[most_common_player]} events)"
        )

        return most_common_player

    def _get_available_players(self, raw_data: list) -> list:
        """Get list of all available player IDs in the demo.

        Args:
            raw_data: List of input events

        Returns:
            List of unique Steam IDs
        """
        players = set()
        for event in raw_data:
            steam_id = event.get('m_steamID')
            if steam_id:
                players.add(steam_id)
        return sorted(list(players))

    def get_metadata(self, cache_path: str) -> DemoMetadata:
        """Load metadata from a cache file.

        Args:
            cache_path: Path to cache file

        Returns:
            DemoMetadata object with demo information
        """
        cache_data = self.cache_manager.load_cache(cache_path)
        meta = cache_data.get('meta', {})

        tick_range = tuple(meta.get('tick_range', [0, 0]))
        tick_rate = meta.get('tick_rate', 64)
        duration = (tick_range[1] - tick_range[0]) / tick_rate if tick_rate > 0 else 0

        return DemoMetadata(
            file_path=meta.get('demo_file', ''),
            player_id=meta.get('player_id', ''),
            player_name=meta.get('player_name', 'Unknown'),
            tick_range=tick_range,
            tick_rate=tick_rate,
            duration_seconds=duration
        )


def main():
    """CLI entry point for ETL pipeline."""
    import argparse

    parser = argparse.ArgumentParser(
        description='CS2 Demo ETL Pipeline - Extract, Transform, Load demo input data',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process demo with auto-detected player
  python -m src.parsers.etl_pipeline --demo match.dem

  # Process specific player
  python -m src.parsers.etl_pipeline --demo match.dem --player STEAM_1:0:123456

  # Custom output directory and format
  python -m src.parsers.etl_pipeline --demo match.dem --output ./my_cache --format msgpack

  # Disable optimization (keep all ticks)
  python -m src.parsers.etl_pipeline --demo match.dem --no-optimize
        """
    )

    parser.add_argument(
        '--demo',
        type=str,
        required=True,
        help='Path to .dem demo file'
    )

    parser.add_argument(
        '--player',
        type=str,
        default=None,
        help='Steam ID of player to extract (auto-detect if not specified)'
    )

    parser.add_argument(
        '--output',
        type=str,
        default='./cache',
        help='Output directory for cache files (default: ./cache)'
    )

    parser.add_argument(
        '--format',
        type=str,
        choices=['json', 'msgpack', 'sqlite'],
        default='json',
        help='Cache output format (default: json)'
    )

    parser.add_argument(
        '--no-optimize',
        action='store_true',
        help='Disable cache optimization (keep duplicate ticks)'
    )

    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        # Initialize and run pipeline
        pipeline = DemoETLPipeline(
            demo_path=args.demo,
            output_dir=args.output
        )

        cache_path = pipeline.run(
            player_id=args.player,
            optimize=not args.no_optimize,
            format=args.format
        )

        print(f"\n✓ Success! Cache saved to: {cache_path}")

        # Display metadata
        metadata = pipeline.get_metadata(cache_path)
        print(f"\nDemo Information:")
        print(f"  Player: {metadata.player_name} ({metadata.player_id})")
        print(f"  Duration: {metadata.duration_seconds:.2f} seconds")
        print(f"  Tick Range: {metadata.tick_range[0]} - {metadata.tick_range[1]}")
        print(f"  Tick Rate: {metadata.tick_rate} ticks/second")

        return 0

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Invalid input: {e}")
        return 1
    except RuntimeError as e:
        logger.error(f"Runtime error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
