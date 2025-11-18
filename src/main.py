"""CS2 Input Visualizer - Main Entry Point

This is the main entry point for the CS2 Input Visualizer application.
It provides a CLI interface for running the application in development or
production mode.

Usage:
    Development mode (testing without CS2):
        python src/main.py --mode dev

    Production mode (with CS2 and demo file):
        python src/main.py --mode prod --demo path/to/demo.dem

    Generate example config:
        python src/main.py --generate-config

    Custom configuration:
        python src/main.py --mode prod --demo demo.dem --config my_config.json

For more information, see README_USAGE.md
"""

import sys
import asyncio
import argparse
from pathlib import Path
from PyQt6.QtWidgets import QApplication

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from core.config import AppConfig, load_config, save_config, validate_config, create_default_config
from core.factory import create_dev_app, create_prod_app, validate_production_config


class Application:
    """Main application runner.

    This class manages the Qt application lifecycle and runs the orchestrator
    in an asyncio event loop.

    Attributes:
        config: Application configuration
        mode: Run mode ("dev" or "prod")
        qt_app: PyQt6 QApplication instance
        orchestrator: Main orchestrator instance
    """

    def __init__(self, config: AppConfig, mode: str = "dev"):
        """Initialize application.

        Args:
            config: Application configuration
            mode: Run mode - "dev" (mocks) or "prod" (real CS2)
        """
        self.config = config
        self.mode = mode

        # Create Qt application
        self.qt_app = QApplication.instance()
        if self.qt_app is None:
            self.qt_app = QApplication(sys.argv)

        # Set application metadata
        self.qt_app.setApplicationName("CS2 Input Visualizer")
        self.qt_app.setOrganizationName("CS2 Input Visualizer")

        # Create orchestrator based on mode
        print(f"\n[App] Creating application in {mode.upper()} mode...")

        try:
            if mode == "dev":
                self.orchestrator = create_dev_app(config)
            else:
                # Validate production config
                errors = validate_production_config(config)
                if errors:
                    print("\n[App] Configuration errors:")
                    for error in errors:
                        print(f"  - {error}")
                    print("\nPlease fix configuration errors and try again.")
                    raise ValueError("Invalid production configuration")

                self.orchestrator = create_prod_app(config)

        except Exception as e:
            print(f"\n[App] Failed to create application: {e}")
            raise

    def run(self):
        """Run application.

        Starts the orchestrator in an asyncio event loop and handles cleanup
        on exit.
        """
        print(f"\n[App] Starting CS2 Input Visualizer in {self.mode.upper()} mode...")
        print("[App] Press Ctrl+C to stop")
        print("-" * 60)

        # Create asyncio event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            # Run orchestrator
            loop.run_until_complete(self.orchestrator.start())

        except KeyboardInterrupt:
            print("\n[App] Interrupted by user (Ctrl+C)")

        except Exception as e:
            print(f"\n[App] Error during execution: {e}")
            import traceback
            traceback.print_exc()

        finally:
            # Cleanup
            print("\n[App] Shutting down...")

            # Stop orchestrator if still running
            try:
                loop.run_until_complete(self.orchestrator.stop())
            except Exception as e:
                print(f"[App] Error during cleanup: {e}")

            # Close Qt application
            self.qt_app.quit()

            # Close event loop
            loop.close()

        print("[App] Exited cleanly")


def main():
    """Main entry point with CLI argument parsing."""

    parser = argparse.ArgumentParser(
        description="CS2 Input Visualizer - Visualize player inputs from CS2 demo files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test mode (no CS2 required)
  python src/main.py --mode dev

  # Production mode with demo file
  python src/main.py --mode prod --demo demos/match.dem

  # Custom configuration
  python src/main.py --mode prod --demo demos/match.dem --config my_config.json

  # Generate example configuration
  python src/main.py --generate-config

  # Specify player manually
  python src/main.py --mode prod --demo demos/match.dem --player STEAM_1:0:123456789

For more information, see README_USAGE.md
        """
    )

    # Mode selection
    parser.add_argument(
        "--mode",
        choices=["dev", "prod"],
        default="dev",
        help="Run mode: 'dev' (mock components, no CS2 needed) or 'prod' (real CS2 connection)"
    )

    # Configuration
    parser.add_argument(
        "--config",
        type=str,
        default="config.json",
        help="Path to configuration file (default: config.json)"
    )

    # Demo file
    parser.add_argument(
        "--demo",
        type=str,
        help="Path to demo file (.dem) - required for prod mode"
    )

    # Player selection
    parser.add_argument(
        "--player",
        type=str,
        help="Player Steam ID to visualize (default: auto-detect from demo)"
    )

    # Config generation
    parser.add_argument(
        "--generate-config",
        action="store_true",
        help="Generate example configuration file and exit"
    )

    # Debug mode
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode with verbose logging"
    )

    args = parser.parse_args()

    # Handle config generation
    if args.generate_config:
        print("[Config] Generating example configuration...")
        try:
            create_default_config("config.example.json")
            print("[Config] Example configuration saved to: config.example.json")
            print("[Config] Copy to config.json and edit as needed:")
            print("  cp config.example.json config.json")
            return 0
        except Exception as e:
            print(f"[Config] Error generating config: {e}")
            return 1

    # Load configuration
    print(f"[Config] Loading configuration from: {args.config}")
    try:
        config = load_config(args.config)
    except Exception as e:
        print(f"[Config] Error loading config: {e}")
        print("[Config] Using default configuration")
        config = AppConfig()

    # Apply CLI argument overrides
    if args.demo:
        config.demo_path = args.demo
        print(f"[Config] Demo path: {args.demo}")

    if args.player:
        config.target_player_id = args.player
        print(f"[Config] Target player: {args.player}")

    if args.debug:
        config.debug_mode = True
        print("[Config] Debug mode enabled")

    # Validate configuration
    print("\n[Config] Validating configuration...")
    validation_errors = validate_config(config)

    if validation_errors:
        print("[Config] Configuration warnings/errors:")
        for error in validation_errors:
            print(f"  - {error}")

        # Only abort on critical errors in production mode
        if args.mode == "prod":
            critical_errors = [e for e in validation_errors if not e.startswith("Warning:")]
            if critical_errors:
                print("\n[Config] Critical errors found. Please fix and try again.")
                return 1

    # Additional validation for production mode
    if args.mode == "prod":
        if not config.demo_path:
            print("\n[Error] --demo is required for production mode")
            print("Usage: python src/main.py --mode prod --demo path/to/demo.dem")
            return 1

        demo_path = Path(config.demo_path)
        if not demo_path.exists():
            print(f"\n[Error] Demo file not found: {config.demo_path}")
            return 1

        # Check if cache exists
        cache_dir = Path(config.cache_dir)
        cache_file = cache_dir / f"{demo_path.stem}_cache.json"

        if not cache_file.exists():
            print(f"\n[Error] Cache file not found: {cache_file}")
            print("\nYou need to run the ETL pipeline first to process the demo:")
            print(f"  python -m src.parsers.etl_pipeline --demo {config.demo_path}")
            print("\nThis will create the cache file needed for playback.")
            return 1

    # Display configuration summary
    print("\n" + "=" * 60)
    print("CS2 INPUT VISUALIZER")
    print("=" * 60)
    print(f"Mode:              {args.mode.upper()}")
    print(f"Demo file:         {config.demo_path or 'None (using mocks)'}")
    print(f"Player:            {config.target_player_id or 'Auto-detect'}")
    print(f"CS2 connection:    {config.cs2_host}:{config.cs2_port}")
    print(f"Render FPS:        {config.render_fps}")
    print(f"Polling interval:  {config.polling_interval * 1000:.0f}ms")
    print(f"Overlay position:  ({config.overlay_x}, {config.overlay_y})")
    print(f"Overlay opacity:   {config.overlay_opacity * 100:.0f}%")
    print("=" * 60)

    # Additional instructions for production mode
    if args.mode == "prod":
        print("\nCS2 SETUP REQUIRED:")
        print("  1. Launch CS2 with: -netconport 2121 -insecure")
        print("  2. Load demo in CS2: playdemo <demo_name>")
        print("  3. The overlay will sync automatically")
        print("\nWARNING: -insecure disables VAC. Only use for demo playback!")
        print("=" * 60)

    # Create and run application
    try:
        app = Application(config, mode=args.mode)
        app.run()
        return 0

    except ValueError as e:
        # Configuration or validation error
        print(f"\n[Error] {e}")
        return 1

    except FileNotFoundError as e:
        # Missing file error
        print(f"\n[Error] {e}")
        return 1

    except Exception as e:
        # Unexpected error
        print(f"\n[Error] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
