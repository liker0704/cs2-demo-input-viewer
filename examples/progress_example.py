"""Example demonstrating ETL progress reporting.

This script shows how to use the progress callback feature in the ETL pipeline
to track progress during demo processing.

Usage:
    python examples/progress_example.py path/to/demo.dem
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.parsers.etl_pipeline import DemoETLPipeline
from src.utils.progress import ProgressBar


def main():
    """Run ETL pipeline with progress bar."""
    if len(sys.argv) < 2:
        print("Usage: python progress_example.py <demo_file>")
        print("\nExample:")
        print("  python progress_example.py tests/fixtures/demo.dem")
        return 1

    demo_path = sys.argv[1]

    # Create progress bar
    progress_bar = ProgressBar(width=50)

    def on_progress(info):
        """Progress callback that renders a terminal progress bar."""
        phase = info.get('phase', '')
        overall_progress = info.get('overall_progress', 0.0)
        message = info.get('message', '')

        # Format the display message
        phase_display = phase.upper()
        full_message = f"[{phase_display}] {message}"

        # Render progress bar
        progress_bar.render(overall_progress, full_message)

    try:
        # Initialize pipeline
        pipeline = DemoETLPipeline(demo_path, output_dir="./cache")

        # Run with progress callback
        print("Processing demo with progress tracking...\n")
        cache_path = pipeline.run(
            player_id=None,  # Auto-detect
            optimize=True,
            format="json",
            progress_callback=on_progress
        )

        # Finish progress bar
        progress_bar.finish("Complete!")

        print(f"\nSuccess! Cache saved to: {cache_path}")

        # Show metadata
        metadata = pipeline.get_metadata(cache_path)
        print(f"\nDemo Information:")
        print(f"  Player: {metadata.player_name} ({metadata.player_id})")
        print(f"  Duration: {metadata.duration_seconds:.2f} seconds")
        print(f"  Tick Range: {metadata.tick_range[0]} - {metadata.tick_range[1]}")

        return 0

    except Exception as e:
        progress_bar.clear()
        print(f"\nError: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
