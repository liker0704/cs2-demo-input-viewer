"""Tests for progress reporting functionality."""

import unittest
from unittest.mock import Mock, patch
from io import StringIO

from src.utils.progress import ProgressBar, ProgressReporter


class TestProgressBar(unittest.TestCase):
    """Test cases for ProgressBar class."""

    def setUp(self):
        """Set up test fixtures."""
        self.stream = StringIO()
        self.progress_bar = ProgressBar(width=20, stream=self.stream)

    def test_render_basic(self):
        """Test basic progress bar rendering."""
        self.progress_bar.render(0.5, "Processing")

        output = self.stream.getvalue()
        self.assertIn("50%", output)
        self.assertIn("Processing", output)
        self.assertIn("█", output)
        self.assertIn("░", output)

    def test_render_zero_progress(self):
        """Test rendering with zero progress."""
        self.progress_bar.render(0.0, "Starting")

        output = self.stream.getvalue()
        self.assertIn("0%", output)
        self.assertIn("Starting", output)

    def test_render_full_progress(self):
        """Test rendering with full progress."""
        self.progress_bar.render(1.0, "Complete")

        output = self.stream.getvalue()
        self.assertIn("100%", output)
        self.assertIn("Complete", output)

    def test_render_clamps_progress(self):
        """Test that progress is clamped to 0-1 range."""
        # Test negative progress
        self.progress_bar.render(-0.5, "Test")
        output = self.stream.getvalue()
        self.assertIn("0%", output)

        # Clear stream
        self.stream.truncate(0)
        self.stream.seek(0)

        # Test progress > 1
        self.progress_bar.render(1.5, "Test")
        output = self.stream.getvalue()
        self.assertIn("100%", output)

    def test_finish(self):
        """Test finish method."""
        self.progress_bar.finish("Done!")

        output = self.stream.getvalue()
        self.assertIn("100%", output)
        self.assertIn("Done!", output)
        self.assertIn("\n", output)

    def test_clear(self):
        """Test clear method."""
        self.progress_bar.render(0.5, "Test")
        self.progress_bar.clear()

        # After clear, last line length should be reset
        self.assertEqual(self.progress_bar._last_line_length, 0)


class TestProgressReporter(unittest.TestCase):
    """Test cases for ProgressReporter class."""

    def test_basic_reporting(self):
        """Test basic progress reporting."""
        callback = Mock()
        reporter = ProgressReporter(callback)

        reporter.report("extract", 0.5, "Processing...")

        # Verify callback was called
        callback.assert_called_once()

        # Check callback arguments
        call_args = callback.call_args[0][0]
        self.assertEqual(call_args['phase'], 'extract')
        self.assertEqual(call_args['phase_progress'], 0.5)
        self.assertEqual(call_args['message'], "Processing...")

    def test_overall_progress_calculation(self):
        """Test overall progress calculation across phases."""
        callback = Mock()
        phases = {
            'extract': 0.4,
            'transform': 0.4,
            'load': 0.2
        }
        reporter = ProgressReporter(callback, phases=phases)

        # Test extract phase at 50%
        reporter.report("extract", 0.5, "Extracting...")
        call_args = callback.call_args[0][0]
        # Should be 40% * 50% = 20% overall
        self.assertAlmostEqual(call_args['overall_progress'], 0.2, places=2)

        # Test transform phase at 50%
        reporter.report("transform", 0.5, "Transforming...")
        call_args = callback.call_args[0][0]
        # Should be 40% (extract complete) + 40% * 50% = 60% overall
        self.assertAlmostEqual(call_args['overall_progress'], 0.6, places=2)

        # Test load phase at 50%
        reporter.report("load", 0.5, "Loading...")
        call_args = callback.call_args[0][0]
        # Should be 80% (extract + transform) + 20% * 50% = 90% overall
        self.assertAlmostEqual(call_args['overall_progress'], 0.9, places=2)

    def test_no_callback(self):
        """Test reporter with no callback doesn't crash."""
        reporter = ProgressReporter(callback=None)

        # Should not raise an error
        reporter.report("extract", 0.5, "Processing...")

    def test_callback_error_handling(self):
        """Test that callback errors don't crash the reporter."""
        def failing_callback(info):
            raise RuntimeError("Callback error!")

        reporter = ProgressReporter(failing_callback)

        # Should not raise an error
        with patch('src.utils.progress.logging.getLogger') as mock_logger:
            reporter.report("extract", 0.5, "Processing...")
            # Verify warning was logged
            mock_logger.return_value.warning.assert_called()

    def test_unknown_phase(self):
        """Test handling of unknown phase."""
        callback = Mock()
        reporter = ProgressReporter(callback)

        reporter.report("unknown_phase", 0.5, "Processing...")

        # Should still call callback with the phase progress
        call_args = callback.call_args[0][0]
        self.assertEqual(call_args['phase'], 'unknown_phase')
        self.assertEqual(call_args['phase_progress'], 0.5)


class TestProgressIntegration(unittest.TestCase):
    """Integration tests for progress reporting with ETL pipeline."""

    @patch('src.parsers.etl_pipeline.HAS_DEMOPARSER', False)
    def test_pipeline_without_demoparser(self):
        """Test that pipeline fails gracefully without demoparser."""
        from src.parsers.etl_pipeline import DemoETLPipeline

        callback = Mock()

        # Create pipeline with mock demo path
        with patch('pathlib.Path.exists', return_value=True):
            pipeline = DemoETLPipeline("mock.dem")

            with self.assertRaises(RuntimeError):
                pipeline.run(progress_callback=callback)

    def test_progress_callback_format(self):
        """Test that progress callback receives correct format."""
        callback = Mock()
        reporter = ProgressReporter(callback)

        # Simulate ETL phases
        reporter.report("extract", 0.0, "Starting extraction...")
        reporter.report("extract", 0.5, "Processing tick 50000/100000")
        reporter.report("extract", 1.0, "Extracted 100000 events")

        # Verify all calls
        self.assertEqual(callback.call_count, 3)

        # Check the format of the last call
        call_args = callback.call_args[0][0]
        self.assertIn('phase', call_args)
        self.assertIn('phase_progress', call_args)
        self.assertIn('overall_progress', call_args)
        self.assertIn('message', call_args)


if __name__ == '__main__':
    unittest.main()
