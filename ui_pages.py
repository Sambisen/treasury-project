"""
Page classes for Onyx Terminal.
Contains all specific page views.
"""
import tkinter as tk
from tkinter import ttk

from config import THEME, CURRENT_MODE, RULES_DB, MARKET_STRUCTURE
from ui_components import OnyxButtonTK, MetricChipTK, DataTableTree
from utils import safe_float
from calculations import calc_implied_yield


class DashboardPage(tk.Frame):
    """Main dashboard with system status overview."""

    def __init__(self, master, app):
        super().__init__(master, bg=THEME["bg_panel"])
        self.app = app
        pad = CURRENT_MODE["pad"]

        header = tk.Frame(self, bg=THEME["bg_panel"])
        header.pack(fill="x", padx=pad, pady=(pad, 10))

        lbl = tk.Label(header, text="SYSTEM STATUS OVERVIEW", fg=THEME["muted"], bg=THEME["bg_panel"],
                       font=("Segoe UI", CURRENT_MODE["h2"], "bold"))
        lbl.pack(side="left")

        btns = tk.Frame(header, bg=THEME["bg_panel"])
        btns.pack(side="right")

        OnyxButtonTK(btns, "History", command=self.app.open_history_folder).pack(side="left", padx=6)
        OnyxButtonTK(btns, "GRSS Spreadsheets", command=self.app.open_stibor_folder).pack(side="left", padx=6)

        self.btn_update = OnyxButtonTK(btns, "UPDATE SYSTEM", command=self.app.refresh_data, variant="accent")
        self.btn_update.pack(side="left", padx=(12, 0))
        self.app.register_update_button(self.btn_update)

        grid = tk.Frame(self, bg=THEME["bg_panel"])
        grid.pack(fill="x", padx=pad, pady=(0, pad))

        self.card_spot = self._status_card(grid, "SPOT (EURNOK/USDNOK)", lambda: self.app.show_page("recon", focus="SPOT"))
        self.card_fwds = self._status_card(grid, "FX FORWARDS PIPS", lambda: self.app.show_page("recon", focus="FWDS"))
        self.card_ecp = self._status_card(grid, "ECP / INTERNAL", lambda: self.app.show_page("recon", focus="ALL"))
        self.card_days = self._status_card(grid, "DAYS CHECK", lambda: self.app.show_page("recon", focus="DAYS"))
        self.card_cells = self._status_card(grid, "EXCEL CELL CHECKS", lambda: self.app.show_page("recon", focus="CELLS"))
        self.card_weights = self._status_card(grid, "WEIGHTS (MONTHLY CONTROL)", lambda: self.app.show_page("recon", focus="WEIGHTS"))

        self.card_spot.grid(row=0, column=0, sticky="ew", padx=(0, 10), pady=(0, 10))
        self.card_fwds.grid(row=0, column=1, sticky="ew", padx=(10, 0), pady=(0, 10))
        self.card_ecp.grid(row=1, column=0, sticky="ew", padx=(0, 10), pady=(10, 0))
        self.card_days.grid(row=1, column=1, sticky="ew", padx=(10, 0), pady=(10, 0))
        self.card_cells.grid(row=2, column=0, sticky="ew", padx=(0, 10), pady=(12, 0))
        self.card_weights.grid(row=2, column=1, sticky="ew", padx=(10, 0), pady=(12, 0))

        grid.grid_columnconfigure(0, weight=1, uniform="g")
        grid.grid_columnconfigure(1, weight=1, uniform="g")

        # IMPLIED RATES SECTION
        implied_title = tk.Label(self, text="IMPLIED NOK RATES (WEIGHTED)", fg=THEME["muted"], bg=THEME["bg_panel"],
                                 font=("Segoe UI", CURRENT_MODE["h2"], "bold"))
        implied_title.pack(anchor="w", padx=pad, pady=(pad, 8))

        implied_chips = tk.Frame(self, bg=THEME["bg_panel"])
        implied_chips.pack(fill="x", padx=pad, pady=(0, pad))
        for i in range(4):
            implied_chips.grid_columnconfigure(i, weight=1, uniform="impl")

        self.chip_impl_1m = MetricChipTK(implied_chips, "1M IMPLIED", "-")
        self.chip_impl_2m = MetricChipTK(implied_chips, "2M IMPLIED", "-")
        self.chip_impl_3m = MetricChipTK(implied_chips, "3M IMPLIED", "-")
        self.chip_impl_6m = MetricChipTK(implied_chips, "6M IMPLIED", "-")

        self.chip_impl_1m.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.chip_impl_2m.grid(row=0, column=1, sticky="ew", padx=(0, 10))
        self.chip_impl_3m.grid(row=0, column=2, sticky="ew", padx=(0, 10))
        self.chip_impl_6m.grid(row=0, column=3, sticky="ew")

        title2 = tk.Label(self, text="ACTIVE ALERTS", fg=THEME["muted"], bg=THEME["bg_panel"],
                          font=("Segoe UI", CURRENT_MODE["h2"], "bold"))
        title2.pack(anchor="w", padx=pad, pady=(0, 8))

        self.alert_table = DataTableTree(self, columns=["EXCEL CELL", "REASON", "VALUE", "EXPECTED"],
                                         col_widths=[140, 420, 180, 180], height=10)
        self.alert_table.pack(fill="both", expand=True, padx=pad, pady=(0, pad))

        self.ok_panel = tk.Frame(self, bg=THEME["bg_card"], highlightthickness=1, highlightbackground=THEME["border"])
        self.ok_panel.pack(fill="both", expand=True, padx=pad, pady=(0, pad))
        self.ok_panel.pack_forget()

        ok_icon = tk.Label(self.ok_panel, text="✔", fg=THEME["good"], bg=THEME["bg_card"], font=("Segoe UI", 44, "bold"))
        ok_icon.pack(pady=(24, 8))
        ok_txt1 = tk.Label(self.ok_panel, text="SYSTEM VALIDATED", fg=THEME["text"], bg=THEME["bg_card"], font=("Segoe UI", 18, "bold"))
        ok_txt1.pack()
        ok_txt2 = tk.Label(self.ok_panel, text="NIBOR CONTRIBUTIONS ARE READY", fg=THEME["muted"], bg=THEME["bg_card"], font=("Segoe UI", 12))
        ok_txt2.pack(pady=(0, 24))

    def _status_card(self, master, title, details_cmd):
        card = tk.Frame(master, bg=THEME["bg_card"], highlightthickness=1, highlightbackground=THEME["border"])
        icon = tk.Label(card, text="●", fg=THEME["muted2"], bg=THEME["bg_card"], font=("Segoe UI", 20, "bold"))
        icon.grid(row=0, column=0, rowspan=2, padx=(16, 10), pady=16, sticky="w")

        lbl_title = tk.Label(card, text=title, fg=THEME["muted"], bg=THEME["bg_card"], font=("Segoe UI", CURRENT_MODE["small"], "bold"))
        lbl_title.grid(row=0, column=1, sticky="w", padx=(0, 12), pady=(14, 0))

        lbl_status = tk.Label(card, text="WAITING...", fg=THEME["text"], bg=THEME["bg_card"],
                              font=("Segoe UI", 16 if CURRENT_MODE["type"] == "OFFICE" else 14, "bold"))
        lbl_status.grid(row=1, column=1, sticky="w", padx=(0, 12), pady=(0, 14))

        lbl_sub = tk.Label(card, text="-", fg=THEME["muted2"], bg=THEME["bg_card"], font=("Segoe UI", CURRENT_MODE["small"]))
        lbl_sub.grid(row=2, column=1, sticky="w", padx=(0, 12), pady=(0, 14))

        btn = OnyxButtonTK(card, "DETAILS  →", command=details_cmd, variant="default")
        btn.configure(padx=10, pady=8, font=("Segoe UI", CURRENT_MODE["small"], "bold"))
        btn.grid(row=0, column=2, rowspan=3, padx=16, pady=16, sticky="e")

        card.grid_columnconfigure(1, weight=1)

        card._icon = icon
        card._status = lbl_status
        card._sub = lbl_sub
        return card

    def _apply_state(self, card, state: str, subtext: str = "—"):
        s = (state or "WAIT").upper()

        if s == "OK":
            card._icon.configure(text="✔", fg=THEME["good"])
            card._status.configure(text="OK", fg=THEME["good"])
            card.configure(highlightbackground=THEME["good"])
        elif s == "PENDING":
            card._icon.configure(text="!", fg=THEME["yellow"])
            card._status.configure(text="PENDING", fg=THEME["yellow"])
            card.configure(highlightbackground=THEME["yellow"])
        elif s == "ALERT":
            card._icon.configure(text="!", fg=THEME["warn"])
            card._status.configure(text="ALERT", fg=THEME["warn"])
            card.configure(highlightbackground=THEME["warn"])
        elif s == "FAIL":
            card._icon.configure(text="✘", fg=THEME["bad"])
            card._status.configure(text="DIFF / ERROR", fg=THEME["bad"])
            card.configure(highlightbackground=THEME["bad"])
        else:
            card._icon.configure(text="●", fg=THEME["muted2"])
            card._status.configure(text="WAITING...", fg=THEME["text"])
            card.configure(highlightbackground=THEME["border"])

        card._sub.configure(text=subtext)

    def update(self):
        gh = self.app.group_health or {}

        self._apply_state(self.card_spot, "OK" if self.app.status_spot else "FAIL", gh.get("SPOT", "—"))
        self._apply_state(self.card_fwds, "OK" if self.app.status_fwds else "FAIL", gh.get("FWDS", "—"))
        self._apply_state(self.card_ecp, "OK" if self.app.status_ecp else "FAIL", gh.get("ECP", "—"))
        self._apply_state(self.card_days, "OK" if self.app.status_days else "FAIL", gh.get("DAYS", "—"))
        self._apply_state(self.card_cells, "OK" if self.app.status_cells else "FAIL", gh.get("CELLS", "—"))
        self._apply_state(self.card_weights, self.app.weights_state, gh.get("WEIGHTS", "—"))

        # Update implied rates
        self._update_implied_rates()

        if not self.app.active_alerts:
            self.alert_table.pack_forget()
            self.ok_panel.pack(fill="both", expand=True)
        else:
            self.ok_panel.pack_forget()
            self.alert_table.pack(fill="both", expand=True)
            self.alert_table.clear()
            for a in self.app.active_alerts[:250]:
                self.alert_table.add_row([a["source"], a["msg"], a["val"], a["exp"]], style="bad")

    def _get_ticker_val(self, ticker):
        """Get price value from cached market data."""
        data = self.app.cached_market_data or {}
        inf = data.get(ticker)
        if inf:
            return float(inf.get("price", 0.0))
        return None

    def _get_weights(self):
        """Get weights from Excel engine or use defaults."""
        weights = {"USD": 0.45, "EUR": 0.05, "NOK": 0.50}
        if hasattr(self.app, 'excel_engine') and self.app.excel_engine.weights_ok:
            parsed = self.app.excel_engine.weights_cells_parsed
            if parsed.get("USD") is not None:
                weights["USD"] = parsed["USD"]
            if parsed.get("EUR") is not None:
                weights["EUR"] = parsed["EUR"]
            if parsed.get("NOK") is not None:
                weights["NOK"] = parsed["NOK"]
        return weights

    def _update_implied_rates(self):
        """Calculate and display weighted implied rates."""
        weights = self._get_weights()

        # Spots
        usd_spot = self._get_ticker_val("NOK F033 Curncy")
        eur_spot = self._get_ticker_val("NKEU F033 Curncy")

        # Excel days
        excel_days_data = self.app.current_days_data or {}

        tenors = [
            {"tenor": "1M", "key": "1m", "chip": self.chip_impl_1m,
             "usd_fwd": "NK1M F033 Curncy", "usd_rate": "USCM1M SWET Curncy", "usd_days": "NK1M TPSF Curncy",
             "eur_fwd": "NKEU1M F033 Curncy", "eur_rate": "EUCM1M SWET Curncy", "eur_days": "EURNOK1M TPSF Curncy",
             "nok_cm": "NKCM1M SWET Curncy"},
            {"tenor": "2M", "key": "2m", "chip": self.chip_impl_2m,
             "usd_fwd": "NK2M F033 Curncy", "usd_rate": "USCM2M SWET Curncy", "usd_days": "NK2M TPSF Curncy",
             "eur_fwd": "NKEU2M F033 Curncy", "eur_rate": "EUCM2M SWET Curncy", "eur_days": "EURNOK2M TPSF Curncy",
             "nok_cm": "NKCM2M SWET Curncy"},
            {"tenor": "3M", "key": "3m", "chip": self.chip_impl_3m,
             "usd_fwd": "NK3M F033 Curncy", "usd_rate": "USCM3M SWET Curncy", "usd_days": "NK3M TPSF Curncy",
             "eur_fwd": "NKEU3M F033 Curncy", "eur_rate": "EUCM3M SWET Curncy", "eur_days": "EURNOK3M TPSF Curncy",
             "nok_cm": "NKCM3M SWET Curncy"},
            {"tenor": "6M", "key": "6m", "chip": self.chip_impl_6m,
             "usd_fwd": "NK6M F033 Curncy", "usd_rate": "USCM6M SWET Curncy", "usd_days": "NK6M TPSF Curncy",
             "eur_fwd": "NKEU6M F033 Curncy", "eur_rate": "EUCM6M SWET Curncy", "eur_days": "EURNOK6M TPSF Curncy",
             "nok_cm": "NKCM6M SWET Curncy"},
        ]

        fallback_days = {"1m": 30, "2m": 58, "3m": 90, "6m": 181}

        for t in tenors:
            # Get days
            bbg_days = self._get_ticker_val(t["usd_days"])
            if bbg_days is None:
                bbg_days = fallback_days.get(t["key"])

            excel_days = safe_float(excel_days_data.get(t["key"]), None)
            if excel_days is None:
                excel_days = bbg_days

            # Get pips
            usd_fwd = self._get_ticker_val(t["usd_fwd"])
            eur_fwd = self._get_ticker_val(t["eur_fwd"])
            pips_usd = (usd_fwd - usd_spot) * 10000 if usd_fwd and usd_spot else None
            pips_eur = (eur_fwd - eur_spot) * 10000 if eur_fwd and eur_spot else None

            # Adjust pips for Excel days
            if pips_usd is not None and bbg_days and excel_days:
                pips_usd = (pips_usd / bbg_days) * excel_days
            if pips_eur is not None and bbg_days and excel_days:
                pips_eur = (pips_eur / bbg_days) * excel_days

            # Get rates
            usd_rate = self._get_ticker_val(t["usd_rate"])
            eur_rate = self._get_ticker_val(t["eur_rate"])
            nok_cm = self._get_ticker_val(t["nok_cm"])

            # Calculate implied
            impl_usd = calc_implied_yield(usd_spot, pips_usd, usd_rate, excel_days) if excel_days else None
            impl_eur = calc_implied_yield(eur_spot, pips_eur, eur_rate, excel_days) if excel_days else None

            # Calculate weighted total
            w_usd = impl_usd * weights["USD"] if impl_usd else None
            w_eur = impl_eur * weights["EUR"] if impl_eur else None
            w_nok = nok_cm * weights["NOK"] if nok_cm else None

            if w_usd is not None and w_eur is not None and w_nok is not None:
                total = w_usd + w_eur + w_nok
                t["chip"].set_value(f"{total:.4f}%")
            else:
                t["chip"].set_value("-")


class ReconPage(tk.Frame):
    """Model integrity check page."""

    def __init__(self, master, app):
        super().__init__(master, bg=THEME["bg_panel"])
        self.app = app
        pad = CURRENT_MODE["pad"]

        top = tk.Frame(self, bg=THEME["bg_panel"])
        top.pack(fill="x", padx=pad, pady=(pad, 10))

        tk.Label(top, text="MODEL INTEGRITY CHECK", fg=THEME["muted"], bg=THEME["bg_panel"],
                 font=("Segoe UI", CURRENT_MODE["h2"], "bold")).pack(side="left")

        self.mode_var = tk.StringVar(value="ALL")
        self.mode_combo = ttk.Combobox(top, textvariable=self.mode_var, values=["ALL", "SPOT", "FWDS", "DAYS", "CELLS", "WEIGHTS"], state="readonly", width=10)
        self.mode_combo.pack(side="right")
        self.mode_combo.bind("<<ComboboxSelected>>", lambda _e: self.on_mode_change())

        self.table = DataTableTree(self, columns=["CELL", "DESC", "MODEL", "MARKET/FILE", "DIFF", "STATUS"],
                                   col_widths=[110, 330, 170, 170, 140, 90], height=20)
        self.table.pack(fill="both", expand=True, padx=pad, pady=(0, pad))

    def on_mode_change(self):
        self.app.recon_view_mode = self.mode_var.get()
        self.update()

    def set_focus_mode(self, mode: str):
        if mode not in ["ALL", "SPOT", "FWDS", "DAYS", "CELLS", "WEIGHTS"]:
            mode = "ALL"
        self.mode_var.set(mode)
        self.app.recon_view_mode = mode
        self.update()

    def update(self):
        self.table.clear()
        rows = self.app.build_recon_rows(view=self.app.recon_view_mode)
        for r in rows:
            style = r.get("style", "normal")
            if style == "section":
                s = "section"
            elif style == "bad":
                s = "bad"
            elif style == "good":
                s = "good"
            elif style == "warn":
                s = "warn"
            elif style == "yellow":
                s = "yellow"
            else:
                s = "normal"
            self.table.add_row(r["values"], style=s)


class RulesPage(tk.Frame):
    """Validation rules database page."""

    def __init__(self, master, app):
        super().__init__(master, bg=THEME["bg_panel"])
        self.app = app
        pad = CURRENT_MODE["pad"]

        top = tk.Frame(self, bg=THEME["bg_panel"])
        top.pack(fill="x", padx=pad, pady=(pad, 10))

        tk.Label(top, text="ACTIVE VALIDATION RULES DATABASE", fg=THEME["muted"], bg=THEME["bg_panel"],
                 font=("Segoe UI", CURRENT_MODE["h2"], "bold")).pack(side="left")

        self.filter_var = tk.StringVar(value="ALL")
        self.filter_combo = ttk.Combobox(top, textvariable=self.filter_var,
                                         values=["ALL", "MATCHING", "ID CHECKS", "ROUNDING", "THRESHOLDS"],
                                         state="readonly", width=14)
        self.filter_combo.pack(side="right")
        self.filter_combo.bind("<<ComboboxSelected>>", lambda _e: self.update())

        self.table = DataTableTree(self, columns=["ID", "TOP CELL", "REF CELL", "LOGIC", "MESSAGE"],
                                   col_widths=[70, 110, 110, 160, 560], height=22)
        self.table.pack(fill="both", expand=True, padx=pad, pady=(0, pad))

    def update(self, *_):
        self.table.clear()
        cat = self.filter_var.get()

        for rule in RULES_DB:
            rid = int(rule[0])
            include = False
            if cat == "ALL":
                include = True
            elif cat == "MATCHING" and (1 <= rid <= 100):
                include = True
            elif cat == "ID CHECKS" and (101 <= rid <= 110):
                include = True
            elif cat == "ROUNDING" and (111 <= rid <= 118):
                include = True
            elif cat == "THRESHOLDS" and (119 <= rid <= 128):
                include = True

            if include:
                self.table.add_row(list(rule), style="normal")


class BloombergPage(tk.Frame):
    """Bloomberg market snapshot page."""

    def __init__(self, master, app):
        super().__init__(master, bg=THEME["bg_panel"])
        self.app = app
        pad = CURRENT_MODE["pad"]

        top = tk.Frame(self, bg=THEME["bg_panel"])
        top.pack(fill="x", padx=pad, pady=(pad, 10))

        tk.Label(top, text="BLOOMBERG MARKET SNAPSHOT", fg=THEME["muted"], bg=THEME["bg_panel"],
                 font=("Segoe UI", CURRENT_MODE["h2"], "bold")).pack(side="left")

        self.btn_refresh = OnyxButtonTK(top, "REFRESH", command=self.app.refresh_data, variant="accent")
        self.btn_refresh.pack(side="right")
        self.app.register_update_button(self.btn_refresh)

        chips = tk.Frame(self, bg=THEME["bg_panel"])
        chips.pack(fill="x", padx=pad, pady=(0, 12))
        for i in range(5):
            chips.grid_columnconfigure(i, weight=1, uniform="d")

        self.chip_1w = MetricChipTK(chips, "1W DAYS", "-")
        self.chip_1m = MetricChipTK(chips, "1M DAYS", "-")
        self.chip_2m = MetricChipTK(chips, "2M DAYS", "-")
        self.chip_3m = MetricChipTK(chips, "3M DAYS", "-")
        self.chip_6m = MetricChipTK(chips, "6M DAYS", "-")

        self.chip_1w.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.chip_1m.grid(row=0, column=1, sticky="ew", padx=(0, 10))
        self.chip_2m.grid(row=0, column=2, sticky="ew", padx=(0, 10))
        self.chip_3m.grid(row=0, column=3, sticky="ew", padx=(0, 10))
        self.chip_6m.grid(row=0, column=4, sticky="ew")

        self.table = DataTableTree(self, columns=["GROUP", "NAME", "PRICE", "CHG", "TIME"],
                                   col_widths=[200, 260, 160, 140, 260], height=20)
        self.table.pack(fill="both", expand=True, padx=pad, pady=(0, pad))

    def update(self):
        d = self.app.current_days_data or {}
        self.chip_1w.set_value(d.get("1w", "-"))
        self.chip_1m.set_value(d.get("1m", "-"))
        self.chip_2m.set_value(d.get("2m", "-"))
        self.chip_3m.set_value(d.get("3m", "-"))
        self.chip_6m.set_value(d.get("6m", "-"))

        self.table.clear()
        data = self.app.cached_market_data or {}

        for group_name, items in MARKET_STRUCTURE.items():
            self.table.add_row([group_name, "", "", "", ""], style="section")
            for ticker, label in items:
                inf = data.get(ticker)
                price = f"{inf['price']:,.6f}" if inf else "-"
                chg = f"{inf['change']:+,.6f}" if inf else "-"
                tms = inf.get("time", "-") if inf else "-"
                self.table.add_row([group_name, label, price, chg, tms], style="normal")


class NiborDaysPage(tk.Frame):
    """Nibor days search page."""

    def __init__(self, master, app):
        super().__init__(master, bg=THEME["bg_panel"])
        self.app = app
        pad = CURRENT_MODE["pad"]

        top = tk.Frame(self, bg=THEME["bg_panel"])
        top.pack(fill="x", padx=pad, pady=(pad, 10))

        tk.Label(top, text="NIBOR DAYS (FUTURE) — SEARCH", fg=THEME["muted"], bg=THEME["bg_panel"],
                 font=("Segoe UI", CURRENT_MODE["h2"], "bold")).pack(side="left")

        self.search_var = tk.StringVar(value="")
        self.search_entry = tk.Entry(top, textvariable=self.search_var, bg=THEME["chip2"], fg=THEME["text"],
                                     insertbackground=THEME["text"], relief="flat", font=("Segoe UI", CURRENT_MODE["body"]), width=28)
        self.search_entry.pack(side="right")
        self._search_after_id = None
        self.search_var.trace_add("write", lambda *_: self._debounced_update())

        self.table = DataTableTree(self, columns=["date", "1w_Days", "1m_Days", "2m_Days", "3m_Days", "6m_Days"],
                                   col_widths=[160, 110, 110, 110, 110, 110], height=24)
        self.table.pack(fill="both", expand=True, padx=pad, pady=(0, pad))

    def _debounced_update(self):
        if self._search_after_id is not None:
            try:
                self.after_cancel(self._search_after_id)
            except Exception:
                pass
        self._search_after_id = self.after(200, self.update)

    def update(self):
        self.table.clear()
        df = self.app.excel_engine.get_future_days_data(limit_rows=400)
        if df.empty:
            return

        cols = ["date", "1w_Days", "1m_Days", "2m_Days", "3m_Days", "6m_Days"]
        for c in cols:
            if c not in df.columns:
                df[c] = ""

        q = (self.search_var.get() or "").strip().lower()
        if q:
            df2 = df[df.apply(lambda r: r.astype(str).str.lower().str.contains(q).any(), axis=1)].copy()
        else:
            df2 = df

        for _, r in df2.head(400).iterrows():
            self.table.add_row([r.get(c, "") for c in cols], style="normal")


class NokImpliedPage(tk.Frame):
    """NOK implied yield calculation page with two sections: Bloomberg CM and Excel CM."""

    def __init__(self, master, app):
        super().__init__(master, bg=THEME["bg_panel"])
        self.app = app
        pad = CURRENT_MODE["pad"]

        # Create scrollable canvas
        canvas = tk.Canvas(self, bg=THEME["bg_panel"], highlightthickness=0)
        scrollbar = tk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.scroll_frame = tk.Frame(canvas, bg=THEME["bg_panel"])

        self.scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        # Bind mousewheel
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

        container = self.scroll_frame

        # Top header with title and button
        top = tk.Frame(container, bg=THEME["bg_panel"])
        top.pack(fill="x", padx=pad, pady=(pad, 5))

        tk.Label(top, text="IMPLIED NOK YIELD", fg=THEME["muted"], bg=THEME["bg_panel"],
                 font=("Segoe UI", CURRENT_MODE["h2"], "bold")).pack(side="left")

        OnyxButtonTK(top, "Recalculate", command=self.update, variant="default").pack(side="right")

        # Weights display
        self.weights_frame = tk.Frame(container, bg=THEME["bg_panel"])
        self.weights_frame.pack(fill="x", padx=pad, pady=(0, 10))

        self.weights_label = tk.Label(self.weights_frame, text="VIKTER:  USD = 45%  |  EUR = 5%  |  NOK = 50%",
                                      fg=THEME["accent"], bg=THEME["bg_panel"],
                                      font=("Segoe UI", CURRENT_MODE["body"], "bold"))
        self.weights_label.pack(side="left")

        # ============ SECTION 1: Bloomberg CM + Excel Days ============
        tk.Label(container, text="SEKTION 1: BLOOMBERG CM + EXCEL DAGAR", fg=THEME["good"], bg=THEME["bg_panel"],
                 font=("Segoe UI", CURRENT_MODE["body"], "bold")).pack(anchor="w", padx=pad, pady=(10, 5))

        # USDNOK Table (Section 1)
        tk.Label(container, text="USDNOK", fg=THEME["muted"], bg=THEME["bg_panel"],
                 font=("Segoe UI", CURRENT_MODE["small"], "bold")).pack(anchor="w", padx=pad)

        self.usd_table_bbg = DataTableTree(container, columns=[
            "TENOR", "USD RATE", "BBG DAYS", "EXC DAYS", "PIPS BBG", "PIPS EXC", "IMPLIED", "NOK CM"
        ], col_widths=[50, 70, 70, 70, 80, 80, 80, 70], height=4)
        self.usd_table_bbg.pack(fill="x", padx=pad, pady=(0, 5))

        # EURNOK Table (Section 1)
        tk.Label(container, text="EURNOK", fg=THEME["muted"], bg=THEME["bg_panel"],
                 font=("Segoe UI", CURRENT_MODE["small"], "bold")).pack(anchor="w", padx=pad)

        self.eur_table_bbg = DataTableTree(container, columns=[
            "TENOR", "EUR RATE", "BBG DAYS", "EXC DAYS", "PIPS BBG", "PIPS EXC", "IMPLIED", "NOK CM"
        ], col_widths=[50, 70, 70, 70, 80, 80, 80, 70], height=4)
        self.eur_table_bbg.pack(fill="x", padx=pad, pady=(0, 5))

        # Weighted (Section 1)
        tk.Label(container, text="VIKTAD (BBG CM)", fg=THEME["accent"], bg=THEME["bg_panel"],
                 font=("Segoe UI", CURRENT_MODE["small"], "bold")).pack(anchor="w", padx=pad)

        self.weighted_table_bbg = DataTableTree(container, columns=[
            "TENOR", "USD IMPL", "× 45%", "EUR IMPL", "× 5%", "NOK CM", "× 50%", "TOTAL"
        ], col_widths=[50, 70, 60, 70, 60, 70, 60, 80], height=4)
        self.weighted_table_bbg.pack(fill="x", padx=pad, pady=(0, 15))

        # ============ SECTION 2: Excel CM + Bloomberg Days ============
        tk.Label(container, text="SEKTION 2: EXCEL CM + BLOOMBERG DAGAR", fg=THEME["warn"], bg=THEME["bg_panel"],
                 font=("Segoe UI", CURRENT_MODE["body"], "bold")).pack(anchor="w", padx=pad, pady=(10, 5))

        # USDNOK Table (Section 2)
        tk.Label(container, text="USDNOK", fg=THEME["muted"], bg=THEME["bg_panel"],
                 font=("Segoe UI", CURRENT_MODE["small"], "bold")).pack(anchor="w", padx=pad)

        self.usd_table_exc = DataTableTree(container, columns=[
            "TENOR", "USD RATE", "BBG DAYS", "PIPS BBG", "IMPLIED", "NOK CM"
        ], col_widths=[50, 70, 70, 90, 90, 70], height=4)
        self.usd_table_exc.pack(fill="x", padx=pad, pady=(0, 5))

        # EURNOK Table (Section 2)
        tk.Label(container, text="EURNOK", fg=THEME["muted"], bg=THEME["bg_panel"],
                 font=("Segoe UI", CURRENT_MODE["small"], "bold")).pack(anchor="w", padx=pad)

        self.eur_table_exc = DataTableTree(container, columns=[
            "TENOR", "EUR RATE", "BBG DAYS", "PIPS BBG", "IMPLIED", "NOK CM"
        ], col_widths=[50, 70, 70, 90, 90, 70], height=4)
        self.eur_table_exc.pack(fill="x", padx=pad, pady=(0, 5))

        # Weighted (Section 2)
        tk.Label(container, text="VIKTAD (EXCEL CM)", fg=THEME["accent"], bg=THEME["bg_panel"],
                 font=("Segoe UI", CURRENT_MODE["small"], "bold")).pack(anchor="w", padx=pad)

        self.weighted_table_exc = DataTableTree(container, columns=[
            "TENOR", "USD IMPL", "× 45%", "EUR IMPL", "× 5%", "NOK CM", "× 50%", "TOTAL"
        ], col_widths=[50, 70, 60, 70, 60, 70, 60, 80], height=4)
        self.weighted_table_exc.pack(fill="x", padx=pad, pady=(0, pad))

    def _get_ticker_val(self, ticker):
        """Get price value from cached market data."""
        data = self.app.cached_market_data or {}
        inf = data.get(ticker)
        if inf:
            return float(inf.get("price", 0.0))
        return None

    def _get_spot_price(self, fwd_ticker, spot_ticker):
        """Get forward pips (forward price - spot price) * 10000."""
        fwd = self._get_ticker_val(fwd_ticker)
        spot = self._get_ticker_val(spot_ticker)
        if fwd is not None and spot is not None:
            return (fwd - spot) * 10000
        return None

    def _get_weights(self):
        """Get weights from Excel engine or use defaults."""
        weights = {"USD": 0.45, "EUR": 0.05, "NOK": 0.50}
        if hasattr(self.app, 'excel_engine') and self.app.excel_engine.weights_ok:
            parsed = self.app.excel_engine.weights_cells_parsed
            if parsed.get("USD") is not None:
                weights["USD"] = parsed["USD"]
            if parsed.get("EUR") is not None:
                weights["EUR"] = parsed["EUR"]
            if parsed.get("NOK") is not None:
                weights["NOK"] = parsed["NOK"]
        return weights

    def _get_excel_cm_rates(self):
        """Get CM rates from Excel file."""
        if hasattr(self.app, 'excel_engine'):
            return self.app.excel_engine.excel_cm_rates or {}
        return {}

    def update(self):
        # Clear all tables
        self.usd_table_bbg.clear()
        self.eur_table_bbg.clear()
        self.weighted_table_bbg.clear()
        self.usd_table_exc.clear()
        self.eur_table_exc.clear()
        self.weighted_table_exc.clear()

        # Get weights
        weights = self._get_weights()
        self.weights_label.config(
            text=f"VIKTER:  USD = {weights['USD']*100:.0f}%  |  EUR = {weights['EUR']*100:.0f}%  |  NOK = {weights['NOK']*100:.0f}%"
        )

        # Get Excel CM rates
        excel_cm = self._get_excel_cm_rates()

        # Spots
        usd_spot = self._get_ticker_val("NOK F033 Curncy")
        eur_spot = self._get_ticker_val("NKEU F033 Curncy")

        # Excel days from Nibor days file
        excel_days_data = self.app.current_days_data or {}

        # Tenor configuration
        tenors = [
            {"tenor": "1M", "key": "1m",
             "usd_fwd": "NK1M F033 Curncy", "usd_rate_bbg": "USCM1M SWET Curncy", "usd_days_bbg": "NK1M TPSF Curncy",
             "eur_fwd": "NKEU1M F033 Curncy", "eur_rate_bbg": "EUCM1M SWET Curncy", "eur_days_bbg": "EURNOK1M TPSF Curncy",
             "nok_cm": "NKCM1M SWET Curncy", "usd_rate_exc": "USD_1M", "eur_rate_exc": "EUR_1M"},
            {"tenor": "2M", "key": "2m",
             "usd_fwd": "NK2M F033 Curncy", "usd_rate_bbg": "USCM2M SWET Curncy", "usd_days_bbg": "NK2M TPSF Curncy",
             "eur_fwd": "NKEU2M F033 Curncy", "eur_rate_bbg": "EUCM2M SWET Curncy", "eur_days_bbg": "EURNOK2M TPSF Curncy",
             "nok_cm": "NKCM2M SWET Curncy", "usd_rate_exc": "USD_2M", "eur_rate_exc": "EUR_2M"},
            {"tenor": "3M", "key": "3m",
             "usd_fwd": "NK3M F033 Curncy", "usd_rate_bbg": "USCM3M SWET Curncy", "usd_days_bbg": "NK3M TPSF Curncy",
             "eur_fwd": "NKEU3M F033 Curncy", "eur_rate_bbg": "EUCM3M SWET Curncy", "eur_days_bbg": "EURNOK3M TPSF Curncy",
             "nok_cm": "NKCM3M SWET Curncy", "usd_rate_exc": "USD_3M", "eur_rate_exc": "EUR_3M"},
            {"tenor": "6M", "key": "6m",
             "usd_fwd": "NK6M F033 Curncy", "usd_rate_bbg": "USCM6M SWET Curncy", "usd_days_bbg": "NK6M TPSF Curncy",
             "eur_fwd": "NKEU6M F033 Curncy", "eur_rate_bbg": "EUCM6M SWET Curncy", "eur_days_bbg": "EURNOK6M TPSF Curncy",
             "nok_cm": "NKCM6M SWET Curncy", "usd_rate_exc": "USD_6M", "eur_rate_exc": "EUR_6M"},
        ]

        fallback_bbg_days = {"1m": 30, "2m": 58, "3m": 90, "6m": 181}

        def fmt_days(v):
            return str(int(v)) if v is not None else "-"

        def fmt_pips(v):
            return f"{v:.3f}" if v is not None else "-"

        def fmt_rate(v):
            return f"{v:.2f}%" if v is not None else "-"

        def fmt_impl(v):
            return f"{v:.4f}%" if v is not None else "-"

        # Store implied values for weighted calculations
        implied_data_bbg = []
        implied_data_exc = []

        for t in tenors:
            # Bloomberg days
            bbg_days_usd = self._get_ticker_val(t["usd_days_bbg"])
            if bbg_days_usd is None:
                bbg_days_usd = fallback_bbg_days.get(t["key"])

            bbg_days_eur = self._get_ticker_val(t["eur_days_bbg"])
            if bbg_days_eur is None:
                bbg_days_eur = fallback_bbg_days.get(t["key"])

            # Excel days
            excel_days = safe_float(excel_days_data.get(f"{t['key']}_Days"), None)
            if excel_days is None:
                excel_days = safe_float(excel_days_data.get(t["key"]), None)
            if excel_days is None:
                excel_days = bbg_days_usd

            # Bloomberg pips
            pips_bbg_usd = self._get_spot_price(t["usd_fwd"], "NOK F033 Curncy")
            pips_bbg_eur = self._get_spot_price(t["eur_fwd"], "NKEU F033 Curncy")

            # NOK CM (same for both sections)
            nok_cm = self._get_ticker_val(t["nok_cm"]) if t["nok_cm"] else None

            # ============ SECTION 1: Bloomberg CM + Excel Days ============
            # USD: adjust pips for Excel days
            pips_exc_usd = None
            if pips_bbg_usd is not None and bbg_days_usd and excel_days:
                pips_exc_usd = (pips_bbg_usd / bbg_days_usd) * excel_days

            usd_rate_bbg = self._get_ticker_val(t["usd_rate_bbg"]) if t["usd_rate_bbg"] else None
            impl_usd_bbg = calc_implied_yield(usd_spot, pips_exc_usd, usd_rate_bbg, excel_days) if excel_days else None

            # EUR: adjust pips for Excel days
            pips_exc_eur = None
            if pips_bbg_eur is not None and bbg_days_eur and excel_days:
                pips_exc_eur = (pips_bbg_eur / bbg_days_eur) * excel_days

            eur_rate_bbg = self._get_ticker_val(t["eur_rate_bbg"]) if t["eur_rate_bbg"] else None
            impl_eur_bbg = calc_implied_yield(eur_spot, pips_exc_eur, eur_rate_bbg, excel_days) if excel_days else None

            # Add rows to Section 1 tables
            self.usd_table_bbg.add_row([
                t["tenor"], fmt_rate(usd_rate_bbg),
                fmt_days(bbg_days_usd), fmt_days(excel_days),
                fmt_pips(pips_bbg_usd), fmt_pips(pips_exc_usd),
                fmt_impl(impl_usd_bbg), fmt_rate(nok_cm)
            ], style="normal")

            self.eur_table_bbg.add_row([
                t["tenor"], fmt_rate(eur_rate_bbg),
                fmt_days(bbg_days_eur), fmt_days(excel_days),
                fmt_pips(pips_bbg_eur), fmt_pips(pips_exc_eur),
                fmt_impl(impl_eur_bbg), fmt_rate(nok_cm)
            ], style="normal")

            implied_data_bbg.append({
                "tenor": t["tenor"], "impl_usd": impl_usd_bbg, "impl_eur": impl_eur_bbg, "nok_cm": nok_cm
            })

            # ============ SECTION 2: Excel CM + Bloomberg Days ============
            # Use Bloomberg days and pips directly (no adjustment)
            usd_rate_exc = excel_cm.get(t["usd_rate_exc"])
            eur_rate_exc = excel_cm.get(t["eur_rate_exc"])

            impl_usd_exc = calc_implied_yield(usd_spot, pips_bbg_usd, usd_rate_exc, bbg_days_usd) if bbg_days_usd else None
            impl_eur_exc = calc_implied_yield(eur_spot, pips_bbg_eur, eur_rate_exc, bbg_days_eur) if bbg_days_eur else None

            # Add rows to Section 2 tables
            self.usd_table_exc.add_row([
                t["tenor"], fmt_rate(usd_rate_exc),
                fmt_days(bbg_days_usd), fmt_pips(pips_bbg_usd),
                fmt_impl(impl_usd_exc), fmt_rate(nok_cm)
            ], style="normal")

            self.eur_table_exc.add_row([
                t["tenor"], fmt_rate(eur_rate_exc),
                fmt_days(bbg_days_eur), fmt_pips(pips_bbg_eur),
                fmt_impl(impl_eur_exc), fmt_rate(nok_cm)
            ], style="normal")

            implied_data_exc.append({
                "tenor": t["tenor"], "impl_usd": impl_usd_exc, "impl_eur": impl_eur_exc, "nok_cm": nok_cm
            })

        # Add weighted rows for Section 1
        for d in implied_data_bbg:
            w_usd = d["impl_usd"] * weights["USD"] if d["impl_usd"] else None
            w_eur = d["impl_eur"] * weights["EUR"] if d["impl_eur"] else None
            w_nok = d["nok_cm"] * weights["NOK"] if d["nok_cm"] else None
            total = (w_usd or 0) + (w_eur or 0) + (w_nok or 0) if all([w_usd, w_eur, w_nok]) else None

            self.weighted_table_bbg.add_row([
                d["tenor"], fmt_impl(d["impl_usd"]), fmt_impl(w_usd),
                fmt_impl(d["impl_eur"]), fmt_impl(w_eur),
                fmt_rate(d["nok_cm"]), fmt_impl(w_nok), fmt_impl(total)
            ], style="normal")

        # Add weighted rows for Section 2
        for d in implied_data_exc:
            w_usd = d["impl_usd"] * weights["USD"] if d["impl_usd"] else None
            w_eur = d["impl_eur"] * weights["EUR"] if d["impl_eur"] else None
            w_nok = d["nok_cm"] * weights["NOK"] if d["nok_cm"] else None
            total = (w_usd or 0) + (w_eur or 0) + (w_nok or 0) if all([w_usd, w_eur, w_nok]) else None

            self.weighted_table_exc.add_row([
                d["tenor"], fmt_impl(d["impl_usd"]), fmt_impl(w_usd),
                fmt_impl(d["impl_eur"]), fmt_impl(w_eur),
                fmt_rate(d["nok_cm"]), fmt_impl(w_nok), fmt_impl(total)
            ], style="normal")


class NiborMetaDataPage(tk.Frame):
    """Nibor meta data page."""

    def __init__(self, master, app):
        super().__init__(master, bg=THEME["bg_panel"])
        self.app = app
        pad = CURRENT_MODE["pad"]

        top = tk.Frame(self, bg=THEME["bg_panel"])
        top.pack(fill="x", padx=pad, pady=(pad, 10))

        tk.Label(top, text="NIBOR META DATA", fg=THEME["muted"], bg=THEME["bg_panel"],
                 font=("Segoe UI", CURRENT_MODE["h2"], "bold")).pack(side="left")

        OnyxButtonTK(top, "Refresh Meta", command=self.update, variant="default").pack(side="right")

        self.table = DataTableTree(self, columns=["ATTRIBUTE", "VALUE", "SOURCE", "STATUS"],
                                   col_widths=[200, 300, 150, 100], height=20)
        self.table.pack(fill="both", expand=True, padx=pad, pady=(0, pad))

    def update(self):
        self.table.clear()
        self.table.add_row(["Calculation Agent", "GRSS", "System", "Active"], style="normal")
        self.table.add_row(["Fixing Time", "12:00 CET", "Config", "OK"], style="normal")
        self.table.add_row(["Publication Delay", "24h (T+1)", "License", "Active"], style="normal")
        self.table.add_row(["Panel Banks", "6", "GRSS Feed", "OK"], style="normal")
        self.table.add_row(["Algorithm", "Waterfall Level 1", "Manual", "Info"], style="section")
