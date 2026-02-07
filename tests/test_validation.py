"""Tests for validation.py — ValidationEngine."""
import pytest
from unittest.mock import MagicMock
from validation import ValidationEngine


@pytest.fixture
def mock_excel_engine():
    engine = MagicMock()
    engine.get_recon_value.return_value = None
    engine.weights_ok = True
    engine.weights_cells_parsed = {}
    return engine


@pytest.fixture
def validator(mock_excel_engine):
    return ValidationEngine(excel_engine=mock_excel_engine)


class TestValidationEngineInit:
    def test_default_state(self, validator):
        assert validator.status_spot is True
        assert validator.status_fwds is True
        assert validator.status_ecp is True
        assert validator.status_days is True
        assert validator.status_cells is True
        assert validator.status_weights is True
        assert validator.weights_state == "WAIT"
        assert validator.checks_passed == 0
        assert validator.checks_total == 0
        assert validator.active_alerts == []

    def test_reset_status(self, validator):
        validator.status_spot = False
        validator.status_cells = False
        validator.active_alerts = [{"msg": "test"}]
        validator.weights_state = "FAIL"

        validator.reset_status()

        assert validator.status_spot is True
        assert validator.status_cells is True
        assert validator.active_alerts == []
        assert validator.weights_state == "WAIT"


class TestBuildReconRows:
    def test_empty_data_returns_rows(self, validator):
        rows = validator.build_recon_rows("ALL", {}, {}, {}, {})
        assert isinstance(rows, list)
        assert len(rows) > 0  # At least section headers

    def test_spot_only_view(self, validator):
        rows = validator.build_recon_rows("SPOT", {}, {}, {}, {})
        sections = [r for r in rows if r.get("style") == "section"]
        section_titles = [r["values"][0] for r in sections]
        assert any("SPOT" in t for t in section_titles)
        # Should not have DAYS or CELLS sections
        assert not any("DAYS" in t for t in section_titles)
        assert not any("CELLS" in t for t in section_titles)

    def test_checks_counter_increments(self, validator):
        validator.build_recon_rows("ALL", {}, {}, {}, {})
        assert validator.checks_total > 0

    def test_weights_file_not_readable(self, validator, mock_excel_engine):
        mock_excel_engine.weights_ok = False
        group_health = {}
        validator.build_recon_rows("ALL", {}, {}, {}, group_health)
        assert validator.status_weights is False
        assert validator.weights_state == "FAIL"
        assert "WEIGHTS" in group_health

    def test_all_status_flags_set_on_full_run(self, validator):
        """After a full ALL run, all status flags should be set."""
        group_health = {}
        validator.build_recon_rows("ALL", {}, {}, {}, group_health)
        # With no market data, spot/fwds default to True
        assert validator.status_spot is True
        assert validator.status_fwds is True

    def test_view_filter_only_runs_requested_section(self, validator):
        """FWDS view should not touch status_spot."""
        validator.status_spot = False  # Pre-set to False
        validator.build_recon_rows("FWDS", {}, {}, {}, {})
        assert validator.status_spot is False  # Should not have been changed


class TestCheckGate:
    def test_always_returns_unlocked(self, validator):
        """Current implementation always returns False (unlocked)."""
        is_locked, changed = validator.check_gate()
        assert is_locked is False

    def test_changed_flag_on_initial_call(self, validator):
        """First call changes from True (default) to False."""
        is_locked, changed = validator.check_gate()
        assert changed is True  # Was True, now False

    def test_no_change_on_second_call(self, validator):
        validator.check_gate()  # First call
        is_locked, changed = validator.check_gate()
        assert changed is False  # Already unlocked
