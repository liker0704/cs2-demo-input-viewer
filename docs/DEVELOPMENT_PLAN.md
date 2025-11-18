# Development Plan

## Detailed Step-by-Step Implementation Guide

This document provides a concrete, actionable plan for implementing the CS2 Subtick Input Visualizer.

---

## Implementation Strategy

### Core Principle: Mock-First Development

All components are developed in this order:
1. **Interface** → 2. **Mock** → 3. **Tests** → 4. **Real Implementation**

This allows parallel development and immediate testing without external dependencies.

---

## Phase 1: Foundation & Interfaces

**Duration**: 2-3 days
**Goal**: Complete type system and abstract interfaces

### Task 1.1: Domain Models

**File**: `src/domain/models.py`

```python
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class InputData:
    """Player input state for a single tick."""
    tick: int
    keys: List[str]
    mouse: List[str]
    subtick: dict
    timestamp: Optional[float] = None

@dataclass
class PlayerInfo:
    """Player identification."""
    steam_id: str
    name: str
    entity_id: Optional[int] = None

@dataclass
class DemoMetadata:
    """Demo file metadata."""
    file_path: str
    player_id: str
    player_name: str
    tick_range: tuple[int, int]
    tick_rate: int
    duration_seconds: float
```

**Completion Criteria**:
- [ ] All dataclasses defined
- [ ] Type hints complete
- [ ] Docstrings added
- [ ] No import errors

---

### Task 1.2: Interface Definitions

**Files**:
- `src/interfaces/tick_source.py`
- `src/interfaces/demo_repository.py`
- `src/interfaces/player_tracker.py`
- `src/interfaces/input_visualizer.py`

**Template** (each interface):

```python
from abc import ABC, abstractmethod

class ITickSource(ABC):
    """Interface for tick synchronization sources."""

    @abstractmethod
    async def connect(self) -> bool:
        """Establish connection."""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection."""
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """Check connection status."""
        pass

    @abstractmethod
    async def get_current_tick(self) -> int:
        """Get current tick number."""
        pass
```

**Completion Criteria**:
- [ ] 4 interface files created
- [ ] All methods decorated with `@abstractmethod`
- [ ] Type hints on all signatures
- [ ] Can import without errors

---

### Task 1.3: Mock Implementations

**Files**:
- `src/mocks/tick_source.py`
- `src/mocks/demo_repository.py`
- `src/mocks/player_tracker.py`

**Example** (`MockTickSource`):

```python
import time
from interfaces.tick_source import ITickSource

class MockTickSource(ITickSource):
    """Timer-based tick source for testing."""

    def __init__(self, start_tick: int = 0, tick_rate: int = 64):
        self.start_tick = start_tick
        self.tick_rate = tick_rate
        self.start_time = time.time()
        self._connected = False

    async def connect(self) -> bool:
        self._connected = True
        return True

    async def disconnect(self) -> None:
        self._connected = False

    def is_connected(self) -> bool:
        return self._connected

    async def get_current_tick(self) -> int:
        elapsed = time.time() - self.start_time
        return self.start_tick + int(elapsed * self.tick_rate)
```

**Completion Criteria**:
- [ ] All mocks implement their interfaces
- [ ] Mocks can run without external dependencies
- [ ] Basic functionality works (tick increments, returns data, etc.)

---

### Task 1.4: Unit Tests

**File**: `tests/test_foundation.py`

```python
import pytest
from src.mocks.tick_source import MockTickSource

@pytest.mark.asyncio
async def test_mock_tick_source():
    """Test mock tick source."""
    mock = MockTickSource(start_tick=1000)

    assert await mock.connect()
    assert mock.is_connected()

    tick1 = await mock.get_current_tick()
    assert tick1 >= 1000

    await asyncio.sleep(0.1)
    tick2 = await mock.get_current_tick()
    assert tick2 > tick1  # Should advance

    await mock.disconnect()
    assert not mock.is_connected()
```

**Completion Criteria**:
- [ ] Tests for all mocks
- [ ] All tests pass (`pytest tests/`)
- [ ] Coverage >80%

---

## Phase 2: Data Layer (ETL)

**Duration**: 3-4 days
**Goal**: Parse demo files and generate cache

### Task 2.1: Button Decoder

**File**: `src/parsers/button_decoder.py`

```python
from typing import List
from dataclasses import dataclass

@dataclass
class ButtonPress:
    key: str
    subtick_offset: float = 0.0

class ButtonMask:
    """CS2 button bitmask constants."""
    IN_ATTACK = 1 << 0
    IN_JUMP = 1 << 1
    IN_DUCK = 1 << 2
    IN_FORWARD = 1 << 3
    IN_BACK = 1 << 4
    IN_MOVELEFT = 1 << 9
    IN_MOVERIGHT = 1 << 10
    IN_ATTACK2 = 1 << 11
    IN_RELOAD = 1 << 13
    IN_SPEED = 1 << 17
    # ... add more as needed

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
}

def decode_buttons(mask: int, subtick_moves: list = None) -> List[ButtonPress]:
    """Decode bitmask to button list."""
    buttons = []

    for button_value, key_name in BUTTON_TO_KEY.items():
        if mask & button_value:
            offset = 0.0

            # Find subtick timing
            if subtick_moves:
                for move in subtick_moves:
                    if move.get("button") == button_value and move.get("pressed"):
                        offset = move.get("when", 0.0)
                        break

            buttons.append(ButtonPress(key=key_name, subtick_offset=offset))

    return buttons
```

**Testing**:

```python
def test_decode_buttons():
    # W pressed (bit 3)
    mask = 8
    buttons = decode_buttons(mask)
    assert len(buttons) == 1
    assert buttons[0].key == "W"

    # W + A pressed
    mask = 8 | 512
    buttons = decode_buttons(mask)
    assert len(buttons) == 2
    assert set(b.key for b in buttons) == {"W", "A"}
```

**Completion Criteria**:
- [ ] Decoder handles all common buttons
- [ ] Subtick offset extraction works
- [ ] Unit tests pass

---

### Task 2.2: Mock Data Generator

**File**: `src/parsers/mock_data_generator.py`

Generate realistic test data without real demos:

```python
import random
import json
from pathlib import Path

def generate_mock_cache(
    num_ticks: int = 5000,
    output_path: str = "./cache/mock_cache.json"
):
    """Generate mock input cache for testing."""

    cache = {
        "meta": {
            "demo_file": "mock_demo.dem",
            "player_id": "MOCK_PLAYER_123",
            "player_name": "TestPlayer",
            "tick_range": [0, num_ticks],
            "tick_rate": 64
        },
        "inputs": {}
    }

    # Simulate movement patterns
    current_keys = set()

    for tick in range(num_ticks):
        # 10% chance to change input state
        if random.random() < 0.1:
            keys = ["W", "A", "S", "D", "SPACE", "CTRL", "SHIFT"]

            if random.random() < 0.5:
                # Press key
                if len(current_keys) < 3:
                    current_keys.add(random.choice(keys))
            else:
                # Release key
                if current_keys:
                    current_keys.discard(random.choice(list(current_keys)))

        # 5% chance for mouse click
        mouse = []
        if random.random() < 0.05:
            mouse.append("MOUSE1")

        # Generate subtick data
        subtick = {key: round(random.random(), 2) for key in list(current_keys) + mouse}

        cache["inputs"][str(tick)] = {
            "keys": list(current_keys),
            "mouse": mouse,
            "subtick": subtick
        }

    # Save
    Path(output_path).parent.mkdir(exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(cache, f, indent=2)

    print(f"Generated {num_ticks} ticks at {output_path}")
```

**Completion Criteria**:
- [ ] Generates valid JSON cache
- [ ] Data looks realistic (not random noise)
- [ ] Can load in MockDemoRepository

---

### Task 2.3: Mock Demo Repository

**File**: `src/mocks/demo_repository.py`

```python
import json
from typing import Optional
from interfaces.demo_repository import IDemoRepository
from domain.models import InputData, DemoMetadata

class MockDemoRepository(IDemoRepository):
    """Mock repository loading from JSON cache."""

    def __init__(self, cache_path: str = "./cache/mock_cache.json"):
        self.cache_path = cache_path
        self.cache = None
        self.metadata = None

    def load_demo(self, demo_path: str) -> bool:
        """Load cache file."""
        try:
            with open(self.cache_path, 'r') as f:
                self.cache = json.load(f)

            # Load metadata
            meta = self.cache["meta"]
            self.metadata = DemoMetadata(
                file_path=meta["demo_file"],
                player_id=meta["player_id"],
                player_name=meta.get("player_name", "Unknown"),
                tick_range=tuple(meta["tick_range"]),
                tick_rate=meta["tick_rate"],
                duration_seconds=meta["tick_range"][1] / meta["tick_rate"]
            )

            return True

        except Exception as e:
            print(f"Failed to load cache: {e}")
            return False

    def get_inputs(self, tick: int, player_id: str) -> Optional[InputData]:
        """Get inputs for tick."""
        if not self.cache:
            return None

        tick_str = str(tick)
        if tick_str not in self.cache["inputs"]:
            return None

        data = self.cache["inputs"][tick_str]

        return InputData(
            tick=tick,
            keys=data.get("keys", []),
            mouse=data.get("mouse", []),
            subtick=data.get("subtick", {})
        )

    def get_tick_range(self) -> tuple[int, int]:
        """Get available tick range."""
        if self.metadata:
            return self.metadata.tick_range
        return (0, 0)

    def get_default_player(self) -> str:
        """Get default player ID."""
        if self.metadata:
            return self.metadata.player_id
        return ""
```

**Testing**:

```python
def test_mock_repo():
    repo = MockDemoRepository()
    assert repo.load_demo("dummy_path")

    # Check metadata
    assert repo.metadata.tick_rate == 64

    # Get input at tick 100
    data = repo.get_inputs(100, "MOCK_PLAYER_123")
    assert data is not None
    assert isinstance(data.keys, list)
```

**Completion Criteria**:
- [ ] Loads mock cache successfully
- [ ] Returns valid InputData objects
- [ ] Tests pass

---

### Task 2.4: Real ETL Pipeline (demoparser2)

**File**: `src/parsers/etl_pipeline.py`

**Note**: This task requires a real demo file for testing.

```python
from demoparser2 import DemoParser
from pathlib import Path
import json
from .button_decoder import decode_buttons

class DemoETLPipeline:
    """ETL pipeline using demoparser2."""

    def __init__(self, demo_path: str, output_dir: str = "./cache"):
        self.demo_path = Path(demo_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def run(self, player_id: str = None) -> str:
        """Run ETL pipeline."""
        print(f"[ETL] Processing {self.demo_path.name}...")

        # Extract
        raw_data = self._extract()

        # Transform
        cache_data = self._transform(raw_data, player_id)

        # Load
        cache_path = self._load(cache_data)

        print(f"[ETL] Complete: {cache_path}")
        return cache_path

    def _extract(self):
        """Extract data using demoparser2."""
        parser = DemoParser(str(self.demo_path))

        df = parser.parse_event(
            "player_input",
            player=["m_steamID", "name"],
            other=["m_nButtonDownMaskPrev", "subtick_moves", "tick"]
        )

        return df

    def _transform(self, df, player_id):
        """Transform raw data to cache format."""
        # Auto-detect player if not specified
        if not player_id:
            player_id = df['m_steamID'].value_counts().idxmax()

        # Filter for player
        player_data = df[df['m_steamID'] == player_id]

        # Build cache
        cache = {
            "meta": {
                "demo_file": self.demo_path.name,
                "player_id": player_id,
                "tick_range": [int(player_data['tick'].min()), int(player_data['tick'].max())],
                "tick_rate": 64
            },
            "inputs": {}
        }

        # Process each tick
        for _, row in player_data.iterrows():
            tick = int(row['tick'])
            mask = int(row['m_nButtonDownMaskPrev'])
            subtick_moves = row.get('subtick_moves', [])

            buttons = decode_buttons(mask, subtick_moves)

            keys = [b.key for b in buttons if not b.key.startswith('MOUSE')]
            mouse = [b.key for b in buttons if b.key.startswith('MOUSE')]
            subtick = {b.key: b.subtick_offset for b in buttons}

            cache["inputs"][str(tick)] = {
                "keys": keys,
                "mouse": mouse,
                "subtick": subtick
            }

        return cache

    def _load(self, cache_data):
        """Save cache to disk."""
        cache_path = self.output_dir / f"{self.demo_path.stem}_cache.json"

        with open(cache_path, 'w') as f:
            json.dump(cache_data, f, indent=2)

        return str(cache_path)
```

**Completion Criteria**:
- [ ] Parses real demo file without errors
- [ ] Generates valid cache JSON
- [ ] Cache can be loaded by MockDemoRepository

---

## Phase 3: UI Layer

**Duration**: 3-4 days
**Goal**: Working overlay with mock data

### Task 3.1: Layouts & Positions

**File**: `src/ui/layouts.py`

Implement `KeyboardLayout`, `MouseLayout`, `KeyPosition`, `MousePosition` classes from documentation.

**Completion Criteria**:
- [ ] All key positions calculated correctly
- [ ] Mouse component positions correct
- [ ] Unit tests for position calculations

---

### Task 3.2: Renderers

**Files**:
- `src/ui/keyboard_renderer.py`
- `src/ui/mouse_renderer.py`

Implement rendering logic using QPainter.

**Testing Strategy**: Visual testing with screenshots.

**Completion Criteria**:
- [ ] Keys render at correct positions
- [ ] Active state changes color
- [ ] Mouse buttons render correctly
- [ ] No rendering glitches

---

### Task 3.3: Main Overlay

**File**: `src/ui/overlay.py`

Complete `CS2InputOverlay` class with integration of renderers.

**Manual Test**:

```python
from PyQt6.QtWidgets import QApplication
from src.ui.overlay import CS2InputOverlay
from src.domain.models import InputData

app = QApplication([])
overlay = CS2InputOverlay()
overlay.show()

# Test with mock data
test_data = InputData(
    tick=100,
    keys=["W", "A"],
    mouse=["MOUSE1"],
    subtick={}
)

overlay.update_inputs(test_data)
app.exec()
```

**Completion Criteria**:
- [ ] Overlay shows on screen
- [ ] Transparent background works
- [ ] Click-through works
- [ ] Updates render smoothly

---

## Phase 4: Network Layer

**Duration**: 2-3 days
**Goal**: Real-time sync with CS2

### Task 4.1: Telnet Client

**File**: `src/network/telnet_client.py`

Implement `CS2TelnetClient` using asyncio.

**Manual Test**:

```bash
# 1. Launch CS2
cs2.exe -netconport 2121 -insecure

# 2. Play any demo

# 3. Test script
python scripts/test_telnet.py
```

**Completion Criteria**:
- [ ] Connects to CS2 successfully
- [ ] Parses demo_info response
- [ ] Returns current tick
- [ ] Handles disconnection gracefully

---

### Task 4.2: Sync & Prediction Engines

**Files**:
- `src/network/sync_engine.py`
- `src/core/prediction_engine.py`

Implement as per documentation.

**Testing**:

```python
# Compare predicted vs actual
async def test_prediction_accuracy():
    telnet = CS2TelnetClient()
    await telnet.connect()

    sync = SyncEngine(telnet)
    pred = PredictionEngine(sync)

    await sync.update()

    for i in range(100):
        predicted = pred.get_current_tick()
        await asyncio.sleep(0.016)  # 60 FPS

    # Check drift
    assert pred.get_drift() < 5  # Less than 5 tick drift
```

**Completion Criteria**:
- [ ] Prediction stays within 5 ticks of actual
- [ ] Handles demo pause/resume
- [ ] Handles tick jumps (Shift+F2)

---

## Phase 5: Integration

**Duration**: 2-3 days
**Goal**: Complete application

### Task 5.1: Orchestrator

**File**: `src/core/orchestrator.py`

Implement main orchestrator connecting all components.

**Completion Criteria**:
- [ ] All components initialize correctly
- [ ] Sync, prediction, and render loops run
- [ ] Player tracking works
- [ ] Graceful shutdown

---

### Task 5.2: Configuration

**Files**:
- `src/core/config.py`
- `config.json`

Implement config loading/saving.

**Completion Criteria**:
- [ ] Config loads from JSON
- [ ] Defaults work if no config
- [ ] Config saves user preferences

---

### Task 5.3: Main Entry Point

**File**: `src/main.py`

Complete CLI and application runner.

**Completion Criteria**:
- [ ] `--mode dev` works with mocks
- [ ] `--mode prod` works with real CS2
- [ ] `--demo` argument works
- [ ] Help text is clear

---

## Phase 6: Testing & Polish

**Duration**: 3-5 days
**Goal**: Production ready

### Task 6.1: Integration Tests

**File**: `tests/test_integration.py`

End-to-end tests.

**Completion Criteria**:
- [ ] Full pipeline test (mock mode)
- [ ] Error handling tested
- [ ] Edge cases covered

---

### Task 6.2: Performance Optimization

**Targets**:
- [ ] <2% CPU usage during playback
- [ ] <100MB RAM usage
- [ ] 60 FPS rendering stable

**Tools**:
- `cProfile` for Python profiling
- `memory_profiler` for memory analysis

---

### Task 6.3: Documentation

**Files**:
- `README.md` (user-facing)
- `CONTRIBUTING.md`
- `CHANGELOG.md`

**Completion Criteria**:
- [ ] Installation instructions clear
- [ ] Usage examples provided
- [ ] Troubleshooting section complete

---

## Success Metrics

### Code Quality

- ✓ All tests pass
- ✓ Coverage >80%
- ✓ No linting errors (flake8/pylint)
- ✓ Type checking passes (mypy)

### Performance

- ✓ <2% CPU usage
- ✓ <100MB RAM
- ✓ 60 FPS stable
- ✓ <100ms cache load time

### Functionality

- ✓ Parses 400MB demo successfully
- ✓ Syncs with CS2 in real-time
- ✓ Overlay renders correctly
- ✓ No crashes during 1-hour session

---

## Risk Mitigation

### Risk 1: demoparser2 doesn't work as expected

**Mitigation**: Early testing in Phase 2, fallback to manual parsing if needed

### Risk 2: Telnet API changes in CS2 update

**Mitigation**: Abstract behind ITickSource, easy to swap implementation

### Risk 3: Performance issues

**Mitigation**: Mock-first development allows profiling early

### Risk 4: Button mask values incorrect for Source 2

**Mitigation**: Experimental verification script in Phase 2

---

## Next Actions

1. **Set up project structure** (30 min)
2. **Create virtual environment** (5 min)
3. **Implement Phase 1, Task 1.1** (1 hour)
4. **Continue following plan sequentially**

---

**Total Estimated Time**: 3-4 weeks for full implementation
