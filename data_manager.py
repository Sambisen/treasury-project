"""
Data manager for Nibor Calculation Terminal.
Orchestrates Bloomberg + Excel data fetching, caching, and change detection.
Extracted from main.py for testability and separation of concerns.
"""
from datetime import datetime
from pathlib import Path
from typing import Callable

from config import get_logger, get_market_structure, get_all_real_tickers
from utils import fmt_ts, safe_float

log = get_logger("data_manager")


class DataManager:
    """Manages data fetching, caching, and change detection for Bloomberg and Excel sources."""

    def __init__(
        self,
        excel_engine,
        bbg_engine,
        on_notify: Callable[[str, str], None] | None = None,
        on_safe_after: Callable | None = None,
    ):
        """
        Args:
            excel_engine: ExcelEngine instance.
            bbg_engine: BloombergEngine instance.
            on_notify: Callback(level, message) for toast-like notifications.
            on_safe_after: Thread-safe scheduler callback(delay_ms, func, *args).
        """
        self.excel_engine = excel_engine
        self.bbg_engine = bbg_engine
        self._on_notify = on_notify
        self._on_safe_after = on_safe_after

        # Cached data
        self.cached_market_data: dict = {}
        self.cached_excel_data: dict = {}
        self.current_days_data: dict = {}

        # Status flags
        self.bbg_ok: bool = False
        self.excel_ok: bool = False
        self.bbg_last_ok_ts: datetime | None = None
        self.excel_last_ok_ts: datetime | None = None
        self.bbg_last_update: str = "-"
        self.excel_last_update: str = "-"

        # Metadata
        self.last_bbg_meta: dict = {}
        self.group_health: dict[str, str] = {}
        self._excel_change_pending: bool = False

    def _notify(self, level: str, message: str):
        """Send a notification via the registered callback."""
        if self._on_notify:
            try:
                self._on_notify(level, message)
            except Exception as e:
                log.warning(f"Notification callback failed: {e}")

    def _safe_after(self, delay: int, callback, *args):
        """Delegate to the injected thread-safe scheduler."""
        if self._on_safe_after:
            self._on_safe_after(delay, callback, *args)
        else:
            callback(*args)

    # =========================================================================
    # DATA REFRESH
    # =========================================================================

    def refresh(self, on_excel_done: Callable, on_bbg_done: Callable):
        """
        Worker method to run in a background thread.
        Fetches Excel data, then Bloomberg data.
        Calls on_excel_done and on_bbg_done via safe_after.
        """
        log.info("===== REFRESH DATA WORKER STARTED =====")
        log.info("Loading Excel data...")
        excel_ok, excel_msg = self.excel_engine.load_recon_direct()
        log.info(f"Excel load result: success={excel_ok}, msg={excel_msg}")

        if excel_ok:
            log.info(f"Excel engine recon_data has {len(self.excel_engine.recon_data)} entries")
        else:
            log.error(f"Excel load FAILED: {excel_msg}")

        self._safe_after(0, on_excel_done, excel_ok, excel_msg)

        self.bbg_engine.fetch_snapshot(
            get_all_real_tickers(),
            lambda d, meta: self._safe_after(0, on_bbg_done, d, meta, None),
            lambda e: self._safe_after(0, on_bbg_done, {}, {}, str(e)),
            fields=["PX_LAST", "CHG_NET_1D", "LAST_UPDATE"]
        )

    # =========================================================================
    # RESULT HANDLERS
    # =========================================================================

    def apply_excel_result(self, excel_ok: bool, excel_msg: str):
        """Process Excel load result — cache data and update status."""
        log.debug(f"apply_excel_result: excel_ok={excel_ok}, msg={excel_msg}")

        if excel_ok:
            self.cached_excel_data = dict(self.excel_engine.recon_data)
            log.info(f"Excel data cached: {len(self.cached_excel_data)} cells")

            sample_cells = list(self.cached_excel_data.items())[:5]
            log.debug(f"Sample cached cells: {sample_cells}")

            self.excel_last_ok_ts = datetime.now()
            self.excel_ok = True
            self.excel_last_update = fmt_ts(self.excel_last_ok_ts)

            if self.excel_engine.used_cache_fallback:
                self._notify(
                    "warning",
                    "Excel file was locked \u2014 data read from cache copy.\n"
                    "Save & close Excel, then press F5 to get fresh data."
                )
        else:
            self.cached_excel_data = {}
            self.excel_ok = False
            log.error("Excel failed, cached_excel_data cleared")

    def apply_bbg_result(self, bbg_data: dict, bbg_meta: dict, bbg_err: str | None):
        """Process Bloomberg result — cache data and compute group health."""
        self.last_bbg_meta = dict(bbg_meta or {})

        if bbg_data and not bbg_err:
            self.cached_market_data = dict(bbg_data)
            self.bbg_last_ok_ts = datetime.now()
            self.bbg_ok = True
            self.bbg_last_update = fmt_ts(self.bbg_last_ok_ts)
            self.group_health = self._compute_group_health(self.last_bbg_meta, self.cached_market_data)
        else:
            self.cached_market_data = dict(bbg_data) if bbg_data else {}
            self.bbg_ok = False
            self.group_health = self._compute_group_health(self.last_bbg_meta, self.cached_market_data)

    # =========================================================================
    # GROUP HEALTH
    # =========================================================================

    def _compute_group_health(self, bbg_meta: dict, market_data: dict) -> dict[str, str]:
        """Calculate health status per data group."""
        meta = bbg_meta or {}
        dur = meta.get("duration_ms", None)
        from_cache = meta.get("from_cache", False)

        def fmt_group(tickers: list[str]) -> str:
            if not tickers:
                return "\u2014"
            ok = sum(1 for t in set(tickers) if t in market_data and market_data[t] is not None)
            total = len(set(tickers))
            if dur is None:
                return f"BBG {ok}/{total} OK"
            suffix = "cache" if from_cache else f"{dur}ms"
            return f"BBG {ok}/{total} OK | {suffix}"

        ms = get_market_structure()
        spot_tickers = [t for t, _ in ms.get("SPOT RATES", [])]
        fwd_tickers = [t for g in ("USDNOK FORWARDS", "EURNOK FORWARDS") for t, _ in ms.get(g, [])]
        cm_tickers = [t for t, _ in ms.get("SWET CM CURVES", [])]

        return {
            "SPOT": fmt_group(spot_tickers),
            "FWDS": fmt_group(fwd_tickers),
            "ECP": "\u2014",
            "DAYS": "\u2014",
            "CELLS": "\u2014",
            "WEIGHTS": "\u2014",
            "SWETCM": fmt_group(cm_tickers),
        }

    # =========================================================================
    # EXCEL FILE CHANGES
    # =========================================================================

    def on_excel_file_changed(self, file_path: Path):
        """Handle Excel file change notification (data-layer concern)."""
        log.info(f"[DataManager] Excel file changed: {file_path.name}")
        self._excel_change_pending = True

    # =========================================================================
    # HELPERS
    # =========================================================================

    def update_days_from_date(self, date_str: str):
        """Load day reference data for a given date."""
        days_map = self.excel_engine.get_days_for_date(date_str)
        self.current_days_data = days_map if days_map else {}

    def clear_cache(self):
        """Clear all cached data and reset status flags."""
        self.cached_market_data = {}
        self.cached_excel_data = {}
        self.current_days_data = {}
        self.bbg_ok = False
        self.excel_ok = False
