# Mock Data Generator Usage Guide

## Overview

The `mock_data_generator.py` module generates realistic test data for CS2 Input Visualizer. It simulates actual CS2 gameplay patterns including movement, shooting, jumping, crouching, and utility usage.

## Quick Start

### Python API

```python
from src.parsers.mock_data_generator import generate_mock_cache

# Generate 10 seconds of gameplay data
cache = generate_mock_cache(
    num_ticks=640,           # 10 seconds at 64 tick rate
    output_path="test.json", # Where to save the cache
    seed=42,                 # For reproducibility
    player_name="TestPlayer"
)
```

### Command Line Interface

```bash
# Generate 5000 ticks with default settings
python -m src.parsers.mock_data_generator

# Generate with custom parameters
python -m src.parsers.mock_data_generator \
    --ticks 1000 \
    --output my_cache.json \
    --seed 42 \
    --tick-rate 64 \
    --player-name "ProPlayer"
```

## Features

### 1. Realistic Movement Patterns

The generator uses a state machine to create believable movement sequences:
- **Forward movement** (W): Held for 0.5-1.5 seconds
- **Strafing** (A/D): Quick directional changes
- **Counter-strafing**: Natural transitions (W → W+D → D)
- **Idle periods**: Realistic pauses in movement

### 2. Shooting Patterns

Simulates different shooting behaviors:
- **Burst fire**: 2-5 bullets (most common)
- **Tap shooting**: 1-2 bullets
- **Occasional sprays**: 6-10 bullets
- **Realistic timing**: Based on typical fire rates

### 3. Subtick Precision

Each input has a subtick offset (0.0-1.0) indicating when during the tick it was pressed:
- Movement keys: Usually 0.0 (tick start)
- Mouse clicks: 0.1-0.5 (reaction delay)
- Utility keys: Random timing within tick

### 4. Additional Actions

- **Jumping** (SPACE): Occurs while moving forward (2% chance)
- **Crouching** (CTRL): Often combined with shooting
- **Utility** (E, R, TAB, SHIFT): Occasional realistic usage

## Cache Structure

The generated cache is compatible with `MockDemoRepository`:

```json
{
  "meta": {
    "demo_file": "mock_demo.dem",
    "player_id": "MOCK_PLAYER_123",
    "player_name": "TestPlayer",
    "tick_range": [0, 5000],
    "tick_rate": 64
  },
  "inputs": {
    "0": {
      "tick": 0,
      "keys": ["W"],
      "mouse": [],
      "subtick": {"W": 0.0}
    },
    "64": {
      "tick": 64,
      "keys": ["W", "D"],
      "mouse": ["MOUSE1"],
      "subtick": {"W": 0.0, "D": 0.0, "MOUSE1": 0.3}
    }
  }
}
```

## Advanced Usage

### Custom Pattern Generation

```python
from src.parsers.mock_data_generator import RealisticPatternGenerator

# Create pattern generator with seed
gen = RealisticPatternGenerator(seed=42)

# Generate individual patterns
movement_keys = gen.generate_movement_pattern(tick=0)
shooting = gen.generate_shooting_pattern(tick=0)
utility = gen.generate_utility_pattern(tick=0)
```

### Integration with MockDemoRepository

```python
from src.parsers.mock_data_generator import generate_mock_cache
from src.mocks.demo_repository import MockDemoRepository

# Generate cache
cache = generate_mock_cache(
    num_ticks=1000,
    output_path="test_cache.json",
    seed=42
)

# Load with repository
repo = MockDemoRepository()
repo.load_demo("test_cache.json")

# Use the data
player_id = repo.get_default_player()
input_data = repo.get_inputs(tick=100, player_id=player_id)
print(f"Keys: {input_data.keys}, Mouse: {input_data.mouse}")
```

### Reproducible Testing

Use seeds for consistent test data:

```python
# These will generate identical data
cache1 = generate_mock_cache(num_ticks=100, seed=42)
cache2 = generate_mock_cache(num_ticks=100, seed=42)
assert cache1['inputs'] == cache2['inputs']  # True

# Without seed, data is random
cache3 = generate_mock_cache(num_ticks=100)
cache4 = generate_mock_cache(num_ticks=100)
assert cache3['inputs'] != cache4['inputs']  # True (probably)
```

## Examples

See `/home/user/cs2-demo-input-viewer/examples/generate_mock_data_example.py` for comprehensive examples including:
- Basic generation
- Different duration demos
- Integration with MockDemoRepository
- Reproducibility testing
- Pattern analysis

Run examples:
```bash
cd examples
python generate_mock_data_example.py
```

## Performance

The generator is optimized for sparse storage:
- Only stores ticks with actual input (not idle ticks)
- Typical compression: 15-30% reduction
- Example: 5000 ticks → ~3500-4250 stored entries

## Pattern Quality

Typical distribution for 5000 ticks (~78 seconds at 64 tick rate):
- **Movement**: 70-80% of active ticks
- **Shooting**: 10-15% of active ticks
- **Jumping**: 1-2% of active ticks
- **Crouching**: 30-40% of active ticks
- **Utility**: 8-12% of active ticks
- **Idle**: 10-15% of all ticks

## API Reference

### `generate_mock_cache()`

Generate complete mock cache data.

**Parameters:**
- `num_ticks` (int): Number of ticks to generate (default: 5000)
- `output_path` (str, optional): Path to save JSON file
- `seed` (int, optional): Random seed for reproducibility
- `tick_rate` (int): Server tick rate - 64 or 128 (default: 64)
- `player_name` (str): Player display name (default: "TestPlayer")

**Returns:**
- `dict`: Complete cache structure with metadata and inputs

### `generate_subtick_offsets()`

Generate subtick timing offsets for inputs.

**Parameters:**
- `keys` (List[str]): Keyboard keys pressed
- `mouse` (List[str]): Mouse buttons pressed
- `seed` (int, optional): Random seed

**Returns:**
- `dict`: Mapping of inputs to subtick offsets (0.0-1.0)

### `RealisticPatternGenerator`

Main pattern generation class.

**Methods:**
- `generate_movement_pattern(tick)`: Generate WASD movement
- `generate_shooting_pattern(tick)`: Generate shooting bursts
- `generate_utility_pattern(tick)`: Generate utility key presses
- `generate_jump(tick)`: Determine if SPACE should be pressed
- `generate_crouch(tick)`: Determine if CTRL should be pressed

## Notes

- The generator creates realistic patterns, not random noise
- All patterns are based on common CS2 gameplay mechanics
- Subtick timing adds precision for visualization
- Compatible with existing MockDemoRepository implementation
- No external dependencies beyond Python standard library
