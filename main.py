"""
Onyx Terminal - Main Application
Treasury Suite for NIBOR validation and monitoring.
"""
import os
import threading
import time
from datetime import datetime
from tkinter import messagebox

import tkinter as tk

from openpyxl.utils import coordinate_to_tuple

from config import (
    APP_VERSION, THEME, FONTS, CURRENT_MODE, set_mode,
    APP_DIR, DATA_DIR, BASE_HISTORY_PATH, STIBOR_GRSS_PATH,
    DAY_FILES, RECON_FILE, WEIGHTS_FILE, CACHE_DIR,
    EXCEL_LOGO_CANDIDATES, BBG_LOGO_CANDIDATES,
    RULES_DB, RECON_MAPPING, DAYS_MAPPING, MARKET_STRUCTURE,
    WEIGHTS_FILE_CELLS, WEIGHTS_MODEL_CELLS, SWET_CM_RECON_MAPPING,
    ALL_REAL_TICKERS,
    setup_logging, get_logger
)

# Initialize logging
setup_logging()
log = get_logger("main")
from utils import (
    fmt_ts, fmt_date, safe_float, to_date,
    business_day_index_in_month, calendar_days_since_month_start,
    LogoPipelineTK
)
from engines import ExcelEngine, BloombergEngine, blpapi
from ui_components import style_ttk, NavButtonTK, SourceCardTK
from ui_pages import (
    DashboardPage, ReconPage, RulesPage, BloombergPage,
    NiborDaysPage, NokImpliedPage, WeightsPage, NiborMetaDataPage
)


class OnyxTerminalTK(tk.Tk):
    """Main application window for Onyx Terminal."""

    def __init__(self):
        super().__init__()

        set_mode("OFFICE")

        self.title(f"Onyx Terminal v{APP_VERSION} — Treasury Suite ({CURRENT_MODE['type']} Mode)")
        self.geometry("1400x900")
        self.minsize(1320, 820)
        self.configure(bg=THEME["bg_main"])

        style_ttk(self)

        self.logo_pipeline = LogoPipelineTK()
        self.engine = BloombergEngine(cache_ttl_sec=3.0)
        self.excel_engine = ExcelEngine()

        self.status_spot = True
        self.status_fwds = True
        self.status_ecp = True
        self.status_days = True
        self.status_cells = True

        self.status_weights = True
        self.weights_state = "WAIT"

        self.recon_view_mode = "ALL"

        self.current_days_data = {}
        self.cached_market_data: dict = {}
        self.cached_excel_data: dict = {}
        self.active_alerts: list[dict] = []

        self.bbg_last_ok_ts: datetime | None = None
        self.excel_last_ok_ts: datetime | None = None
        self.last_bbg_meta: dict = {}
        self.group_health: dict[str, str] = {}

        # Store for Dashboard to access
        self.bbg_ok = False
        self.excel_ok = False

        self._nav_buttons = {}
        self._pages = {}
        self._current_page = None

        self._busy = False
        self._update_buttons: list[tk.Button] = []
        self._update_btn_original_text: dict[int, str] = {}

        self.build_ui()

        self.after(250, self.refresh_data)

    def build_ui(self):
        hpad = CURRENT_MODE["hpad"]

        # ====================================================================
        # GLOBAL HEADER - Visible on ALL pages
        # ====================================================================
        from PIL import Image, ImageTk
        
        global_header = tk.Frame(self, bg=THEME["bg_main"])
        global_header.pack(fill="x", padx=hpad, pady=(hpad, 10))

        # LEFT: Swedbank header image (250px)
        header_left = tk.Frame(global_header, bg=THEME["bg_main"])
        header_left.pack(side="left")

        image_path = r"C:\Users\p901sbf\OneDrive - Swedbank\GroupTreasury-ShortTermFunding - Documents\Referensräntor\Nibor\Bilder\Swed.png"

        if os.path.exists(image_path):
            try:
                img = Image.open(image_path)
                target_width = 350
                aspect_ratio = img.height / img.width
                target_height = int(target_width * aspect_ratio)
                img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
                
                photo = ImageTk.PhotoImage(img)
                img_label = tk.Label(header_left, image=photo, bg=THEME["bg_main"])
                img_label.image = photo
                img_label.pack()
                log.info(f"Global Swedbank header loaded: {target_width}x{target_height}px")
            except Exception as e:
                log.warning(f"Failed to load Swedbank header: {e}")
                tk.Label(header_left, text="ONYX TERMINAL",
                        fg=THEME["text"], bg=THEME["bg_main"],
                        font=("Segoe UI", 24, "bold")).pack()
        else:
            log.warning(f"Image not found: {image_path}")
            tk.Label(header_left, text="ONYX TERMINAL",
                    fg=THEME["text"], bg=THEME["bg_main"],
                    font=("Segoe UI", 24, "bold")).pack()

        # RIGHT: Compact status indicators + UPDATE button
        header_right = tk.Frame(global_header, bg=THEME["bg_main"])
        header_right.pack(side="right")

        # Status bar frame with border
        status_frame = tk.Frame(header_right, bg=THEME["bg_card"],
                               highlightthickness=2,
                               highlightbackground=THEME["border"],
                               relief="solid")
        status_frame.pack(side="left", padx=(0, 15))

        # Excel status
        excel_status = tk.Frame(status_frame, bg=THEME["bg_card"])
        excel_status.pack(side="left", padx=15, pady=10)
        
        tk.Label(excel_status, text="EXCEL:", fg=THEME["muted"],
                bg=THEME["bg_card"],
                font=("Segoe UI", 9, "bold")).pack(side="left", padx=(0, 8))
        
        self.excel_status_dot = tk.Label(excel_status, text="●",
                                         fg=THEME["good"],
                                         bg=THEME["bg_card"],
                                         font=("Segoe UI", 14, "bold"))
        self.excel_status_dot.pack(side="left", padx=(0, 5))
        
        self.excel_conn_lbl = tk.Label(excel_status, text="OK",
                                       fg=THEME["good"],
                                       bg=THEME["bg_card"],
                                       font=("Segoe UI", 10, "bold"))
        self.excel_conn_lbl.pack(side="left")

        # Separator
        tk.Frame(status_frame, bg=THEME["border"], width=2).pack(side="left", fill="y", padx=5)

        # Bloomberg status
        bbg_status = tk.Frame(status_frame, bg=THEME["bg_card"])
        bbg_status.pack(side="left", padx=15, pady=10)
        
        tk.Label(bbg_status, text="BLOOMBERG:", fg=THEME["muted"],
                bg=THEME["bg_card"],
                font=("Segoe UI", 9, "bold")).pack(side="left", padx=(0, 8))
        
        self.bbg_status_dot = tk.Label(bbg_status, text="●",
                                       fg=THEME["good"],
                                       bg=THEME["bg_card"],
                                       font=("Segoe UI", 14, "bold"))
        self.bbg_status_dot.pack(side="left", padx=(0, 5))
        
        self.bbg_conn_lbl = tk.Label(bbg_status, text="OK",
                                     fg=THEME["good"],
                                     bg=THEME["bg_card"],
                                     font=("Segoe UI", 10, "bold"))
        self.bbg_conn_lbl.pack(side="left")

        # Separator
        tk.Frame(status_frame, bg=THEME["border"], width=2).pack(side="left", fill="y", padx=5)

        # Alerts
        alerts_status = tk.Frame(status_frame, bg=THEME["bg_card"])
        alerts_status.pack(side="left", padx=15, pady=10)
        
        tk.Label(alerts_status, text="ALERTS:", fg=THEME["muted"],
                bg=THEME["bg_card"],
                font=("Segoe UI", 9, "bold")).pack(side="left", padx=(0, 8))
        
        self.alerts_count_lbl = tk.Label(alerts_status, text="0",
                                        fg=THEME["good"],
                                        bg=THEME["bg_card"],
                                        font=("Segoe UI", 10, "bold"))
        self.alerts_count_lbl.pack(side="left")

        # UPDATE SYSTEM button (in top-right corner)
        from ui_components import OnyxButtonTK
        self.header_update_btn = OnyxButtonTK(header_right, "UPDATE SYSTEM",
                                             command=self.refresh_data,
                                             variant="primary")
        self.header_update_btn.pack(side="left", padx=(0, 10))
        self.register_update_button(self.header_update_btn)

        # ====================================================================
        # BODY with Command Center Sidebar + Content
        # ====================================================================
        self.body = tk.Frame(self, bg=THEME["bg_main"])
        self.body.pack(fill="both", expand=True, padx=hpad, pady=(0, hpad))

        # Configure grid layout: sidebar (0) | separator (1) | content (2)
        self.body.grid_columnconfigure(0, weight=0, minsize=220)  # Sidebar fixed
        self.body.grid_columnconfigure(1, weight=0, minsize=3)    # Separator fixed
        self.body.grid_columnconfigure(2, weight=1)               # Content expandable
        self.body.grid_rowconfigure(0, weight=1)

        # ====================================================================
        # COMMAND CENTER SIDEBAR - ALWAYS VISIBLE
        # ====================================================================
        sidebar = tk.Frame(self.body, bg=THEME["bg_panel"], width=220,
                          highlightthickness=2,
                          highlightbackground=THEME["border"])
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)

        # Sidebar title
        tk.Label(sidebar, text="COMMAND CENTER",
                fg=THEME["muted"],
                bg=THEME["bg_panel"],
                font=("Segoe UI", 9)).pack(anchor="w", padx=20, pady=(20, 15))

        # Navigation buttons
        self.PAGES_CONFIG = [
            ("dashboard", "Dashboard", DashboardPage),
            ("nibor_recon", "Nibor Recon", ReconPage),
            ("nok_implied", "NOK Implied", NokImpliedPage),
            ("weights", "Weights", WeightsPage),
            ("nibor_meta", "NIBOR Meta Data", NiborMetaDataPage),
            ("rules_logic", "Rules & Logic", RulesPage),
            ("bloomberg", "Bloomberg", BloombergPage),
            ("nibor_days", "Nibor Days", NiborDaysPage),
        ]

        for page_key, page_name in [(k, n) for k, n, _ in self.PAGES_CONFIG]:
            btn = tk.Button(sidebar,
                          text=page_name,
                          command=lambda pk=page_key: self.show_page(pk),
                          bg=THEME["bg_panel"],
                          fg=THEME["text"],
                          font=FONTS["body"],
                          relief="flat",
                          anchor="w",
                          padx=15,
                          pady=10,
                          cursor="hand2")
            btn.pack(fill="x", padx=12, pady=3)
            self._nav_buttons[page_key] = btn

            # Hover effects
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg=THEME["bg_hover"]))
            btn.bind("<Leave>", lambda e, b=btn: b.config(bg=THEME["bg_panel"]))

        # Divider
        tk.Frame(sidebar, bg=THEME["border"], height=1).pack(fill="x", padx=20, pady=15)

        # Quick Access
        tk.Label(sidebar, text="QUICK ACCESS",
                fg=THEME["muted"],
                bg=THEME["bg_panel"],
                font=("Segoe UI", 9)).pack(anchor="w", padx=20, pady=(0, 10))

        # History folder
        history_label = tk.Label(sidebar,
                                text="📂 History",
                                fg=THEME["muted"],
                                bg=THEME["bg_panel"],
                                font=("Segoe UI", 10),
                                anchor="w",
                                cursor="hand2",
                                padx=15,
                                pady=5)
        history_label.pack(fill="x", padx=12)
        history_label.bind("<Enter>", lambda e: history_label.config(fg=THEME["accent"], bg=THEME["bg_hover"]))
        history_label.bind("<Leave>", lambda e: history_label.config(fg=THEME["muted"], bg=THEME["bg_panel"]))
        history_label.bind("<Button-1>", lambda e: self.open_history_folder())

        # GRSS folder
        grss_label = tk.Label(sidebar,
                             text="📂 GRSS",
                             fg=THEME["muted"],
                             bg=THEME["bg_panel"],
                             font=("Segoe UI", 10),
                             anchor="w",
                             cursor="hand2",
                             padx=15,
                             pady=5)
        grss_label.pack(fill="x", padx=12)
        grss_label.bind("<Enter>", lambda e: grss_label.config(fg=THEME["accent"], bg=THEME["bg_hover"]))
        grss_label.bind("<Leave>", lambda e: grss_label.config(fg=THEME["muted"], bg=THEME["bg_panel"]))
        grss_label.bind("<Button-1>", lambda e: self.open_stibor_folder())

        # Spacer
        tk.Frame(sidebar, bg=THEME["bg_panel"]).pack(fill="both", expand=True)

        # Visual separator line
        separator = tk.Frame(self.body, bg=THEME["accent"], width=3)
        separator.grid(row=0, column=1, sticky="ns")

        # ====================================================================
        # CONTENT AREA
        # ====================================================================
        self.content = tk.Frame(self.body, bg=THEME["bg_panel"],
                               highlightthickness=0)
        self.content.grid(row=0, column=2, sticky="nsew")
        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_columnconfigure(0, weight=1)

        for key, _, page_class in self.PAGES_CONFIG:
            page_instance = page_class(self.content, self)
            self._pages[key] = page_instance
            page_instance.grid(row=0, column=0, sticky="nsew")
            page_instance.grid_remove()

        if self.PAGES_CONFIG:
            self.show_page(self.PAGES_CONFIG[0][0])

    def register_update_button(self, btn: tk.Button):
        if btn not in self._update_buttons:
            self._update_buttons.append(btn)
            self._update_btn_original_text[id(btn)] = btn.cget("text")

    def set_busy(self, busy: bool, text: str | None = None):
        self._busy = bool(busy)
        for b in self._update_buttons:
            try:
                b.configure(state=("disabled" if busy else "normal"))
                if text and busy:
                    b.configure(text=text)
                elif not busy:
                    orig = self._update_btn_original_text.get(id(b), b.cget("text"))
                    b.configure(text=orig)
            except Exception:
                pass

    def show_page(self, key: str, focus: str | None = None):
        if key not in self._pages:
            return

        if self._current_page:
            self._pages[self._current_page].grid_remove()

        self._current_page = key
        self._pages[key].grid()

        # Update navigation button highlighting
        for btn_key, btn in self._nav_buttons.items():
            if btn_key == key:
                btn.config(fg=THEME["accent"], font=("Segoe UI", 11, "bold"))
            else:
                btn.config(fg=THEME["text"], font=FONTS["body"])

        if key == "nibor_recon" and focus:
            self._pages["nibor_recon"].set_focus_mode(focus)

        # Auto-refresh NOK Implied page when shown (if data is available)
        if key == "nok_implied":
            # Delay to ensure page is visible before updating
            self.after(100, lambda: self._pages["nok_implied"].update())

        self.refresh_ui()

    def open_history_folder(self):
        folder_path = self.excel_engine.current_folder_path
        if folder_path.exists():
            os.startfile(folder_path)
        else:
            messagebox.showerror("Onyx", f"Folder missing: {folder_path}")

    def open_stibor_folder(self):
        if STIBOR_GRSS_PATH.exists():
            os.startfile(STIBOR_GRSS_PATH)
        else:
            messagebox.showerror("Onyx", f"Folder missing: {STIBOR_GRSS_PATH}")

    def refresh_data(self):
        if self._busy:
            return

        self.set_busy(True, text="FETCHING…")

        today = datetime.now().strftime("%Y-%m-%d")
        self.update_days_from_date(today)

        threading.Thread(target=self._worker_refresh_excel_then_bbg, daemon=True).start()

    def _worker_refresh_excel_then_bbg(self):
        log.info("===== REFRESH DATA WORKER STARTED =====")
        log.info("Loading Excel data...")
        excel_ok, excel_msg = self.excel_engine.load_recon_direct()
        log.info(f"Excel load result: success={excel_ok}, msg={excel_msg}")

        if excel_ok:
            log.info(f"Excel engine recon_data has {len(self.excel_engine.recon_data)} entries")
        else:
            log.error(f"Excel load FAILED: {excel_msg}")
        
        self.after(0, self._apply_excel_result, excel_ok, excel_msg)

        if blpapi:
            self.engine.fetch_snapshot(
                ALL_REAL_TICKERS,
                lambda d, meta: self.after(0, self._apply_bbg_result, d, meta, None),
                lambda e: self.after(0, self._apply_bbg_result, {}, {}, str(e)),
                fields=["PX_LAST", "CHG_NET_1D", "LAST_UPDATE"]
            )
        else:
            self.after(0, self._apply_bbg_result, {}, {}, "BLPAPI not installed")

    def _compute_group_health(self, bbg_meta: dict, market_data: dict) -> dict[str, str]:
        meta = bbg_meta or {}
        dur = meta.get("duration_ms", None)
        from_cache = meta.get("from_cache", False)

        def fmt_group(tickers: list[str]) -> str:
            if not tickers:
                return "—"
            ok = sum(1 for t in set(tickers) if t in market_data and market_data[t] is not None)
            total = len(set(tickers))
            if dur is None:
                return f"BBG {ok}/{total} OK"
            suffix = "cache" if from_cache else f"{dur}ms"
            return f"BBG {ok}/{total} OK | {suffix}"

        spot_tickers = [t for t, _ in MARKET_STRUCTURE.get("SPOT RATES", [])]
        fwd_tickers = [t for g in ("USDNOK FORWARDS", "EURNOK FORWARDS") for t, _ in MARKET_STRUCTURE.get(g, [])]
        cm_tickers = [t for t, _ in MARKET_STRUCTURE.get("SWET CM CURVES", [])]

        return {
            "SPOT": fmt_group(spot_tickers),
            "FWDS": fmt_group(fwd_tickers),
            "ECP": "—",
            "DAYS": "—",
            "CELLS": "—",
            "WEIGHTS": "—",
            "SWETCM": fmt_group(cm_tickers),
        }

    def _apply_excel_result(self, excel_ok: bool, excel_msg: str):
        log.debug(f"_apply_excel_result called with excel_ok={excel_ok}, msg={excel_msg}")

        if excel_ok:
            self.cached_excel_data = dict(self.excel_engine.recon_data)
            log.info(f"Excel data cached: {len(self.cached_excel_data)} cells")

            # Log sample cells to verify data
            sample_cells = list(self.cached_excel_data.items())[:5]
            log.debug(f"Sample cached cells: {sample_cells}")
            
            self.excel_last_ok_ts = datetime.now()
            self.excel_ok = True
            self.excel_last_update = fmt_ts(self.excel_last_ok_ts)
            
            # Update Excel status in global header (compact format)
            self.excel_status_dot.config(fg=THEME["good"])
            self.excel_conn_lbl.config(text="OK", fg=THEME["good"])
        else:
            self.cached_excel_data = {}
            self.excel_ok = False
            log.error("Excel failed, cached_excel_data cleared")
            
            # Update Excel status (compact format)
            self.excel_status_dot.config(fg=THEME["bad"])
            self.excel_conn_lbl.config(text="FAIL", fg=THEME["bad"])

        self.active_alerts = []
        self.status_spot = True
        self.status_fwds = True
        self.status_ecp = True
        self.status_days = True
        self.status_cells = True
        self.status_weights = True
        self.weights_state = "WAIT"

        _ = self.build_recon_rows(view="ALL")
        
        # Update alerts count in global header (compact format)
        alert_count = len(self.active_alerts)
        if alert_count > 0:
            self.alerts_count_lbl.config(text=str(alert_count), fg=THEME["bad"])
        else:
            self.alerts_count_lbl.config(text="0", fg=THEME["good"])
        
        self.refresh_ui()

    def _apply_bbg_result(self, bbg_data: dict, bbg_meta: dict, bbg_err: str | None):
        self.last_bbg_meta = dict(bbg_meta or {})

        if bbg_data and not bbg_err and blpapi:
            self.cached_market_data = dict(bbg_data)
            self.bbg_last_ok_ts = datetime.now()
            self.bbg_ok = True
            self.bbg_last_update = fmt_ts(self.bbg_last_ok_ts)

            gh = self._compute_group_health(self.last_bbg_meta, self.cached_market_data)
            self.group_health = dict(gh)

            # Update Bloomberg status in global header (compact format)
            self.bbg_status_dot.config(fg=THEME["good"])
            self.bbg_conn_lbl.config(text="OK", fg=THEME["good"])
        else:
            self.cached_market_data = dict(bbg_data) if bbg_data else {}
            self.bbg_ok = False
            self.group_health = self._compute_group_health(self.last_bbg_meta, self.cached_market_data)
            
            # Update Bloomberg status (compact format)
            self.bbg_status_dot.config(fg=THEME["bad"])
            self.bbg_conn_lbl.config(text="FAIL", fg=THEME["bad"])

        self.active_alerts = []
        self.status_spot = True
        self.status_fwds = True
        self.status_ecp = True
        self.status_days = True
        self.status_cells = True
        self.status_weights = True
        self.weights_state = "WAIT"

        _ = self.build_recon_rows(view="ALL")

        # Update NokImpliedPage FIRST to populate impl_calc_data
        if "nok_implied" in self._pages:
            try:
                log.debug("Updating NokImpliedPage to populate impl_calc_data...")
                self._pages["nok_implied"].update()
                log.debug(f"impl_calc_data populated with {len(getattr(self, 'impl_calc_data', {}))} entries")
            except Exception as e:
                log.error(f"Error updating NokImpliedPage: {e}")

        self.set_busy(False)
        self.refresh_ui()

    def refresh_ui(self):
        if self._current_page and self._current_page in self._pages:
            try:
                self._pages[self._current_page].update()
            except Exception:
                pass

    def update_days_from_date(self, date_str):
        days_map = self.excel_engine.get_days_for_date(date_str)
        self.current_days_data = days_map if days_map else {}

    def build_recon_rows(self, view="ALL"):
        excel_data = self.cached_excel_data or {}
        market_data = self.cached_market_data or {}

        rows_out = []

        TOL_SPOT = 0.0005
        TOL_FWDS = 0.0005
        TOL_W = 1e-9

        def add_section(title):
            rows_out.append({"values": [title, "", "", "", "", ""], "style": "section"})

        def add_row(cell, desc, model, market, diff, ok, style_override=None):
            status = "✔" if ok else "✘"
            style = style_override if style_override else ("good" if ok and view != "ALL" else ("normal" if ok else "bad"))
            rows_out.append({"values": [cell, desc, model, market, diff, status], "style": style})
            return ok

        def collect_market_section(title, filter_prefixes, tol):
            add_section(title)
            section_ok = True
            market_ready = bool(market_data)

            for cell, desc, ticker in RECON_MAPPING:
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
                    self.active_alerts.append({"source": cell, "msg": f"{desc} Diff", "val": f"{diff:+.6f}", "exp": f"±{tol}"})
            return section_ok

        if view in ("ALL", "SPOT"):
            ok_n = collect_market_section("EURNOK SPOT", ["N"], TOL_SPOT)
            ok_s = collect_market_section("USDNOK SPOT", ["S"], TOL_SPOT)
            if view == "ALL":
                self.status_spot = (ok_n and ok_s) if market_data else True

        if view in ("ALL", "FWDS"):
            ok_o = collect_market_section("EURNOK FORWARDS", ["O"], TOL_FWDS)
            ok_t = collect_market_section("USDNOK FORWARDS", ["T"], TOL_FWDS)
            if view == "ALL":
                self.status_fwds = (ok_o and ok_t) if market_data else True

        if view in ("ALL", "DAYS"):
            add_section("DAYS VALIDATION")
            days_ok = True
            for cell, desc, key in DAYS_MAPPING:
                model_val = excel_data.get(coordinate_to_tuple(cell), None)
                ref_val = (self.current_days_data or {}).get(key, None)
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
                self.group_health["DAYS"] = "OK" if days_ok else "CHECK"

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
                self.group_health["CELLS"] = "OK" if cells_ok else "CHECK"

        if view in ("ALL", "WEIGHTS"):
            add_section("WEIGHTS — FILE VS MODEL (MONTHLY)")

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
                self.group_health["WEIGHTS"] = "FAIL | Weights.xlsx not readable"

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
                        f"{WEIGHTS_MODEL_CELLS['DATE']} ↔ {label}",
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
                        f"{model_cell} ↔ {file_cell}",
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
                    self.group_health["WEIGHTS"] = "FAIL | Mismatch"
                else:
                    if updated_this_month:
                        self.weights_state = "OK"
                        sf = "-" if sum_file is None else f"{sum_file:.3f}"
                        self.group_health["WEIGHTS"] = f"OK | Updated {fmt_date(model_date)} | Sum {sf}"
                    else:
                        if bday_idx >= 5:
                            self.weights_state = "ALERT"
                            self.group_health["WEIGHTS"] = f"ALERT | Not updated | BDay {bday_idx}/5 | {cal_days} days"
                            if view == "ALL":
                                self.active_alerts.append({
                                    "source": "WEIGHTS",
                                    "msg": f"ALERT: Weights not updated (BDay {bday_idx}/5)",
                                    "val": fmt_date(model_date),
                                    "exp": f"Update required in {today_d.strftime('%Y-%m')}"
                                })
                        else:
                            self.weights_state = "PENDING"
                            self.group_health["WEIGHTS"] = f"SOON | Update weights | BDay {bday_idx}/5 | {cal_days} days"

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
            self.group_health["SWETCM"] = "OK" if cm_ok else "CHECK"

        return rows_out


# ==============================================================================
#  TERMINAL MODE (för körning utan GUI)
# ==============================================================================
def run_terminal_mode():
    """Kör systemet i terminal-läge utan GUI."""
    log.info("=" * 60)
    log.info("  ONYX TERMINAL - Terminal-läge")
    log.info("=" * 60)
    log.info("Systemet startat i terminal-läge")

    log.info(f"Data-katalog: {DATA_DIR}")
    log.info("Filer som systemet letar efter:")
    log.info("-" * 40)

    all_files = [
        ("DAY_FILES[0]", DAY_FILES[0]),
        ("DAY_FILES[1]", DAY_FILES[1]),
        ("RECON_FILE", RECON_FILE),
        ("WEIGHTS_FILE", WEIGHTS_FILE),
    ]

    for name, path in all_files:
        exists = "FINNS" if path.exists() else "SAKNAS"
        log.info(f"  {name}: {path} - {exists}")

    log.info("-" * 40)
    log.info("Övriga sökvägar:")
    log.info(f"  BASE_HISTORY_PATH: {BASE_HISTORY_PATH}")
    log.info(f"  STIBOR_GRSS_PATH:  {STIBOR_GRSS_PATH}")
    log.info(f"  CACHE_DIR:         {CACHE_DIR}")

    generate_alerts_report()


def generate_alerts_report():
    """Genererar alerts baserat på filvalidering och sparar till rapport.txt."""
    log.info("=" * 60)
    log.info("  GENERERAR ALERT-RAPPORT")
    log.info("=" * 60)

    active_alerts = []
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    file_checks = [
        ("DAY_FILES[0]", DAY_FILES[0], "Nibor days 2025"),
        ("DAY_FILES[1]", DAY_FILES[1], "Nibor days 2026"),
        ("RECON_FILE", RECON_FILE, "Recon Workbook"),
        ("WEIGHTS_FILE", WEIGHTS_FILE, "Weights file"),
    ]

    for name, path, desc in file_checks:
        if not path.exists():
            active_alerts.append({
                "source": name,
                "msg": f"{desc} saknas",
                "val": "SAKNAS",
                "exp": str(path)
            })

    engine = ExcelEngine()

    for _ in range(20):
        if engine._day_data_ready:
            break
        time.sleep(0.1)

    if engine._day_data_err:
        active_alerts.append({
            "source": "DAY_FILES",
            "msg": "Fel vid laddning av day files",
            "val": engine._day_data_err,
            "exp": "Inga fel"
        })

    recon_ok, recon_msg = engine.load_recon_direct()
    if not recon_ok:
        active_alerts.append({
            "source": "RECON_FILE",
            "msg": "Kunde inte ladda recon-fil",
            "val": recon_msg,
            "exp": "OK"
        })
    else:
        for rule in RULES_DB:
            rule_id, top_cell, ref_target, logic, msg = rule
            val_top = engine.get_recon_value(top_cell)
            val_bot = engine.get_recon_value(ref_target)

            ok = False
            try:
                if logic == "Exakt Match":
                    try:
                        ok = abs(float(val_top) - float(val_bot)) < 0.000001
                    except (TypeError, ValueError):
                        ok = (str(val_top).strip() == str(val_bot).strip())
                elif logic == "Avrundat 2 dec":
                    ok = abs(round(float(val_top), 2) - round(float(val_bot), 2)) < 0.000001
                elif "-" in logic and logic[0].isdigit():
                    a, b = logic.split("-")
                    ok = float(a) <= float(val_top) <= float(b)
                elif "Exakt" in logic:
                    target = float(logic.split()[1].replace(",", "."))
                    ok = abs(float(val_top) - target) < 0.000001
            except Exception:
                ok = False

            if not ok:
                active_alerts.append({
                    "source": f"Rule {rule_id}: {top_cell}",
                    "msg": msg,
                    "val": str(val_top),
                    "exp": str(val_bot)
                })

    if not engine.weights_ok:
        active_alerts.append({
            "source": "WEIGHTS",
            "msg": "Weights-fil kunde inte laddas",
            "val": engine.weights_err or "Okänt fel",
            "exp": "OK"
        })

    rapport_path = APP_DIR / "rapport.txt"
    with open(rapport_path, "w", encoding="utf-8") as f:
        f.write("=" * 60 + "\n")
        f.write("  ONYX TERMINAL - ALERT RAPPORT\n")
        f.write("=" * 60 + "\n")
        f.write(f"Genererad: {timestamp}\n")
        f.write(f"Data-katalog: {DATA_DIR}\n\n")

        if not active_alerts:
            f.write("✓ INGA AKTIVA ALERTS\n")
            f.write("Alla valideringar godkända.\n")
        else:
            f.write(f"⚠ ANTAL AKTIVA ALERTS: {len(active_alerts)}\n")
            f.write("-" * 60 + "\n\n")

            for i, alert in enumerate(active_alerts, 1):
                f.write(f"Alert #{i}\n")
                f.write(f"  Källa:     {alert['source']}\n")
                f.write(f"  Meddelande: {alert['msg']}\n")
                f.write(f"  Värde:     {alert['val']}\n")
                f.write(f"  Förväntat: {alert['exp']}\n")
                f.write("\n")

        f.write("-" * 60 + "\n")
        f.write("Slut på rapport\n")

    log.info(f"Antal aktiva alerts: {len(active_alerts)}")
    if active_alerts:
        log.info("Alerts:")
        for alert in active_alerts[:10]:
            log.warning(f"  [{alert['source']}] {alert['msg']}")
        if len(active_alerts) > 10:
            log.info(f"  ... och {len(active_alerts) - 10} till")

    log.info(f"Rapport sparad till: {rapport_path}")


# ==============================================================================
#  RUN
# ==============================================================================
if __name__ == "__main__":
    # För att köra i terminal-läge (utan GUI):
    # run_terminal_mode()

    # För att köra i GUI-läge:
    app = OnyxTerminalTK()
    app.mainloop()
    # run_terminal_mode()
