"""Tests for history.py — Snapshot saving, loading, and querying."""
import json
import pytest
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock

from history import (
    load_history, save_history, get_user_info,
    get_rate_change, get_previous_day_rates, should_save_fixing,
    save_fixing_for_date, compute_overall_status,
)


@pytest.fixture
def tmp_history_file(tmp_path):
    """Create a temporary history file and patch the path."""
    history_file = tmp_path / "nibor_log.json"
    with patch("history.get_history_file_path", return_value=history_file), \
         patch("history.HISTORY_DIR", tmp_path):
        yield history_file


class TestLoadSaveHistory:
    """Test basic history I/O."""

    def test_load_empty_returns_dict(self, tmp_history_file):
        result = load_history()
        assert result == {}

    def test_save_and_load(self, tmp_history_file):
        data = {"2026-01-01": {"rates": {"1m": {"nibor": 4.5}}}}
        save_history(data)
        loaded = load_history()
        assert loaded == data

    def test_load_corrupt_file_returns_empty(self, tmp_history_file):
        tmp_history_file.write_text("not json")
        result = load_history()
        assert result == {}


class TestGetUserInfo:
    """Test user info retrieval."""

    def test_returns_tuple(self):
        user, machine = get_user_info()
        assert isinstance(user, str)
        assert isinstance(machine, str)
        assert len(user) > 0


class TestComputeOverallStatus:
    """Test overall status computation."""

    def test_all_ok_returns_ok(self):
        app = MagicMock()
        app.status_spot = True
        app.status_fwds = True
        app.status_days = True
        app.status_cells = True
        app.status_weights = True
        app.active_alerts = []
        assert compute_overall_status(app) == "OK"

    def test_failed_spot_returns_fail(self):
        app = MagicMock()
        app.status_spot = False
        app.status_fwds = True
        app.status_days = True
        app.status_cells = True
        app.status_weights = True
        app.active_alerts = []
        assert compute_overall_status(app) == "FAIL"

    def test_alerts_present_returns_fail(self):
        app = MagicMock()
        app.status_spot = True
        app.status_fwds = True
        app.status_days = True
        app.status_cells = True
        app.status_weights = True
        app.active_alerts = [{"msg": "Rate alert"}]
        assert compute_overall_status(app) == "FAIL"


class TestGetRateChange:
    """Test rate change calculations."""

    def test_basic_change(self):
        current = {"1m": {"nibor": 4.55}, "2m": {"nibor": 4.60}}
        previous = {"1m": {"nibor": 4.50}, "2m": {"nibor": 4.60}}
        changes = get_rate_change(current, previous)
        assert abs(changes["1m"] - 0.05) < 1e-10
        assert changes["2m"] == 0.0

    def test_no_previous_returns_empty(self):
        current = {"1m": {"nibor": 4.55}}
        assert get_rate_change(current, None) == {}

    def test_missing_tenor_returns_none(self):
        current = {"1m": {"nibor": 4.55}}
        previous = {"1m": {"nibor": None}}
        changes = get_rate_change(current, previous)
        assert changes["1m"] is None


class TestShouldSaveFixing:
    """Test idempotent save-fixing logic."""

    def test_new_date_should_save(self):
        assert should_save_fixing({}, "2026-01-15") is True

    def test_date_without_fixing_rates_should_save(self):
        history = {"2026-01-15": {"rates": {}}}
        assert should_save_fixing(history, "2026-01-15") is True

    def test_complete_fixing_should_not_save(self):
        history = {
            "2026-01-15": {
                "fixing_rates": {
                    "1w": 4.0, "1m": 4.1, "2m": 4.2, "3m": 4.3, "6m": 4.5
                }
            }
        }
        assert should_save_fixing(history, "2026-01-15") is False

    def test_partial_fixing_should_save(self):
        history = {
            "2026-01-15": {
                "fixing_rates": {"1w": 4.0, "1m": 4.1}
            }
        }
        assert should_save_fixing(history, "2026-01-15") is True


class TestSaveFixingForDate:
    """Test saving fixing data for a specific date."""

    def test_save_new_date(self):
        history = {}
        result = save_fixing_for_date(history, "2026-01-15", {"1w": 4.0})
        assert result is True
        assert "2026-01-15" in history
        assert history["2026-01-15"]["fixing_rates"] == {"1w": 4.0}

    def test_force_overwrite(self):
        history = {"2026-01-15": {"fixing_rates": {"1w": 3.0, "1m": 3.1, "2m": 3.2, "3m": 3.3, "6m": 3.5}}}
        result = save_fixing_for_date(history, "2026-01-15", {"1w": 4.0}, force=True)
        assert result is True
        assert history["2026-01-15"]["fixing_rates"]["1w"] == 4.0

    def test_skip_existing_without_force(self):
        history = {"2026-01-15": {"fixing_rates": {"1w": 3.0, "1m": 3.1, "2m": 3.2, "3m": 3.3, "6m": 3.5}}}
        result = save_fixing_for_date(history, "2026-01-15", {"1w": 4.0}, force=False)
        assert result is False  # Skipped because already exists


class TestGetPreviousDayRates:
    """Test previous day rates lookup."""

    def test_gets_previous_date(self, tmp_history_file):
        data = {
            "2026-01-14": {"rates": {"1m": {"nibor": 4.50}}},
            "2026-01-15": {"rates": {"1m": {"nibor": 4.55}}},
        }
        save_history(data)
        rates = get_previous_day_rates("2026-01-15")
        assert rates is not None
        assert rates["1m"]["nibor"] == 4.50

    def test_no_history_returns_none(self, tmp_history_file):
        assert get_previous_day_rates("2026-01-15") is None
