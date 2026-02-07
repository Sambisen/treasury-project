"""Tests for settings.py — Settings singleton and persistence."""
import json
import threading
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from settings import Settings, DEFAULT_SETTINGS, get_settings, get_setting, set_setting


@pytest.fixture(autouse=True)
def reset_singleton():
    """Reset the Settings singleton before each test."""
    Settings._instance = None
    import settings as mod
    mod._settings_instance = None
    yield
    Settings._instance = None
    mod._settings_instance = None


class TestSettingsSingleton:
    """Test the singleton pattern."""

    def test_singleton_returns_same_instance(self):
        s1 = Settings()
        s2 = Settings()
        assert s1 is s2

    def test_get_settings_convenience(self):
        s = get_settings()
        assert isinstance(s, Settings)

    def test_singleton_thread_safety(self):
        """Multiple threads creating Settings should all get the same instance."""
        instances = []

        def create():
            instances.append(id(Settings()))

        threads = [threading.Thread(target=create) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(set(instances)) == 1, "All threads should get the same singleton instance"


class TestSettingsGetSet:
    """Test getting and setting values."""

    def test_get_default_value(self):
        s = Settings()
        assert s.get("theme") == "dark"

    def test_get_missing_key_returns_default(self):
        s = Settings()
        assert s.get("nonexistent_key", "fallback") == "fallback"

    def test_set_and_get(self):
        s = Settings()
        s.set("theme", "light")
        assert s.get("theme") == "light"

    def test_get_all_returns_copy(self):
        s = Settings()
        all_settings = s.get_all()
        all_settings["theme"] = "modified"
        assert s.get("theme") == "dark", "get_all should return a copy"

    def test_reset_to_defaults(self):
        s = Settings()
        s.set("theme", "light")
        s.reset_to_defaults()
        assert s.get("theme") == "dark"


class TestSettingsCallbacks:
    """Test change notification callbacks."""

    def test_callback_fires_on_change(self):
        s = Settings()
        calls = []
        s.on_change("theme", lambda key, new, old: calls.append((key, new, old)))
        s.set("theme", "light")
        assert len(calls) == 1
        assert calls[0] == ("theme", "light", "dark")

    def test_callback_not_fired_when_same_value(self):
        s = Settings()
        calls = []
        s.on_change("theme", lambda key, new, old: calls.append(1))
        s.set("theme", "dark")  # Same as default
        assert len(calls) == 0

    def test_callback_error_does_not_propagate(self):
        s = Settings()
        s.on_change("theme", lambda k, n, o: 1 / 0)  # Will raise ZeroDivisionError
        # Should not raise
        s.set("theme", "light")
        assert s.get("theme") == "light"


class TestConvenienceFunctions:
    """Test module-level convenience functions."""

    def test_get_setting(self):
        assert get_setting("theme") == "dark"

    def test_set_setting(self):
        set_setting("theme", "light")
        assert get_setting("theme") == "light"


class TestDefaultSettings:
    """Test that all expected default keys exist."""

    def test_all_default_keys_exist(self):
        expected_keys = [
            "development_mode", "fixing_time", "theme", "auto_refresh",
            "bloomberg_auto_connect", "decimal_places", "language",
        ]
        for key in expected_keys:
            assert key in DEFAULT_SETTINGS, f"Missing default key: {key}"

    def test_default_mode_is_prod(self):
        assert DEFAULT_SETTINGS["development_mode"] is False
