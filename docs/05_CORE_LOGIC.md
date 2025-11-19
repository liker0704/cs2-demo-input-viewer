# Core Logic Documentation

## CS2 Subtick Input Visualizer - Orchestrator & Integration

### 1. Overview

The Core Logic ties all layers together: Data, Network, and UI. It manages:

1. **Dependency Injection**: Switching between Mock and Real implementations
2. **Prediction Engine**: Smooth tick interpolation
3. **Event Loop**: Coordinating sync, prediction, and rendering
4. **State Management**: Tracking current state across components

---

## 2. Main Orchestrator

### 2.1 Orchestrator Class

```python
import asyncio
from typing import Optional
from interfaces.tick_source import ITickSource
from interfaces.demo_repository import IDemoRepository
from interfaces.player_tracker import IPlayerTracker
from interfaces.input_visualizer import IInputVisualizer


class Orchestrator:
    """Main orchestrator coordinating all system components.

    This class implements dependency injection pattern,
    allowing easy switching between mock and real implementations.
    """

    def __init__(
        self,
        tick_source: ITickSource,
        demo_repository: IDemoRepository,
        player_tracker: IPlayerTracker,
        visualizer: IInputVisualizer,
        polling_interval: float = 0.25,
        render_fps: int = 60
    ):
        """Initialize orchestrator with dependencies.

        Args:
            tick_source: Source of current tick (Telnet or Mock)
            demo_repository: Source of input data (Parser or Mock)
            player_tracker: Tracker for current player (CS2 or Mock)
            visualizer: UI overlay (PyQt6 or Mock)
            polling_interval: Network polling frequency in seconds
            render_fps: Target rendering FPS
        """
        # Dependencies
        self.tick_source = tick_source
        self.demo_repo = demo_repository
        self.player_tracker = player_tracker
        self.visualizer = visualizer

        # Configuration
        self.polling_interval = polling_interval
        self.render_fps = render_fps
        self.tick_rate = 64  # CS2 tick rate

        # State
        self._running = False
        self._current_tick = 0
        self._current_player = None

        # Components
        self.prediction_engine: Optional[PredictionEngine] = None
        self.sync_engine: Optional[SyncEngine] = None

    async def initialize(self) -> bool:
        """Initialize all components.

        Returns:
            bool: True if initialization successful
        """
        print("[Orchestrator] Initializing components...")

        # Connect to tick source
        if not await self.tick_source.connect():
            print("[Orchestrator] Failed to connect tick source")
            return False

        # Initialize player tracker
        await self.player_tracker.update()
        self._current_player = await self.player_tracker.get_current_player()

        if not self._current_player:
            print("[Orchestrator] Warning: No player selected")

        # Initialize sync and prediction engines
        self.sync_engine = SyncEngine(
            self.tick_source,
            self.polling_interval
        )

        self.prediction_engine = PredictionEngine(
            self.sync_engine,
            self.tick_rate
        )

        # Show visualizer
        self.visualizer.show()

        print("[Orchestrator] Initialization complete")
        return True

    async def start(self):
        """Start main loop."""
        if not await self.initialize():
            print("[Orchestrator] Initialization failed, aborting")
            return

        self._running = True

        # Start sync loop
        sync_task = asyncio.create_task(self._sync_loop())

        # Start render loop
        render_task = asyncio.create_task(self._render_loop())

        # Start player tracking loop
        player_task = asyncio.create_task(self._player_tracking_loop())

        print("[Orchestrator] All loops started")

        # Wait for all tasks
        await asyncio.gather(sync_task, render_task, player_task)

    async def stop(self):
        """Stop all loops and cleanup."""
        print("[Orchestrator] Stopping...")

        self._running = False

        # Disconnect tick source
        await self.tick_source.disconnect()

        # Hide visualizer
        self.visualizer.hide()

        print("[Orchestrator] Stopped")

    async def _sync_loop(self):
        """Periodic sync with tick source."""
        while self._running:
            try:
                # Update sync engine
                await self.sync_engine.update()

            except Exception as e:
                print(f"[Orchestrator] Sync error: {e}")

            await asyncio.sleep(self.polling_interval)

    async def _render_loop(self):
        """Render loop at target FPS."""
        frame_time = 1.0 / self.render_fps

        while self._running:
            try:
                # Get predicted tick
                self._current_tick = self.prediction_engine.get_current_tick()

                # Get input data for current tick and player
                input_data = self.demo_repo.get_inputs(
                    self._current_tick,
                    self._current_player
                )

                # Render
                if input_data:
                    self.visualizer.render(input_data)

            except Exception as e:
                print(f"[Orchestrator] Render error: {e}")

            await asyncio.sleep(frame_time)

    async def _player_tracking_loop(self):
        """Track current player (update every 1 second)."""
        while self._running:
            try:
                await self.player_tracker.update()
                new_player = await self.player_tracker.get_current_player()

                if new_player != self._current_player:
                    print(f"[Orchestrator] Player changed: {self._current_player} → {new_player}")
                    self._current_player = new_player

            except Exception as e:
                print(f"[Orchestrator] Player tracking error: {e}")

            await asyncio.sleep(1.0)
```

---

## 3. Prediction Engine

### 3.1 Basic Prediction

```python
import time
from typing import Optional


class PredictionEngine:
    """Tick prediction engine for smooth interpolation between syncs.

    CS2 runs at 64 Hz (one tick every 15.625ms).
    We poll network at 2-4 Hz (every 250-500ms).
    This engine predicts intermediate ticks for smooth visualization.
    """

    def __init__(self, sync_engine: 'SyncEngine', tick_rate: int = 64):
        """Initialize prediction engine.

        Args:
            sync_engine: Sync engine providing server tick updates
            tick_rate: Game tick rate (ticks per second)
        """
        self.sync_engine = sync_engine
        self.tick_rate = tick_rate
        self.tick_duration = 1.0 / tick_rate  # 15.625ms for 64 Hz

        # Prediction state
        self._predicted_tick = 0
        self._last_update_time = time.time()

    def get_current_tick(self) -> int:
        """Get current tick using prediction.

        Returns:
            int: Predicted current tick
        """
        # Get last known server tick
        server_tick = self.sync_engine.get_last_tick()

        if server_tick == 0:
            return 0

        # Time since last server update
        server_time = self.sync_engine.get_last_update_time()
        time_elapsed = time.time() - server_time

        # Predict ticks elapsed
        ticks_elapsed = int(time_elapsed / self.tick_duration)

        # Calculate predicted tick
        predicted = server_tick + ticks_elapsed

        # Apply drift correction
        predicted = self._apply_drift_correction(predicted, server_tick)

        self._predicted_tick = predicted
        return predicted

    def _apply_drift_correction(
        self,
        predicted: int,
        server_tick: int,
        max_drift: int = 10
    ) -> int:
        """Apply drift correction to prevent excessive prediction error.

        Args:
            predicted: Predicted tick
            server_tick: Last known server tick
            max_drift: Maximum allowed drift before snapping

        Returns:
            int: Corrected tick
        """
        drift = abs(predicted - server_tick)

        if drift > max_drift:
            # Large drift detected, snap to server tick
            print(f"[Prediction] Large drift ({drift} ticks), snapping to server")
            return server_tick

        return predicted

    def get_drift(self) -> int:
        """Get current drift between prediction and server.

        Returns:
            int: Tick drift
        """
        server_tick = self.sync_engine.get_last_tick()
        return self._predicted_tick - server_tick
```

### 3.2 Advanced Prediction with Smoothing

```python
class SmoothPredictionEngine(PredictionEngine):
    """Prediction engine with smoothing for jumps and pauses."""

    def __init__(self, *args, smoothing_window: int = 5, **kwargs):
        super().__init__(*args, **kwargs)
        self.smoothing_window = smoothing_window
        self._tick_history = []  # Recent tick measurements

    def get_current_tick(self) -> int:
        """Get smoothed predicted tick."""
        # Get base prediction
        predicted = super().get_current_tick()

        # Add to history
        self._tick_history.append(predicted)

        # Keep only recent history
        if len(self._tick_history) > self.smoothing_window:
            self._tick_history.pop(0)

        # Detect jump (user pressed Shift+F2 to jump to tick)
        if len(self._tick_history) >= 2:
            jump_size = abs(self._tick_history[-1] - self._tick_history[-2])

            if jump_size > 100:  # Large jump detected
                print(f"[Prediction] Jump detected ({jump_size} ticks)")
                # Clear history and accept new tick
                self._tick_history = [predicted]
                return predicted

        # Detect pause
        if self._is_paused():
            print("[Prediction] Pause detected")
            return self._tick_history[-1] if self._tick_history else 0

        return predicted

    def _is_paused(self) -> bool:
        """Detect if demo is paused.

        Returns:
            bool: True if paused
        """
        if len(self._tick_history) < 3:
            return False

        # If last 3 ticks are identical, likely paused
        recent = self._tick_history[-3:]
        return len(set(recent)) == 1
```

---

## 4. Sync Engine

### 4.1 Sync Engine Implementation

```python
class SyncEngine:
    """Synchronization engine for network polling."""

    def __init__(self, tick_source: ITickSource, polling_interval: float = 0.25):
        """Initialize sync engine.

        Args:
            tick_source: Source of tick data
            polling_interval: Polling frequency in seconds
        """
        self.tick_source = tick_source
        self.polling_interval = polling_interval

        # State
        self._last_tick = 0
        self._last_update_time = 0.0

    async def update(self):
        """Update tick from source."""
        try:
            tick = await self.tick_source.get_current_tick()
            self._last_tick = tick
            self._last_update_time = time.time()

        except Exception as e:
            print(f"[SyncEngine] Update error: {e}")

    def get_last_tick(self) -> int:
        """Get last known server tick.

        Returns:
            int: Last tick
        """
        return self._last_tick

    def get_last_update_time(self) -> float:
        """Get timestamp of last update.

        Returns:
            float: Unix timestamp
        """
        return self._last_update_time
```

---

## 5. Configuration System

### 5.1 Configuration Class

```python
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class AppConfig:
    """Application configuration."""

    # Network
    cs2_host: str = "127.0.0.1"
    cs2_port: int = 2121
    polling_interval: float = 0.25  # seconds

    # Rendering
    render_fps: int = 60
    overlay_opacity: float = 0.9

    # Data
    cache_dir: str = "./cache"
    demo_path: Optional[str] = None

    # Player
    target_player_id: Optional[str] = None  # None = auto-detect

    # Prediction
    max_drift: int = 10  # ticks
    smoothing_window: int = 5

    # UI
    overlay_scale: float = 1.0
    overlay_x: int = 100
    overlay_y: int = 100

    # Debug
    debug_mode: bool = False
    show_fps: bool = False


def load_config(path: str = "config.json") -> AppConfig:
    """Load configuration from file.

    Args:
        path: Path to config file

    Returns:
        AppConfig instance
    """
    import json
    from pathlib import Path

    config_path = Path(path)

    if not config_path.exists():
        print(f"[Config] No config file at {path}, using defaults")
        return AppConfig()

    with open(config_path, 'r') as f:
        data = json.load(f)

    return AppConfig(**data)


def save_config(config: AppConfig, path: str = "config.json"):
    """Save configuration to file.

    Args:
        config: AppConfig instance
        path: Output path
    """
    import json
    from dataclasses import asdict

    with open(path, 'w') as f:
        json.dump(asdict(config), f, indent=2)
```

---

## 6. Application Factory

### 6.1 Development Mode (Mocks)

```python
from mocks.tick_source import MockTickSource
from mocks.demo_repository import MockDemoRepository
from mocks.player_tracker import MockPlayerTracker


def create_dev_app(config: AppConfig) -> Orchestrator:
    """Create application with mock components for development.

    Args:
        config: Application configuration

    Returns:
        Orchestrator instance with mocks
    """
    print("[Factory] Creating DEV application (mocks)")

    # Create mock components
    tick_source = MockTickSource(
        start_tick=0,
        tick_rate=64
    )

    demo_repo = MockDemoRepository(
        cache_path="./cache/mock_cache.json"
    )

    player_tracker = MockPlayerTracker(
        player_id="MOCK_PLAYER_123"
    )

    visualizer = CS2InputOverlay()
    visualizer.set_opacity(config.overlay_opacity)

    # Create orchestrator
    orchestrator = Orchestrator(
        tick_source=tick_source,
        demo_repository=demo_repo,
        player_tracker=player_tracker,
        visualizer=visualizer,
        polling_interval=config.polling_interval,
        render_fps=config.render_fps
    )

    return orchestrator
```

### 6.2 Production Mode (Real)

```python
from network.telnet_client import CS2TelnetClient
from parsers.demo_parser import RealDemoParser
from network.player_tracker import ManualPlayerTracker


def create_prod_app(config: AppConfig) -> Orchestrator:
    """Create application with real components for production.

    Args:
        config: Application configuration

    Returns:
        Orchestrator instance with real implementations
    """
    print("[Factory] Creating PROD application (real)")

    # Create real components
    tick_source = CS2TelnetClient(
        host=config.cs2_host,
        port=config.cs2_port
    )

    demo_repo = RealDemoParser()

    # Load demo
    if config.demo_path:
        if not demo_repo.load_demo(config.demo_path):
            raise RuntimeError(f"Failed to load demo: {config.demo_path}")

    # Player tracker
    if config.target_player_id:
        player_tracker = ManualPlayerTracker(config.target_player_id)
    else:
        # Auto-detect from demo metadata
        player_id = demo_repo.get_default_player()
        player_tracker = ManualPlayerTracker(player_id)

    visualizer = CS2InputOverlay()
    visualizer.set_opacity(config.overlay_opacity)
    visualizer.setGeometry(
        config.overlay_x,
        config.overlay_y,
        700,
        300
    )

    # Create orchestrator with advanced prediction
    orchestrator = Orchestrator(
        tick_source=tick_source,
        demo_repository=demo_repo,
        player_tracker=player_tracker,
        visualizer=visualizer,
        polling_interval=config.polling_interval,
        render_fps=config.render_fps
    )

    # Use smooth prediction
    orchestrator.prediction_engine = SmoothPredictionEngine(
        orchestrator.sync_engine,
        tick_rate=64,
        smoothing_window=config.smoothing_window
    )

    return orchestrator
```

---

## 7. Main Entry Point

### 7.1 Application Runner

```python
import sys
import asyncio
from PyQt6.QtWidgets import QApplication


class Application:
    """Main application runner."""

    def __init__(self, config: AppConfig, mode: str = "dev"):
        """Initialize application.

        Args:
            config: Application configuration
            mode: "dev" or "prod"
        """
        self.config = config
        self.mode = mode

        # Create Qt application
        self.qt_app = QApplication(sys.argv)

        # Create orchestrator
        if mode == "dev":
            self.orchestrator = create_dev_app(config)
        else:
            self.orchestrator = create_prod_app(config)

    def run(self):
        """Run application."""
        print(f"[App] Starting in {self.mode.upper()} mode...")

        # Start orchestrator in async context
        loop = asyncio.get_event_loop()

        try:
            # Run orchestrator
            loop.run_until_complete(self.orchestrator.start())

        except KeyboardInterrupt:
            print("[App] Interrupted by user")

        finally:
            # Cleanup
            loop.run_until_complete(self.orchestrator.stop())
            self.qt_app.quit()

        print("[App] Exited")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="CS2 Input Visualizer")
    parser.add_argument(
        "--mode",
        choices=["dev", "prod"],
        default="dev",
        help="Run mode (dev with mocks, prod with real CS2)"
    )
    parser.add_argument(
        "--config",
        default="config.json",
        help="Path to config file"
    )
    parser.add_argument(
        "--demo",
        help="Path to demo file (overrides config)"
    )

    args = parser.parse_args()

    # Load config
    config = load_config(args.config)

    # Override with CLI args
    if args.demo:
        config.demo_path = args.demo

    # Create and run app
    app = Application(config, mode=args.mode)
    app.run()


if __name__ == "__main__":
    main()
```

---

## 8. Extensibility Examples

### 8.1 Adding Grenade Visualization

```python
# 1. Define interface
class IGrenadeTracker(ABC):
    @abstractmethod
    def get_grenades(self, tick: int, player_id: str) -> list:
        pass


# 2. Add to orchestrator
class ExtendedOrchestrator(Orchestrator):
    def __init__(self, *args, grenade_tracker: IGrenadeTracker, **kwargs):
        super().__init__(*args, **kwargs)
        self.grenade_tracker = grenade_tracker

    async def _render_loop(self):
        while self._running:
            # Get input data
            input_data = self.demo_repo.get_inputs(
                self._current_tick,
                self._current_player
            )

            # Get grenade data
            grenades = self.grenade_tracker.get_grenades(
                self._current_tick,
                self._current_player
            )

            # Render both
            self.visualizer.render(input_data)
            self.visualizer.render_grenades(grenades)

            await asyncio.sleep(1.0 / self.render_fps)
```

### 8.2 Adding Input Recording

```python
class RecordingOrchestrator(Orchestrator):
    """Orchestrator with recording capability."""

    def __init__(self, *args, output_file: str = "recording.json", **kwargs):
        super().__init__(*args, **kwargs)
        self.output_file = output_file
        self.recorded_data = []

    async def _render_loop(self):
        while self._running:
            input_data = self.demo_repo.get_inputs(
                self._current_tick,
                self._current_player
            )

            if input_data:
                # Record
                self.recorded_data.append({
                    "tick": self._current_tick,
                    "keys": input_data.keys,
                    "mouse": input_data.mouse
                })

                # Render
                self.visualizer.render(input_data)

            await asyncio.sleep(1.0 / self.render_fps)

    async def stop(self):
        # Save recording before stopping
        import json
        with open(self.output_file, 'w') as f:
            json.dump(self.recorded_data, f, indent=2)

        print(f"[Recording] Saved {len(self.recorded_data)} frames to {self.output_file}")

        await super().stop()
```

---

## 9. Error Handling & Recovery

### 9.1 Robust Orchestrator

```python
class RobustOrchestrator(Orchestrator):
    """Orchestrator with comprehensive error handling."""

    async def _sync_loop(self):
        retry_count = 0
        max_retries = 3

        while self._running:
            try:
                await self.sync_engine.update()
                retry_count = 0  # Reset on success

            except ConnectionError as e:
                retry_count += 1
                print(f"[Orchestrator] Connection error ({retry_count}/{max_retries}): {e}")

                if retry_count >= max_retries:
                    print("[Orchestrator] Max retries reached, reconnecting...")
                    await self.tick_source.disconnect()
                    await asyncio.sleep(2)

                    if await self.tick_source.connect():
                        retry_count = 0
                    else:
                        print("[Orchestrator] Reconnection failed, stopping")
                        await self.stop()
                        break

            except Exception as e:
                print(f"[Orchestrator] Unexpected sync error: {e}")
                import traceback
                traceback.print_exc()

            await asyncio.sleep(self.polling_interval)
```

---

## 10. Performance Monitoring

### 10.1 Performance Monitor

```python
import time
from collections import deque


class PerformanceMonitor:
    """Monitor application performance."""

    def __init__(self, window_size: int = 60):
        self.window_size = window_size
        self.frame_times = deque(maxlen=window_size)
        self.last_frame_time = time.time()

    def record_frame(self):
        """Record frame timing."""
        current_time = time.time()
        frame_time = current_time - self.last_frame_time
        self.frame_times.append(frame_time)
        self.last_frame_time = current_time

    def get_fps(self) -> float:
        """Get current FPS.

        Returns:
            float: Average FPS over window
        """
        if not self.frame_times:
            return 0.0

        avg_frame_time = sum(self.frame_times) / len(self.frame_times)
        return 1.0 / avg_frame_time if avg_frame_time > 0 else 0.0

    def get_stats(self) -> dict:
        """Get performance statistics.

        Returns:
            dict: Performance metrics
        """
        if not self.frame_times:
            return {}

        return {
            "fps": self.get_fps(),
            "avg_frame_time_ms": sum(self.frame_times) / len(self.frame_times) * 1000,
            "min_frame_time_ms": min(self.frame_times) * 1000,
            "max_frame_time_ms": max(self.frame_times) * 1000
        }


# Add to orchestrator
class MonitoredOrchestrator(Orchestrator):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.perf_monitor = PerformanceMonitor()

    async def _render_loop(self):
        while self._running:
            # Render
            # ... existing render logic ...

            # Record frame
            self.perf_monitor.record_frame()

            # Print stats every 60 frames
            if len(self.perf_monitor.frame_times) >= 60:
                stats = self.perf_monitor.get_stats()
                print(f"[Perf] FPS: {stats['fps']:.1f}, "
                      f"Avg: {stats['avg_frame_time_ms']:.2f}ms")

            await asyncio.sleep(1.0 / self.render_fps)
```

---

## 11. Testing

### 11.1 Orchestrator Unit Tests

```python
import pytest


@pytest.mark.asyncio
async def test_orchestrator_initialization():
    """Test orchestrator initialization."""
    config = AppConfig()
    orchestrator = create_dev_app(config)

    assert orchestrator.tick_source is not None
    assert orchestrator.demo_repo is not None
    assert orchestrator.player_tracker is not None


@pytest.mark.asyncio
async def test_orchestrator_lifecycle():
    """Test orchestrator start/stop."""
    config = AppConfig()
    orchestrator = create_dev_app(config)

    # Start
    start_task = asyncio.create_task(orchestrator.start())
    await asyncio.sleep(1)  # Let it run briefly

    # Stop
    await orchestrator.stop()

    assert not orchestrator._running
```

---

## 12. Next Steps

The Core Logic completes the system architecture. Next steps:

1. Implement all interfaces in `src/interfaces/`
2. Create mock implementations in `src/mocks/`
3. Build UI in `src/ui/`
4. Implement ETL in `src/parsers/`
5. Build network layer in `src/network/`
6. Assemble everything with orchestrator in `src/core/`
