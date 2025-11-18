"""E2E Smoke Tests for Auto Mode - Phase 6.

Simple end-to-end smoke tests to verify:
1. AutoOrchestrator can be imported and instantiated
2. All components are initialized correctly
3. start() and stop() methods exist
4. CS2PathDetector works with mock paths
5. CacheValidator works with real temp files

These tests are designed to run in headless environments without CS2.
"""

import pytest
import asyncio
import tempfile
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

# Import components for smoke testing
from src.core.auto_orchestrator import AutoOrchestrator
from src.core.config import AppConfig
from src.utils.cs2_detector import CS2PathDetector
from src.parsers.cache_validator import CacheValidator


class TestAutoOrchestratorSmoke:
    """Smoke tests for AutoOrchestrator initialization and basic functionality."""

    def test_import_auto_orchestrator(self):
        """Test that AutoOrchestrator can be imported successfully."""
        from src.core.auto_orchestrator import AutoOrchestrator
        assert AutoOrchestrator is not None

    def test_instantiate_with_default_config(self):
        """Test that AutoOrchestrator can be instantiated with default config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            # Use Path as config for backward compatibility
            orchestrator = AutoOrchestrator(
                config=cache_dir,
                host="127.0.0.1",
                port=2121
            )

            assert orchestrator is not None
            assert orchestrator.cache_dir == cache_dir
            assert cache_dir.exists()  # Should be created automatically

    def test_all_components_initialized(self):
        """Test that all required components are initialized."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            orchestrator = AutoOrchestrator(config=cache_dir)

            # Verify core components exist
            assert orchestrator.cs2_detector is not None
            assert isinstance(orchestrator.cs2_detector, CS2PathDetector)

            assert orchestrator.cache_validator is not None
            assert isinstance(orchestrator.cache_validator, CacheValidator)

            assert orchestrator.telnet_client is not None
            assert orchestrator.demo_repository is not None

            # Verify state variables exist
            assert hasattr(orchestrator, '_running')
            assert hasattr(orchestrator, '_current_demo')
            assert hasattr(orchestrator, '_current_cache')
            assert hasattr(orchestrator, '_current_player')
            assert hasattr(orchestrator, '_current_tick')

            # Verify configuration
            assert orchestrator.cache_dir == cache_dir

    def test_start_and_stop_methods_exist(self):
        """Test that start() and stop() methods exist and are callable."""
        with tempfile.TemporaryDirectory() as tmpdir:
            orchestrator = AutoOrchestrator(config=Path(tmpdir) / "cache")

            # Verify methods exist
            assert hasattr(orchestrator, 'start')
            assert hasattr(orchestrator, 'stop')

            # Verify they're coroutines
            assert asyncio.iscoroutinefunction(orchestrator.start)
            assert asyncio.iscoroutinefunction(orchestrator.stop)

    @pytest.mark.asyncio
    async def test_graceful_stop_without_start(self):
        """Test that stop() can be called without start()."""
        with tempfile.TemporaryDirectory() as tmpdir:
            orchestrator = AutoOrchestrator(config=Path(tmpdir) / "cache")

            # Should not raise exception
            await orchestrator.stop()

            # Verify running flag is False
            assert orchestrator._running is False


class TestCS2PathDetectorIsolated:
    """Isolated tests for CS2PathDetector with mock paths."""

    def test_detector_initialization(self):
        """Test that CS2PathDetector can be initialized."""
        detector = CS2PathDetector()
        assert detector is not None

    def test_find_cs2_path_with_valid_mock_path(self):
        """Test finding CS2 path with a valid mock directory structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create fake CS2 directory structure
            cs2_root = Path(tmpdir) / "Counter-Strike 2"
            csgo_dir = cs2_root / "game" / "csgo"
            csgo_dir.mkdir(parents=True)

            detector = CS2PathDetector()
            result = detector.find_cs2_path(config_path=cs2_root)

            assert result is not None
            assert result == csgo_dir
            assert result.exists()
            assert result.is_dir()

    def test_find_cs2_path_with_csgo_dir_directly(self):
        """Test finding CS2 path when config points directly to csgo dir."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create fake CS2 directory structure
            cs2_root = Path(tmpdir) / "Counter-Strike 2"
            csgo_dir = cs2_root / "game" / "csgo"
            csgo_dir.mkdir(parents=True)

            detector = CS2PathDetector()
            result = detector.find_cs2_path(config_path=csgo_dir)

            assert result == csgo_dir

    def test_find_cs2_path_with_invalid_path(self):
        """Test finding CS2 path with invalid path returns None."""
        detector = CS2PathDetector()
        result = detector.find_cs2_path(config_path=Path("/nonexistent/path"))

        # Should return None or find CS2 via other methods
        # In headless environment without CS2, should be None
        assert result is None or (result.exists() and result.is_dir())

    def test_validate_cs2_path_internal(self):
        """Test internal path validation logic."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create valid structure
            csgo_dir = Path(tmpdir) / "game" / "csgo"
            csgo_dir.mkdir(parents=True)

            detector = CS2PathDetector()

            # Test validation with csgo dir directly
            result = detector._validate_cs2_path(csgo_dir)
            assert result == csgo_dir

            # Test validation with game dir
            game_dir = csgo_dir.parent
            result = detector._validate_cs2_path(game_dir)
            assert result == csgo_dir

            # Test validation with nonexistent path
            fake_path = Path("/fake/path")
            result = detector._validate_cs2_path(fake_path)
            assert result is None


class TestCacheValidatorWithRealFiles:
    """Tests for CacheValidator using real temporary files."""

    def test_validator_initialization(self):
        """Test that CacheValidator can be initialized."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            validator = CacheValidator(cache_dir)

            assert validator is not None
            assert cache_dir.exists()  # Should be created
            assert validator.cache_dir == cache_dir

    def test_get_demo_hash_with_real_file(self):
        """Test computing hash of a real demo file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test demo file with some content
            demo_file = Path(tmpdir) / "test.dem"
            demo_data = b"CS2DEMO" * 1000  # Create some test data
            demo_file.write_bytes(demo_data)

            cache_dir = Path(tmpdir) / "cache"
            validator = CacheValidator(cache_dir)

            # Compute hash
            hash_result = validator.get_demo_hash(demo_file)

            # Verify hash format: "size_md5hash"
            assert "_" in hash_result
            size_part, hash_part = hash_result.split("_", 1)

            # Verify size matches
            assert size_part == str(len(demo_data))

            # Verify hash is MD5 (32 hex characters)
            assert len(hash_part) == 32
            assert all(c in "0123456789abcdef" for c in hash_part)

    def test_cache_validation_lifecycle(self):
        """Test complete cache validation lifecycle."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create demo file
            demo_file = Path(tmpdir) / "match.dem"
            demo_file.write_bytes(b"demo content here")

            cache_dir = Path(tmpdir) / "cache"
            validator = CacheValidator(cache_dir)

            # Step 1: Initial check - should be invalid (no cache)
            assert validator.is_cache_valid(demo_file) is False

            # Step 2: Create cache file
            cache_path = validator.get_cache_path(demo_file)
            cache_path.write_text('{"meta": {}, "inputs": {}}')

            # Still invalid (no hash file)
            assert validator.is_cache_valid(demo_file) is False

            # Step 3: Save hash
            success = validator.save_hash(demo_file)
            assert success is True

            # Step 4: Now cache should be valid
            assert validator.is_cache_valid(demo_file) is True

            # Step 5: Modify demo file
            demo_file.write_bytes(b"modified content")

            # Cache should now be invalid
            assert validator.is_cache_valid(demo_file) is False

    def test_get_cache_path_conversion(self):
        """Test cache path generation from demo file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            validator = CacheValidator(cache_dir)

            # Test with .dem file
            demo_file = Path(tmpdir) / "match.dem"
            cache_path = validator.get_cache_path(demo_file)

            # Cache path should preserve demo filename and add .json
            assert cache_path == cache_dir / "match.dem.json"
            assert cache_path.suffix == ".json"

    def test_invalidate_cache(self):
        """Test cache invalidation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create demo and cache
            demo_file = Path(tmpdir) / "test.dem"
            demo_file.write_bytes(b"content")

            cache_dir = Path(tmpdir) / "cache"
            validator = CacheValidator(cache_dir)

            # Create valid cache
            cache_path = validator.get_cache_path(demo_file)
            cache_path.write_text("{}")
            validator.save_hash(demo_file)

            # Verify valid
            assert validator.is_cache_valid(demo_file) is True

            # Invalidate
            result = validator.invalidate_cache(demo_file)
            assert result is True

            # Should now be invalid
            assert validator.is_cache_valid(demo_file) is False

    def test_get_cache_info(self):
        """Test getting cache information."""
        with tempfile.TemporaryDirectory() as tmpdir:
            demo_file = Path(tmpdir) / "test.dem"
            demo_file.write_bytes(b"x" * 1024)  # 1KB file

            cache_dir = Path(tmpdir) / "cache"
            validator = CacheValidator(cache_dir)

            # Get info for demo without cache
            info = validator.get_cache_info(demo_file)

            assert info["demo_exists"] is True
            assert info["cache_exists"] is False
            assert info["hash_exists"] is False
            assert info["is_valid"] is False
            assert info["demo_size"] == 1024
            assert info["current_hash"] is not None

            # Create cache and hash
            cache_path = validator.get_cache_path(demo_file)
            cache_path.write_text("{}")
            validator.save_hash(demo_file)

            # Get info again
            info = validator.get_cache_info(demo_file)

            assert info["demo_exists"] is True
            assert info["cache_exists"] is True
            assert info["hash_exists"] is True
            assert info["is_valid"] is True


class TestAutoModeIntegration:
    """Integration tests verifying components work together."""

    def test_components_can_be_used_together(self):
        """Test that CS2PathDetector and CacheValidator can work together."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup CS2 mock directory
            cs2_root = Path(tmpdir) / "cs2"
            csgo_dir = cs2_root / "game" / "csgo"
            csgo_dir.mkdir(parents=True)

            # Create demo file
            demo_file = csgo_dir / "match.dem"
            demo_file.write_bytes(b"demo data")

            # Test CS2 detection
            detector = CS2PathDetector()
            cs2_path = detector.find_cs2_path(config_path=cs2_root)
            assert cs2_path == csgo_dir

            # Test cache validation
            cache_dir = Path(tmpdir) / "cache"
            validator = CacheValidator(cache_dir)

            # Validate cache for demo in detected CS2 path
            assert validator.is_cache_valid(demo_file) is False

            # Create cache
            cache_path = validator.get_cache_path(demo_file)
            cache_path.write_text("{}")
            validator.save_hash(demo_file)

            assert validator.is_cache_valid(demo_file) is True


if __name__ == "__main__":
    """Run smoke tests directly."""
    print("=" * 70)
    print("CS2 Input Visualizer - Auto Mode E2E Smoke Tests")
    print("=" * 70)
    print()

    # Run with pytest
    pytest.main([__file__, "-v", "--tb=short"])
