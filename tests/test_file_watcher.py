"""Tests for file_watcher.py — File change detection."""
import time
import tempfile
import threading
import pytest
from pathlib import Path
from unittest.mock import MagicMock

from file_watcher import FileWatcher, compute_file_hash


class TestComputeFileHash:
    """Test the MD5 hashing function."""

    def test_hash_existing_file(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("hello world")
        h = compute_file_hash(f)
        assert h is not None
        assert len(h) == 32  # MD5 hex digest length

    def test_hash_nonexistent_file(self, tmp_path):
        f = tmp_path / "does_not_exist.txt"
        assert compute_file_hash(f) is None

    def test_same_content_same_hash(self, tmp_path):
        f1 = tmp_path / "a.txt"
        f2 = tmp_path / "b.txt"
        f1.write_text("content")
        f2.write_text("content")
        assert compute_file_hash(f1) == compute_file_hash(f2)

    def test_different_content_different_hash(self, tmp_path):
        f1 = tmp_path / "a.txt"
        f2 = tmp_path / "b.txt"
        f1.write_text("content1")
        f2.write_text("content2")
        assert compute_file_hash(f1) != compute_file_hash(f2)

    def test_empty_file_has_hash(self, tmp_path):
        f = tmp_path / "empty.txt"
        f.write_text("")
        h = compute_file_hash(f)
        assert h is not None


class TestFileWatcher:
    """Test FileWatcher lifecycle and tracking."""

    def test_watch_existing_file(self, tmp_path):
        f = tmp_path / "test.xlsx"
        f.write_text("data")
        watcher = FileWatcher()
        assert watcher.watch_file(f) is True
        watcher.stop()

    def test_watch_nonexistent_file(self, tmp_path):
        f = tmp_path / "missing.xlsx"
        watcher = FileWatcher()
        assert watcher.watch_file(f) is False
        watcher.stop()

    def test_unwatch_file(self, tmp_path):
        f = tmp_path / "test.xlsx"
        f.write_text("data")
        watcher = FileWatcher()
        watcher.watch_file(f)
        watcher.unwatch_file(f)
        assert not watcher.has_pending_changes(f)
        watcher.stop()

    def test_start_stop(self):
        watcher = FileWatcher()
        watcher.start()
        assert watcher._started is True
        watcher.stop()
        assert watcher._started is False

    def test_double_start_is_safe(self):
        watcher = FileWatcher()
        watcher.start()
        watcher.start()  # Should not create duplicate threads
        watcher.stop()

    def test_double_stop_is_safe(self):
        watcher = FileWatcher()
        watcher.start()
        watcher.stop()
        watcher.stop()  # Should not raise

    def test_get_current_hash(self, tmp_path):
        f = tmp_path / "test.xlsx"
        f.write_text("data")
        watcher = FileWatcher()
        watcher.watch_file(f)
        h = watcher.get_current_hash(f)
        assert h is not None
        assert h == compute_file_hash(f)
        watcher.stop()

    def test_force_rehash(self, tmp_path):
        f = tmp_path / "test.xlsx"
        f.write_text("original")
        watcher = FileWatcher()
        watcher.watch_file(f)
        old_hash = watcher.get_current_hash(f)

        f.write_text("modified")
        new_hash = watcher.force_rehash(f)
        assert new_hash != old_hash
        assert watcher.get_current_hash(f) == new_hash
        watcher.stop()

    def test_check_now_detects_change(self, tmp_path):
        f = tmp_path / "test.xlsx"
        f.write_text("original")

        callback = MagicMock()
        watcher = FileWatcher(on_change_callback=callback)
        watcher.watch_file(f)

        f.write_text("modified content")
        changed = watcher.check_now(f)
        assert changed is True
        callback.assert_called_once()
        watcher.stop()

    def test_check_now_no_change(self, tmp_path):
        f = tmp_path / "test.xlsx"
        f.write_text("same")

        callback = MagicMock()
        watcher = FileWatcher(on_change_callback=callback)
        watcher.watch_file(f)

        changed = watcher.check_now(f)
        assert changed is False
        callback.assert_not_called()
        watcher.stop()
