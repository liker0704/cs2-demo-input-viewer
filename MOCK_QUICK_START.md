# Mock Implementation Quick Start

This guide shows you how to quickly get started with the mock implementations.

## Files Created

### Interface Definitions
- `/src/interfaces/tick_source.py` - ITickSource interface
- `/src/interfaces/demo_repository.py` - IDemoRepository interface  
- `/src/interfaces/player_tracker.py` - IPlayerTracker interface

### Mock Implementations
- `/src/mocks/tick_source.py` - MockTickSource
- `/src/mocks/demo_repository.py` - MockDemoRepository
- `/src/mocks/player_tracker.py` - MockPlayerTracker
- `/src/mocks/__init__.py` - Package exports

### Sample Data & Examples
- `/data/sample_cache.json` - Sample input data cache
- `/examples/mock_usage_example.py` - Complete usage example
- `/src/mocks/README.md` - Detailed documentation

## Quick Test

```bash
# Test imports
python3 -c "
import sys
sys.path.insert(0, 'src')
from mocks import MockTickSource, MockDemoRepository, MockPlayerTracker
print('✓ All imports successful')
"

# Run complete example
python3 examples/mock_usage_example.py
```

## 30-Second Tutorial

```python
import asyncio
import sys
sys.path.insert(0, 'src')

from mocks import MockTickSource, MockDemoRepository, MockPlayerTracker

async def quick_demo():
    # 1. Create mocks
    tick_source = MockTickSource(start_tick=1000, tick_rate=64)
    repo = MockDemoRepository()
    tracker = MockPlayerTracker()
    
    # 2. Initialize
    await tick_source.connect()
    repo.load_demo("data/sample_cache.json")
    await tracker.update()
    
    # 3. Use them
    tick = await tick_source.get_current_tick()
    player = await tracker.get_current_player()
    inputs = repo.get_inputs(1000, "76561198012345678")
    
    print(f"Tick: {tick}")
    print(f"Player: {player}")
    print(f"Inputs: {inputs.keys if inputs else 'None'}")

asyncio.run(quick_demo())
```

## Key Features

### MockTickSource
- ✓ Simulates 64 Hz tick progression
- ✓ Uses system timer (no real connection needed)
- ✓ Configurable start tick and tick rate

### MockDemoRepository  
- ✓ Loads data from JSON cache files
- ✓ Gracefully handles missing files
- ✓ Returns InputData objects
- ✓ Provides tick range and player info

### MockPlayerTracker
- ✓ Returns fixed player ID
- ✓ Simple implementation for testing
- ✓ Includes set_player() helper method

## Next Steps

1. **UI Development**: Use these mocks to develop the PyQt6 overlay
2. **Core Logic**: Test prediction engine with MockTickSource
3. **Integration**: Build complete system with mocks before real implementation
4. **Real Implementation**: Later replace with CS2TelnetClient and RealDemoParser

## Documentation

- Full API documentation: `/src/mocks/README.md`
- Architecture overview: `/docs/01_ARCHITECTURE.md`
- Complete example: `/examples/mock_usage_example.py`

## Support

All mocks:
- Implement their interfaces completely
- Include comprehensive docstrings
- Handle errors gracefully
- Have no external dependencies (except domain models)
- Are ready for immediate use in development
