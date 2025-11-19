# Data Layer Documentation

## CS2 Subtick Input Visualizer - ETL Pipeline

### 1. Overview

The Data Layer is responsible for extracting, transforming, and loading player input data from CS2 demo files. This is an **offline process** that happens before demo playback.

**Goal**: Convert a 400MB .dem file into a lightweight, indexed cache optimized for real-time lookup.

---

## 2. Extract Phase

### 2.1 Demo File Format

- **File Extension**: `.dem`
- **Source**: Faceit, HLTV, GOTV, or local recordings
- **Average Size**: 300-500 MB
- **Format**: Binary protobuf-based format (Source 2)

### 2.2 Using demoparser2

#### Installation

```bash
pip install demoparser2
```

#### Required Fields

```python
fields = [
    "m_nButtonDownMaskPrev",  # Button bitmask (primary input source)
    "subtick_moves",           # Subtick timing data (array of moves)
    "m_steamID",               # Player identification
    "tick",                    # Current tick number
    "name",                    # Player name (optional, for UI)
]
```

#### Basic Usage

```python
from demoparser2 import DemoParser

parser = DemoParser("/path/to/demo.dem")

# Parse only required events
df = parser.parse_event("player_input", player=["m_steamID"], other=fields)

# Iterate through ticks
for tick, events in df.groupby("tick"):
    for event in events:
        button_mask = event["m_nButtonDownMaskPrev"]
        subtick_data = event["subtick_moves"]
        player_id = event["m_steamID"]
        # Process...
```

### 2.3 Subtick Data Structure

Subtick moves contain precise timing information:

```python
# Example subtick_moves structure
subtick_moves = [
    {
        "button": 8,      # IN_FORWARD
        "when": 0.0,      # Start of tick
        "pressed": True
    },
    {
        "button": 2,      # IN_JUMP
        "when": 0.3,      # 30% through the tick
        "pressed": True
    },
    {
        "button": 8,
        "when": 0.8,      # 80% through the tick
        "pressed": False  # Released
    }
]
```

**Note**: `when` is a float from 0.0 to 1.0 representing position within the tick.

---

## 3. Transform Phase

### 3.1 Button Mask Decoding

CS2 uses bitmasking for input states. Each button is a power of 2.

#### Button Definitions (Source 2)

```python
class ButtonMask:
    """CS2 button bitmask constants.

    Note: These values are based on Source 1 SDK.
    For CS2/Source 2, verification needed via demoparser2 testing.
    """
    IN_ATTACK      = 1 << 0   # 1      (Mouse1)
    IN_JUMP        = 1 << 1   # 2      (Space)
    IN_DUCK        = 1 << 2   # 4      (Ctrl)
    IN_FORWARD     = 1 << 3   # 8      (W)
    IN_BACK        = 1 << 4   # 16     (S)
    IN_USE         = 1 << 5   # 32     (E)
    IN_CANCEL      = 1 << 6   # 64
    IN_LEFT        = 1 << 7   # 128
    IN_RIGHT       = 1 << 8   # 256
    IN_MOVELEFT    = 1 << 9   # 512    (A)
    IN_MOVERIGHT   = 1 << 10  # 1024   (D)
    IN_ATTACK2     = 1 << 11  # 2048   (Mouse2)
    IN_RUN         = 1 << 12  # 4096
    IN_RELOAD      = 1 << 13  # 8192   (R)
    IN_ALT1        = 1 << 14  # 16384
    IN_ALT2        = 1 << 15  # 32768
    IN_SCORE       = 1 << 16  # 65536  (Tab)
    IN_SPEED       = 1 << 17  # 131072 (Shift)
    IN_WALK        = 1 << 18  # 262144
    IN_ZOOM        = 1 << 19  # 524288 (Mouse3/Wheel)
    # ... more buttons

# Mapping for UI display
BUTTON_TO_KEY = {
    ButtonMask.IN_FORWARD: "W",
    ButtonMask.IN_BACK: "S",
    ButtonMask.IN_MOVELEFT: "A",
    ButtonMask.IN_MOVERIGHT: "D",
    ButtonMask.IN_JUMP: "SPACE",
    ButtonMask.IN_DUCK: "CTRL",
    ButtonMask.IN_SPEED: "SHIFT",
    ButtonMask.IN_ATTACK: "MOUSE1",
    ButtonMask.IN_ATTACK2: "MOUSE2",
    ButtonMask.IN_RELOAD: "R",
    ButtonMask.IN_USE: "E",
    ButtonMask.IN_SCORE: "TAB",
}
```

#### Decoding Algorithm

```python
from typing import List
from dataclasses import dataclass

@dataclass
class ButtonPress:
    key: str
    subtick_offset: float = 0.0

def decode_buttons(mask: int, subtick_moves: list = None) -> List[ButtonPress]:
    """Decode button bitmask into list of active keys.

    Args:
        mask: Integer bitmask from m_nButtonDownMaskPrev
        subtick_moves: Optional list of subtick timing data

    Returns:
        List of ButtonPress objects with key names and timing
    """
    active_buttons = []

    # Check each known button
    for button_value, key_name in BUTTON_TO_KEY.items():
        if mask & button_value:
            # Button is pressed
            subtick_offset = 0.0

            # Find subtick timing if available
            if subtick_moves:
                for move in subtick_moves:
                    if move["button"] == button_value and move["pressed"]:
                        subtick_offset = move["when"]
                        break

            active_buttons.append(ButtonPress(
                key=key_name,
                subtick_offset=subtick_offset
            ))

    return active_buttons


# Example usage
mask = 8 | 512  # W + A pressed
buttons = decode_buttons(mask)
print(buttons)  # [ButtonPress(key='W', subtick_offset=0.0), ButtonPress(key='A', subtick_offset=0.0)]
```

### 3.2 Player Filtering

Filter data for specific player:

```python
def filter_player_inputs(demo_data, target_steam_id: str = None):
    """Filter demo data for a specific player.

    Args:
        demo_data: Raw parsed data from demoparser2
        target_steam_id: SteamID to filter, or None for auto-detect

    Returns:
        Filtered data for single player
    """
    if target_steam_id is None:
        # Auto-detect: Use most frequent player in data
        player_counts = demo_data['m_steamID'].value_counts()
        target_steam_id = player_counts.idxmax()

    return demo_data[demo_data['m_steamID'] == target_steam_id]
```

---

## 4. Load Phase

### 4.1 Cache Structure

The cache is optimized for tick-based lookup:

```json
{
  "meta": {
    "demo_file": "match_12345.dem",
    "player_id": "STEAM_1:0:123456789",
    "player_name": "s1mple",
    "tick_range": [0, 160000],
    "tick_rate": 64
  },
  "inputs": {
    "100": {
      "keys": ["W", "A"],
      "mouse": ["MOUSE1"],
      "subtick": {
        "W": 0.0,
        "A": 0.2,
        "MOUSE1": 0.5
      }
    },
    "101": {
      "keys": ["W"],
      "mouse": [],
      "subtick": {
        "W": 0.0
      }
    }
  }
}
```

### 4.2 Storage Options

#### Option A: JSON (Development)

**Pros:**
- Human-readable
- Easy to debug
- No additional dependencies

**Cons:**
- Larger file size (~50-100 MB for full match)
- Slower loading (~100-200 ms)

```python
import json

def save_cache_json(cache_data: dict, output_path: str):
    """Save cache as JSON file."""
    with open(output_path, 'w') as f:
        json.dump(cache_data, f, indent=2)

def load_cache_json(cache_path: str) -> dict:
    """Load cache from JSON file."""
    with open(cache_path, 'r') as f:
        return json.load(f)
```

#### Option B: MessagePack (Production)

**Pros:**
- 50-70% smaller than JSON
- 5-10x faster loading
- Binary format

**Cons:**
- Not human-readable
- Requires `msgpack` library

```python
import msgpack

def save_cache_msgpack(cache_data: dict, output_path: str):
    """Save cache as MessagePack file."""
    with open(output_path, 'wb') as f:
        msgpack.pack(cache_data, f)

def load_cache_msgpack(cache_path: str) -> dict:
    """Load cache from MessagePack file."""
    with open(cache_path, 'rb') as f:
        return msgpack.unpack(f, raw=False)
```

#### Option C: SQLite (Advanced)

For very large demos or random access patterns:

```python
import sqlite3

def create_cache_db(db_path: str):
    """Create SQLite cache database."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE inputs (
            tick INTEGER PRIMARY KEY,
            keys TEXT,
            mouse TEXT,
            subtick TEXT
        )
    ''')

    conn.commit()
    return conn

def get_inputs_from_db(conn, tick: int) -> dict:
    """Query inputs for specific tick."""
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM inputs WHERE tick = ?', (tick,))
    row = cursor.fetchone()

    if row:
        return {
            'keys': json.loads(row[1]),
            'mouse': json.loads(row[2]),
            'subtick': json.loads(row[3])
        }
    return None
```

---

## 5. Complete ETL Pipeline

### 5.1 Pipeline Implementation

```python
from pathlib import Path
from typing import Optional
import json

class DemoETLPipeline:
    """Complete ETL pipeline for demo processing."""

    def __init__(self, demo_path: str, output_dir: str = "./cache"):
        self.demo_path = Path(demo_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def run(self, player_id: Optional[str] = None) -> str:
        """Run complete ETL pipeline.

        Args:
            player_id: Target player SteamID (None for auto-detect)

        Returns:
            Path to generated cache file
        """
        print(f"[ETL] Starting pipeline for {self.demo_path.name}")

        # EXTRACT
        print("[ETL] Phase 1/3: Extracting data...")
        raw_data = self._extract()

        # TRANSFORM
        print("[ETL] Phase 2/3: Transforming data...")
        transformed_data = self._transform(raw_data, player_id)

        # LOAD
        print("[ETL] Phase 3/3: Loading to cache...")
        cache_path = self._load(transformed_data)

        print(f"[ETL] Complete! Cache saved to {cache_path}")
        return cache_path

    def _extract(self) -> dict:
        """Extract phase: Parse demo file."""
        from demoparser2 import DemoParser

        parser = DemoParser(str(self.demo_path))

        # Parse required fields
        df = parser.parse_event(
            "player_input",
            player=["m_steamID", "name"],
            other=["m_nButtonDownMaskPrev", "subtick_moves", "tick"]
        )

        return df

    def _transform(self, raw_data, player_id: Optional[str]) -> dict:
        """Transform phase: Decode and filter data."""

        # Filter for target player
        if player_id is None:
            # Auto-detect most frequent player
            player_id = raw_data['m_steamID'].value_counts().idxmax()

        player_data = raw_data[raw_data['m_steamID'] == player_id]

        # Build cache structure
        cache = {
            "meta": {
                "demo_file": self.demo_path.name,
                "player_id": player_id,
                "tick_range": [
                    int(player_data['tick'].min()),
                    int(player_data['tick'].max())
                ],
                "tick_rate": 64
            },
            "inputs": {}
        }

        # Transform each tick
        for _, row in player_data.iterrows():
            tick = int(row['tick'])
            mask = int(row['m_nButtonDownMaskPrev'])
            subtick_moves = row.get('subtick_moves', [])

            # Decode buttons
            buttons = decode_buttons(mask, subtick_moves)

            # Separate keyboard and mouse inputs
            keyboard_keys = []
            mouse_keys = []
            subtick_data = {}

            for btn in buttons:
                if btn.key.startswith('MOUSE'):
                    mouse_keys.append(btn.key)
                else:
                    keyboard_keys.append(btn.key)

                subtick_data[btn.key] = btn.subtick_offset

            cache["inputs"][str(tick)] = {
                "keys": keyboard_keys,
                "mouse": mouse_keys,
                "subtick": subtick_data
            }

        return cache

    def _load(self, cache_data: dict) -> str:
        """Load phase: Save to cache file."""

        # Generate cache filename
        demo_name = self.demo_path.stem
        cache_path = self.output_dir / f"{demo_name}_cache.json"

        # Save as JSON
        with open(cache_path, 'w') as f:
            json.dump(cache_data, f, indent=2)

        return str(cache_path)


# Usage example
if __name__ == "__main__":
    pipeline = DemoETLPipeline("/path/to/faceit_match.dem")
    cache_path = pipeline.run()
    print(f"Cache ready at: {cache_path}")
```

---

## 6. Mock Data Generator

For development without real demos:

```python
import random
import json

class MockDataGenerator:
    """Generate mock input data for testing."""

    @staticmethod
    def generate_cache(num_ticks: int = 10000, output_path: str = "mock_cache.json"):
        """Generate mock cache file.

        Args:
            num_ticks: Number of ticks to generate
            output_path: Where to save the cache
        """

        cache = {
            "meta": {
                "demo_file": "mock_demo.dem",
                "player_id": "MOCK_PLAYER_123",
                "tick_range": [0, num_ticks],
                "tick_rate": 64
            },
            "inputs": {}
        }

        # Simulate realistic input patterns
        current_keys = set()

        for tick in range(num_ticks):
            # Random chance to press/release keys
            if random.random() < 0.1:  # 10% chance to change input
                possible_keys = ["W", "A", "S", "D", "SPACE", "CTRL", "SHIFT"]
                action = random.choice(["press", "release"])

                if action == "press" and len(current_keys) < 3:
                    current_keys.add(random.choice(possible_keys))
                elif action == "release" and current_keys:
                    current_keys.remove(random.choice(list(current_keys)))

            # Random mouse clicks
            mouse_keys = []
            if random.random() < 0.05:  # 5% chance
                mouse_keys.append("MOUSE1")

            # Generate subtick offsets
            subtick = {}
            for key in list(current_keys) + mouse_keys:
                subtick[key] = round(random.random(), 2)

            cache["inputs"][str(tick)] = {
                "keys": list(current_keys),
                "mouse": mouse_keys,
                "subtick": subtick
            }

        # Save
        with open(output_path, 'w') as f:
            json.dump(cache, f, indent=2)

        print(f"Generated mock cache with {num_ticks} ticks at {output_path}")


# Usage
MockDataGenerator.generate_cache(num_ticks=5000, output_path="./cache/mock_cache.json")
```

---

## 7. Performance Optimization

### 7.1 Sparse Storage

Only store ticks where inputs change:

```python
def optimize_cache(cache: dict) -> dict:
    """Remove duplicate consecutive entries."""

    optimized = cache.copy()
    optimized["inputs"] = {}

    prev_state = None

    for tick, data in sorted(cache["inputs"].items(), key=lambda x: int(x[0])):
        current_state = (tuple(data["keys"]), tuple(data["mouse"]))

        if current_state != prev_state:
            optimized["inputs"][tick] = data
            prev_state = current_state

    original_size = len(cache["inputs"])
    optimized_size = len(optimized["inputs"])

    print(f"Optimized: {original_size} → {optimized_size} ticks "
          f"({100 * (1 - optimized_size/original_size):.1f}% reduction)")

    return optimized
```

### 7.2 Memory-Mapped Files

For very large caches:

```python
import mmap

def load_cache_mmap(cache_path: str):
    """Load cache using memory mapping for efficiency."""
    with open(cache_path, 'rb') as f:
        mmapped_file = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
        return json.loads(mmapped_file)
```

---

## 8. Verification & Testing

### 8.1 ETL Test Script

```python
def test_etl_pipeline():
    """Test ETL pipeline with mock data."""

    # Create mock demo file (placeholder)
    demo_path = "/path/to/test.dem"

    # Run pipeline
    pipeline = DemoETLPipeline(demo_path)
    cache_path = pipeline.run()

    # Load and verify
    with open(cache_path, 'r') as f:
        cache = json.load(f)

    # Assertions
    assert "meta" in cache
    assert "inputs" in cache
    assert len(cache["inputs"]) > 0

    # Check tick 100 exists and has valid structure
    if "100" in cache["inputs"]:
        tick_data = cache["inputs"]["100"]
        assert "keys" in tick_data
        assert "mouse" in tick_data
        assert "subtick" in tick_data
        assert isinstance(tick_data["keys"], list)

    print("✓ ETL pipeline test passed")


test_etl_pipeline()
```

---

## 9. Next Steps

After ETL completion:
1. Cache is ready for real-time consumption
2. Proceed to Network Layer (Telnet sync)
3. Integrate with UI Layer for visualization
