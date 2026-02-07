"""Tests for calculations.py — core financial calculation functions."""
import pytest
from calculations import calc_implied_yield, calc_funding_rate


class TestCalcImpliedYield:
    """Tests for calc_implied_yield."""

    def test_basic_calculation(self):
        """A positive spot, pips, base_rate and days should return a float."""
        result = calc_implied_yield(spot=10.20, pips=100.0, base_rate=3.65, days=30)
        assert result is not None
        assert isinstance(result, float)

    def test_zero_days_returns_none(self):
        assert calc_implied_yield(10.0, 100.0, 3.0, 0) is None

    def test_negative_days_returns_none(self):
        assert calc_implied_yield(10.0, 100.0, 3.0, -5) is None

    def test_none_spot_returns_none(self):
        assert calc_implied_yield(None, 100.0, 3.0, 30) is None

    def test_none_pips_returns_none(self):
        assert calc_implied_yield(10.0, None, 3.0, 30) is None

    def test_none_base_rate_returns_none(self):
        assert calc_implied_yield(10.0, 100.0, None, 30) is None

    def test_base_rate_must_be_percentage_form(self):
        """base_rate must be in percentage form (e.g. 3.65, not 0.0365)."""
        result_decimal = calc_implied_yield(10.0, 100.0, 0.0365, 30)
        result_percent = calc_implied_yield(10.0, 100.0, 3.65, 30)
        assert result_decimal is not None
        assert result_percent is not None
        # These should NOT be equal — no auto-conversion
        assert abs(result_decimal - result_percent) > 1.0

    def test_zero_pips_returns_base_rate_equivalent(self):
        """With zero pips, implied yield should be close to base_rate."""
        result = calc_implied_yield(spot=10.0, pips=0.0, base_rate=3.0, days=30)
        assert result is not None
        # With 0 pips, the implied yield should equal the base rate
        assert abs(result - 3.0) < 0.01

    def test_positive_pips_increases_yield(self):
        """Positive pips should result in higher implied yield than base rate."""
        base = calc_implied_yield(10.0, 0.0, 3.0, 90)
        with_pips = calc_implied_yield(10.0, 500.0, 3.0, 90)
        assert with_pips > base


class TestCalcFundingRate:
    """Tests for calc_funding_rate."""

    def test_basic_weighted_rate(self):
        weights = {"EUR": 0.50, "USD": 0.30, "NOK": 0.20}
        result = calc_funding_rate(4.0, 5.0, 3.0, weights)
        expected = 4.0 * 0.50 + 5.0 * 0.30 + 3.0 * 0.20
        assert result is not None
        assert abs(result - expected) < 1e-10

    def test_single_currency_weight(self):
        """With 100% EUR weight, result should equal EUR implied."""
        weights = {"EUR": 1.0, "USD": 0.0, "NOK": 0.0}
        result = calc_funding_rate(4.5, 5.0, 3.0, weights)
        assert abs(result - 4.5) < 1e-10

    def test_none_eur_returns_none(self):
        weights = {"EUR": 0.5, "USD": 0.3, "NOK": 0.2}
        assert calc_funding_rate(None, 5.0, 3.0, weights) is None

    def test_none_usd_returns_none(self):
        weights = {"EUR": 0.5, "USD": 0.3, "NOK": 0.2}
        assert calc_funding_rate(4.0, None, 3.0, weights) is None

    def test_none_nok_returns_none(self):
        weights = {"EUR": 0.5, "USD": 0.3, "NOK": 0.2}
        assert calc_funding_rate(4.0, 5.0, None, weights) is None

    def test_missing_weight_key_returns_none(self):
        weights = {"EUR": 0.5, "USD": 0.5}  # Missing NOK
        assert calc_funding_rate(4.0, 5.0, 3.0, weights) is None

    def test_empty_weights_returns_none(self):
        assert calc_funding_rate(4.0, 5.0, 3.0, {}) is None

    def test_zero_weights_returns_zero(self):
        weights = {"EUR": 0.0, "USD": 0.0, "NOK": 0.0}
        result = calc_funding_rate(4.0, 5.0, 3.0, weights)
        assert result == 0.0
