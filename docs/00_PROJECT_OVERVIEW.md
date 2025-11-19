# Project Overview

## CS2 Subtick Input Visualizer

**Version:** 2.0 (Research-Based Architecture)
**Type:** Desktop Overlay Application
**Stack:** Python 3.10+, PyQt6, demoparser2, asyncio

---

## Table of Contents

1. [Project Goal](#project-goal)
2. [Architecture Summary](#architecture-summary)
3. [Documentation Structure](#documentation-structure)
4. [Technology Stack](#technology-stack)
5. [Project Structure](#project-structure)
6. [Development Workflow](#development-workflow)
7. [Quick Start](#quick-start)
8. [Milestones](#milestones)

---

## Project Goal

Visualize player inputs (keyboard and mouse) in real-time while watching CS2 demo files. The overlay shows exactly when and which keys were pressed, including subtick-precise timing information.

**Use Cases:**
- Analyzing professional player movements
- Creating content for YouTube/Twitch
- Understanding optimal input patterns
- Learning counter-strafing techniques

---

## Architecture Summary

### Hybrid Architecture

The system uses a two-phase approach:

```
┌─────────────────────────────────────────┐
│  PHASE 1: OFFLINE (ETL)                 │
│  .dem file → Parse → Transform → Cache  │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│  PHASE 2: RUNTIME (Real-time)           │
│  CS2 ← Telnet → Sync → Predict → UI    │
└─────────────────────────────────────────┘
```

**Why Hybrid?**
- **Performance**: 400MB demo parsed once, not during playback
- **Responsiveness**: Real-time lookup from cache (O(1))
- **Flexibility**: Can pre-process multiple demos offline

### Core Principles

1. **SOLID Design**: Interface-based, dependency injection
2. **Mock-First Development**: Build UI without CS2 running
3. **Extensibility**: Easy to add grenades, analytics, etc.
4. **Performance**: Hardware-accelerated UI, <2% CPU usage

---

## Documentation Structure

| Document | Purpose | For Whom |
|----------|---------|----------|
| **00_PROJECT_OVERVIEW.md** | High-level overview (this file) | Everyone |
| **01_ARCHITECTURE.md** | System design, interfaces, SOLID | Architects, Leads |
| **02_DATA_LAYER.md** | ETL pipeline, demoparser2 | Backend Devs |
| **03_NETWORK_LAYER.md** | Telnet sync, prediction | Network/Backend |
| **04_UI_LAYER.md** | PyQt6 overlay, rendering | Frontend Devs |
| **05_CORE_LOGIC.md** | Orchestrator, integration | System Integrators |

**Reading Order:**
1. Start with 00 (this file) for overview
2. Read 01 for architecture understanding
3. Read 02-05 based on your focus area

---

## Technology Stack

### Core Technologies

| Technology | Version | Purpose | Why? |
|------------|---------|---------|------|
| **Python** | 3.10-3.12 | Core language | Balance of performance and ease |
| **PyQt6** | Latest | UI overlay | Hardware acceleration, transparency support |
| **demoparser2** | Latest | Demo parsing | Only library with subtick support |
| **asyncio** | Stdlib | Async networking | Modern, non-blocking I/O |

### Key Libraries

```python
# requirements.txt
PyQt6>=6.4.0
demoparser2>=0.x.x
msgpack>=1.0.0  # Optional: fast cache serialization
pytest>=7.0.0   # Testing
pytest-asyncio>=0.21.0  # Async tests
```

### CS2 Requirements

- **Launch Flags**: `-netconport 2121 -insecure`
- **Network Console**: Telnet to `localhost:2121`
- **VAC Safety**: `-insecure` disables VAC (safe for demos)

---

## Project Structure

```
cs2-demo-input-viewer/
├── docs/                          # Documentation
│   ├── 00_PROJECT_OVERVIEW.md
│   ├── 01_ARCHITECTURE.md
│   ├── 02_DATA_LAYER.md
│   ├── 03_NETWORK_LAYER.md
│   ├── 04_UI_LAYER.md
│   └── 05_CORE_LOGIC.md
│
├── src/                           # Source code
│   ├── domain/                    # Domain models
│   │   └── models.py              # InputData, PlayerID, etc.
│   │
│   ├── interfaces/                # Abstract interfaces
│   │   ├── tick_source.py         # ITickSource
│   │   ├── demo_repository.py     # IDemoRepository
│   │   ├── player_tracker.py      # IPlayerTracker
│   │   └── input_visualizer.py    # IInputVisualizer
│   │
│   ├── mocks/                     # Mock implementations
│   │   ├── tick_source.py         # MockTickSource
│   │   ├── demo_repository.py     # MockDemoRepository
│   │   └── player_tracker.py      # MockPlayerTracker
│   │
│   ├── parsers/                   # ETL layer
│   │   ├── etl_pipeline.py        # DemoETLPipeline
│   │   ├── button_decoder.py      # decode_buttons()
│   │   └── cache_manager.py       # Cache I/O
│   │
│   ├── network/                   # Network layer
│   │   ├── telnet_client.py       # CS2TelnetClient
│   │   ├── sync_engine.py         # SyncEngine
│   │   └── player_tracker.py      # CS2PlayerTracker
│   │
│   ├── ui/                        # UI layer
│   │   ├── overlay.py             # CS2InputOverlay
│   │   ├── keyboard_renderer.py   # KeyboardRenderer
│   │   ├── mouse_renderer.py      # MouseRenderer
│   │   └── layouts.py             # KeyboardLayout, MouseLayout
│   │
│   ├── core/                      # Core logic
│   │   ├── orchestrator.py        # Main Orchestrator
│   │   ├── prediction_engine.py   # PredictionEngine
│   │   └── config.py              # AppConfig
│   │
│   └── main.py                    # Entry point
│
├── tests/                         # Unit tests
│   ├── test_data_layer.py
│   ├── test_network_layer.py
│   ├── test_ui_layer.py
│   └── test_core_logic.py
│
├── cache/                         # Cached demo data
│   └── .gitkeep
│
├── demos/                         # Demo files (gitignored)
│   └── .gitkeep
│
├── config.json                    # User configuration
├── requirements.txt               # Python dependencies
└── README.md                      # User-facing README
```

---

## Development Workflow

### Phase 1: Foundation (Week 1)

**Goal**: Establish interfaces and mocks

```bash
# Tasks
1. Create all interface files (src/interfaces/)
2. Implement mock classes (src/mocks/)
3. Write domain models (src/domain/models.py)
4. Unit test mocks
```

**Deliverable**: Can import and instantiate all mocks without errors.

### Phase 2: Data Layer (Week 1-2)

**Goal**: ETL pipeline working offline

```bash
# Tasks
1. Implement button decoder
2. Create ETL pipeline with demoparser2
3. Generate mock cache for testing
4. Test with real 400MB demo
```

**Deliverable**: `cache.json` file with decoded inputs.

### Phase 3: UI Layer (Week 2)

**Goal**: Overlay renders with mock data

```bash
# Tasks
1. Implement PyQt6 overlay window
2. Create keyboard renderer
3. Create mouse renderer
4. Test with MockDemoRepository
```

**Deliverable**: Overlay shows animated inputs from mock data.

### Phase 4: Network Layer (Week 2-3)

**Goal**: Real-time sync with CS2

```bash
# Tasks
1. Implement asyncio Telnet client
2. Create sync engine
3. Build prediction engine
4. Test with running CS2
```

**Deliverable**: Can read current tick from CS2 demo playback.

### Phase 5: Integration (Week 3)

**Goal**: Complete application

```bash
# Tasks
1. Build main orchestrator
2. Create config system
3. Add command-line interface
4. Integration testing
```

**Deliverable**: Full app running end-to-end.

### Phase 6: Polish (Week 4)

**Goal**: Production ready

```bash
# Tasks
1. Performance optimization
2. Error handling improvements
3. User documentation
4. Packaging/distribution
```

**Deliverable**: Releasable v1.0.

---

## Quick Start

### For Developers

```bash
# 1. Clone repository
git clone <repo-url>
cd cs2-demo-input-viewer

# 2. Create virtual environment
python3.10 -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Generate mock data
python -m src.parsers.etl_pipeline --mock

# 5. Run in development mode (with mocks)
python src/main.py --mode dev

# 6. Run tests
pytest tests/
```

### For Users

```bash
# 1. Install from release
# (Future: download .exe or .dmg)

# 2. Launch CS2 with flags
cs2.exe -netconport 2121 -insecure

# 3. Run visualizer
cs2-input-viewer --demo path/to/demo.dem

# 4. Play demo in CS2
# Overlay will sync automatically
```

---

## Milestones

### Milestone 1: Data Proof ✓

**Status**: Planned
**Goal**: Verify demoparser2 extracts buttons from real demo

```bash
# Run extraction test
python scripts/extract_test.py --demo demos/faceit_match.dem

# Expected output:
# Tick: 500 | Mask: 8 (W pressed)
# Tick: 501 | Mask: 520 (W + A pressed)
# ...
```

**Success Criteria**:
- ✓ Script parses 400MB demo without crashes
- ✓ Outputs readable button presses
- ✓ Subtick data present

### Milestone 2: Sync Proof ✓

**Status**: Planned
**Goal**: Read current tick from CS2 via Telnet

```bash
# Run sync test
python scripts/sync_test.py

# Expected output:
# [Telnet] Connected to CS2
# [Sync] Tick: 12500
# [Sync] Tick: 12564
# [Sync] Tick: 12628
# ...
```

**Success Criteria**:
- ✓ Connects to CS2 network console
- ✓ Parses tick from demo_info command
- ✓ Updates in real-time (~4 Hz)

### Milestone 3: MVP ✓

**Status**: Planned
**Goal**: Combine data + sync (console output only)

```bash
# Run MVP
python src/main.py --mode mvp --demo demos/match.dem

# Expected output:
# [MVP] Tick: 12500 -> Keys: W, A | Mouse: MOUSE1
# [MVP] Tick: 12501 -> Keys: W, D | Mouse: -
# ...
```

**Success Criteria**:
- ✓ Real-time sync working
- ✓ Correct inputs displayed
- ✓ No UI yet (console only)

### Milestone 4: Overlay ✓

**Status**: Planned
**Goal**: Full graphical overlay

```bash
# Run with overlay
python src/main.py --mode prod --demo demos/match.dem
```

**Success Criteria**:
- ✓ Transparent overlay renders
- ✓ Keys highlight on press
- ✓ Smooth 60 FPS
- ✓ <2% CPU usage

---

## Design Decisions

### Why Python?

- **Rapid Development**: Fast iteration for prototype
- **Ecosystem**: `demoparser2`, `PyQt6` available
- **Async Support**: `asyncio` for networking
- **Future**: Can port performance-critical parts to Rust if needed

### Why PyQt6 over Tkinter/Pygame?

- **Hardware Acceleration**: GPU-accelerated rendering
- **Transparency**: Native support for transparent windows
- **Modern**: Active development, Python 3.10+ compatible

### Why Hybrid Architecture?

- **User Experience**: Instant response during playback
- **Scalability**: Can cache multiple demos
- **Separation**: ETL can run on server, runtime on client

### Why Interfaces/Mocks?

- **Parallel Development**: UI team doesn't wait for network team
- **Testing**: Easy to unit test in isolation
- **Flexibility**: Swap implementations without code changes

---

## Future Extensions

### Planned Features (v2.0+)

1. **Grenade Visualization**
   - Show grenade trajectories
   - Lineup indicators

2. **Advanced Analytics**
   - Counter-strafe detection
   - Movement heatmaps
   - Input timing statistics

3. **Multi-Player View**
   - Compare two players side-by-side
   - Highlight differences

4. **Recording**
   - Export inputs to video overlay
   - OBS integration via plugin

5. **Cloud Processing**
   - Upload demo for ETL on server
   - Download pre-processed cache

---

## Contributing

### Code Style

- **PEP 8**: Follow Python style guide
- **Type Hints**: All public functions must have type annotations
- **Docstrings**: Google-style docstrings

```python
def example_function(param: int) -> str:
    """Brief description.

    Args:
        param: Parameter description

    Returns:
        Return value description
    """
    return str(param)
```

### Testing

- Minimum 80% code coverage
- All new features must have tests
- Use pytest for testing

### Pull Requests

1. Create feature branch from `main`
2. Write code + tests
3. Ensure tests pass: `pytest tests/`
4. Submit PR with description

---

## License

MIT License - See LICENSE file

---

## Support

- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions
- **Discord**: [TBD]

---

## Acknowledgments

- **demoparser2**: LaihoE for the amazing parser
- **CS2 Community**: For reverse engineering help
- **PyQt6**: Riverbank Computing for the framework
