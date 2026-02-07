"""
Validation engine for Nibor Calculation Terminal.
Performs reconciliation checks, gate logic, and status tracking.
Extracted from main.py for testability and separation of concerns.
"""
from datetime import datetime, time as dt_time
from typing import Callable

from openpyxl.utils import coordinate_to_tuple

try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo

from config import (
    RULES_DB, DAYS_MAPPING, SWET_CM_RECON_MAPPING,
    WEIGHTS_FILE, WEIGHTS_FILE_CELLS, WEIGHTS_MODEL_CELLS,
    VALIDATION_GATE_TZ, DEFAULT_FIXING_TIME,
    get_recon_mapping, get_gate_window, get_logger,
)
from utils import safe_float, fmt_date, business_day_index_in_month, calendar_days_since_month_start, to_date
from settings import is_dev_mode, is_prod_mode, get_setting

log = get_logger("validation")


class ValidationEngine:
    """Runs reconciliation and validation checks against Excel and market data."""

    def __init__(self, excel_engine, notify_callback: Callable[[str, str], None] | None = None):
        """
        Args:
            excel_engine: ExcelEngine instance for get_recon_value() and weights access.
            notify_callback: Optional callback(level, message) for notifications.
        """
        self.excel_engine = excel_engine
        self._notify = notify_callback

        # Validation status flags
        self.status_spot: bool = True
        self.status_fwds: bool = True
        self.status_ecp: bool = True
        self.status_days: bool = True
        self.status_cells: bool = True
        self.status_weights: bool = True
        self.weights_state: str = "WAIT"
        self.active_alerts: list[dict] = []
        self.checks_passed: int = 0
        self.checks_total: int = 0
        self.recon_view_mode: str = "ALL"

        # Gate state
        self._validation_locked: bool = True

    def reset_status(self):
        """Reset all status flags and alerts to initial values."""
        self.active_alerts = []
        self.status_spot = True
        self.status_fwds = True
        self.status_ecp = True
        self.status_days = True
        self.status_cells = True
        self.status_weights = True
        self.weights_state = "WAIT"

    # =========================================================================
    # VALIDATION GATE
    # =========================================================================

    def _is_validation_locked(self) -> bool:
        """
        Check if validation is currently locked based on time window.

        In DEV mode: Always unlocked (returns False)
        In PROD mode: Only unlocked within the validation window

        NOTE: The user requested to *disable the gate* in production, because it caused
        the main "Run Calculation" button to appear blocked/unreliable.
        We therefore never lock validation/runs based on time.
        """
        return False

        # DEV mode: never locked
        if is_dev_mode():
            return False

        # Get current Stockholm time
        try:
            stockholm_tz = ZoneInfo(VALIDATION_GATE_TZ)
            now = datetime.now(stockholm_tz)
        except Exception:
            now = datetime.now()
            log.warning("Could not get Stockholm time, using local time")

        # Check if weekend (Saturday=5, Sunday=6)
        if now.weekday() >= 5:
            return True

        # Get validation window based on selected fixing
        (start_hour, start_min), (end_hour, end_min) = get_gate_window()
        window_start = dt_time(start_hour, start_min, 0)
        window_end = dt_time(end_hour, end_min, 0)

        current_time = now.time()
        is_within_window = window_start <= current_time <= window_end
        return not is_within_window

    def check_gate(self) -> tuple[bool, bool]:
        """Check validation gate.
        Returns: (is_locked, changed) — current lock state and whether it changed.
        """
        was_locked = self._validation_locked
        self._validation_locked = self._is_validation_locked()
        return self._validation_locked, (was_locked != self._validation_locked)

    # =========================================================================
    # BUILD RECON ROWS
    # =========================================================================

    def build_recon_rows(self, view, excel_data, market_data, current_days_data, group_health):
        """
        Build all validation/reconciliation rows.

        Args:
            view: "ALL", "SPOT", "FWDS", "DAYS", "CELLS", "WEIGHTS"
            excel_data: dict of (row, col) -> value from Excel
            market_data: dict of ticker -> {price, ...} from Bloomberg
            current_days_data: dict of tenor_key -> days
            group_health: mutable dict for health status (mutated in place)

        Returns:
            List of row dicts: [{"values": [...], "style": "..."}]
        """
        excel_data = excel_data or {}
        market_data = market_data or {}

        rows_out = []
        checks_passed = 0
        checks_total = 0

        TOL_SPOT = 0.0005
        TOL_FWDS = 0.0005
        TOL_W = 1e-9

        def add_section(title):
            rows_out.append({"values": [title, "", "", "", "", ""], "style": "section"})

        def add_row(cell, desc, model, market, diff, ok, style_override=None):
            nonlocal checks_passed, checks_total
            checks_total += 1
            if ok:
                checks_passed += 1
            status = "\u2713" if ok else "\u2715"
            style = style_override if style_override else ("good" if ok and view != "ALL" else ("normal" if ok else "bad"))
            rows_out.append({"values": [cell, desc, model, market, diff, status], "style": style})
            return ok

        def collect_market_section(title, filter_prefixes, tol):
            add_section(title)
            section_ok = True
            market_ready = bool(market_data)

            for cell, desc, ticker in get_recon_mapping():
                if not any(cell.startswith(p) for p in filter_prefixes):
                    continue

                model_val = excel_data.get(coordinate_to_tuple(cell), None)

                if not market_ready:
                    add_row(cell, desc, str(model_val), "-", "-", True)
                    continue

                market_inf = market_data.get(ticker)
                if not market_inf:
                    section_ok = False
                    add_row(cell, desc, str(model_val), "-", "-", False)
                    if view == "ALL":
                        self.active_alerts.append({"source": cell, "msg": f"{desc} Missing ticker", "val": "-", "exp": ticker})
                    continue

                market_val = float(market_inf.get("price", 0.0))
                mf = safe_float(model_val, 0.0)
                diff = mf - market_val
                ok = abs(diff) < tol
                section_ok = section_ok and ok

                add_row(cell, desc, f"{mf:,.6f}", f"{market_val:,.6f}", f"{diff:+.6f}", ok)

                if view == "ALL" and not ok:
                    self.active_alerts.append({"source": cell, "msg": f"{desc} Diff", "val": f"{diff:+.6f}", "exp": f"\u00b1{tol}"})
            return section_ok

        # --- SPOT ---
        if view in ("ALL", "SPOT"):
            ok_n = collect_market_section("EURNOK SPOT", ["N"], TOL_SPOT)
            ok_s = collect_market_section("USDNOK SPOT", ["S"], TOL_SPOT)
            if view == "ALL":
                self.status_spot = (ok_n and ok_s) if market_data else True

        # --- FORWARDS ---
        if view in ("ALL", "FWDS"):
            ok_o = collect_market_section("EURNOK FORWARDS", ["O"], TOL_FWDS)
            ok_t = collect_market_section("USDNOK FORWARDS", ["T"], TOL_FWDS)
            if view == "ALL":
                self.status_fwds = (ok_o and ok_t) if market_data else True

        # --- DAYS ---
        if view in ("ALL", "DAYS"):
            add_section("DAYS VALIDATION")
            days_ok = True
            for cell, desc, key in DAYS_MAPPING:
                model_val = excel_data.get(coordinate_to_tuple(cell), None)
                ref_val = (current_days_data or {}).get(key, None)
                try:
                    mi = int(model_val)
                    ri = int(ref_val)
                    diff = mi - ri
                    ok = (diff == 0)
                    days_ok = days_ok and ok
                    add_row(cell, desc, str(mi), str(ri), str(diff), ok)
                    if view == "ALL" and not ok:
                        self.active_alerts.append({"source": cell, "msg": f"{desc} Mismatch", "val": str(mi), "exp": str(ri)})
                except Exception:
                    days_ok = False
                    add_row(cell, desc, str(model_val), str(ref_val), "-", False)
                    if view == "ALL":
                        self.active_alerts.append({"source": cell, "msg": f"{desc} Parse error", "val": str(model_val), "exp": str(ref_val)})
            if view == "ALL":
                self.status_days = days_ok
                group_health["DAYS"] = "OK" if days_ok else "CHECK"

        # --- CELLS ---
        if view in ("ALL", "CELLS"):
            add_section("EXCEL CONSISTENCY CHECKS")
            cells_ok = True
            for rule in RULES_DB:
                _, top_cell, ref_target, logic, msg = rule
                val_top = self.excel_engine.get_recon_value(top_cell)
                val_bot = "-"
                ok = False

                try:
                    if logic == "Exakt Match":
                        val_bot = self.excel_engine.get_recon_value(ref_target)
                        try:
                            ok = abs(float(val_top) - float(val_bot)) < 0.000001
                        except Exception:
                            ok = (str(val_top).strip() == str(val_bot).strip())

                    elif logic == "Avrundat 2 dec":
                        val_bot = self.excel_engine.get_recon_value(ref_target)
                        ok = abs(round(float(val_top), 2) - round(float(val_bot), 2)) < 0.000001

                    elif logic == "Minimum":
                        val_bot = self.excel_engine.get_recon_value(ref_target)
                        ok = float(val_top) >= float(val_bot)

                    elif "-" in logic and logic[0].isdigit():
                        a, b = logic.split("-")
                        ok = float(a) <= float(val_top) <= float(b)
                        val_bot = f"Range {logic}"

                    elif "Exakt" in logic:
                        target = float(logic.split()[1].replace(",", "."))
                        ok = abs(float(val_top) - target) < 0.000001
                        val_bot = f"== {target}"
                except Exception:
                    ok = False

                cells_ok = cells_ok and ok

                show = (view == "CELLS") or (view == "ALL" and not ok)
                if show:
                    add_row(top_cell, msg, str(val_top), str(val_bot), "-", ok)

                if view == "ALL" and not ok:
                    self.active_alerts.append({"source": top_cell, "msg": msg, "val": str(val_top), "exp": str(val_bot)})

            if view == "ALL":
                self.status_cells = cells_ok
                group_health["CELLS"] = "OK" if cells_ok else "CHECK"

        # --- WEIGHTS ---
        if view in ("ALL", "WEIGHTS"):
            add_section("WEIGHTS \u2014 FILE VS MODEL (MONTHLY)")

            today_d = datetime.now().date()
            bday_idx = business_day_index_in_month(today_d)
            cal_days = calendar_days_since_month_start(today_d)

            model_date_raw = self.excel_engine.get_recon_value(WEIGHTS_MODEL_CELLS["DATE"])
            model_date = to_date(model_date_raw)

            model_usd = safe_float(self.excel_engine.get_recon_value(WEIGHTS_MODEL_CELLS["USD"]), None)
            model_eur = safe_float(self.excel_engine.get_recon_value(WEIGHTS_MODEL_CELLS["EUR"]), None)
            model_nok = safe_float(self.excel_engine.get_recon_value(WEIGHTS_MODEL_CELLS["NOK"]), None)

            file_ok = bool(self.excel_engine.weights_ok)
            if not file_ok:
                self.status_weights = False
                self.weights_state = "FAIL"
                group_health["WEIGHTS"] = "FAIL | Weights.xlsx not readable"

                add_row("WEIGHTS.xlsx", "Weights file not available", "-", "-", "-", False)
                if view == "ALL":
                    self.active_alerts.append({"source": "WEIGHTS.xlsx", "msg": "Weights file missing/unreadable", "val": "-", "exp": str(WEIGHTS_FILE)})

            else:
                p = self.excel_engine.weights_cells_parsed or {}
                file_h3 = p.get("H3")
                file_h4 = p.get("H4")
                file_h5 = p.get("H5")
                file_h6 = p.get("H6")

                file_usd = p.get("USD")
                file_eur = p.get("EUR")
                file_nok = p.get("NOK")

                dates_to_check = [("H3", file_h3), ("H4", file_h4), ("H5", file_h5), ("H6", file_h6)]
                date_ok = True
                for label, dval in dates_to_check:
                    if label != "H3" and dval is None:
                        continue
                    ok = (model_date is not None and dval is not None and model_date == dval)
                    date_ok = date_ok and ok
                    add_row(
                        f"{WEIGHTS_MODEL_CELLS['DATE']} \u2194 {label}",
                        f"Weights effective date ({label} in Weights.xlsx)",
                        fmt_date(model_date),
                        fmt_date(dval),
                        "" if ok else "DIFF",
                        ok
                    )
                    if view == "ALL" and not ok:
                        self.active_alerts.append({"source": "WEIGHTS DATE", "msg": f"Date mismatch ({label})", "val": fmt_date(model_date), "exp": fmt_date(dval)})

                w_ok = True

                def w_cmp(name, model_val, file_val, model_cell, file_cell):
                    nonlocal w_ok
                    if model_val is None or file_val is None:
                        ok = False
                        diff = "-"
                    else:
                        diffv = float(model_val) - float(file_val)
                        ok = abs(diffv) <= TOL_W
                        diff = f"{diffv:+.6f}"
                    w_ok = w_ok and ok
                    add_row(
                        f"{model_cell} \u2194 {file_cell}",
                        f"{name} weight",
                        "-" if model_val is None else f"{float(model_val):.6f}",
                        "-" if file_val is None else f"{float(file_val):.6f}",
                        diff,
                        ok
                    )
                    if view == "ALL" and not ok:
                        self.active_alerts.append({"source": f"WEIGHTS {name}", "msg": f"{name} weight mismatch", "val": str(model_val), "exp": str(file_val)})
                    return ok

                w_cmp("USD", model_usd, file_usd, WEIGHTS_MODEL_CELLS["USD"], WEIGHTS_FILE_CELLS["USD"])
                w_cmp("EUR", model_eur, file_eur, WEIGHTS_MODEL_CELLS["EUR"], WEIGHTS_FILE_CELLS["EUR"])
                w_cmp("NOK", model_nok, file_nok, WEIGHTS_MODEL_CELLS["NOK"], WEIGHTS_FILE_CELLS["NOK"])

                sum_file = None
                if file_usd is not None and file_eur is not None and file_nok is not None:
                    sum_file = float(file_usd) + float(file_eur) + float(file_nok)

                weights_match_ok = bool(date_ok and w_ok)
                self.status_weights = weights_match_ok

                updated_this_month = False
                if weights_match_ok and model_date is not None:
                    updated_this_month = (model_date.year == today_d.year and model_date.month == today_d.month)

                if not weights_match_ok:
                    self.weights_state = "FAIL"
                    group_health["WEIGHTS"] = "FAIL | Mismatch"
                else:
                    if updated_this_month:
                        self.weights_state = "OK"
                        sf = "-" if sum_file is None else f"{sum_file:.3f}"
                        group_health["WEIGHTS"] = f"OK | Updated {fmt_date(model_date)} | Sum {sf}"
                    else:
                        if bday_idx >= 5:
                            self.weights_state = "ALERT"
                            group_health["WEIGHTS"] = f"ALERT | Not updated | BDay {bday_idx}/5 | {cal_days} days"
                            if view == "ALL":
                                self.active_alerts.append({
                                    "source": "WEIGHTS",
                                    "msg": f"ALERT: Weights not updated (BDay {bday_idx}/5)",
                                    "val": fmt_date(model_date),
                                    "exp": f"Update required in {today_d.strftime('%Y-%m')}"
                                })
                        else:
                            self.weights_state = "PENDING"
                            group_health["WEIGHTS"] = f"SOON | Update weights | BDay {bday_idx}/5 | {cal_days} days"

        # --- SWET CM ---
        if view == "ALL" and SWET_CM_RECON_MAPPING:
            add_section("SWET CM (MODEL VS MARKET)")
            cm_ok = True
            market_ready = bool(market_data)
            for cell, desc, ticker in SWET_CM_RECON_MAPPING:
                model_val = excel_data.get(coordinate_to_tuple(cell), None)
                if not market_ready:
                    add_row(cell, desc, str(model_val), "-", "-", True)
                    continue
                mi = safe_float(model_val, 0.0)
                inf = market_data.get(ticker)
                if not inf:
                    cm_ok = False
                    add_row(cell, desc, str(model_val), "-", "-", False)
                    self.active_alerts.append({"source": cell, "msg": f"{desc} Missing ticker", "val": "-", "exp": ticker})
                    continue
                mv = float(inf.get("price", 0.0))
                diff = mi - mv
                ok = abs(diff) < 0.0005
                cm_ok = cm_ok and ok
                add_row(cell, desc, f"{mi:,.6f}", f"{mv:,.6f}", f"{diff:+.6f}", ok)
            group_health["SWETCM"] = "OK" if cm_ok else "CHECK"

        if view == "ALL":
            self.checks_passed = checks_passed
            self.checks_total = checks_total

        return rows_out
