"""Foundation tests for CS2 Input Visualizer.

This module contains unit tests for core domain models and mock implementations,
ensuring the foundation of the application works correctly before building on it.
"""

import pytest
import pytest_asyncio
import asyncio
from src.domain.models import InputData, PlayerInfo, DemoMetadata
from src.mocks.tick_source import MockTickSource
from src.mocks.player_tracker import MockPlayerTracker


# ============================================================================
# Domain Model Tests
# ============================================================================

def test_input_data_creation():
    """Test InputData model creation and attribute access."""
    data = InputData(
        tick=100,
        keys=["W", "A"],
        mouse=["MOUSE1"],
        subtick={"W": 0.0, "MOUSE1": 0.5}
    )
    assert data.tick == 100
    assert "W" in data.keys
    assert "A" in data.keys
    assert "MOUSE1" in data.mouse
    assert data.subtick["W"] == 0.0
    assert data.subtick["MOUSE1"] == 0.5
    assert data.timestamp is None


def test_input_data_with_timestamp():
    """Test InputData model with optional timestamp."""
    timestamp = 1234567890.5
    data = InputData(
        tick=200,
        keys=["SPACE"],
        mouse=[],
        subtick={"SPACE": 0.25},
        timestamp=timestamp
    )
    assert data.timestamp == timestamp


def test_player_info_creation():
    """Test PlayerInfo model creation."""
    player = PlayerInfo(
        steam_id="76561198012345678",
        name="TestPlayer",
        entity_id=42
    )
    assert player.steam_id == "76561198012345678"
    assert player.name == "TestPlayer"
    assert player.entity_id == 42


def test_player_info_without_entity():
    """Test PlayerInfo model without optional entity_id."""
    player = PlayerInfo(
        steam_id="76561198087654321",
        name="AnotherPlayer"
    )
    assert player.entity_id is None


def test_demo_metadata_creation():
    """Test DemoMetadata model creation."""
    metadata = DemoMetadata(
        file_path="/path/to/demo.dem",
        player_id="76561198012345678",
        player_name="TestPlayer",
        tick_range=(1000, 5000),
        tick_rate=64,
        duration_seconds=62.5
    )
    assert metadata.file_path == "/path/to/demo.dem"
    assert metadata.player_id == "76561198012345678"
    assert metadata.player_name == "TestPlayer"
    assert metadata.tick_range == (1000, 5000)
    assert metadata.tick_rate == 64
    assert metadata.duration_seconds == 62.5


# ============================================================================
# MockTickSource Tests
# ============================================================================

@pytest.mark.asyncio
async def test_mock_tick_source_connection():
    """Test MockTickSource connection lifecycle."""
    mock = MockTickSource(start_tick=1000)

    # Initially not connected
    assert not mock.is_connected()

    # Connect
    result = await mock.connect()
    assert result is True
    assert mock.is_connected()

    # Disconnect
    await mock.disconnect()
    assert not mock.is_connected()


@pytest.mark.asyncio
async def test_mock_tick_source_tick_progression():
    """Test MockTickSource tick progression over time."""
    mock = MockTickSource(start_tick=1000, tick_rate=64)

    await mock.connect()

    # Get initial tick
    tick1 = await mock.get_current_tick()
    assert tick1 >= 1000

    # Wait and verify tick progression
    await asyncio.sleep(0.1)  # 100ms = 6.4 ticks at 64 Hz
    tick2 = await mock.get_current_tick()
    assert tick2 > tick1

    # Verify tick increment is reasonable (should be ~6 ticks)
    tick_diff = tick2 - tick1
    assert 4 <= tick_diff <= 10  # Allow some timing variance

    await mock.disconnect()


@pytest.mark.asyncio
async def test_mock_tick_source_custom_tick_rate():
    """Test MockTickSource with custom tick rate."""
    # Use 128 Hz tick rate (higher than default)
    mock = MockTickSource(start_tick=500, tick_rate=128)

    await mock.connect()

    tick1 = await mock.get_current_tick()
    await asyncio.sleep(0.1)  # 100ms = 12.8 ticks at 128 Hz
    tick2 = await mock.get_current_tick()

    tick_diff = tick2 - tick1
    # Should be roughly twice as many ticks as 64 Hz
    assert 10 <= tick_diff <= 16

    await mock.disconnect()


@pytest.mark.asyncio
async def test_mock_tick_source_error_when_not_connected():
    """Test MockTickSource raises error when getting tick while disconnected."""
    mock = MockTickSource(start_tick=1000)

    # Should raise error when not connected
    with pytest.raises(ConnectionError, match="Not connected"):
        await mock.get_current_tick()

    # Connect and verify it works
    await mock.connect()
    tick = await mock.get_current_tick()
    assert tick >= 1000

    # Disconnect and verify error again
    await mock.disconnect()
    with pytest.raises(ConnectionError, match="Not connected"):
        await mock.get_current_tick()


# ============================================================================
# MockPlayerTracker Tests
# ============================================================================

@pytest.mark.asyncio
async def test_mock_player_tracker_basic():
    """Test MockPlayerTracker basic functionality."""
    tracker = MockPlayerTracker(player_id="76561198012345678")

    # Initially returns None before update
    player = await tracker.get_current_player()
    assert player is None

    # After update, returns configured player
    await tracker.update()
    player = await tracker.get_current_player()
    assert player == "76561198012345678"


@pytest.mark.asyncio
async def test_mock_player_tracker_set_player():
    """Test MockPlayerTracker set_player method."""
    tracker = MockPlayerTracker()

    # Set a new player
    tracker.set_player("76561198087654321")
    player = await tracker.get_current_player()
    assert player == "76561198087654321"

    # Set another player
    tracker.set_player("76561198999999999")
    player = await tracker.get_current_player()
    assert player == "76561198999999999"


@pytest.mark.asyncio
async def test_mock_player_tracker_set_none():
    """Test MockPlayerTracker with None player (no active player)."""
    tracker = MockPlayerTracker()

    # Set and verify player
    tracker.set_player("76561198012345678")
    assert await tracker.get_current_player() is not None

    # Set to None (simulate no player)
    tracker.set_player(None)
    player = await tracker.get_current_player()
    assert player is None


@pytest.mark.asyncio
async def test_mock_player_tracker_default_player():
    """Test MockPlayerTracker with default player ID."""
    tracker = MockPlayerTracker()

    # Should have default player after update
    await tracker.update()
    player = await tracker.get_current_player()
    assert player is not None
    assert isinstance(player, str)
    assert player.startswith("765611")  # Steam ID format


# ============================================================================
# Integration Tests
# ============================================================================

@pytest.mark.asyncio
async def test_mock_components_together():
    """Test MockTickSource and MockPlayerTracker working together."""
    tick_source = MockTickSource(start_tick=1000, tick_rate=64)
    player_tracker = MockPlayerTracker(player_id="76561198012345678")

    # Connect and initialize
    assert await tick_source.connect()
    await player_tracker.update()

    # Get synchronized state
    current_tick = await tick_source.get_current_tick()
    current_player = await player_tracker.get_current_player()

    assert current_tick >= 1000
    assert current_player == "76561198012345678"

    # Simulate time passing
    await asyncio.sleep(0.05)
    new_tick = await tick_source.get_current_tick()
    assert new_tick > current_tick

    # Player should remain the same
    same_player = await player_tracker.get_current_player()
    assert same_player == current_player

    # Cleanup
    await tick_source.disconnect()


@pytest.mark.asyncio
async def test_input_data_with_mock_tick():
    """Test creating InputData with tick from MockTickSource."""
    tick_source = MockTickSource(start_tick=5000, tick_rate=64)
    await tick_source.connect()

    current_tick = await tick_source.get_current_tick()

    # Create input data using the tick
    input_data = InputData(
        tick=current_tick,
        keys=["W", "D"],
        mouse=["MOUSE1"],
        subtick={"W": 0.0, "D": 0.1, "MOUSE1": 0.3}
    )

    assert input_data.tick >= 5000
    assert len(input_data.keys) == 2
    assert len(input_data.mouse) == 1

    await tick_source.disconnect()


# ============================================================================
# Fixtures
# ============================================================================

@pytest_asyncio.fixture
async def connected_tick_source():
    """Fixture providing a connected MockTickSource."""
    mock = MockTickSource(start_tick=1000, tick_rate=64)
    await mock.connect()
    yield mock
    await mock.disconnect()


@pytest_asyncio.fixture
async def updated_player_tracker():
    """Fixture providing an updated MockPlayerTracker."""
    tracker = MockPlayerTracker(player_id="76561198012345678")
    await tracker.update()
    yield tracker


@pytest.mark.asyncio
async def test_with_tick_source_fixture(connected_tick_source):
    """Test using the tick source fixture."""
    assert connected_tick_source.is_connected()
    tick = await connected_tick_source.get_current_tick()
    assert tick >= 1000


@pytest.mark.asyncio
async def test_with_player_tracker_fixture(updated_player_tracker):
    """Test using the player tracker fixture."""
    player = await updated_player_tracker.get_current_player()
    assert player == "76561198012345678"
