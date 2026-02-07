"""Tests for engines.py — Helper functions and ExcelEngine basics."""
import pytest
from datetime import datetime
from pathlib import Path

from engines import _parse_date_cell, _parse_weights_row


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
