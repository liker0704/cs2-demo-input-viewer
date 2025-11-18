# Mock Implementations

This directory contains mock implementations of the CS2 Input Visualizer interfaces for testing and development.

## Overview

Mock implementations allow you to develop and test the UI and core logic without requiring:
- A real CS2 connection
- Actual demo file parsing
- The `demoparser2` library

This enables parallel development where UI, logic, and data layers can be built independently.

## Available Mocks

### 1. MockTickSource

**File**: `tick_source.py`

**Purpose**: Simulates CS2 tick progression using system timer.

**Features**:
- Uses `time.time()` to calculate tick progression
- Configurable start tick and tick rate (default: 64 Hz)
- Simulates connection/disconnection
- No external dependencies

**Usage**:
```python
from mocks import MockTickSource

# Create mock with custom settings
tick_source = MockTickSource(start_tick=1000, tick_rate=64)

# Connect (starts the timer)
await tick_source.connect()

# Get current tick (automatically progresses)
tick = await tick_source.get_current_tick()  # e.g., 1000 initially
await asyncio.sleep(1.0)
tick = await tick_source.get_current_tick()  # e.g., 1064 (after 1 second)

# Disconnect
await tick_source.disconnect()
```

**Key Methods**:
- `connect()` - Start the timer
- `get_current_tick()` - Get current tick based on elapsed time
- `disconnect()` - Stop the timer
- `is_connected()` - Check connection status

---

### 2. MockDemoRepository

**File**: `demo_repository.py`

**Purpose**: Loads pre-parsed demo data from JSON cache files.

**Features**:
- Loads data from JSON cache files
- Gracefully handles missing files (creates empty cache)
- Returns `InputData` objects
- Supports tick range queries
- Provides default player ID

**Cache File Format**:
```json
{
  "metadata": {
    "player_id": "76561198012345678",
    "player_name": "PlayerName",
    "tick_range": [0, 100000],
    "tick_rate": 64
  },
  "inputs": {
    "1000": {
      "tick": 1000,
      "keys": ["W", "A"],
      "mouse": ["MOUSE1"],
      "subtick": {"W": 0.0, "A": 0.3, "MOUSE1": 0.5}
    }
  }
}
```

**Usage**:
```python
from mocks import MockDemoRepository

# Create repository
repo = MockDemoRepository()

# Load cache file (or create empty if missing)
loaded = repo.load_demo("data/cache.json")

# Get player and tick information
player_id = repo.get_default_player()
min_tick, max_tick = repo.get_tick_range()

# Get inputs for specific tick
inputs = repo.get_inputs(1000, player_id)
if inputs:
    print(inputs.keys)   # ["W", "A"]
    print(inputs.mouse)  # ["MOUSE1"]
```

**Key Methods**:
- `load_demo(path)` - Load JSON cache file
- `get_inputs(tick, player_id)` - Get input data for tick
- `get_tick_range()` - Get (min_tick, max_tick)
- `get_default_player()` - Get default player ID

---

### 3. MockPlayerTracker

**File**: `player_tracker.py`

**Purpose**: Returns a fixed player ID for testing.

**Features**:
- Configurable player ID
- Simple state tracking
- No external dependencies
- Includes test helper method `set_player()`

**Usage**:
```python
from mocks import MockPlayerTracker

# Create tracker with default player
tracker = MockPlayerTracker(player_id="76561198012345678")

# Update state
await tracker.update()

# Get current player
player = await tracker.get_current_player()
print(player)  # "76561198012345678"

# Change player (for testing)
tracker.set_player("76561198999999999")
```

**Key Methods**:
- `update()` - Mark as updated
- `get_current_player()` - Get configured player ID
- `set_player(player_id)` - Set new player ID (testing helper)

---

## Complete Example

See `examples/mock_usage_example.py` for a complete demonstration of using all three mocks together.

Quick example:
```python
import asyncio
from mocks import MockTickSource, MockDemoRepository, MockPlayerTracker

async def main():
    # Initialize all mocks
    tick_source = MockTickSource(start_tick=1000, tick_rate=64)
    demo_repo = MockDemoRepository()
    player_tracker = MockPlayerTracker()
    
    # Setup
    await tick_source.connect()
    demo_repo.load_demo("data/cache.json")
    await player_tracker.update()
    
    # Get data
    player_id = await player_tracker.get_current_player()
    current_tick = await tick_source.get_current_tick()
    inputs = demo_repo.get_inputs(current_tick, player_id)
    
    if inputs:
        print(f"Tick {current_tick}: {inputs.keys}")
    
    # Cleanup
    await tick_source.disconnect()

asyncio.run(main())
```

---

## Testing

Run the test suite:
```bash
python -c "
import sys
sys.path.insert(0, 'src')
from mocks import MockTickSource, MockDemoRepository, MockPlayerTracker
print('All imports successful!')
"
```

---

## Sample Data

A sample cache file is provided at `data/sample_cache.json` with example input data for ticks 1000-1004.

You can create your own cache files following the format shown above, or wait for the real demo parser implementation to generate them.

---

## Development Workflow

1. **Phase 1**: Develop UI using mocks
   - Use `MockTickSource` for tick progression
   - Use `MockDemoRepository` with sample cache
   - Use `MockPlayerTracker` for fixed player

2. **Phase 2**: Develop core logic
   - Test prediction engine with `MockTickSource`
   - Test data flow with `MockDemoRepository`
   - Test player switching with `MockPlayerTracker`

3. **Phase 3**: Integration
   - Replace mocks with real implementations
   - Keep mocks for unit tests
   - Use mocks for CI/CD testing

---

## Notes

- All mocks implement their respective interfaces completely
- Mocks are suitable for unit testing and integration testing
- Graceful error handling (missing files, etc.)
- No external dependencies beyond Python standard library
- Fully documented with docstrings and examples
