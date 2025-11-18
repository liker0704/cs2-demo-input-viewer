"""Interface for input visualization display.

This module defines the abstract interface for components that render
and display player input data on screen.
"""

from abc import ABC, abstractmethod

from ..domain.models import InputData


class IInputVisualizer(ABC):
    """Interface for input visualization display.

    An input visualizer handles rendering player inputs (keyboard/mouse)
    in a visual overlay, typically displayed on top of the game or as
    a separate window.
    """

    @abstractmethod
    def render(self, data: InputData) -> None:
        """Render the provided input data to the display.

        Args:
            data: The input data to visualize (keys, mouse, etc.).
        """
        pass

    @abstractmethod
    def show(self) -> None:
        """Make the visualizer visible on screen.

        Displays the input visualization overlay/window if it was
        previously hidden.
        """
        pass

    @abstractmethod
    def hide(self) -> None:
        """Hide the visualizer from screen.

        Conceals the input visualization overlay/window without
        destroying it, allowing it to be shown again later.
        """
        pass

    @abstractmethod
    def set_position(self, x: int, y: int) -> None:
        """Set the screen position of the visualizer.

        Args:
            x: Horizontal position in pixels from the left edge of the screen.
            y: Vertical position in pixels from the top edge of the screen.
        """
        pass
