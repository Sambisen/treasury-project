"""Integration tests: refresh -> validate -> confirm flow."""
import pytest
from unittest.mock import MagicMock, patch
from data_manager import DataManager
from validation import ValidationEngine


@pytest.fixture
def mock_excel_engine():
    engine = MagicMock()
    engine.recon_data = {}
    engine.load_recon_direct.return_value = (True, "OK")
    engine.used_cache_fallback = False
    engine.get_recon_value.return_value = None
    engine.weights_ok = True
    engine.weights_cells_parsed = {}
    engine.get_days_for_date.return_value = {}
    return engine


@pytest.fixture
def mock_bbg_engine():
    return MagicMock()


@pytest.fixture
def dm(mock_excel_engine, mock_bbg_engine):
    return DataManager(
        excel_engine=mock_excel_engine,
        bbg_engine=mock_bbg_engine,
        on_notify=MagicMock(),
        on_safe_after=lambda delay, fn, *args: fn(*args),
    )


@pytest.fixture
def validator(mock_excel_engine):
    return ValidationEngine(excel_engine=mock_excel_engine)


class TestRefreshThenValidateFlow:
    """Test the complete refresh -> apply -> validate pipeline."""

    def test_full_flow_empty_data(self, dm, validator):
        """Refresh with empty data should produce a valid validation."""
        dm.apply_excel_result(True, "OK")
        dm.apply_bbg_result({}, {}, None)

        validator.reset_status()
        rows = validator.build_recon_rows(
            "ALL", dm.cached_excel_data, dm.cached_market_data,
            dm.current_days_data, dm.group_health,
        )
        assert isinstance(rows, list)
        assert validator.checks_total > 0

    def test_full_flow_bbg_failure(self, dm, validator):
        """BBG failure still allows validation to proceed."""
        dm.apply_excel_result(True, "OK")
        dm.apply_bbg_result({}, {}, "Connection refused")
        assert dm.bbg_ok is False

        validator.reset_status()
        rows = validator.build_recon_rows(
            "ALL", dm.cached_excel_data, dm.cached_market_data,
            dm.current_days_data, dm.group_health,
        )
        # With no market data, spot/fwd checks default to True
        assert validator.status_spot is True
        assert validator.status_fwds is True

    def test_full_flow_excel_failure(self, dm, validator):
        """Excel failure gives empty data but validation still runs."""
        dm.apply_excel_result(False, "File not found")
        dm.apply_bbg_result({"T Curncy": {"price": 10.0}}, {}, None)
        assert dm.excel_ok is False
        assert dm.bbg_ok is True

        validator.reset_status()
        rows = validator.build_recon_rows(
            "ALL", dm.cached_excel_data, dm.cached_market_data,
            dm.current_days_data, dm.group_health,
        )
        assert isinstance(rows, list)

    def test_cache_cleared_between_runs(self, dm, validator):
        """After clear_cache, next validation should start fresh."""
        dm.apply_excel_result(True, "OK")
        dm.apply_bbg_result({"T Curncy": {"price": 10.0}}, {}, None)
        assert dm.bbg_ok is True

        dm.clear_cache()
        assert dm.bbg_ok is False
        assert dm.cached_market_data == {}

        validator.reset_status()
        rows = validator.build_recon_rows(
            "ALL", dm.cached_excel_data, dm.cached_market_data,
            dm.current_days_data, dm.group_health,
        )
        assert isinstance(rows, list)


class TestComputeOverallStatus:
    """Test compute_overall_status with mock app object."""

    def test_all_ok_returns_ok(self):
        from history import compute_overall_status

        app = MagicMock()
        app.status_spot = True
        app.status_fwds = True
        app.status_days = True
        app.status_cells = True
        app.status_weights = True
        app.active_alerts = []

        result = compute_overall_status(app)
        assert result == "OK"

    def test_spot_fail_returns_check(self):
        from history import compute_overall_status

        app = MagicMock()
        app.status_spot = False
        app.status_fwds = True
        app.status_days = True
        app.status_cells = True
        app.status_weights = True
        app.active_alerts = []

        result = compute_overall_status(app)
        assert result != "OK"

    def test_alerts_present_returns_check(self):
        from history import compute_overall_status

        app = MagicMock()
        app.status_spot = True
        app.status_fwds = True
        app.status_days = True
        app.status_cells = True
        app.status_weights = True
        app.active_alerts = [{"msg": "something wrong"}]

        result = compute_overall_status(app)
        assert result != "OK"
