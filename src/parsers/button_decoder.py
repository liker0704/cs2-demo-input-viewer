"""
Button Decoder Module for CS2 Input Visualizer.

This module provides functionality to decode Source 2 button masks into readable
button press information, including subtick timing data when available.

The button mask is a bitwise representation of all buttons pressed in a given tick,
where each bit corresponds to a specific button/key input in Counter-Strike 2.
"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class ButtonPress:
    """
    Represents a single button press event with timing information.

    Attributes:
        key: The human-readable key name (e.g., "W", "Mouse1", "Space")
        subtick_offset: The timing offset within the tick (0.0-1.0) when the button was pressed
    """
    key: str
    subtick_offset: float = 0.0


class ButtonMask:
    """
    Source 2 button mask constants for Counter-Strike 2.

    Each constant represents a specific button input as a bit flag.
    These values correspond to the IN_* constants from the Source 2 engine.
    """
    IN_ATTACK = 1 << 0      # 1 - Mouse1 (Primary fire)
    IN_JUMP = 1 << 1        # 2 - Space (Jump)
    IN_DUCK = 1 << 2        # 4 - Ctrl (Crouch)
    IN_FORWARD = 1 << 3     # 8 - W (Move forward)
    IN_BACK = 1 << 4        # 16 - S (Move backward)
    IN_USE = 1 << 5         # 32 - E (Use/Interact)
    IN_MOVELEFT = 1 << 9    # 512 - A (Move left)
    IN_MOVERIGHT = 1 << 10  # 1024 - D (Move right)
    IN_ATTACK2 = 1 << 11    # 2048 - Mouse2 (Secondary fire)
    IN_RELOAD = 1 << 13     # 8192 - R (Reload)
    IN_SCORE = 1 << 16      # 65536 - Tab (Scoreboard)
    IN_SPEED = 1 << 17      # 131072 - Shift (Walk)


# Mapping of button mask values to human-readable key names
BUTTON_TO_KEY = {
    ButtonMask.IN_ATTACK: "Mouse1",
    ButtonMask.IN_JUMP: "Space",
    ButtonMask.IN_DUCK: "Ctrl",
    ButtonMask.IN_FORWARD: "W",
    ButtonMask.IN_BACK: "S",
    ButtonMask.IN_USE: "E",
    ButtonMask.IN_MOVELEFT: "A",
    ButtonMask.IN_MOVERIGHT: "D",
    ButtonMask.IN_ATTACK2: "Mouse2",
    ButtonMask.IN_RELOAD: "R",
    ButtonMask.IN_SCORE: "Tab",
    ButtonMask.IN_SPEED: "Shift",
}


def is_button_pressed(mask: int, button: int) -> bool:
    """
    Check if a specific button is pressed in the given button mask.

    Args:
        mask: The button mask to check
        button: The button constant to test (e.g., ButtonMask.IN_JUMP)

    Returns:
        True if the button is pressed, False otherwise

    Example:
        >>> is_button_pressed(10, ButtonMask.IN_JUMP)  # 10 = 0b1010 (JUMP + FORWARD)
        True
        >>> is_button_pressed(10, ButtonMask.IN_DUCK)
        False
    """
    return (mask & button) != 0


def get_active_buttons(mask: int) -> List[str]:
    """
    Get a list of all active (pressed) button names from a button mask.

    Args:
        mask: The button mask to decode

    Returns:
        List of human-readable key names for all pressed buttons

    Example:
        >>> get_active_buttons(10)  # 10 = 0b1010 (JUMP + FORWARD)
        ['Space', 'W']
        >>> get_active_buttons(0)
        []
    """
    active_buttons = []

    for button_value, key_name in BUTTON_TO_KEY.items():
        if is_button_pressed(mask, button_value):
            active_buttons.append(key_name)

    return active_buttons


def decode_buttons(mask: int, subtick_moves: Optional[list] = None) -> List[ButtonPress]:
    """
    Decode a button mask into a list of ButtonPress objects with timing information.

    This function converts a bitwise button mask into a structured list of button
    presses, optionally including subtick timing data if available from the demo file.

    Args:
        mask: The button mask to decode (bitwise combination of button flags)
        subtick_moves: Optional list of subtick move data containing timing information.
                      Each entry should have a 'button' field and 'when' field for timing.

    Returns:
        List of ButtonPress objects representing all pressed buttons with their timing

    Example:
        >>> # Simple decoding without subtick data
        >>> decode_buttons(10)  # JUMP + FORWARD
        [ButtonPress(key='Space', subtick_offset=0.0), ButtonPress(key='W', subtick_offset=0.0)]

        >>> # Decoding with subtick timing data
        >>> subtick_data = [{'button': 2, 'when': 0.25}, {'button': 8, 'when': 0.5}]
        >>> decode_buttons(10, subtick_data)
        [ButtonPress(key='Space', subtick_offset=0.25), ButtonPress(key='W', subtick_offset=0.5)]

        >>> # Empty mask returns empty list
        >>> decode_buttons(0)
        []
    """
    button_presses = []

    # Create a mapping of button values to subtick offsets if subtick data is available
    subtick_timing = {}
    if subtick_moves:
        for move in subtick_moves:
            if isinstance(move, dict) and 'button' in move and 'when' in move:
                button_value = move['button']
                subtick_timing[button_value] = move['when']

    # Iterate through all known buttons and check if they're pressed
    for button_value, key_name in BUTTON_TO_KEY.items():
        if is_button_pressed(mask, button_value):
            # Get subtick offset if available, otherwise default to 0.0
            subtick_offset = subtick_timing.get(button_value, 0.0)
            button_presses.append(ButtonPress(key=key_name, subtick_offset=subtick_offset))

    return button_presses
