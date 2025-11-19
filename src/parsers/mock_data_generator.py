"""Mock data generator for CS2 Input Visualizer testing and development.

This module generates realistic test data that simulates actual CS2 gameplay
patterns including movement, shooting, and utility usage. The generated data
can be used for UI development and testing without requiring real demo files.

The generator creates believable input sequences based on common CS2 mechanics:
- Counter-strafing patterns (W -> W+D -> D -> released)
- Burst fire shooting (short MOUSE1 sequences)
- Movement sequences with proper transitions
- Realistic crouch and jump timing
- Occasional utility usage

Example:
    >>> from parsers.mock_data_generator import generate_mock_cache
    >>> cache = generate_mock_cache(num_ticks=5000, seed=42)
    >>> # Save to file for use with MockDemoRepository
    >>> import json
    >>> with open("mock_cache.json", "w") as f:
    ...     json.dump(cache, f, indent=2)
"""

import json
import random
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


class MovementState(Enum):
    """Player movement states for realistic pattern generation."""
    IDLE = "idle"
    FORWARD = "forward"
    STRAFE_LEFT = "strafe_left"
    STRAFE_RIGHT = "strafe_right"
    FORWARD_LEFT = "forward_left"
    FORWARD_RIGHT = "forward_right"
    BACKWARD = "backward"


class ActionState(Enum):
    """Player action states."""
    IDLE = "idle"
    SHOOTING = "shooting"
    CROUCHING = "crouching"
    JUMPING = "jumping"


@dataclass
class InputState:
    """Current input state during pattern generation.

    Tracks the current state of all inputs to generate realistic transitions
    and sequences.

    Attributes:
        active_keys: Set of currently pressed keyboard keys
        active_mouse: Set of currently pressed mouse buttons
        movement_state: Current movement pattern state
        action_state: Current action being performed
        state_duration: How many ticks the current state has been active
        next_transition_tick: Tick when state should potentially change
    """
    active_keys: Set[str]
    active_mouse: Set[str]
    movement_state: MovementState
    action_state: ActionState
    state_duration: int
    next_transition_tick: int


class RealisticPatternGenerator:
    """Generates realistic CS2 input patterns.

    This class creates believable sequences of player inputs based on
    common CS2 gameplay mechanics and patterns. It uses weighted probabilities
    and state machines to generate natural-looking input transitions.

    Attributes:
        rng: Random number generator (seeded for reproducibility)
        current_state: Current input state being tracked
    """

    # Movement pattern probabilities and durations (in ticks)
    MOVEMENT_PATTERNS = {
        MovementState.FORWARD: {
            "duration_range": (32, 96),  # 0.5-1.5 seconds at 64 tick
            "transitions": {
                MovementState.FORWARD_LEFT: 0.25,
                MovementState.FORWARD_RIGHT: 0.25,
                MovementState.STRAFE_LEFT: 0.15,
                MovementState.STRAFE_RIGHT: 0.15,
                MovementState.IDLE: 0.20,
            }
        },
        MovementState.FORWARD_LEFT: {
            "duration_range": (16, 48),  # Counter-strafe timing
            "transitions": {
                MovementState.STRAFE_LEFT: 0.30,
                MovementState.FORWARD: 0.25,
                MovementState.FORWARD_RIGHT: 0.20,  # Quick direction change
                MovementState.IDLE: 0.25,
            }
        },
        MovementState.FORWARD_RIGHT: {
            "duration_range": (16, 48),
            "transitions": {
                MovementState.STRAFE_RIGHT: 0.30,
                MovementState.FORWARD: 0.25,
                MovementState.FORWARD_LEFT: 0.20,
                MovementState.IDLE: 0.25,
            }
        },
        MovementState.STRAFE_LEFT: {
            "duration_range": (8, 32),  # Quick strafes
            "transitions": {
                MovementState.STRAFE_RIGHT: 0.25,  # Counter-strafe
                MovementState.FORWARD_LEFT: 0.25,
                MovementState.FORWARD: 0.20,
                MovementState.IDLE: 0.30,
            }
        },
        MovementState.STRAFE_RIGHT: {
            "duration_range": (8, 32),
            "transitions": {
                MovementState.STRAFE_LEFT: 0.25,  # Counter-strafe
                MovementState.FORWARD_RIGHT: 0.25,
                MovementState.FORWARD: 0.20,
                MovementState.IDLE: 0.30,
            }
        },
        MovementState.BACKWARD: {
            "duration_range": (16, 48),
            "transitions": {
                MovementState.FORWARD: 0.30,
                MovementState.IDLE: 0.40,
                MovementState.STRAFE_LEFT: 0.15,
                MovementState.STRAFE_RIGHT: 0.15,
            }
        },
        MovementState.IDLE: {
            "duration_range": (8, 64),
            "transitions": {
                MovementState.FORWARD: 0.40,
                MovementState.STRAFE_LEFT: 0.15,
                MovementState.STRAFE_RIGHT: 0.15,
                MovementState.BACKWARD: 0.10,
                MovementState.FORWARD_LEFT: 0.10,
                MovementState.FORWARD_RIGHT: 0.10,
            }
        },
    }

    # Movement state to key mapping
    MOVEMENT_KEYS = {
        MovementState.IDLE: set(),
        MovementState.FORWARD: {"W"},
        MovementState.BACKWARD: {"S"},
        MovementState.STRAFE_LEFT: {"A"},
        MovementState.STRAFE_RIGHT: {"D"},
        MovementState.FORWARD_LEFT: {"W", "A"},
        MovementState.FORWARD_RIGHT: {"W", "D"},
    }

    def __init__(self, seed: Optional[int] = None):
        """Initialize pattern generator.

        Args:
            seed: Random seed for reproducibility (None for random behavior)
        """
        self.rng = random.Random(seed)
        self.current_state = InputState(
            active_keys=set(),
            active_mouse=set(),
            movement_state=MovementState.IDLE,
            action_state=ActionState.IDLE,
            state_duration=0,
            next_transition_tick=0
        )

    def generate_movement_pattern(self, tick: int) -> Set[str]:
        """Generate realistic WASD movement keys for current tick.

        Uses a state machine to create believable movement patterns including
        proper strafing, counter-strafing, and natural transitions.

        Args:
            tick: Current tick number

        Returns:
            Set of active movement keys (subset of {W, A, S, D})
        """
        # Check if we need to transition to a new movement state
        if tick >= self.current_state.next_transition_tick:
            self._transition_movement_state()

        # Return keys for current movement state
        return self.MOVEMENT_KEYS[self.current_state.movement_state].copy()

    def _transition_movement_state(self) -> None:
        """Transition to a new movement state based on current state probabilities."""
        current_pattern = self.MOVEMENT_PATTERNS[self.current_state.movement_state]

        # Choose next state based on weighted probabilities
        transitions = current_pattern["transitions"]
        states = list(transitions.keys())
        weights = list(transitions.values())

        new_state = self.rng.choices(states, weights=weights)[0]

        # Set duration for new state
        duration_range = self.MOVEMENT_PATTERNS[new_state]["duration_range"]
        duration = self.rng.randint(*duration_range)

        # Update state
        self.current_state.movement_state = new_state
        self.current_state.state_duration = 0
        self.current_state.next_transition_tick += duration

    def generate_shooting_pattern(self, tick: int) -> List[str]:
        """Generate realistic shooting patterns (burst fire).

        Simulates different shooting behaviors:
        - Short bursts (2-5 bullets)
        - Tap shooting (1-2 bullets)
        - Occasional sprays (6-10 bullets)

        Args:
            tick: Current tick number

        Returns:
            List of active mouse buttons (empty or ["MOUSE1"])
        """
        # Check if currently shooting
        if self.current_state.action_state == ActionState.SHOOTING:
            self.current_state.state_duration += 1

            # Determine burst length based on pattern
            # Most bursts are 2-5 bullets (at 64 tick = ~8-20 ticks for typical fire rate)
            if self.current_state.state_duration < 3:  # Minimum burst of 2-3 ticks
                return ["MOUSE1"]
            elif self.current_state.state_duration < 20:  # Extended possible burst
                # Gradually decrease probability of continuing
                if self.rng.random() < 0.5:  # 50% chance to continue each tick
                    return ["MOUSE1"]

            # End shooting burst
            self.current_state.action_state = ActionState.IDLE
            return []

        # Random chance to start shooting (5% per tick when moving, 3% when idle)
        is_moving = self.current_state.movement_state != MovementState.IDLE
        shoot_chance = 0.05 if is_moving else 0.03

        if self.rng.random() < shoot_chance:
            self.current_state.action_state = ActionState.SHOOTING
            self.current_state.state_duration = 0
            return ["MOUSE1"]

        return []

    def generate_utility_pattern(self, tick: int) -> List[str]:
        """Generate occasional utility and misc key presses.

        Simulates realistic usage of:
        - E (use/interact) - rare
        - R (reload) - after shooting sequences
        - TAB (scoreboard) - very occasional
        - SHIFT (walk) - occasional when moving

        Args:
            tick: Current tick number

        Returns:
            List of utility keys being pressed
        """
        utility_keys = []

        # SHIFT (walk) - use occasionally when moving (10% chance)
        if self.current_state.movement_state != MovementState.IDLE:
            if self.rng.random() < 0.10:
                utility_keys.append("SHIFT")

        # R (reload) - more likely right after shooting ends
        just_finished_shooting = (
            self.current_state.action_state == ActionState.IDLE and
            "MOUSE1" in self.current_state.active_mouse
        )
        reload_chance = 0.3 if just_finished_shooting else 0.01
        if self.rng.random() < reload_chance:
            utility_keys.append("R")

        # E (use) - rare, random (0.5% per tick)
        if self.rng.random() < 0.005:
            utility_keys.append("E")

        # TAB (scoreboard) - very rare (0.2% per tick)
        if self.rng.random() < 0.002:
            utility_keys.append("TAB")

        return utility_keys

    def generate_jump(self, tick: int) -> bool:
        """Generate realistic jump timing.

        Jumps occur:
        - Rarely when idle (0.5%)
        - More often when moving forward (2%)
        - Never during consecutive ticks (jump cooldown)

        Args:
            tick: Current tick number

        Returns:
            True if SPACE should be pressed this tick
        """
        # Don't jump if we just jumped (simulate jump cooldown)
        if "SPACE" in self.current_state.active_keys:
            return False

        # Jump probability based on movement
        if self.current_state.movement_state == MovementState.IDLE:
            return self.rng.random() < 0.005
        elif self.current_state.movement_state in [MovementState.FORWARD,
                                                     MovementState.FORWARD_LEFT,
                                                     MovementState.FORWARD_RIGHT]:
            return self.rng.random() < 0.02
        else:
            return self.rng.random() < 0.01

    def generate_crouch(self, tick: int) -> bool:
        """Generate realistic crouch timing.

        Crouch behavior:
        - Often held while shooting (spray control)
        - Sometimes while moving (crouch-walking)
        - Held for multiple ticks (5-20 typically)

        Args:
            tick: Current tick number

        Returns:
            True if CTRL should be pressed this tick
        """
        # Continue crouching if already crouching
        if self.current_state.action_state == ActionState.CROUCHING:
            self.current_state.state_duration += 1

            # Hold crouch for 5-30 ticks typically
            if self.current_state.state_duration < 5:
                return True
            elif self.current_state.state_duration < 30:
                if self.rng.random() < 0.7:  # 70% chance to continue
                    return True

            # End crouching
            self.current_state.action_state = ActionState.IDLE
            return False

        # Start crouching
        # Higher chance while shooting (30%), lower when moving (5%), very low when idle (2%)
        if self.current_state.action_state == ActionState.SHOOTING:
            crouch_chance = 0.30
        elif self.current_state.movement_state != MovementState.IDLE:
            crouch_chance = 0.05
        else:
            crouch_chance = 0.02

        if self.rng.random() < crouch_chance:
            self.current_state.action_state = ActionState.CROUCHING
            self.current_state.state_duration = 0
            return True

        return False


def generate_subtick_offsets(keys: List[str], mouse: List[str],
                             seed: Optional[int] = None) -> Dict[str, float]:
    """Generate realistic subtick timing offsets for inputs.

    Subtick offsets represent when during a tick (0.0 to 1.0) each input
    was activated. This adds precision to input timing visualization.

    Most inputs start at tick beginning (0.0), but some have realistic delays:
    - Movement keys: Usually 0.0 (held from tick start)
    - Mouse clicks: Often 0.1-0.5 (reaction during tick)
    - Utility keys: Random timing within tick

    Args:
        keys: List of keyboard keys pressed this tick
        mouse: List of mouse buttons pressed this tick
        seed: Random seed for reproducibility

    Returns:
        Dictionary mapping each input to its subtick offset (0.0-1.0)
    """
    rng = random.Random(seed)
    subtick = {}

    # Movement keys typically start at tick beginning
    movement_keys = {"W", "A", "S", "D"}
    for key in keys:
        if key in movement_keys:
            # Mostly 0.0, but occasionally slightly delayed
            if rng.random() < 0.9:
                subtick[key] = 0.0
            else:
                subtick[key] = round(rng.uniform(0.0, 0.2), 2)
        else:
            # Utility keys can happen anywhere in the tick
            subtick[key] = round(rng.uniform(0.0, 0.8), 2)

    # Mouse clicks usually have some delay (reaction time)
    for button in mouse:
        if button == "MOUSE1":
            # Shooting often has small delay (0.1-0.5)
            subtick[button] = round(rng.uniform(0.1, 0.5), 2)
        else:
            subtick[button] = round(rng.uniform(0.0, 0.6), 2)

    return subtick


def generate_mock_cache(
    num_ticks: int = 5000,
    output_path: Optional[str] = None,
    seed: Optional[int] = None,
    tick_rate: int = 64,
    player_name: str = "TestPlayer"
) -> Dict:
    """Generate realistic mock cache data for CS2 Input Visualizer.

    Creates a complete cache file with believable input patterns that simulate
    actual CS2 gameplay. The generated data includes proper movement sequences,
    shooting bursts, jumps, crouches, and utility usage with realistic timing.

    This function is the main entry point for mock data generation. It produces
    data compatible with MockDemoRepository for UI development and testing.

    Args:
        num_ticks: Number of game ticks to generate (default: 5000 = ~78 seconds at 64 tick)
        output_path: Optional path to save JSON cache file. If None, data is returned but not saved.
        seed: Random seed for reproducible generation (default: None for random behavior)
        tick_rate: Server tick rate, typically 64 or 128 (default: 64)
        player_name: Display name for the mock player (default: "TestPlayer")

    Returns:
        Dictionary containing complete cache data structure with metadata and inputs

    Example:
        >>> # Generate and save 10 seconds of gameplay data
        >>> cache = generate_mock_cache(
        ...     num_ticks=640,
        ...     output_path="test_cache.json",
        ...     seed=42,
        ...     player_name="ProPlayer"
        ... )
        >>> print(f"Generated {len(cache['inputs'])} tick entries")

        >>> # Generate data without saving
        >>> cache = generate_mock_cache(num_ticks=1000, seed=123)
        >>> # Use cache data directly in tests
    """
    # Initialize pattern generator
    pattern_gen = RealisticPatternGenerator(seed=seed)

    # Initialize cache structure
    cache = {
        "meta": {
            "demo_file": "mock_demo.dem",
            "player_id": "MOCK_PLAYER_123",
            "player_name": player_name,
            "tick_range": [0, num_ticks],
            "tick_rate": tick_rate
        },
        "inputs": {}
    }

    # Also create metadata key for compatibility with MockDemoRepository
    cache["metadata"] = {
        "player_id": "MOCK_PLAYER_123",
        "player_name": player_name,
        "tick_range": [0, num_ticks],
        "tick_rate": tick_rate
    }

    # Generate inputs for each tick
    for tick in range(num_ticks):
        # Generate all input components
        movement_keys = pattern_gen.generate_movement_pattern(tick)
        mouse_buttons = pattern_gen.generate_shooting_pattern(tick)
        utility_keys = pattern_gen.generate_utility_pattern(tick)

        # Combine all keyboard inputs
        all_keys = list(movement_keys)

        # Add jump if appropriate (SPACE held for 1-2 ticks typically)
        if pattern_gen.generate_jump(tick):
            all_keys.append("SPACE")

        # Add crouch if appropriate (CTRL can be held longer)
        if pattern_gen.generate_crouch(tick):
            all_keys.append("CTRL")

        # Add utility keys
        all_keys.extend(utility_keys)

        # Update current state for next iteration
        pattern_gen.current_state.active_keys = set(all_keys)
        pattern_gen.current_state.active_mouse = set(mouse_buttons)

        # Generate subtick offsets
        subtick = generate_subtick_offsets(all_keys, mouse_buttons, seed=seed)

        # Only store ticks where there's actual input (sparse storage optimization)
        if all_keys or mouse_buttons:
            cache["inputs"][str(tick)] = {
                "tick": tick,
                "keys": sorted(all_keys),  # Sort for consistency
                "mouse": mouse_buttons,
                "subtick": subtick
            }

    # Save to file if path provided
    if output_path:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(cache, f, indent=2)

        print(f"Mock cache generated successfully!")
        print(f"  File: {output_path}")
        print(f"  Ticks: {num_ticks} ({num_ticks / tick_rate:.1f} seconds)")
        print(f"  Stored entries: {len(cache['inputs'])} (sparse)")
        print(f"  Compression: {(1 - len(cache['inputs']) / num_ticks) * 100:.1f}% reduction")

    return cache


# Example usage and testing
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate mock CS2 input data for testing and development"
    )
    parser.add_argument(
        "--ticks", "-t",
        type=int,
        default=5000,
        help="Number of ticks to generate (default: 5000)"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default="mock_cache.json",
        help="Output file path (default: mock_cache.json)"
    )
    parser.add_argument(
        "--seed", "-s",
        type=int,
        default=None,
        help="Random seed for reproducibility (default: random)"
    )
    parser.add_argument(
        "--tick-rate", "-r",
        type=int,
        default=64,
        choices=[64, 128],
        help="Server tick rate (default: 64)"
    )
    parser.add_argument(
        "--player-name", "-p",
        type=str,
        default="TestPlayer",
        help="Player display name (default: TestPlayer)"
    )

    args = parser.parse_args()

    # Generate mock data
    cache = generate_mock_cache(
        num_ticks=args.ticks,
        output_path=args.output,
        seed=args.seed,
        tick_rate=args.tick_rate,
        player_name=args.player_name
    )

    # Print some statistics
    print("\nSample data from generated cache:")
    print("-" * 50)

    # Show first few ticks with inputs
    sample_count = 0
    for tick_str, data in sorted(cache["inputs"].items(), key=lambda x: int(x[0]))[:5]:
        print(f"Tick {tick_str}:")
        print(f"  Keys: {data['keys']}")
        print(f"  Mouse: {data['mouse']}")
        print(f"  Subtick: {data['subtick']}")
        sample_count += 1

    print("\nCache ready for use with MockDemoRepository!")
