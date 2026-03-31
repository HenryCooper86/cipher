"""Tests for progress indicators."""
import pytest
from io import StringIO
from unittest.mock import patch, MagicMock

from pwd_generator import progress


class TestProgressBar:
    """Tests for ProgressBar class."""

    def test_init(self):
        bar = progress.ProgressBar(100, "Test", 40)
        assert bar.total == 100
        assert bar.current == 0
        assert bar.description == "Test"
        assert bar.width == 40

    def test_update(self):
        bar = progress.ProgressBar(100)
        bar._enabled = False  # Disable display for testing
        bar.update(10)
        assert bar.current == 10
        bar.update(5)
        assert bar.current == 15

    def test_update_exceeds_total(self):
        bar = progress.ProgressBar(10)
        bar._enabled = False
        bar.update(15)
        assert bar.current == 10  # Should be capped at total

    def test_display(self, capsys):
        bar = progress.ProgressBar(10, "Test", 20)
        bar._enabled = True
        bar.current = 5
        bar._display()
        captured = capsys.readouterr()
        assert "Test:" in captured.out or "Test:" in captured.err
        assert "50%" in captured.out or "50%" in captured.err

    def test_display_zero_total(self, capsys):
        bar = progress.ProgressBar(0, "Test", 20)
        bar._enabled = True
        bar._display()
        captured = capsys.readouterr()
        assert "100%" in captured.out or "100%" in captured.err

    def test_finish_enabled(self, capsys):
        bar = progress.ProgressBar(10, "Test")
        bar._enabled = True
        bar.finish()
        captured = capsys.readouterr()
        # Should print completion

    def test_finish_disabled(self, capsys):
        bar = progress.ProgressBar(10, "Test")
        bar._enabled = False
        bar.finish()
        captured = capsys.readouterr()
        assert "Complete" in captured.out


class TestShowProgress:
    """Tests for show_progress function."""

    def test_progress_with_description(self, capsys):
        items = [1, 2, 3]
        result = list(progress.show_progress(items, "Processing", len(items)))
        assert result == items

    def test_progress_no_total(self):
        items = [1, 2, 3]
        result = list(progress.show_progress(items, "Processing"))
        assert result == items

    def test_progress_empty_iterable(self):
        result = list(progress.show_progress([], "Processing", 0))
        assert result == []

    def test_progress_single_item(self):
        items = [1]
        result = list(progress.show_progress(items, "Processing", 1))
        assert result == items

    def test_progress_no_len_iterable(self):
        # Test with generator (no len)
        def gen():
            yield 1
            yield 2
            yield 3
        
        result = list(progress.show_progress(gen(), "Processing"))
        assert result == [1, 2, 3]

    def test_progress_type_error_for_len(self):
        # Test when len() raises TypeError
        class NoLenIterable:
            def __iter__(self):
                return iter([1, 2, 3])
        
        result = list(progress.show_progress(NoLenIterable(), "Processing"))
        assert result == [1, 2, 3]
