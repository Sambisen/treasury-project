"""Tests for data_manager.py — DataManager."""
import pytest
from unittest.mock import MagicMock, call
from data_manager import DataManager


@pytest.fixture
def mock_excel_engine():
    engine = MagicMock()
    engine.recon_data = {(1, 1): 10.5, (2, 1): 20.3}
    engine.load_recon_direct.return_value = (True, "OK")
    engine.used_cache_fallback = False
    engine.get_days_for_date.return_value = {"1m_Days": 30, "3m_Days": 90}
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


class TestApplyExcelResult:
    def test_success_caches_data(self, dm, mock_excel_engine):
        dm.apply_excel_result(True, "OK")
        assert dm.cached_excel_data == {(1, 1): 10.5, (2, 1): 20.3}
        assert dm.excel_ok is True
        assert dm.excel_last_ok_ts is not None
        assert dm.excel_last_update != "-"

    def test_failure_clears_cache(self, dm):
        dm.cached_excel_data = {(1, 1): "old"}
        dm.apply_excel_result(False, "File not found")
        assert dm.cached_excel_data == {}
        assert dm.excel_ok is False

    def test_cache_fallback_notifies(self, dm, mock_excel_engine):
        mock_excel_engine.used_cache_fallback = True
        dm.apply_excel_result(True, "OK")
        dm._on_notify.assert_called_once()
        args = dm._on_notify.call_args[0]
        assert args[0] == "warning"
        assert "locked" in args[1].lower()


class TestApplyBbgResult:
    def test_success_caches_data(self, dm):
        data = {"USDNOK Curncy": {"price": 10.5}}
        dm.apply_bbg_result(data, {"duration_ms": 100}, None)
        assert dm.cached_market_data == data
        assert dm.bbg_ok is True
        assert dm.bbg_last_ok_ts is not None

    def test_error_clears_ok(self, dm):
        dm.apply_bbg_result({}, {}, "Connection refused")
        assert dm.bbg_ok is False

    def test_group_health_populated(self, dm):
        dm.apply_bbg_result({"T1 Curncy": {"price": 1.0}}, {}, None)
        assert isinstance(dm.group_health, dict)
        assert "SPOT" in dm.group_health

    def test_empty_data_with_no_error_still_ok(self, dm):
        """Non-empty data with no error should be OK."""
        dm.apply_bbg_result({"T Curncy": {"price": 1}}, {}, None)
        assert dm.bbg_ok is True


class TestClearCache:
    def test_clears_all_state(self, dm):
        dm.cached_market_data = {"t": 1}
        dm.cached_excel_data = {"c": 2}
        dm.current_days_data = {"d": 3}
        dm.bbg_ok = True
        dm.excel_ok = True

        dm.clear_cache()

        assert dm.cached_market_data == {}
        assert dm.cached_excel_data == {}
        assert dm.current_days_data == {}
        assert dm.bbg_ok is False
        assert dm.excel_ok is False


class TestUpdateDays:
    def test_delegates_to_engine(self, dm, mock_excel_engine):
        dm.update_days_from_date("2026-01-15")
        mock_excel_engine.get_days_for_date.assert_called_once_with("2026-01-15")
        assert dm.current_days_data == {"1m_Days": 30, "3m_Days": 90}

    def test_none_result_gives_empty(self, dm, mock_excel_engine):
        mock_excel_engine.get_days_for_date.return_value = None
        dm.update_days_from_date("2026-01-15")
        assert dm.current_days_data == {}


class TestOnExcelFileChanged:
    def test_sets_pending_flag(self, dm):
        from pathlib import Path
        dm.on_excel_file_changed(Path("/test/file.xlsx"))
        assert dm._excel_change_pending is True


class TestRefresh:
    def test_calls_callbacks(self, dm, mock_excel_engine, mock_bbg_engine):
        """Refresh should call on_excel_done and trigger bbg fetch."""
        on_excel = MagicMock()
        on_bbg = MagicMock()

        dm.refresh(on_excel, on_bbg)

        # Excel callback should have been called with (True, "OK")
        on_excel.assert_called_once_with(True, "OK")

        # BBG engine fetch_snapshot should have been called
        mock_bbg_engine.fetch_snapshot.assert_called_once()
