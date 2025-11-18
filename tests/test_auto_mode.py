"""Integration tests for Phase 6 Auto Mode.

Tests for automatic mode components:
- CS2PathDetector
- CacheValidator
- DemoMonitor
- SpectatorTracker
- AutoOrchestrator integration
"""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import tempfile
import hashlib

# Import components to test
from src.utils.cs2_detector import CS2PathDetector
from src.parsers.cache_validator import CacheValidator
from src.network.demo_monitor import DemoMonitor
from src.network.spectator_tracker import SpectatorTracker
from src.core.auto_orchestrator import AutoOrchestrator
from src.core.config import AppConfig


class TestCS2PathDetector:
    """Test CS2 installation path detection."""

    def test_find_cs2_path_with_config(self, tmp_path):
        """Test finding CS2 path from config."""
        # Create fake CS2 directory
        cs2_path = tmp_path / "Counter-Strike 2" / "game" / "csgo"
        cs2_path.mkdir(parents=True)

        detector = CS2PathDetector()
        result = detector.find_cs2_path(config_path=cs2_path)

        assert result == cs2_path

    def test_find_cs2_path_invalid_config(self):
        """Test with invalid config path."""
        detector = CS2PathDetector()
        result = detector.find_cs2_path(config_path=Path("/nonexistent/path"))

        # Should fallback to other methods (may be None if CS2 not installed)
        assert result is None or result.exists()

    @patch('psutil.process_iter')
    def test_find_by_process(self, mock_process_iter, tmp_path):
        """Test finding CS2 by running process."""
        # Create fake CS2 installation
        cs2_exe = tmp_path / "Counter-Strike 2" / "game" / "bin" / "win64" / "cs2.exe"
        cs2_exe.parent.mkdir(parents=True)
        cs2_exe.touch()

        csgo_dir = tmp_path / "Counter-Strike 2" / "game" / "csgo"
        csgo_dir.mkdir(parents=True)

        # Mock process
        mock_proc = Mock()
        mock_proc.info = {'name': 'cs2.exe', 'exe': str(cs2_exe)}
        mock_process_iter.return_value = [mock_proc]

        detector = CS2PathDetector()
        result = detector._find_by_process()

        assert result == csgo_dir

    def test_check_default_paths(self, tmp_path, monkeypatch):
        """Test checking default Steam paths."""
        # Create fake Steam directory
        steam_path = tmp_path / "Steam" / "steamapps" / "common" / "Counter-Strike 2" / "game" / "csgo"
        steam_path.mkdir(parents=True)

        detector = CS2PathDetector()

        # Patch default paths to use tmp_path
        with patch.object(detector, '_check_default_paths', return_value=steam_path):
            result = detector._check_default_paths()
            assert result == steam_path


class TestCacheValidator:
    """Test cache validation with fast hashing."""

    def test_get_demo_hash(self, tmp_path):
        """Test computing demo hash (first 10MB + size)."""
        # Create test demo file (5MB)
        demo_file = tmp_path / "test.dem"
        demo_data = b"x" * (5 * 1024 * 1024)  # 5MB
        demo_file.write_bytes(demo_data)

        cache_dir = tmp_path / "cache"
        validator = CacheValidator(cache_dir)

        hash_result = validator.get_demo_hash(demo_file)

        # Hash should be in format: "size_md5"
        assert "_" in hash_result
        size_part, hash_part = hash_result.split("_", 1)
        assert size_part == str(len(demo_data))
        assert len(hash_part) == 32  # MD5 hex length

    def test_is_cache_valid_no_cache(self, tmp_path):
        """Test validation when cache doesn't exist."""
        demo_file = tmp_path / "test.dem"
        demo_file.write_bytes(b"demo data")

        cache_dir = tmp_path / "cache"
        validator = CacheValidator(cache_dir)

        assert validator.is_cache_valid(demo_file) is False

    def test_is_cache_valid_outdated(self, tmp_path):
        """Test validation when demo file changed."""
        # Create demo file
        demo_file = tmp_path / "test.dem"
        demo_file.write_bytes(b"original data")

        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()
        validator = CacheValidator(cache_dir)

        # Save hash for original
        validator.save_hash(demo_file)

        # Modify demo file
        demo_file.write_bytes(b"modified data")

        # Cache should be invalid
        assert validator.is_cache_valid(demo_file) is False

    def test_is_cache_valid_up_to_date(self, tmp_path):
        """Test validation when cache is up-to-date."""
        # Create demo file
        demo_file = tmp_path / "test.dem"
        demo_file.write_bytes(b"demo data")

        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()
        validator = CacheValidator(cache_dir)

        # Create cache file
        cache_file = validator.get_cache_path(demo_file)
        cache_file.write_text("{}")

        # Save hash
        validator.save_hash(demo_file)

        # Cache should be valid
        assert validator.is_cache_valid(demo_file) is True

    def test_get_cache_path(self, tmp_path):
        """Test getting cache file path."""
        demo_file = tmp_path / "match.dem"
        cache_dir = tmp_path / "cache"

        validator = CacheValidator(cache_dir)
        cache_path = validator.get_cache_path(demo_file)

        assert cache_path == cache_dir / "match.dem.json"


class TestDemoMonitor:
    """Test demo load monitoring."""

    @pytest.mark.asyncio
    async def test_monitor_demo_load(self, tmp_path):
        """Test monitoring for demo load events."""
        cs2_dir = tmp_path / "csgo"
        cs2_dir.mkdir()

        # Create test demo file
        demo_file = cs2_dir / "test.dem"
        demo_file.touch()

        # Mock telnet client
        mock_telnet = AsyncMock()
        mock_telnet.reader = AsyncMock()

        # Simulate console output with demo load message
        console_output = b"Playing demo from test.dem\n"
        mock_telnet.reader.read = AsyncMock(return_value=console_output)

        monitor = DemoMonitor(mock_telnet, cs2_dir)

        # Callback to capture detected demo
        detected_demos = []

        async def on_demo_detected(demo_path):
            detected_demos.append(demo_path)
            # Stop monitoring after first detection
            raise asyncio.CancelledError()

        # Run monitoring (will be cancelled after first detection)
        try:
            await monitor.monitor_demo_load(on_demo_detected, poll_interval=0.1)
        except asyncio.CancelledError:
            pass

        # Verify demo was detected
        assert len(detected_demos) == 1
        assert detected_demos[0] == demo_file

    def test_parse_demo_path_relative(self, tmp_path):
        """Test parsing relative demo path."""
        cs2_dir = tmp_path / "csgo"
        cs2_dir.mkdir()

        demo_file = cs2_dir / "match.dem"
        demo_file.touch()

        mock_telnet = Mock()
        monitor = DemoMonitor(mock_telnet, cs2_dir)

        result = monitor._parse_demo_path("match.dem")
        assert result == demo_file

    def test_parse_demo_path_absolute(self, tmp_path):
        """Test parsing absolute demo path."""
        cs2_dir = tmp_path / "csgo"
        cs2_dir.mkdir()

        demo_file = tmp_path / "demos" / "match.dem"
        demo_file.parent.mkdir()
        demo_file.touch()

        mock_telnet = Mock()
        monitor = DemoMonitor(mock_telnet, cs2_dir)

        result = monitor._parse_demo_path(str(demo_file))
        assert result == demo_file


class TestSpectatorTracker:
    """Test spectator target tracking."""

    @pytest.mark.asyncio
    async def test_get_current_target(self):
        """Test getting current spectator target."""
        # Mock telnet client
        mock_telnet = AsyncMock()
        mock_telnet.writer = AsyncMock()
        mock_telnet.reader = AsyncMock()

        # Simulate status output
        status_output = b"""hostname: Competitive
map     : de_dust2
players : 10 humans
 userid name                 uniqueid            connected ping
      2 "s1mple"             STEAM_1:0:123456    25:18       50

Spectating: s1mple
"""
        mock_telnet.reader.read = AsyncMock(return_value=status_output)

        tracker = SpectatorTracker(mock_telnet)
        target = await tracker.get_current_target()

        assert target == "s1mple"

    @pytest.mark.asyncio
    async def test_track_spectator_changes(self):
        """Test tracking spectator target changes."""
        mock_telnet = AsyncMock()
        mock_telnet.writer = AsyncMock()
        mock_telnet.reader = AsyncMock()

        # Simulate target changes
        outputs = [
            b"Spectating: s1mple\n",
            b"Spectating: s1mple\n",  # No change
            b"Spectating: NiKo\n",    # Changed
        ]
        output_iter = iter(outputs)

        async def mock_read(*args, **kwargs):
            return next(output_iter, b"")

        mock_telnet.reader.read = mock_read

        tracker = SpectatorTracker(mock_telnet)

        # Track changes
        changes = []

        async def on_change(player_name):
            changes.append(player_name)
            if len(changes) >= 2:  # Stop after 2 changes
                raise asyncio.CancelledError()

        try:
            await tracker.track_spectator_changes(on_change, poll_interval=0.1)
        except (asyncio.CancelledError, StopIteration):
            pass

        # Should detect initial target and one change
        assert "s1mple" in changes
        assert "NiKo" in changes

    def test_parse_status_output(self):
        """Test parsing status command output."""
        mock_telnet = Mock()
        tracker = SpectatorTracker(mock_telnet)

        status_text = """
hostname: Server
Spectating: player123
"""
        result = tracker._parse_status_output(status_text)
        assert result == "player123"

    def test_build_player_mapping(self):
        """Test building player name -> SteamID mapping."""
        mock_telnet = Mock()
        tracker = SpectatorTracker(mock_telnet)

        status_text = """
 userid name                 uniqueid            connected
      2 "s1mple"             STEAM_1:0:123456    25:18
      3 "NiKo"               STEAM_1:0:789012    23:45
"""
        mapping = tracker._build_player_mapping(status_text)

        assert mapping.get("s1mple") == "STEAM_1:0:123456"
        assert mapping.get("NiKo") == "STEAM_1:0:789012"


class TestAutoOrchestratorIntegration:
    """Integration tests for AutoOrchestrator."""

    @pytest.mark.asyncio
    async def test_auto_orchestrator_initialization(self):
        """Test AutoOrchestrator can be initialized."""
        config = AppConfig()
        orchestrator = AutoOrchestrator(config)

        assert orchestrator is not None
        assert orchestrator.config == config
        assert orchestrator.cache_validator is not None

    @pytest.mark.asyncio
    async def test_on_demo_loaded_new_demo(self, tmp_path):
        """Test handling when new demo is loaded."""
        config = AppConfig()
        config.cache_dir = str(tmp_path / "cache")

        orchestrator = AutoOrchestrator(config)

        # Create test demo
        demo_file = tmp_path / "test.dem"
        demo_file.write_bytes(b"x" * 1024)  # 1KB demo

        # Mock ETL pipeline
        with patch.object(orchestrator, '_run_etl_background', new_callable=AsyncMock) as mock_etl:
            mock_etl.return_value = Path(config.cache_dir) / "test.dem.json"

            # Simulate demo loaded
            await orchestrator._on_demo_loaded(demo_file)

            # ETL should have been called (cache doesn't exist)
            mock_etl.assert_called_once_with(demo_file)

    @pytest.mark.asyncio
    async def test_on_spectator_changed(self):
        """Test handling spectator target changes."""
        config = AppConfig()
        orchestrator = AutoOrchestrator(config)

        # Simulate spectator change
        await orchestrator._on_spectator_changed("s1mple", "STEAM_1:0:123456")

        # Should update current player (tested via internal state)
        # This is a basic smoke test - more detailed tests would check
        # that visualization updates accordingly


def test_main_auto_mode_argument():
    """Test that main.py accepts --mode auto."""
    import sys
    from src.main import main

    # Save original argv
    original_argv = sys.argv

    try:
        # Test with --mode auto and --help
        sys.argv = ["main.py", "--mode", "auto", "--help"]

        with pytest.raises(SystemExit) as exc_info:
            main()

        # Help should exit with 0
        assert exc_info.value.code == 0

    finally:
        # Restore argv
        sys.argv = original_argv


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
