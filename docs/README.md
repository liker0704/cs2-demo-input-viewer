# Documentation Index

## CS2 Subtick Input Visualizer - Complete Documentation

---

## 📚 Documentation Structure

### For Everyone

| Document | Description | Read Time |
|----------|-------------|-----------|
| **[00_PROJECT_OVERVIEW.md](00_PROJECT_OVERVIEW.md)** | High-level project overview, goals, and architecture summary | 15 min |
| **[USER_GUIDE.md](USER_GUIDE.md)** | Installation and usage instructions for end users | 10 min |

### For Developers

| Document | Description | Read Time | Audience |
|----------|-------------|-----------|----------|
| **[01_ARCHITECTURE.md](01_ARCHITECTURE.md)** | System architecture, SOLID principles, interfaces | 30 min | Architects, Tech Leads |
| **[02_DATA_LAYER.md](02_DATA_LAYER.md)** | ETL pipeline, demoparser2, cache structure | 25 min | Backend Developers |
| **[03_NETWORK_LAYER.md](03_NETWORK_LAYER.md)** | Telnet client, sync engine, prediction | 25 min | Network/Backend Devs |
| **[04_UI_LAYER.md](04_UI_LAYER.md)** | PyQt6 overlay, rendering, layout specs | 30 min | Frontend Developers |
| **[05_CORE_LOGIC.md](05_CORE_LOGIC.md)** | Orchestrator, dependency injection, integration | 25 min | Full-Stack Developers |
| **[DEVELOPMENT_PLAN.md](DEVELOPMENT_PLAN.md)** | Step-by-step implementation guide | 45 min | Project Managers, Developers |

---

## 🚀 Quick Navigation

### "I want to understand the project"

Start here:
1. [00_PROJECT_OVERVIEW.md](00_PROJECT_OVERVIEW.md) - What and why
2. [01_ARCHITECTURE.md](01_ARCHITECTURE.md) - How it works

### "I want to use the tool"

Read:
- [USER_GUIDE.md](USER_GUIDE.md) - Installation and usage

### "I want to contribute"

Follow this path:
1. [00_PROJECT_OVERVIEW.md](00_PROJECT_OVERVIEW.md) - Understand the vision
2. [01_ARCHITECTURE.md](01_ARCHITECTURE.md) - Learn the architecture
3. [DEVELOPMENT_PLAN.md](DEVELOPMENT_PLAN.md) - See what to build
4. Specific layer docs (02-05) based on your interest

### "I want to implement a specific component"

Go directly to:
- **Parsing demos**: [02_DATA_LAYER.md](02_DATA_LAYER.md)
- **Network sync**: [03_NETWORK_LAYER.md](03_NETWORK_LAYER.md)
- **Building UI**: [04_UI_LAYER.md](04_UI_LAYER.md)
- **Tying it together**: [05_CORE_LOGIC.md](05_CORE_LOGIC.md)

---

## 📋 Document Summaries

### 00_PROJECT_OVERVIEW.md

**What**: Introduction to the project
**Contains**:
- Project goals and use cases
- Architecture summary (Hybrid ETL + Runtime)
- Technology stack explanation
- Project structure
- Development workflow
- Quick start commands
- Milestones and success criteria

**Key Takeaway**: Understand *what* we're building and *why*

---

### 01_ARCHITECTURE.md

**What**: System design and principles
**Contains**:
- Hybrid architecture explanation
- SOLID principles application
- Core interfaces (ITickSource, IDemoRepository, etc.)
- Data flow diagrams
- Component dependencies
- Extensibility examples
- Testing strategy

**Key Takeaway**: Understand *how* components interact

---

### 02_DATA_LAYER.md

**What**: Demo parsing and caching
**Contains**:
- ETL pipeline (Extract, Transform, Load)
- demoparser2 usage guide
- Button mask decoding algorithm
- Subtick data processing
- Cache structure (JSON/MessagePack/SQLite)
- Mock data generator
- Complete ETL implementation

**Key Takeaway**: How to convert .dem files to usable cache

---

### 03_NETWORK_LAYER.md

**What**: Real-time synchronization with CS2
**Contains**:
- CS2 network console setup
- Asyncio Telnet client implementation
- Sync engine (polling strategy)
- Prediction engine (tick interpolation)
- Player tracking
- Mock implementations
- Error handling and reconnection

**Key Takeaway**: How to sync overlay with demo playback

---

### 04_UI_LAYER.md

**What**: PyQt6 overlay rendering
**Contains**:
- PyQt6 window configuration (transparency, click-through)
- Keyboard layout specification (exact positions)
- Mouse layout specification
- Rendering implementation
- Visual styles (wireframe with highlights)
- Performance optimization
- Testing strategies

**Key Takeaway**: How to render the visual overlay

---

### 05_CORE_LOGIC.md

**What**: Integration and orchestration
**Contains**:
- Main orchestrator implementation
- Prediction engine details
- Sync engine implementation
- Configuration system
- Application factory (dev/prod modes)
- Entry point and CLI
- Extensibility examples
- Performance monitoring

**Key Takeaway**: How to tie all components together

---

### DEVELOPMENT_PLAN.md

**What**: Step-by-step implementation guide
**Contains**:
- Concrete tasks for each phase
- Code templates and examples
- Completion criteria for each task
- Testing strategies
- Timeline estimates
- Risk mitigation
- Success metrics

**Key Takeaway**: Exactly what to build and in what order

---

### USER_GUIDE.md

**What**: End-user documentation
**Contains**:
- Installation instructions
- Quick start guide
- Configuration options
- Troubleshooting
- FAQ
- Advanced usage

**Key Takeaway**: How users will actually use the tool

---

## 🎯 Learning Paths

### Path 1: Architecture First (Recommended for leads)

1. 00_PROJECT_OVERVIEW.md (context)
2. 01_ARCHITECTURE.md (design)
3. DEVELOPMENT_PLAN.md (execution)
4. 02-05 as needed

### Path 2: Component First (Recommended for individual devs)

1. 00_PROJECT_OVERVIEW.md (context)
2. Your component doc (02, 03, 04, or 05)
3. 01_ARCHITECTURE.md (to understand integration)
4. DEVELOPMENT_PLAN.md (to see tasks)

### Path 3: User First (Recommended for testers)

1. USER_GUIDE.md (usage)
2. 00_PROJECT_OVERVIEW.md (understand internals)
3. Report issues/feedback

---

## 🔧 Code Examples Index

### Data Layer Examples

- Button decoding: [02_DATA_LAYER.md#decoding-algorithm](02_DATA_LAYER.md)
- ETL pipeline: [02_DATA_LAYER.md#complete-etl-pipeline](02_DATA_LAYER.md)
- Mock data generator: [02_DATA_LAYER.md#mock-data-generator](02_DATA_LAYER.md)

### Network Layer Examples

- Telnet client: [03_NETWORK_LAYER.md#async-telnet-client](03_NETWORK_LAYER.md)
- Sync engine: [03_NETWORK_LAYER.md#sync-engine](03_NETWORK_LAYER.md)
- Prediction: [03_NETWORK_LAYER.md#basic-prediction](03_NETWORK_LAYER.md)

### UI Layer Examples

- Overlay setup: [04_UI_LAYER.md#window-configuration](04_UI_LAYER.md)
- Keyboard rendering: [04_UI_LAYER.md#keyboard-rendering](04_UI_LAYER.md)
- Mouse rendering: [04_UI_LAYER.md#mouse-rendering](04_UI_LAYER.md)

### Core Logic Examples

- Orchestrator: [05_CORE_LOGIC.md#orchestrator-class](05_CORE_LOGIC.md)
- Config system: [05_CORE_LOGIC.md#configuration-class](05_CORE_LOGIC.md)
- Main entry point: [05_CORE_LOGIC.md#main-entry-point](05_CORE_LOGIC.md)

---

## 📊 Diagrams Index

### Architecture Diagrams

- System overview: [01_ARCHITECTURE.md#overview](01_ARCHITECTURE.md)
- Data flow: [01_ARCHITECTURE.md#data-flow](01_ARCHITECTURE.md)
- Component dependencies: [01_ARCHITECTURE.md#component-dependencies](01_ARCHITECTURE.md)

### ETL Diagrams

- Pipeline flow: [02_DATA_LAYER.md#load-phase](02_DATA_LAYER.md)

### Sync Diagrams

- Runtime sequence: [03_NETWORK_LAYER.md#runtime-phase](03_NETWORK_LAYER.md)

---

## 🧪 Testing Documentation

- Unit tests: [01_ARCHITECTURE.md#testing-strategy](01_ARCHITECTURE.md)
- Integration tests: [DEVELOPMENT_PLAN.md#phase-6-testing--polish](DEVELOPMENT_PLAN.md)
- UI testing: [04_UI_LAYER.md#testing](04_UI_LAYER.md)

---

## 🔗 External Resources

### Technologies

- **PyQt6**: https://doc.qt.io/qtforpython-6/
- **demoparser2**: https://github.com/LaihoE/demoparser
- **asyncio**: https://docs.python.org/3/library/asyncio.html

### CS2 Documentation

- **Network Console**: https://developer.valvesoftware.com/wiki/Command_Line_Options
- **Source 2 SDK**: Limited public documentation

### Research References

- Subtick system: Community reverse engineering
- Button masks: Source SDK references

---

## 📝 Contribution Guidelines

When adding new documentation:

1. **Update this index** with new document
2. **Add cross-references** in related docs
3. **Include code examples** where applicable
4. **Add to appropriate learning path**
5. **Update diagrams** if architecture changes

### Documentation Style

- Use clear headings (H1, H2, H3)
- Include code examples with language tags
- Add completion criteria for tasks
- Link to related documents
- Include diagrams where helpful

---

## 🆘 Getting Help

Can't find what you need?

1. Check the index above
2. Search across all docs (Ctrl+Shift+F in VS Code)
3. Open an issue on GitHub
4. Ask in Discussions

---

## 📅 Version History

- **v2.0** (Current): Research-based architecture, full documentation
- **v1.0**: Initial concept (see main README.md)

---

Last Updated: 2024
