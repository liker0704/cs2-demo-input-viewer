"""Example script demonstrating mock data generation for CS2 Input Visualizer.

This script shows how to:
1. Generate mock cache data with realistic patterns
2. Use different configurations (tick rate, duration, seeds)
3. Integrate with MockDemoRepository for testing
"""

from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.parsers.mock_data_generator import generate_mock_cache
from src.mocks.demo_repository import MockDemoRepository


def example_basic_generation():
    """Example 1: Basic mock data generation."""
    print("=" * 60)
    print("Example 1: Basic Mock Data Generation")
    print("=" * 60)
    
    # Generate 5 seconds of gameplay (320 ticks at 64 tick rate)
    cache = generate_mock_cache(
        num_ticks=320,
        output_path="example_basic.json",
        seed=42,  # For reproducibility
        player_name="ExamplePlayer"
    )
    
    print(f"\n✓ Generated cache with {len(cache['inputs'])} tick entries")
    print()


def example_different_durations():
    """Example 2: Generate different duration demos."""
    print("=" * 60)
    print("Example 2: Different Duration Demos")
    print("=" * 60)
    
    durations = [
        ("short_demo.json", 640, "10 seconds"),
        ("medium_demo.json", 3200, "50 seconds"),
        ("long_demo.json", 6400, "100 seconds"),
    ]
    
    for filename, ticks, description in durations:
        cache = generate_mock_cache(
            num_ticks=ticks,
            output_path=filename,
            seed=42
        )
        print(f"  {description:15s} -> {len(cache['inputs']):4d} entries")
    
    print()


def example_integration_with_repository():
    """Example 3: Use generated data with MockDemoRepository."""
    print("=" * 60)
    print("Example 3: Integration with MockDemoRepository")
    print("=" * 60)
    
    # Generate cache
    cache_path = "integration_example.json"
    cache = generate_mock_cache(
        num_ticks=1000,
        output_path=cache_path,
        seed=123
    )
    
    # Load with repository
    repo = MockDemoRepository()
    repo.load_demo(cache_path)
    
    # Get player info
    player_id = repo.get_default_player()
    tick_range = repo.get_tick_range()
    
    print(f"\nLoaded demo for player: {player_id}")
    print(f"Tick range: {tick_range[0]} - {tick_range[1]}")
    
    # Sample some inputs
    print("\nSample inputs from demo:")
    for tick in [0, 100, 500, 900]:
        input_data = repo.get_inputs(tick, player_id)
        if input_data:
            print(f"  Tick {tick:4d}: Keys={input_data.keys}, Mouse={input_data.mouse}")
    
    print()


def example_reproducible_vs_random():
    """Example 4: Demonstrate reproducible generation with seeds."""
    print("=" * 60)
    print("Example 4: Reproducible vs Random Generation")
    print("=" * 60)
    
    # Generate with same seed - should be identical
    cache1 = generate_mock_cache(num_ticks=100, seed=999)
    cache2 = generate_mock_cache(num_ticks=100, seed=999)
    
    # Check if first 5 ticks are identical
    identical = True
    for i in range(5):
        tick_str = str(i)
        if cache1["inputs"].get(tick_str) != cache2["inputs"].get(tick_str):
            identical = False
            break
    
    print(f"\nTwo caches with seed=999 are identical: {identical}")
    
    # Generate without seed - should be different
    cache3 = generate_mock_cache(num_ticks=100)
    cache4 = generate_mock_cache(num_ticks=100)
    
    different = cache3["inputs"] != cache4["inputs"]
    print(f"Two caches without seed are different: {different}")
    print()


def example_analyze_patterns():
    """Example 5: Analyze generated patterns."""
    print("=" * 60)
    print("Example 5: Analyze Generated Patterns")
    print("=" * 60)
    
    # Generate a decent sized sample
    cache = generate_mock_cache(num_ticks=5000, seed=42)
    
    # Analyze patterns
    stats = {
        "movement": 0,
        "shooting": 0,
        "jumping": 0,
        "crouching": 0,
        "utility": 0,
        "idle": 0
    }
    
    for tick_data in cache["inputs"].values():
        keys = set(tick_data["keys"])
        mouse = set(tick_data["mouse"])
        
        if keys & {"W", "A", "S", "D"}:
            stats["movement"] += 1
        if "MOUSE1" in mouse:
            stats["shooting"] += 1
        if "SPACE" in keys:
            stats["jumping"] += 1
        if "CTRL" in keys:
            stats["crouching"] += 1
        if keys & {"E", "R", "TAB", "SHIFT"}:
            stats["utility"] += 1
    
    stats["idle"] = 5000 - len(cache["inputs"])
    
    print(f"\nPattern analysis for 5000 ticks (~78 seconds):")
    print(f"  Movement ticks:  {stats['movement']:4d} ({stats['movement']/50:.1f}%)")
    print(f"  Shooting ticks:  {stats['shooting']:4d} ({stats['shooting']/50:.1f}%)")
    print(f"  Jumping ticks:   {stats['jumping']:4d} ({stats['jumping']/50:.1f}%)")
    print(f"  Crouching ticks: {stats['crouching']:4d} ({stats['crouching']/50:.1f}%)")
    print(f"  Utility ticks:   {stats['utility']:4d} ({stats['utility']/50:.1f}%)")
    print(f"  Idle ticks:      {stats['idle']:4d} ({stats['idle']/50:.1f}%)")
    print()


if __name__ == "__main__":
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 8 + "CS2 Mock Data Generator - Examples" + " " * 16 + "║")
    print("╚" + "═" * 58 + "╝")
    print()
    
    # Run all examples
    example_basic_generation()
    example_different_durations()
    example_integration_with_repository()
    example_reproducible_vs_random()
    example_analyze_patterns()
    
    print("=" * 60)
    print("All examples completed successfully!")
    print("=" * 60)
    print()
    print("Generated files:")
    print("  - example_basic.json")
    print("  - short_demo.json")
    print("  - medium_demo.json")
    print("  - long_demo.json")
    print("  - integration_example.json")
    print()
