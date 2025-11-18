"""Progress reporting utilities for ETL pipeline.

This module provides progress bar rendering for terminal output during
long-running ETL operations.

Usage:
    progress_bar = ProgressBar()
    progress_bar.render(0.45, "Processing tick 45000/100000")
    # Output: [████████░░░░░░░░░░] 45% Processing tick 45000/100000
"""

import sys
import logging
from typing import Optional


class ProgressBar:
    """Terminal progress bar renderer.

    Renders a visual progress bar with percentage and custom message.
    Uses Unicode block characters for smooth progress visualization.

    Attributes:
        width: Width of the progress bar in characters (default: 40)
        stream: Output stream (default: sys.stderr)
    """

    def __init__(self, width: int = 40, stream=None):
        """Initialize progress bar.

        Args:
            width: Width of the progress bar in characters
            stream: Output stream (defaults to sys.stderr)
        """
        self.width = width
        self.stream = stream or sys.stderr
        self._last_line_length = 0

    def render(self, progress: float, message: str = "") -> None:
        """Render progress bar to terminal.

        Args:
            progress: Progress value between 0.0 and 1.0
            message: Optional message to display after progress bar

        Example:
            >>> bar = ProgressBar()
            >>> bar.render(0.75, "Processing tick 75000/100000")
            [██████████████████░░] 75% Processing tick 75000/100000
        """
        # Clamp progress to valid range
        progress = max(0.0, min(1.0, progress))

        # Calculate filled and empty portions
        filled_width = int(self.width * progress)
        empty_width = self.width - filled_width

        # Build progress bar string
        bar = '█' * filled_width + '░' * empty_width
        percentage = int(progress * 100)

        # Format output line
        if message:
            line = f"\r[{bar}] {percentage}% {message}"
        else:
            line = f"\r[{bar}] {percentage}%"

        # Clear previous line if it was longer
        if len(line) < self._last_line_length:
            line += ' ' * (self._last_line_length - len(line))

        self._last_line_length = len(line)

        # Write to stream
        self.stream.write(line)
        self.stream.flush()

    def clear(self) -> None:
        """Clear the progress bar line."""
        if self._last_line_length > 0:
            self.stream.write('\r' + ' ' * self._last_line_length + '\r')
            self.stream.flush()
            self._last_line_length = 0

    def finish(self, message: str = "Complete") -> None:
        """Finish progress bar and print final message.

        Args:
            message: Final message to display (default: "Complete")
        """
        self.render(1.0, message)
        self.stream.write('\n')
        self.stream.flush()
        self._last_line_length = 0


class ProgressReporter:
    """Progress reporter that combines progress tracking with callbacks.

    This class helps manage progress reporting across multiple phases,
    automatically calculating phase-weighted progress and calling callbacks.

    Example:
        >>> def on_progress(info):
        ...     print(f"{info['phase']}: {info['progress']:.0%}")
        >>>
        >>> reporter = ProgressReporter(on_progress, phases={
        ...     'extract': 0.4,  # Extract is 40% of total work
        ...     'transform': 0.4,  # Transform is 40% of total work
        ...     'load': 0.2,     # Load is 20% of total work
        ... })
        >>> reporter.report('extract', 0.5, "Parsing tick 50000")
    """

    def __init__(
        self,
        callback: Optional[callable] = None,
        phases: Optional[dict] = None
    ):
        """Initialize progress reporter.

        Args:
            callback: Function to call with progress updates
            phases: Dictionary mapping phase names to their weight (0.0-1.0)
                   Weights should sum to 1.0
        """
        self.callback = callback
        self.phases = phases or {
            'extract': 0.4,
            'transform': 0.4,
            'load': 0.2
        }
        self._phase_order = list(self.phases.keys())
        self._current_phase_index = 0

    def report(
        self,
        phase: str,
        progress: float,
        message: str = ""
    ) -> None:
        """Report progress for a specific phase.

        Args:
            phase: Name of the current phase
            progress: Progress within this phase (0.0 to 1.0)
            message: Optional status message
        """
        if not self.callback:
            return

        # Calculate overall progress based on phase weights
        overall_progress = 0.0

        # Add completed phases
        try:
            phase_index = self._phase_order.index(phase)
            for i in range(phase_index):
                overall_progress += self.phases[self._phase_order[i]]
        except ValueError:
            # Unknown phase, use it as-is
            phase_index = -1

        # Add current phase progress
        if phase in self.phases:
            overall_progress += self.phases[phase] * progress
        else:
            overall_progress = progress

        # Prepare progress info
        progress_info = {
            'phase': phase,
            'phase_progress': progress,
            'overall_progress': overall_progress,
            'message': message
        }

        # Call callback
        try:
            # Support both sync and async callbacks
            import inspect
            if inspect.iscoroutinefunction(self.callback):
                # Async callback - try to run it
                import asyncio
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # Schedule as task
                        asyncio.create_task(self.callback(progress_info))
                    else:
                        # Run directly
                        loop.run_until_complete(self.callback(progress_info))
                except RuntimeError:
                    # No event loop, create one
                    asyncio.run(self.callback(progress_info))
            else:
                # Sync callback
                self.callback(progress_info)
        except Exception as e:
            # Don't let callback errors break the pipeline
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Progress callback error: {e}")
