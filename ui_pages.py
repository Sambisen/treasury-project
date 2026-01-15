"""
Page classes for Onyx Terminal.
Contains all specific page views.
"""
import tkinter as tk
from tkinter import ttk

from config import THEME, CURRENT_MODE, RULES_DB, MARKET_STRUCTURE
from ui_components import OnyxButtonTK, MetricChipTK, DataTableTree, TimeSeriesChartTK, ClickableDataTableTree, MatchDetailPopup, MatchCriteriaPopup
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

        # Match button that shows criteria popup with results
        self.btn_match = OnyxButtonTK(btns, "MATCH", command=self._on_match_click, variant="accent")
        self.btn_match.pack(side="left", padx=(12, 0))
        self.app.register_update_button(self.btn_match)

        self.btn_update = OnyxButtonTK(btns, "UPDATE SYSTEM", command=self.app.refresh_data, variant="default")
        self.btn_update.pack(side="left", padx=(6, 0))
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

        # ============================================================================
        # FUNDING RATES TABLE
        # ============================================================================
        funding_title = tk.Label(self, text="FUNDING RATES", fg=THEME["muted"],
                                bg=THEME["bg_panel"],
                                font=("Segoe UI", CURRENT_MODE["h2"], "bold"))
        funding_title.pack(anchor="w", padx=pad, pady=(pad, 8))

        self.funding_table_frame = tk.Frame(self, bg=THEME["bg_card"],
                                           highlightthickness=1,
                                           highlightbackground=THEME["border"])
        self.funding_table_frame.pack(fill="x", padx=pad, pady=(0, pad))

        # Headers
        headers = ["TENOR", "FUNDING RATE", "SPREAD", "FINAL RATE", "CHANGE"]
        header_frame = tk.Frame(self.funding_table_frame, bg=THEME["bg_card_2"])
        header_frame.grid(row=0, column=0, columnspan=5, sticky="ew", padx=10, pady=(10, 5))

        for i, header_text in enumerate(headers):
            tk.Label(header_frame, text=header_text, fg=THEME["muted"],
                    bg=THEME["bg_card_2"],
                    font=("Segoe UI", CURRENT_MODE["body"], "bold"),
                    width=15 if i == 0 else 18).grid(row=0, column=i, padx=5,
                                                     sticky="w" if i == 0 else "e")

        # Create rows
        self.funding_cells = {}
        tenors = [
            {"key": "1w", "label": "1W"},
            {"key": "1m", "label": "1M"},
            {"key": "2m", "label": "2M"},
            {"key": "3m", "label": "3M"},
            {"key": "6m", "label": "6M"}
        ]

        for row_idx, tenor in enumerate(tenors, start=1):
            tk.Label(self.funding_table_frame, text=tenor["label"],
                    fg=THEME["text"], bg=THEME["bg_card"],
                    font=("Segoe UI", CURRENT_MODE["body"], "bold"),
                    width=15, anchor="w").grid(row=row_idx, column=0,
                                               padx=10, pady=8, sticky="w")

            cells = {}
            for col_idx, cell_type in enumerate(["funding", "spread", "final", "change"], start=1):
                # Determine color based on cell type
                if cell_type == "final":
                    fg_color = THEME["accent"]
                elif cell_type == "change":
                    fg_color = THEME["text"]  # Will be set dynamically based on +/-
                else:
                    fg_color = THEME["text"]

                cell_label = tk.Label(self.funding_table_frame, text="-",
                                    fg=fg_color,
                                    bg=THEME["chip"] if cell_type not in ["spread", "change"] else THEME["bg_card_2"],
                                    font=("Consolas", CURRENT_MODE["body"], "bold"),
                                    width=18,
                                    cursor="hand2" if cell_type not in ["spread", "change"] else "arrow",
                                    relief="raised" if cell_type not in ["spread", "change"] else "flat",
                                    bd=1 if cell_type not in ["spread", "change"] else 0,
                                    anchor="e")
                cell_label.grid(row=row_idx, column=col_idx, padx=5, pady=8, sticky="e")

                if cell_type not in ["spread", "change"]:
                    cell_label.bind("<Button-1>",
                                  lambda e, t=tenor["key"]: self._show_funding_details(t))
                    cell_label.bind("<Enter>",
                                  lambda e, lbl=cell_label: lbl.configure(bg=THEME["chip2"])
                                  if lbl["bg"] == THEME["chip"] else None)
                    cell_label.bind("<Leave>",
                                  lambda e, lbl=cell_label: lbl.configure(bg=THEME["chip"])
                                  if lbl["bg"] == THEME["chip2"] else None)

                cells[cell_type] = cell_label

            self.funding_cells[tenor["key"]] = cells

        # Historical Nibor Chart
        chart_title = tk.Label(self, text="NIBOR HISTORICAL TRENDS (30 DAYS)",
                              fg=THEME["muted"], bg=THEME["bg_panel"],
                              font=("Segoe UI", CURRENT_MODE["h2"], "bold"))
        chart_title.pack(anchor="w", padx=pad, pady=(pad, 8))

        self.nibor_chart = TimeSeriesChartTK(self, title="NIBOR RATES - 30 DAY TREND")
        self.nibor_chart.pack(fill="both", expand=True, padx=pad, pady=(0, 12))

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

    def _on_match_click(self):
        """Handle Match button click - refresh data and show criteria popup."""
        # First refresh the data
        self.app.refresh_data()
        # Show the criteria popup after a delay to allow data to load
        self.after(500, self._show_match_popup)

    def _show_match_popup(self):
        """Show the match criteria popup with current statistics."""
        if self.app._busy:
            # Still loading, check again later
            self.after(500, self._show_match_popup)
            return
        # Show the popup with criteria stats
        MatchCriteriaPopup(self, self.app.criteria_stats)

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

    def _show_funding_details(self, tenor_key):
        """Show detailed breakdown popup for selected tenor."""
        if not hasattr(self.app, 'funding_calc_data') or not self.app.funding_calc_data:
            return

        data = self.app.funding_calc_data.get(tenor_key)
        if not data:
            return

        # Create popup
        popup = tk.Toplevel(self)
        popup.title(f"Funding Rate Breakdown - {tenor_key.upper()}")
        popup.geometry("750x600")
        popup.configure(bg=THEME["bg_panel"])
        popup.transient(self)
        popup.grab_set()

        # Title
        tk.Label(popup, text=f"{tenor_key.upper()} TENOR - DETAILED BREAKDOWN",
                fg=THEME["accent"], bg=THEME["bg_panel"],
                font=("Segoe UI", 18, "bold")).pack(pady=20)

        # Content frame with all details
        content = tk.Frame(popup, bg=THEME["bg_card"],
                          highlightthickness=1, highlightbackground=THEME["border"])
        content.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # Helper function to add section
        def add_section(title, items, y_offset):
            tk.Label(content, text=title, fg=THEME["accent"], bg=THEME["bg_card"],
                    font=("Segoe UI", 12, "bold")).place(x=20, y=y_offset)

            for i, (label, value) in enumerate(items):
                y = y_offset + 30 + (i * 25)
                tk.Label(content, text=label, fg=THEME["muted"], bg=THEME["bg_card"],
                        font=("Segoe UI", 10)).place(x=40, y=y)
                tk.Label(content, text=value, fg=THEME["text"], bg=THEME["bg_card"],
                        font=("Consolas", 10, "bold")).place(x=250, y=y)

        # EUR IMPLIED section
        eur_items = [
            ("Spot Rate:", f"{data.get('eur_spot', 0):.4f}" if data.get('eur_spot') is not None else "N/A"),
            ("Forward Pips:", f"{data.get('eur_pips', 0):.3f}" if data.get('eur_pips') is not None else "N/A"),
            ("EUR Rate:", f"{data.get('eur_rate', 0):.2f}%" if data.get('eur_rate') is not None else "N/A"),
            ("Days:", str(int(data.get('eur_days', 0))) if data.get('eur_days') is not None else "N/A"),
            ("IMPLIED:", f"{data.get('eur_impl', 0):.4f}%" if data.get('eur_impl') is not None else "N/A"),
        ]
        add_section("EUR IMPLIED", eur_items, 20)

        # USD IMPLIED section
        usd_items = [
            ("Spot Rate:", f"{data.get('usd_spot', 0):.4f}" if data.get('usd_spot') is not None else "N/A"),
            ("Forward Pips:", f"{data.get('usd_pips', 0):.3f}" if data.get('usd_pips') is not None else "N/A"),
            ("USD Rate:", f"{data.get('usd_rate', 0):.2f}%" if data.get('usd_rate') is not None else "N/A"),
            ("Days:", str(int(data.get('usd_days', 0))) if data.get('usd_days') is not None else "N/A"),
            ("IMPLIED:", f"{data.get('usd_impl', 0):.4f}%" if data.get('usd_impl') is not None else "N/A"),
        ]
        add_section("USD IMPLIED", usd_items, 180)

        # NOK CM section
        nok_items = [
            ("NOK CM Rate:", f"{data.get('nok_cm', 0):.2f}%" if data.get('nok_cm') is not None else "N/A"),
        ]
        add_section("NOK CM", nok_items, 340)

        # Weights section
        weights = data.get('weights', {})
        weight_items = [
            ("USD Weight:", f"{weights.get('USD', 0)*100:.0f}%"),
            ("EUR Weight:", f"{weights.get('EUR', 0)*100:.0f}%"),
            ("NOK Weight:", f"{weights.get('NOK', 0)*100:.0f}%"),
        ]
        add_section("WEIGHTS", weight_items, 390)

        # Calculation section
        calc_items = [
            ("Funding Rate:", f"{data.get('funding_rate', 0):.4f}%" if data.get('funding_rate') is not None else "N/A"),
            ("Spread:", f"{data.get('spread', 0):.2f}%"),
            ("Final Rate:", f"{data.get('final_rate', 0):.4f}%" if data.get('final_rate') is not None else "N/A"),
        ]
        add_section("CALCULATION", calc_items, 480)

        # Close button
        from ui_components import OnyxButtonTK
        OnyxButtonTK(popup, "Close", command=popup.destroy,
                    variant="default").pack(pady=15)

    def update(self):
        gh = self.app.group_health or {}

        self._apply_state(self.card_spot, "OK" if self.app.status_spot else "FAIL", gh.get("SPOT", "—"))
        self._apply_state(self.card_fwds, "OK" if self.app.status_fwds else "FAIL", gh.get("FWDS", "—"))
        self._apply_state(self.card_ecp, "OK" if self.app.status_ecp else "FAIL", gh.get("ECP", "—"))
        self._apply_state(self.card_days, "OK" if self.app.status_days else "FAIL", gh.get("DAYS", "—"))
        self._apply_state(self.card_cells, "OK" if self.app.status_cells else "FAIL", gh.get("CELLS", "—"))
        self._apply_state(self.card_weights, self.app.weights_state, gh.get("WEIGHTS", "—"))

        # Update funding rates table
        self._update_funding_rates()

        # Update historical chart
        self._update_nibor_chart()

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

    def _update_funding_rates(self):
        """Calculate and display funding rates table."""
        from config import FUNDING_SPREADS
        from calculations import calc_funding_rate

        # Check if we have impl_calc_data from NokImpliedPage
        if not hasattr(self.app, 'impl_calc_data'):
            # Initialize empty funding data
            self.app.funding_calc_data = {}
            for tenor_key in ["1w", "1m", "2m", "3m", "6m"]:
                cells = self.funding_cells.get(tenor_key, {})
                if "funding" in cells:
                    cells["funding"].config(text="N/A")
                if "spread" in cells:
                    spread = FUNDING_SPREADS.get(tenor_key, 0.20)
                    cells["spread"].config(text=f"{spread:.2f}%")
                if "final" in cells:
                    cells["final"].config(text="N/A")
                if "change" in cells:
                    cells["change"].config(text="-", fg=THEME["text"])
            return

        weights = self._get_weights()
        self.app.funding_calc_data = {}

        for tenor_key in ["1w", "1m", "2m", "3m", "6m"]:
            # Get data from impl_calc_data
            eur_data = self.app.impl_calc_data.get(f"eur_{tenor_key}", {})
            usd_data = self.app.impl_calc_data.get(f"usd_{tenor_key}", {})

            eur_impl = eur_data.get('implied')
            usd_impl = usd_data.get('implied')
            nok_cm = eur_data.get('nok_cm')  # Same for both USD and EUR

            # Calculate funding rate
            funding_rate = None
            if all(x is not None for x in [eur_impl, usd_impl, nok_cm]):
                funding_rate = calc_funding_rate(eur_impl, usd_impl, nok_cm, weights)

            # Get spread
            spread = FUNDING_SPREADS.get(tenor_key, 0.20)

            # Calculate final rate
            final_rate = None
            if funding_rate is not None:
                final_rate = funding_rate + spread

            # Get change from Excel engine (comparison between latest and second-to-last sheet)
            change_val = None
            if hasattr(self.app, 'excel_engine') and hasattr(self.app.excel_engine, 'swedbank_contribution_change'):
                # Map tenor_key (1m, 2m, etc.) to Excel tenor (1M, 2M, etc.)
                excel_tenor = tenor_key.upper()  # "1m" -> "1M"
                if excel_tenor in self.app.excel_engine.swedbank_contribution_change:
                    # Use Z cell change (could also use AA)
                    change_val = self.app.excel_engine.swedbank_contribution_change[excel_tenor].get("Z")

            # Update UI cells
            cells = self.funding_cells.get(tenor_key, {})
            if "funding" in cells:
                cells["funding"].config(text=f"{funding_rate:.2f}%" if funding_rate is not None else "N/A")
            if "spread" in cells:
                cells["spread"].config(text=f"{spread:.2f}%")
            if "final" in cells:
                cells["final"].config(text=f"{final_rate:.2f}%" if final_rate is not None else "N/A")
            if "change" in cells:
                if change_val is not None:
                    # Format with +/- sign and 2 decimals
                    change_text = f"{change_val:+.2f}"
                    # Color based on positive/negative
                    change_color = THEME["good"] if change_val > 0 else (THEME["bad"] if change_val < 0 else THEME["text"])
                    cells["change"].config(text=change_text, fg=change_color)
                else:
                    cells["change"].config(text="-", fg=THEME["text"])

            # Store for popup
            self.app.funding_calc_data[tenor_key] = {
                'eur_impl': eur_impl, 'usd_impl': usd_impl, 'nok_cm': nok_cm,
                'eur_spot': eur_data.get('spot'), 'eur_pips': eur_data.get('pips'),
                'eur_rate': eur_data.get('rate'), 'eur_days': eur_data.get('days'),
                'usd_spot': usd_data.get('spot'), 'usd_pips': usd_data.get('pips'),
                'usd_rate': usd_data.get('rate'), 'usd_days': usd_data.get('days'),
                'weights': weights, 'funding_rate': funding_rate,
                'spread': spread, 'final_rate': final_rate
            }

    def _update_nibor_chart(self):
        """Load historical snapshots and update chart."""
        from datetime import datetime, timedelta
        from config import CHART_LOOKBACK_DAYS

        if not hasattr(self.app, 'snapshot_engine'):
            self.nibor_chart.clear_chart()
            return

        # Get last N days of snapshots
        today = datetime.now().date()
        lookback_days = CHART_LOOKBACK_DAYS
        dates = []
        rates_by_tenor = {"1M": [], "2M": [], "3M": [], "6M": []}

        for i in range(lookback_days, -1, -1):
            check_date = today - timedelta(days=i)
            date_str = check_date.strftime("%Y-%m-%d")

            snapshot = self.app.snapshot_engine.load_snapshot(date_str)
            if snapshot:
                dates.append(check_date)

                # Extract NIBOR rates from snapshot
                nibor_rates = snapshot.get("bloomberg", {}).get("nibor_rates", {})

                # Map tickers to tenors
                tenor_map = {
                    "1M": "NKCM1M SWET Curncy",
                    "2M": "NKCM2M SWET Curncy",
                    "3M": "NKCM3M SWET Curncy",
                    "6M": "NKCM6M SWET Curncy"
                }

                for tenor, ticker in tenor_map.items():
                    rate_data = nibor_rates.get(ticker, {})
                    price = rate_data.get("price")
                    if price is not None:
                        rates_by_tenor[tenor].append(price)
                    else:
                        rates_by_tenor[tenor].append(None)

        if dates:
            self.nibor_chart.plot_nibor_history(dates, rates_by_tenor)
        else:
            self.nibor_chart.clear_chart()


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

        # Hint label
        tk.Label(top, text="Dubbelklicka på rad för detaljer", fg=THEME["muted2"], bg=THEME["bg_panel"],
                 font=("Segoe UI", CURRENT_MODE["small"])).pack(side="left", padx=(15, 0))

        self.mode_var = tk.StringVar(value="ALL")
        self.mode_combo = ttk.Combobox(top, textvariable=self.mode_var, values=["ALL", "SPOT", "FWDS", "DAYS", "CELLS", "WEIGHTS"], state="readonly", width=10)
        self.mode_combo.pack(side="right")
        self.mode_combo.bind("<<ComboboxSelected>>", lambda _e: self.on_mode_change())

        # Use ClickableDataTableTree for row click support
        self.table = ClickableDataTableTree(self, columns=["CELL", "DESC", "MODEL", "MARKET/FILE", "DIFF", "STATUS"],
                                            col_widths=[110, 330, 170, 170, 140, 90], height=20,
                                            on_row_click=self._on_row_click)
        self.table.pack(fill="both", expand=True, padx=pad, pady=(0, pad))

    def _on_row_click(self, row_data: dict):
        """Handle row click - show match detail popup."""
        if row_data:
            MatchDetailPopup(self, row_data)

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

        # Get match details from app for CELLS view
        match_details = {d["cell"]: d for d in (self.app.match_details or [])}

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

            # Get row data for click handler
            cell = r["values"][0] if r["values"] else ""
            row_data = None

            # For CELLS section, get the detailed match data
            if cell in match_details:
                row_data = match_details[cell]
            elif style != "section" and len(r["values"]) >= 6:
                # Create basic row data from values for non-CELLS rows
                row_data = {
                    "cell": r["values"][0],
                    "desc": r["values"][1],
                    "model": r["values"][2],
                    "market": r["values"][3],
                    "diff": r["values"][4],
                    "status": r["values"][5] == "✔",
                    "logic": "Marknadsdata" if self.app.recon_view_mode in ("SPOT", "FWDS") else "Validering"
                }

            self.table.add_row(r["values"], style=s, row_data=row_data)


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

        # Initialize impl_calc_data storage for DashboardPage
        if not hasattr(self.app, 'impl_calc_data'):
            self.app.impl_calc_data = {}

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

            # Store data for DashboardPage funding rate table
            self.app.impl_calc_data[f"usd_{t['key']}"] = {
                'implied': impl_usd_bbg, 'spot': usd_spot, 'pips': pips_exc_usd,
                'rate': usd_rate_bbg, 'days': excel_days, 'nok_cm': nok_cm
            }

            self.app.impl_calc_data[f"eur_{t['key']}"] = {
                'implied': impl_eur_bbg, 'spot': eur_spot, 'pips': pips_exc_eur,
                'rate': eur_rate_bbg, 'days': excel_days, 'nok_cm': nok_cm
            }

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
