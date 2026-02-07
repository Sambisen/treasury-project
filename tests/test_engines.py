"""Tests for engines.py — Helper functions and ExcelEngine basics."""
import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock, call

from engines import _parse_date_cell, _parse_weights_row, _open_workbook


class TestParseDateCell:
    """Test the date cell parsing helper."""

    def test_datetime_passthrough(self):
        dt = datetime(2026, 1, 15)
        assert _parse_date_cell(dt) == dt

    def test_string_date(self):
        result = _parse_date_cell("2026-01-15")
        assert result == datetime(2026, 1, 15)

    def test_invalid_string_returns_none(self):
        assert _parse_date_cell("not-a-date") is None

    def test_none_returns_none(self):
        assert _parse_date_cell(None) is None

    def test_integer_returns_none(self):
        assert _parse_date_cell(12345) is None


class TestParseWeightsRow:
    """Test the weights row parsing helper."""

    def test_normal_weights(self):
        result = _parse_weights_row(0.88, 0.12, 0.0)
        assert result == {"USD": 0.88, "EUR": 0.12, "NOK": 0.0}

    def test_none_usd_defaults_to_zero(self):
        result = _parse_weights_row(None, 0.5, 0.5)
        assert result["USD"] == 0.0

    def test_none_nok_computed_from_remainder(self):
        result = _parse_weights_row(0.7, 0.2, None)
        assert abs(result["NOK"] - 0.1) < 1e-10

    def test_all_none_defaults(self):
        result = _parse_weights_row(None, None, None)
        assert result["USD"] == 0.0
        assert result["EUR"] == 0.0
        assert result["NOK"] == 1.0  # 1.0 - 0.0 - 0.0

    def test_string_values_converted(self):
        result = _parse_weights_row("0.5", "0.3", "0.2")
        assert result["USD"] == 0.5
        assert result["EUR"] == 0.3
        assert abs(result["NOK"] - 0.2) < 1e-10

    def test_sum_to_one(self):
        result = _parse_weights_row(0.4, 0.35, 0.25)
        total = result["USD"] + result["EUR"] + result["NOK"]
        assert abs(total - 1.0) < 1e-10


class TestOpenWorkbook:
    """Test the workbook opening helper with retry and cache fallback."""

    @patch("engines.load_workbook")
    def test_direct_read_returns_no_cache_flag(self, mock_load):
        mock_wb = MagicMock()
        mock_load.return_value = mock_wb
        wb, used_cache = _open_workbook(Path("test.xlsx"))
        assert wb is mock_wb
        assert used_cache is False

    @patch("engines.time.sleep")
    @patch("engines.load_workbook")
    def test_retry_succeeds_on_second_attempt(self, mock_load, mock_sleep):
        mock_wb = MagicMock()
        mock_load.side_effect = [PermissionError("locked"), mock_wb]
        wb, used_cache = _open_workbook(Path("test.xlsx"), retries=3, delay=0.1)
        assert wb is mock_wb
        assert used_cache is False
        mock_sleep.assert_called_once_with(0.1)

    @patch("engines.copy_to_cache_fast")
    @patch("engines.time.sleep")
    @patch("engines.load_workbook")
    def test_falls_back_to_cache_after_all_retries(self, mock_load, mock_sleep, mock_copy):
        mock_wb = MagicMock()
        mock_load.side_effect = [
            PermissionError("locked"),
            PermissionError("locked"),
            PermissionError("locked"),
            mock_wb,  # cache copy succeeds
        ]
        mock_copy.return_value = Path("cache.xlsx")
        wb, used_cache = _open_workbook(Path("test.xlsx"), retries=3, delay=0.1)
        assert wb is mock_wb
        assert used_cache is True
        assert mock_sleep.call_count == 2  # retries 0→1, 1→2 (not before cache)
        mock_copy.assert_called_once()

    @patch("engines.time.sleep")
    @patch("engines.load_workbook")
    def test_no_sleep_on_first_attempt(self, mock_load, mock_sleep):
        mock_load.return_value = MagicMock()
        _open_workbook(Path("test.xlsx"))
        mock_sleep.assert_not_called()
