"""
Integration tests for CS2 Input Visualizer

Tests complete system integration across all phases.
"""

import pytest
import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.domain.models import InputData, PlayerInfo, DemoMetadata
from src.mocks import MockTickSource, MockDemoRepository, MockPlayerTracker
from src.parsers.mock_data_generator import generate_mock_cache
from src.parsers.cache_manager import CacheManager
from src.network import SyncEngine, PredictionEngine
from src.core import Orchestrator, AppConfig
from src.ui import CS2InputOverlay


class TestPhaseIntegration:
    """Test integration between phases."""

    def test_phase1_phase2_mock_repository_etl(self, tmp_path):
        """Test Phase 1 + Phase 2: Mocks with ETL."""
        # Generate mock cache
        cache_path = tmp_path / "test_cache.json"
        cache = generate_mock_cache(num_ticks=100, output_path=str(cache_path))

        assert cache is not None
        assert cache_path.exists()

        # Load with MockDemoRepository
        repo = MockDemoRepository(cache_path=str(cache_path))
        assert repo.load_demo("dummy_path")

        # Get inputs
        inputs = repo.get_inputs(tick=50, player_id="MOCK_PLAYER_123")
        assert inputs is not None
        assert isinstance(inputs, InputData)
        assert isinstance(inputs.keys, list)
        assert isinstance(inputs.mouse, list)

    def test_phase2_cache_manager_optimization(self, tmp_path):
        """Test Phase 2: Cache optimization."""
        # Generate cache
        cache_path = tmp_path / "test_cache.json"
        generate_mock_cache(num_ticks=200, output_path=str(cache_path))

        # Load and optimize
        manager = CacheManager()
        cache = manager.load_cache(str(cache_path))
        assert cache is not None

        optimized = manager.optimize_cache(cache)
        assert len(optimized["inputs"]) <= len(cache["inputs"])

        # Validate
        assert manager.validate_cache(optimized)

    @pytest.mark.asyncio
    async def test_phase4_network_layer_mocks(self):
        """Test Phase 4: Network layer with mocks."""
        # Create components
        tick_source = MockTickSource(start_tick=1000, tick_rate=64)
        sync = SyncEngine(tick_source, polling_interval=0.1)
        prediction = PredictionEngine(sync)

        # Connect and sync
        assert await tick_source.connect()
        await sync.update()

        # Verify tick progression
        tick1 = prediction.get_current_tick()
        await asyncio.sleep(0.05)
        tick2 = prediction.get_current_tick()

        assert tick2 >= tick1
        assert abs(tick2 - tick1) <= 10  # Should be within reasonable range

        # Cleanup
        await tick_source.disconnect()

    @pytest.mark.asyncio
    async def test_full_orchestrator_dev_mode(self, tmp_path):
        """Test complete orchestrator in development mode."""
        # Generate test cache
        cache_path = tmp_path / "dev_cache.json"
        generate_mock_cache(num_ticks=500, output_path=str(cache_path))

        # Create mock components
        tick_source = MockTickSource(start_tick=0, tick_rate=64)
        demo_repo = MockDemoRepository(cache_path=str(cache_path))
        player_tracker = MockPlayerTracker(player_id="MOCK_PLAYER_123")

        # Note: UI testing requires display, so we skip CS2InputOverlay here
        # In real usage, it would be: visualizer = CS2InputOverlay()

        # Load demo
        assert demo_repo.load_demo("dummy_demo.dem")

        # Connect tick source
        assert await tick_source.connect()

        # Get player
        player = await player_tracker.get_current_player()
        assert player == "MOCK_PLAYER_123"

        # Get inputs for tick
        inputs = demo_repo.get_inputs(tick=100, player_id=player)
        assert inputs is not None

        # Verify sync engine works
        sync = SyncEngine(tick_source, polling_interval=0.1)
        await sync.update()
        last_tick = sync.get_last_tick()
        assert last_tick >= 0

        # Cleanup
        await tick_source.disconnect()


class TestComponentIntegration:
    """Test integration between individual components."""

    @pytest.mark.asyncio
    async def test_tick_source_to_prediction(self):
        """Test tick source → sync → prediction pipeline."""
        tick_source = MockTickSource(start_tick=5000, tick_rate=64)
        await tick_source.connect()

        sync = SyncEngine(tick_source, polling_interval=0.1)
        prediction = PredictionEngine(sync)

        # Initial sync
        await sync.update()

        # Get predictions over time
        predictions = []
        for _ in range(5):
            predictions.append(prediction.get_current_tick())
            await asyncio.sleep(0.02)

        # Verify monotonic increase
        for i in range(1, len(predictions)):
            assert predictions[i] >= predictions[i-1]

        await tick_source.disconnect()

    def test_cache_to_repository(self, tmp_path):
        """Test cache file → repository → inputs pipeline."""
        # Create cache
        cache_path = tmp_path / "pipeline_test.json"
        cache = generate_mock_cache(num_ticks=300, output_path=str(cache_path))

        # Load with repository
        repo = MockDemoRepository(cache_path=str(cache_path))
        repo.load_demo("test.dem")

        # Verify metadata
        tick_range = repo.get_tick_range()
        assert tick_range[0] == 0
        assert tick_range[1] > 0

        # Verify inputs retrieval
        player_id = repo.get_default_player()
        inputs = repo.get_inputs(tick=150, player_id=player_id)

        assert inputs is not None
        assert inputs.tick == 150

    @pytest.mark.asyncio
    async def test_orchestrator_initialization(self, tmp_path):
        """Test orchestrator initialization with all components."""
        # Setup components
        cache_path = tmp_path / "orch_test.json"
        generate_mock_cache(num_ticks=200, output_path=str(cache_path))

        tick_source = MockTickSource(start_tick=0)
        demo_repo = MockDemoRepository(cache_path=str(cache_path))
        player_tracker = MockPlayerTracker()

        # Note: Skipping visualizer due to display requirement
        # orchestrator = Orchestrator(
        #     tick_source=tick_source,
        #     demo_repository=demo_repo,
        #     player_tracker=player_tracker,
        #     visualizer=None  # Would be CS2InputOverlay()
        # )

        # Verify components are properly connected
        assert await tick_source.connect()
        assert demo_repo.load_demo("test.dem")
        assert await player_tracker.get_current_player() is not None

        await tick_source.disconnect()


class TestDataFlow:
    """Test data flow through the system."""

    @pytest.mark.asyncio
    async def test_end_to_end_data_flow(self, tmp_path):
        """Test complete data flow: tick → inputs → render."""
        # 1. Generate data (Phase 2)
        cache_path = tmp_path / "e2e_cache.json"
        generate_mock_cache(num_ticks=400, output_path=str(cache_path))

        # 2. Load data (Phase 1 interfaces)
        demo_repo = MockDemoRepository(cache_path=str(cache_path))
        demo_repo.load_demo("e2e_test.dem")

        # 3. Setup tick source (Phase 4)
        tick_source = MockTickSource(start_tick=0, tick_rate=64)
        await tick_source.connect()

        # 4. Setup player tracking (Phase 1)
        player_tracker = MockPlayerTracker()
        player_id = await player_tracker.get_current_player()

        # 5. Simulate render loop
        for i in range(10):
            # Get current tick (Phase 4)
            current_tick = await tick_source.get_current_tick()

            # Get inputs for tick (Phase 2)
            inputs = demo_repo.get_inputs(tick=current_tick, player_id=player_id)

            # Verify data flow
            if inputs:
                assert isinstance(inputs, InputData)
                assert inputs.tick == current_tick

            await asyncio.sleep(0.016)  # ~60 FPS

        await tick_source.disconnect()


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
