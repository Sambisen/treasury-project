"""
Page classes for Onyx Terminal.
Contains all specific page views.
"""
import tkinter as tk
from tkinter import ttk
from datetime import datetime

from config import THEME, FONTS, CURRENT_MODE, RULES_DB, MARKET_STRUCTURE, ALERTS_BOX_HEIGHT, get_logger

log = get_logger("ui_pages")
from ui_components import OnyxButtonTK, MetricChipTK, DataTableTree, SummaryCard, CollapsibleSection
from utils import safe_float
from calculations import calc_implied_yield
from history import save_snapshot, get_rates_table_data, get_snapshot, load_history, get_previous_day_rates


class ToolTip:
    """Simple tooltip that shows on hover with 4-decimal precision."""
    def __init__(self, widget, text_func):
        self.widget = widget
        self.text_func = text_func
        self.tooltip_window = None
        # Use add="+" to not replace existing bindings
        widget.bind("<Enter>", self.show, add="+")
        widget.bind("<Leave>", self.hide, add="+")
    
    def show(self, event=None):
        text = self.text_func()
        if text and self.tooltip_window is None:
            x = self.widget.winfo_rootx() + 20
            y = self.widget.winfo_rooty() + 20
            self.tooltip_window = tk.Toplevel(self.widget)
            self.tooltip_window.wm_overrideredirect(True)
            self.tooltip_window.wm_geometry(f"+{x}+{y}")
            label = tk.Label(
                self.tooltip_window, 
                text=text,
                background="#2A2A2A",
                foreground=THEME["accent"],
                relief="solid",
                borderwidth=1,
                font=("Consolas", 10, "bold"),
                padx=8,
                pady=4
            )
            label.pack()
    
    def hide(self, event=None):
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None


class DashboardPage(tk.Frame):
    """Main dashboard with Command Center sidebar and clean layout."""

    def __init__(self, master, app):
        super().__init__(master, bg=THEME["bg_panel"])
        self.app = app
        
        # Initialize blink tracking
        self._blink_widgets = {}

        # ====================================================================
        # NAVIGATION REMOVED - Now in main.py (visible on ALL pages)
        # ====================================================================
        # The Command Center sidebar has been moved to main.py so it's
        # always visible across all pages. DashboardPage now only contains
        # the dashboard content itself.
        # ====================================================================

        # ====================================================================
        # DASHBOARD CONTENT
        # ====================================================================
        content = tk.Frame(self, bg=THEME["bg_panel"])
        content.pack(fill="both", expand=True, padx=20, pady=20)
        
        # ====================================================================
        # NIBOR CALCULATION SECTION
        # ====================================================================
        tk.Label(content, text="NIBOR CALCULATION",
                fg=THEME["muted"],
                bg=THEME["bg_panel"],
                font=FONTS["h3"]).pack(anchor="center", pady=(15, 5))
        
        # Radio buttons for calculation model
        model_selection_frame = tk.Frame(content, bg=THEME["bg_panel"])
        model_selection_frame.pack(anchor="center", pady=(0, 15))

        self.calc_model_var = tk.StringVar(value="swedbank")

        swedbank_radio = tk.Radiobutton(
            model_selection_frame,
            text="Swedbank Calc",
            variable=self.calc_model_var,
            value="swedbank",
            command=self._on_dashboard_model_change,
            bg=THEME["bg_panel"],
            fg=THEME["text"],
            selectcolor=THEME["bg_card"],
            activebackground=THEME["bg_panel"],
            activeforeground=THEME["accent"],
            font=FONTS["body"]
        )
        swedbank_radio.pack(side="left", padx=10)

        nore_radio = tk.Radiobutton(
            model_selection_frame,
            text="Nore Calc",
            variable=self.calc_model_var,
            value="nore",
            command=self._on_dashboard_model_change,
            bg=THEME["bg_panel"],
            fg=THEME["text"],
            selectcolor=THEME["bg_card"],
            activebackground=THEME["bg_panel"],
            activeforeground=THEME["accent"],
            font=FONTS["body"]
        )
        nore_radio.pack(side="left", padx=10)
        
        # ====================================================================
        # NIBOR RATES TABLE with Norway flag 🇳🇴
        # ====================================================================
        tk.Label(content, text="🇳🇴 NIBOR RATES (LIVE)",
                fg=THEME["accent_secondary"],
                bg=THEME["bg_panel"],
                font=FONTS["h2"]).pack(anchor="center", pady=(10, 15))

        # Container for centering
        table_container = tk.Frame(content, bg=THEME["bg_panel"])
        table_container.pack(fill="both", expand=True, pady=(0, 20))

        # Actual table (larger, centered)
        funding_frame = tk.Frame(table_container, bg=THEME["bg_card"],
                                highlightthickness=2,
                                highlightbackground=THEME["accent_secondary"],
                                relief="flat")
        funding_frame.pack(anchor="center")

        # Table headers (6 columns: TENOR, FUNDING, SPREAD, NIBOR, CHG, MATCH)
        headers = ["TENOR", "FUNDING RATE", "SPREAD", "NIBOR", "CHG", "MATCH"]
        widths = [12, 18, 12, 18, 10, 12]

        header_frame = tk.Frame(funding_frame, bg=THEME["bg_card_2"])
        header_frame.grid(row=0, column=0, columnspan=6, sticky="ew")
        for i, (header, width) in enumerate(zip(headers, widths)):
            tk.Label(header_frame, text=header, fg=THEME["muted"],
                    bg=THEME["bg_card_2"],
                    font=("Segoe UI", CURRENT_MODE["body"], "bold"),
                    width=width, anchor="w" if i == 0 else "center").grid(
                        row=0, column=i, padx=5, sticky="ew")

        # Rows with Excel validation
        self.funding_cells = {}
        tenors = [
            {"key": "1m", "label": "1M", "excel_row": 30, "excel_col": 27},
            {"key": "2m", "label": "2M", "excel_row": 31, "excel_col": 27},
            {"key": "3m", "label": "3M", "excel_row": 32, "excel_col": 27},
            {"key": "6m", "label": "6M", "excel_row": 33, "excel_col": 27}
        ]

        for row_idx, tenor in enumerate(tenors, start=1):
            # Tenor label
            tk.Label(funding_frame, text=tenor["label"], fg=THEME["text"],
                    bg=THEME["bg_card"],
                    font=("Segoe UI", CURRENT_MODE["body"], "bold"),
                    width=8, anchor="center").grid(row=row_idx, column=0,
                                             padx=5, pady=6, sticky="ew")

            cells = {}

            # Funding Rate - Clean table style, centered
            funding_lbl = tk.Label(funding_frame, text="-",
                                  fg=THEME["text"], bg=THEME["bg_card"],
                                  font=("Consolas", CURRENT_MODE["body"]),
                                  width=15, cursor="hand2", relief="flat",
                                  anchor="center")
            funding_lbl.grid(row=row_idx, column=1, padx=5, pady=6, sticky="ew")
            funding_lbl.bind("<Button-1>",
                            lambda e, t=tenor["key"]: self._show_funding_details(t))
            funding_lbl.bind("<Enter>", lambda e, lbl=funding_lbl: lbl.config(bg=THEME["bg_card_2"]))
            funding_lbl.bind("<Leave>", lambda e, lbl=funding_lbl: lbl.config(bg=THEME["bg_card"]))
            cells["funding"] = funding_lbl

            # Tooltip showing EUR/USD implied (4 dec) and NOK (2 dec)
            tenor_key_funding = tenor["key"]
            ToolTip(funding_lbl, lambda t=tenor_key_funding: self._get_funding_tooltip(t))

            # Spread - Clean table style, centered, NO %
            spread_lbl = tk.Label(funding_frame, text="-",
                                 fg=THEME["text"], bg=THEME["bg_card"],
                                 font=("Consolas", CURRENT_MODE["body"]),
                                 width=10, anchor="center")
            spread_lbl.grid(row=row_idx, column=2, padx=5, pady=6, sticky="ew")
            cells["spread"] = spread_lbl

            # Final Rate (NIBOR) - Swedbank blue, clean table style, centered
            final_lbl = tk.Label(funding_frame, text="-",
                                fg=THEME["accent_secondary"], bg=THEME["bg_card"],
                                font=("Consolas", CURRENT_MODE["body"], "bold"),
                                width=15, cursor="hand2", relief="flat",
                                anchor="center")
            final_lbl.grid(row=row_idx, column=3, padx=5, pady=6, sticky="ew")
            final_lbl.bind("<Button-1>",
                          lambda e, t=tenor["key"]: self._show_funding_details(t))
            final_lbl.bind("<Enter>", lambda e, lbl=final_lbl: lbl.config(bg=THEME["bg_card_2"]))
            final_lbl.bind("<Leave>", lambda e, lbl=final_lbl: lbl.config(bg=THEME["bg_card"]))
            cells["final"] = final_lbl

            # Tooltip showing 4-decimal precision for NIBOR rate
            tenor_key_capture = tenor["key"]
            ToolTip(final_lbl, lambda t=tenor_key_capture: self._get_nibor_tooltip(t))

            # CHG (Change from previous day)
            chg_lbl = tk.Label(funding_frame, text="-",
                              fg=THEME["muted"], bg=THEME["bg_card"],
                              font=("Consolas", CURRENT_MODE["body"]),
                              width=8, anchor="center")
            chg_lbl.grid(row=row_idx, column=4, padx=5, pady=6, sticky="ew")
            cells["chg"] = chg_lbl

            # Match indicator - Professional text badge
            match_lbl = tk.Label(funding_frame, text="PEND",
                                fg=THEME["badge_pend"], bg=THEME["bg_card_2"],
                                font=("Segoe UI", 9, "bold"), width=8, anchor="center")
            match_lbl.grid(row=row_idx, column=5, padx=5, pady=6, sticky="ew")
            cells["match"] = match_lbl
            cells["excel_row"] = tenor["excel_row"]
            cells["excel_col"] = tenor["excel_col"]

            self.funding_cells[tenor["key"]] = cells

        # ====================================================================
        # DATA SOURCES BAR - Moved here (after table, before alerts)
        # ====================================================================
        status_bar = tk.Frame(content, bg=THEME["bg_card_2"],
                             highlightthickness=1,
                             highlightbackground=THEME["border"])
        status_bar.pack(fill="x", pady=(15, 0))
        
        tk.Label(status_bar, text="Data Sources:",
                fg=THEME["muted"],
                bg=THEME["bg_card_2"],
                font=FONTS["body"]).pack(side="left", padx=(20, 15), pady=12)
        
        self.status_badges_frame = tk.Frame(status_bar, bg=THEME["bg_card_2"])
        self.status_badges_frame.pack(side="left", fill="x", expand=True)
        
        self.status_badges = {}
        
        self.status_summary_lbl = tk.Label(status_bar, text="(0/6 OK)",
                                          fg=THEME["muted"],
                                          bg=THEME["bg_card_2"],
                                          font=FONTS["body"])
        self.status_summary_lbl.pack(side="right", padx=20, pady=12)

        # ===================================================================
        # ACTIVE ALERTS - ALWAYS VISIBLE
        # ===================================================================
        alerts_container = tk.Frame(content, bg=THEME["bg_panel"])
        alerts_container.pack(fill="x", pady=(15, 10))

        # Alert header with icon
        alerts_header = tk.Frame(alerts_container, bg=THEME["bg_panel"])
        alerts_header.pack(fill="x", pady=(0, 10))

        tk.Label(alerts_header, text="⚠", fg=THEME["warning"],
                bg=THEME["bg_panel"],
                font=("Segoe UI", 16)).pack(side="left", padx=(0, 8))

        tk.Label(alerts_header, text="ACTIVE ALERTS", fg=THEME["text"],
                bg=THEME["bg_panel"],
                font=FONTS["h3"]).pack(side="left")

        # Fixed height scrollable box
        self.alerts_box = tk.Frame(alerts_container, bg=THEME["bg_card"],
                                  highlightthickness=1,
                                  highlightbackground=THEME["border"],
                                  height=ALERTS_BOX_HEIGHT)
        self.alerts_box.pack(fill="x")
        self.alerts_box.pack_propagate(False)

        # Scrollable content
        self.alerts_canvas = tk.Canvas(self.alerts_box, bg=THEME["bg_card"],
                                 highlightthickness=0, height=ALERTS_BOX_HEIGHT)
        self.alerts_scrollbar = tk.Scrollbar(self.alerts_box, orient="vertical",
                                       command=self.alerts_canvas.yview)
        self.alerts_scroll_frame = tk.Frame(self.alerts_canvas, bg=THEME["bg_card"])

        self.alerts_scroll_frame.bind("<Configure>", self._on_alerts_configure)
        self.alerts_canvas.create_window((0, 0), window=self.alerts_scroll_frame, anchor="nw")
        self.alerts_canvas.configure(yscrollcommand=self.alerts_scrollbar.set)

        self.alerts_canvas.pack(side="left", fill="both", expand=True)

        # ===================================================================
        # FOOTER - EXPLANATION
        # ===================================================================
        footer_frame = tk.Frame(content, bg=THEME["bg_panel"])
        footer_frame.pack(side="bottom", fill="x", pady=(15, 10))

        tk.Label(footer_frame,
                text="✓ = Excel NIBOR level matches Python calculated NIBOR level",
                fg=THEME["text_light"], bg=THEME["bg_panel"],
                font=FONTS["body_small"],
                anchor="w").pack(padx=20)

    def _on_dashboard_model_change(self):
        """Handle calculation model change on Dashboard."""
        model = self.calc_model_var.get()
        log.info(f"[Dashboard] Calculation model changed to: {model}")
        # Store selected model in app
        self.app.selected_calc_model = model
        # Trigger re-update of funding rates table
        self._update_funding_rates_with_validation()
    
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

    def _show_funding_details(self, tenor_key):
        """Show detailed breakdown popup for funding rate calculation - 3 COLUMN LAYOUT."""
        if not hasattr(self.app, 'funding_calc_data'):
            log.info(f"[Dashboard] No funding calculation data available")
            return
        
        data = self.app.funding_calc_data.get(tenor_key)
        if not data:
            log.info(f"[Dashboard] No funding data found for {tenor_key}")
            return
        
        popup = tk.Toplevel(self)
        popup.title(f"NIBOR Calculation - {tenor_key.upper()}")
        popup.geometry("1100x800")  # Större fönster: 1100x800 (från 950x700)
        popup.configure(bg=THEME["bg_panel"])
        popup.transient(self)
        popup.grab_set()
        
        # Gör fönstret resizable så användaren kan justera om nödvändigt
        popup.resizable(True, True)
        
        # Title - CHANGED to "NIBOR CALCULATION"
        tk.Label(popup, text=f"{tenor_key.upper()} TENOR - NIBOR CALCULATION",
                fg=THEME["accent"], bg=THEME["bg_panel"],
                font=("Segoe UI", 20, "bold")).pack(pady=20)
        
        # Main content frame
        content = tk.Frame(popup, bg=THEME["bg_card"], highlightthickness=1,
                          highlightbackground=THEME["border"])
        content.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # 3-COLUMN LAYOUT - Side by side
        columns_frame = tk.Frame(content, bg=THEME["bg_card"])
        columns_frame.pack(fill="x", padx=15, pady=15)
        
        # Configure 3 equal columns
        for i in range(3):
            columns_frame.grid_columnconfigure(i, weight=1, uniform="col")
        
        # COLUMN 1: EUR IMPLIED
        eur_col = tk.Frame(columns_frame, bg=THEME["bg_card_2"], 
                          highlightthickness=1, highlightbackground=THEME["border"])
        eur_col.grid(row=0, column=0, padx=5, sticky="nsew")
        
        tk.Label(eur_col, text="EUR IMPLIED", fg=THEME["good"], bg=THEME["bg_card_2"],
                font=("Segoe UI", 11, "bold")).pack(pady=(10, 2))
        tk.Label(eur_col, text="NOK RATE", fg=THEME["good"], bg=THEME["bg_card_2"],
                font=("Segoe UI", 9)).pack(pady=(0, 10))
        
        # EUR IMPLIED VALUE - Large with 4 DECIMALS
        tk.Label(eur_col, text=f"{data.get('eur_impl'):.4f}%" if data.get('eur_impl') else "N/A",
                fg=THEME["accent"], bg=THEME["bg_card_2"],
                font=("Consolas", 18, "bold")).pack(pady=5)
        
        # EUR details
        tk.Frame(eur_col, bg=THEME["border"], height=1).pack(fill="x", padx=10, pady=8)
        for lbl, val in [
            ("Spot:", f"{data.get('eur_spot'):.4f}" if data.get('eur_spot') else "N/A"),
            ("Pips:", f"{data.get('eur_pips'):.2f}" if data.get('eur_pips') else "N/A"),
            ("Rate:", f"{data.get('eur_rate'):.4f}%" if data.get('eur_rate') else "N/A"),
            ("Days:", f"{int(data.get('eur_days'))}" if data.get('eur_days') else "N/A"),
        ]:
            row_f = tk.Frame(eur_col, bg=THEME["bg_card_2"])
            row_f.pack(fill="x", padx=15, pady=2)
            tk.Label(row_f, text=lbl, fg=THEME["muted"], bg=THEME["bg_card_2"],
                    font=("Segoe UI", 9), anchor="w").pack(side="left")
            tk.Label(row_f, text=val, fg=THEME["text"], bg=THEME["bg_card_2"],
                    font=("Consolas", 9), anchor="e").pack(side="right")
        
        tk.Label(eur_col, text="", bg=THEME["bg_card_2"]).pack(pady=5)
        
        # COLUMN 2: USD IMPLIED
        usd_col = tk.Frame(columns_frame, bg=THEME["bg_card_2"],
                          highlightthickness=1, highlightbackground=THEME["border"])
        usd_col.grid(row=0, column=1, padx=5, sticky="nsew")
        
        tk.Label(usd_col, text="USD IMPLIED", fg=THEME["good"], bg=THEME["bg_card_2"],
                font=("Segoe UI", 11, "bold")).pack(pady=(10, 2))
        tk.Label(usd_col, text="NOK RATE", fg=THEME["good"], bg=THEME["bg_card_2"],
                font=("Segoe UI", 9)).pack(pady=(0, 10))
        
        # USD IMPLIED VALUE - Large with 4 DECIMALS
        tk.Label(usd_col, text=f"{data.get('usd_impl'):.4f}%" if data.get('usd_impl') else "N/A",
                fg=THEME["accent"], bg=THEME["bg_card_2"],
                font=("Consolas", 18, "bold")).pack(pady=5)
        
        # USD details
        tk.Frame(usd_col, bg=THEME["border"], height=1).pack(fill="x", padx=10, pady=8)
        for lbl, val in [
            ("Spot:", f"{data.get('usd_spot'):.4f}" if data.get('usd_spot') else "N/A"),
            ("Pips:", f"{data.get('usd_pips'):.2f}" if data.get('usd_pips') else "N/A"),
            ("Rate:", f"{data.get('usd_rate'):.4f}%" if data.get('usd_rate') else "N/A"),
            ("Days:", f"{int(data.get('usd_days'))}" if data.get('usd_days') else "N/A"),
        ]:
            row_f = tk.Frame(usd_col, bg=THEME["bg_card_2"])
            row_f.pack(fill="x", padx=15, pady=2)
            tk.Label(row_f, text=lbl, fg=THEME["muted"], bg=THEME["bg_card_2"],
                    font=("Segoe UI", 9), anchor="w").pack(side="left")
            tk.Label(row_f, text=val, fg=THEME["text"], bg=THEME["bg_card_2"],
                    font=("Consolas", 9), anchor="e").pack(side="right")
        
        tk.Label(usd_col, text="", bg=THEME["bg_card_2"]).pack(pady=5)
        
        # COLUMN 3: NOK CM
        nok_col = tk.Frame(columns_frame, bg=THEME["bg_card_2"],
                          highlightthickness=1, highlightbackground=THEME["border"])
        nok_col.grid(row=0, column=2, padx=5, sticky="nsew")
        
        tk.Label(nok_col, text="NOK CM RATE", fg=THEME["good"], bg=THEME["bg_card_2"],
                font=("Segoe UI", 11, "bold")).pack(pady=(10, 2))
        tk.Label(nok_col, text="", fg=THEME["good"], bg=THEME["bg_card_2"],
                font=("Segoe UI", 9)).pack(pady=(0, 10))
        
        # NOK CM VALUE - Large
        tk.Label(nok_col, text=f"{data.get('nok_cm'):.2f}%" if data.get('nok_cm') else "N/A",
                fg=THEME["accent"], bg=THEME["bg_card_2"],
                font=("Consolas", 18, "bold")).pack(pady=5)
        
        tk.Frame(nok_col, bg=THEME["border"], height=1).pack(fill="x", padx=10, pady=8)
        
        tk.Label(nok_col, text="NIBOR Market Rate", fg=THEME["muted"], bg=THEME["bg_card_2"],
                font=("Segoe UI", 9)).pack(pady=40)
        
        # FUNDING RATE CALCULATION SECTION
        calc_section = tk.Frame(content, bg=THEME["bg_card"])
        calc_section.pack(fill="x", padx=15, pady=(10, 15))
        
        tk.Label(calc_section, text="FUNDING RATE CALCULATION", fg=THEME["accent"],
                bg=THEME["bg_card"], font=("Segoe UI", 13, "bold")).pack(anchor="center", pady=(0, 10))
        
        calc_frame = tk.Frame(calc_section, bg=THEME["bg_card_2"],
                             highlightthickness=1, highlightbackground=THEME["border"])
        calc_frame.pack(fill="x", padx=20)
        
        weights = data.get('weights', {})
        
        # Calculation steps with 2 DECIMAL WEIGHTS
        calc_details = tk.Frame(calc_frame, bg=THEME["bg_card_2"])
        calc_details.pack(fill="x", padx=20, pady=15)
        
        # EUR contribution
        eur_w = weights.get('EUR', 0) * 100
        eur_contrib = data.get('eur_impl', 0) * weights.get('EUR', 0) if data.get('eur_impl') else None
        tk.Label(calc_details, 
                text=f"{data.get('eur_impl', 0):.2f}%  ×  {eur_w:.2f}%  =  {eur_contrib:.4f}%  (EUR)",
                fg=THEME["text"], bg=THEME["bg_card_2"],
                font=("Consolas", 11)).pack(anchor="w", pady=3)
        
        # USD contribution
        usd_w = weights.get('USD', 0) * 100
        usd_contrib = data.get('usd_impl', 0) * weights.get('USD', 0) if data.get('usd_impl') else None
        tk.Label(calc_details,
                text=f"{data.get('usd_impl', 0):.2f}%  ×  {usd_w:.2f}%  =  {usd_contrib:.4f}%  (USD)",
                fg=THEME["text"], bg=THEME["bg_card_2"],
                font=("Consolas", 11)).pack(anchor="w", pady=3)
        
        # NOK contribution
        nok_w = weights.get('NOK', 0) * 100
        nok_contrib = data.get('nok_cm', 0) * weights.get('NOK', 0) if data.get('nok_cm') else None
        tk.Label(calc_details,
                text=f"{data.get('nok_cm', 0):.2f}%  ×  {nok_w:.2f}%  =  {nok_contrib:.4f}%  (NOK)",
                fg=THEME["text"], bg=THEME["bg_card_2"],
                font=("Consolas", 11)).pack(anchor="w", pady=3)
        
        # Separator
        tk.Frame(calc_details, bg=THEME["border"], height=2).pack(fill="x", pady=8)
        
        # Funding Rate
        tk.Label(calc_details,
                text=f"=  FUNDING RATE:  {data.get('funding_rate'):.4f}%",
                fg=THEME["accent"], bg=THEME["bg_card_2"],
                font=("Consolas", 12, "bold")).pack(anchor="w", pady=5)
        
        # Spread
        tk.Label(calc_details,
                text=f"+  SPREAD:         {data.get('spread'):.2f}%",
                fg=THEME["text"], bg=THEME["bg_card_2"],
                font=("Consolas", 11)).pack(anchor="w", pady=3)
        
        # Separator
        tk.Frame(calc_details, bg=THEME["border"], height=2).pack(fill="x", pady=8)
        
        # Final Rate
        tk.Label(calc_details,
                text=f"=  NIBOR:          {data.get('final_rate'):.4f}%",
                fg=THEME["accent"], bg=THEME["bg_card_2"],
                font=("Consolas", 14, "bold")).pack(anchor="w", pady=5)
        
        # Close button
        OnyxButtonTK(popup, "Close", command=popup.destroy, variant="default").pack(pady=15)

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
        """Update all dashboard elements."""
        # Populate horizontal status bar
        self._populate_status_badges()
        
        # Update funding rates with Excel validation (cards are in global header, updated by main.py)
        self._update_funding_rates_with_validation()
    
    def _populate_status_badges(self):
        """Populate horizontal status bar with current system status."""
        # Clear existing badges
        for widget in self.status_badges_frame.winfo_children():
            widget.destroy()
        
        self.status_badges = {}
        
        statuses = [
            ("Bloomberg", "bbg"),
            ("Excel", "excel"),
            ("Spot", "spot"),
            ("FX", "fx"),
            ("Days", "days"),
            ("Weights", "weights")
        ]
        
        ok_count = 0
        
        for name, key in statuses:
            # Check status
            if key == "bbg":
                is_ok = self.app.bbg_ok if hasattr(self.app, 'bbg_ok') else False
            elif key == "excel":
                is_ok = self.app.excel_ok if hasattr(self.app, 'excel_ok') else False
            elif key == "spot":
                is_ok = self.app.status_spot if hasattr(self.app, 'status_spot') else False
            elif key == "fx":
                is_ok = self.app.status_fwds if hasattr(self.app, 'status_fwds') else False
            elif key == "days":
                is_ok = self.app.status_days if hasattr(self.app, 'status_days') else False
            elif key == "weights":
                is_ok = getattr(self.app, 'weights_state', 'WAIT') == 'OK'
            else:
                is_ok = False
            
            if is_ok:
                ok_count += 1
            
            # Badge frame
            badge = tk.Frame(self.status_badges_frame, bg=THEME["bg_card_2"],
                            cursor="hand2")
            badge.pack(side="left", padx=8, pady=6)
            
            # Icon
            icon = "✓" if is_ok else "✗"
            color = THEME["good"] if is_ok else THEME["bad"]
            
            icon_lbl = tk.Label(badge, text=icon, fg=color,
                               bg=THEME["bg_card_2"],
                               font=("Segoe UI", 14, "bold"))
            icon_lbl.pack(side="left")
            
            # Name
            name_lbl = tk.Label(badge, text=name, fg=THEME["text"],
                               bg=THEME["bg_card_2"],
                               font=FONTS["body"])
            name_lbl.pack(side="left", padx=(5, 0))
            
            # Hover effect
            badge.bind("<Enter>",
                      lambda e, b=badge: b.config(bg=THEME["bg_hover"]))
            badge.bind("<Leave>",
                      lambda e, b=badge: b.config(bg=THEME["bg_card_2"]))
            
            # Store reference
            self.status_badges[key] = (icon_lbl, name_lbl, badge)
        
        # Update summary
        total = len(statuses)
        color = THEME["good"] if ok_count == total else (
            THEME["warning"] if ok_count > total // 2 else THEME["bad"]
        )
        self.status_summary_lbl.config(
            text=f"({ok_count}/{total} OK)",
            fg=color
        )
    
    def _update_connection_cards(self):
        """Update Excel and Bloomberg connection status in top-right cards."""
        # Excel
        if hasattr(self.app, 'excel_ok') and self.app.excel_ok:
            self.excel_conn_lbl.config(text="CONNECTED", fg=THEME["good"])
            if hasattr(self.app, 'excel_last_update'):
                self.excel_time_lbl.config(text=f"Last updated: {self.app.excel_last_update}")
        else:
            self.excel_conn_lbl.config(text="DISCONNECTED", fg=THEME["bad"])
            self.excel_time_lbl.config(text="Last updated: --")
        
        # Bloomberg
        if hasattr(self.app, 'bbg_ok') and self.app.bbg_ok:
            self.bbg_conn_lbl.config(text="CONNECTED", fg=THEME["good"])
            if hasattr(self.app, 'bbg_last_update'):
                self.bbg_time_lbl.config(text=f"Last updated: {self.app.bbg_last_update}")
        else:
            self.bbg_conn_lbl.config(text="DISCONNECTED", fg=THEME["bad"])
            self.bbg_time_lbl.config(text="Last updated: --")
    
    def _update_alerts_count(self):
        """Update alerts count indicator."""
        alert_count = 0
        
        # System status alerts
        for key in ["bbg", "excel", "spot", "fx", "days", "weights"]:
            if key == "bbg":
                is_ok = self.app.bbg_ok if hasattr(self.app, 'bbg_ok') else False
            elif key == "excel":
                is_ok = self.app.excel_ok if hasattr(self.app, 'excel_ok') else False
            elif key == "spot":
                is_ok = self.app.status_spot if hasattr(self.app, 'status_spot') else False
            elif key == "fx":
                is_ok = self.app.status_fwds if hasattr(self.app, 'status_fwds') else False
            elif key == "days":
                is_ok = self.app.status_days if hasattr(self.app, 'status_days') else False
            elif key == "weights":
                is_ok = getattr(self.app, 'weights_state', 'WAIT') == 'OK'
            else:
                is_ok = False
            
            if not is_ok:
                alert_count += 1
        
        if alert_count > 0:
            self.alerts_count_lbl.config(
                text=f"● ALERTS ({alert_count})",
                fg=THEME["bad"]
            )
        else:
            self.alerts_count_lbl.config(
                text="✓ ALL OK",
                fg=THEME["good"]
            )
    
    def _start_blink(self, widget):
        """Start blinking animation for failed widget."""
        if widget not in self._blink_widgets:
            self._blink_widgets[widget] = {
                "colors": [THEME["badge_fail"], THEME["accent"]],  # Red <-> Orange
                "index": 0,
                "active": True
            }
            self._animate_blink(widget)
    
    def _animate_blink(self, widget):
        """Animate widget color toggle."""
        if widget not in self._blink_widgets:
            return
        
        data = self._blink_widgets[widget]
        if not data["active"]:
            return
        
        try:
            color = data["colors"][data["index"]]
            widget.config(fg=color)
            data["index"] = (data["index"] + 1) % 2
            self.after(800, lambda: self._animate_blink(widget))
        except tk.TclError:
            # Widget destroyed, remove from tracking
            if widget in self._blink_widgets:
                del self._blink_widgets[widget]
    
    def _stop_blink(self, widget):
        """Stop blinking when fixed."""
        if widget in self._blink_widgets:
            self._blink_widgets[widget]["active"] = False
            del self._blink_widgets[widget]
    
    def _update_funding_rates_with_validation(self):
        """Update funding rates table with Excel validation - USES SELECTED MODEL."""
        from config import FUNDING_SPREADS
        from calculations import calc_funding_rate
        
        if not hasattr(self.app, 'impl_calc_data'):
            return
        
        # Get selected calculation model (default: swedbank)
        selected_model = self.calc_model_var.get() if hasattr(self, 'calc_model_var') else "swedbank"
        log.info(f"[Dashboard._update_funding_rates_with_validation] Using model: {selected_model}")
        
        weights = self._get_weights()
        self.app.funding_calc_data = {}

        # Get previous day rates for CHG calculation
        prev_rates = get_previous_day_rates()

        alert_messages = []

        for tenor_key in ["1m", "2m", "3m", "6m"]:
            # Select data based on model choice
            if selected_model == "swedbank":
                # Use Internal Basket Rates (Excel CM - nibor suffix)
                eur_data = self.app.impl_calc_data.get(f"eur_{tenor_key}_nibor", {})
                usd_data = self.app.impl_calc_data.get(f"usd_{tenor_key}_nibor", {})
                log.info(f"[Dashboard] {tenor_key}: Using Swedbank Calc (Excel CM)")
            else:
                # Use Bloomberg CM Rates (nore model - no suffix)
                eur_data = self.app.impl_calc_data.get(f"eur_{tenor_key}", {})
                usd_data = self.app.impl_calc_data.get(f"usd_{tenor_key}", {})
                log.info(f"[Dashboard] {tenor_key}: Using Nore Calc (Bloomberg CM)")
            
            eur_impl = eur_data.get('implied')
            usd_impl = usd_data.get('implied')
            nok_cm = eur_data.get('nok_cm')
            
            funding_rate = None
            if all(x is not None for x in [eur_impl, usd_impl, nok_cm]):
                funding_rate = calc_funding_rate(eur_impl, usd_impl, nok_cm, weights)
            
            spread = FUNDING_SPREADS.get(tenor_key, 0.20)
            final_rate = funding_rate + spread if funding_rate else None
            
            cells = self.funding_cells.get(tenor_key, {})
            
            # Update display cells
            if "funding" in cells:
                cells["funding"].config(text=f"{funding_rate:.2f}%" if funding_rate else "N/A")
            if "spread" in cells:
                # NO % sign in spread column
                cells["spread"].config(text=f"{spread:.2f}")
            if "final" in cells:
                cells["final"].config(text=f"{final_rate:.2f}%" if final_rate else "N/A")

            # CHG (Change from previous day)
            if "chg" in cells:
                prev_nibor = None
                if prev_rates and tenor_key in prev_rates:
                    prev_nibor = prev_rates[tenor_key].get('nibor')

                if final_rate is not None and prev_nibor is not None:
                    chg = final_rate - prev_nibor
                    if chg > 0:
                        chg_text = f"+{chg:.2f}"
                    elif chg < 0:
                        chg_text = f"{chg:.2f}"
                    else:
                        chg_text = "0.00"
                    cells["chg"].config(text=chg_text, fg=THEME["text"])
                else:
                    cells["chg"].config(text="-", fg=THEME["muted"])

            # Excel validation
            if "match" in cells and final_rate is not None:
                excel_row = cells.get("excel_row")
                excel_col = cells.get("excel_col")
                
                if excel_row and excel_col:
                    excel_value = self.app.cached_excel_data.get((excel_row, excel_col))
                    
                    if excel_value is not None:
                        try:
                            excel_value = float(excel_value)
                            # Round both to 4 decimals for comparison
                            final_rate_rounded = round(final_rate, 4)
                            excel_value_rounded = round(excel_value, 4)
                            
                            is_match = (final_rate_rounded == excel_value_rounded)
                            
                            if is_match:
                                cells["match"].config(text="OK", fg=THEME["badge_ok"], bg=THEME["bg_card_2"])
                            else:
                                cells["match"].config(text="FAIL", fg=THEME["badge_fail"], bg=THEME["bg_card_2"])
                                alert_messages.append(f"{tenor_key.upper()}: GUI {final_rate:.4f}% ≠ Excel {excel_value:.4f}%")
                        except (ValueError, TypeError):
                            cells["match"].config(text="WARN", fg=THEME["badge_warn"], bg=THEME["bg_card_2"])
                    else:
                        cells["match"].config(text="—", fg=THEME["muted"], bg=THEME["bg_card"])
                else:
                    cells["match"].config(text="—", fg=THEME["muted"], bg=THEME["bg_card"])
            
            # Store for popup with model information
            self.app.funding_calc_data[tenor_key] = {
                'eur_impl': eur_impl, 'usd_impl': usd_impl, 'nok_cm': nok_cm,
                'eur_spot': eur_data.get('spot'), 'eur_pips': eur_data.get('pips'),
                'eur_rate': eur_data.get('rate'), 'eur_days': eur_data.get('days'),
                'rate_label': eur_data.get('rate_label', 'Unknown'),
                'usd_spot': usd_data.get('spot'), 'usd_pips': usd_data.get('pips'),
                'usd_rate': usd_data.get('rate'), 'usd_days': usd_data.get('days'),
                'weights': weights, 'funding_rate': funding_rate,
                'spread': spread, 'final_rate': final_rate,
                'model': selected_model
            }
        
        # Show/hide alerts
        self._update_alerts(alert_messages)

    def _on_alerts_configure(self, event=None):
        """Update scrollbar visibility and scroll region based on content size."""
        self.alerts_canvas.configure(scrollregion=self.alerts_canvas.bbox("all"))
        # Show scrollbar only if content exceeds visible area
        content_height = self.alerts_scroll_frame.winfo_reqheight()
        if content_height > ALERTS_BOX_HEIGHT:
            self.alerts_scrollbar.pack(side="right", fill="y")
        else:
            self.alerts_scrollbar.pack_forget()

    def _update_alerts(self, messages):
        """Update always-visible alert box with messages or show 'All OK'.

        Messages can be either:
        - Simple strings (treated as critical)
        - Tuples of (message, priority) where priority is 'warning' or 'critical'
        """
        # Clear previous alerts
        for widget in self.alerts_scroll_frame.winfo_children():
            widget.destroy()

        if not messages:
            # All OK - show success message
            tk.Label(self.alerts_scroll_frame, text="✓ All Controls OK",
                    fg=THEME["good"], bg=THEME["bg_card"],
                    font=("Segoe UI", 14, "bold")).pack(expand=True, pady=50)
        else:
            # Get current timestamp
            timestamp = datetime.now().strftime("%H:%M:%S")

            # Show error messages
            for i, msg_item in enumerate(messages):
                # Support both simple strings and (message, priority) tuples
                if isinstance(msg_item, tuple):
                    msg, priority = msg_item
                else:
                    msg, priority = msg_item, "critical"

                # Set colors based on priority
                if priority == "warning":
                    icon_color = THEME["warning"]
                    icon_text = "⚠"
                else:  # critical
                    icon_color = THEME["bad"]
                    icon_text = "●"

                alert_frame = tk.Frame(self.alerts_scroll_frame,
                                      bg=THEME["bg_card_2"] if i % 2 == 0 else THEME["bg_card"])
                alert_frame.pack(fill="x", pady=2, padx=10)

                # Timestamp
                tk.Label(alert_frame, text=timestamp, fg=THEME["muted"],
                        bg=alert_frame["bg"],
                        font=("Consolas", 9)).pack(side="left", padx=(10, 8), pady=8)

                # Priority icon
                tk.Label(alert_frame, text=icon_text, fg=icon_color,
                        bg=alert_frame["bg"],
                        font=("Segoe UI", 12)).pack(side="left", padx=(0, 5), pady=8)

                # Message
                tk.Label(alert_frame, text=msg, fg=THEME["text"],
                        bg=alert_frame["bg"],
                        font=("Segoe UI", 10), anchor="w",
                        wraplength=580).pack(side="left", fill="x", expand=True, pady=8)

    def _on_model_change(self):
        """Called when calculation model selection changes."""
        model = self.calc_model.get()
        log.info(f"[NOK Implied] Calculation model changed to: {model}")
        # Note: Recalculation is triggered manually via Recalculate button
        # This allows user to change model without auto-recalculating
    
    def _get_ticker_val(self, ticker):
        """Get price value from cached market data."""
        data = self.app.cached_market_data or {}
        inf = data.get(ticker)
        if inf:
            return float(inf.get("price", 0.0))
        return None

    def _get_nibor_tooltip(self, tenor_key):
        """Get NIBOR rate with 4 decimal precision for tooltip."""
        calc_data = getattr(self.app, 'funding_calc_data', {})
        tenor_data = calc_data.get(tenor_key, {})
        final_rate = tenor_data.get('final_rate')
        if final_rate is not None:
            return f"NIBOR {tenor_key.upper()}: {final_rate:.4f}%"
        return None

    def _get_funding_tooltip(self, tenor_key):
        """Get Funding Rate breakdown: EUR/USD implied (4 dec), NOK (2 dec)."""
        calc_data = getattr(self.app, 'funding_calc_data', {})
        tenor_data = calc_data.get(tenor_key, {})

        eur_impl = tenor_data.get('eur_impl')
        usd_impl = tenor_data.get('usd_impl')
        nok_cm = tenor_data.get('nok_cm')

        if eur_impl is None and usd_impl is None and nok_cm is None:
            return None

        lines = [f"Funding Rate {tenor_key.upper()}:"]
        if eur_impl is not None:
            lines.append(f"  EUR Implied: {eur_impl:.4f}%")
        if usd_impl is not None:
            lines.append(f"  USD Implied: {usd_impl:.4f}%")
        if nok_cm is not None:
            lines.append(f"  NOK CM:      {nok_cm:.2f}%")

        return "\n".join(lines)

    def _get_weights(self):
        """Get weights from Excel engine or use defaults - ALWAYS USE LATEST."""
        from config import WEIGHTS_FILE
        
        # Default fallback weights
        weights = {"USD": 0.445, "EUR": 0.055, "NOK": 0.500}
        
        # Try to get latest weights from Wheights.xlsx file
        if hasattr(self.app, 'excel_engine'):
            latest_weights = self.app.excel_engine.get_latest_weights(WEIGHTS_FILE)
            if latest_weights:
                weights = {
                    "USD": latest_weights.get("USD", 0.445),
                    "EUR": latest_weights.get("EUR", 0.055),
                    "NOK": latest_weights.get("NOK", 0.500)
                }
                log.info(f"[_get_weights] Using latest weights: USD={weights['USD']:.2%}, EUR={weights['EUR']:.2%}, NOK={weights['NOK']:.2%}")
            else:
                log.info(f"[_get_weights] Could not load weights, using defaults")
        
        return weights

    def _update_implied_rates(self):
        """Calculate and display funding rates in interactive table - USES SELECTED MODEL."""
        from config import FUNDING_SPREADS
        from calculations import calc_funding_rate
        
        if not hasattr(self.app, 'impl_calc_data'):
            return
        
        # Get selected calculation model (default: nore)
        selected_model = getattr(self.app, 'selected_calc_model', 'nore')
        log.info(f"[Dashboard._update_implied_rates] Using calculation model: {selected_model}")
        
        weights = self._get_weights()
        self.app.funding_calc_data = {}
        
        for tenor_key in ["1w", "1m", "2m", "3m", "6m"]:
            # Select data based on model choice
            if selected_model == "nibor":
                # Use Internal Basket Rates (Section 2 data from NokImpliedPage)
                eur_data = self.app.impl_calc_data.get(f"eur_{tenor_key}_nibor", {})
                usd_data = self.app.impl_calc_data.get(f"usd_{tenor_key}_nibor", {})
                log.info(f"[Dashboard] {tenor_key}: Using NIBOR model (Internal Basket)")
            else:
                # Use Bloomberg CM Rates (Section 1 data from NokImpliedPage) - DEFAULT
                eur_data = self.app.impl_calc_data.get(f"eur_{tenor_key}", {})
                usd_data = self.app.impl_calc_data.get(f"usd_{tenor_key}", {})
                log.info(f"[Dashboard] {tenor_key}: Using NORE model (Bloomberg CM)")
            
            eur_impl = eur_data.get('implied')
            usd_impl = usd_data.get('implied')
            nok_cm = eur_data.get('nok_cm')  # Both EUR and USD have same nok_cm
            
            funding_rate = None
            if all(x is not None for x in [eur_impl, usd_impl, nok_cm]):
                funding_rate = calc_funding_rate(eur_impl, usd_impl, nok_cm, weights)
            
            spread = FUNDING_SPREADS.get(tenor_key, 0.20)
            final_rate = funding_rate + spread if funding_rate else None
            
            cells = self.funding_cells.get(tenor_key, {})
            if "funding" in cells:
                cells["funding"].config(text=f"{funding_rate:.2f}%" if funding_rate else "N/A")
            if "spread" in cells:
                cells["spread"].config(text=f"{spread:.2f}%")
            if "final" in cells:
                cells["final"].config(text=f"{final_rate:.2f}%" if final_rate else "N/A")
            
            self.app.funding_calc_data[tenor_key] = {
                'eur_impl': eur_impl, 'usd_impl': usd_impl, 'nok_cm': nok_cm,
                'eur_spot': eur_data.get('spot'), 'eur_pips': eur_data.get('pips'),
                'eur_rate': eur_data.get('rate'), 'eur_days': eur_data.get('days'),
                'rate_label': eur_data.get('rate_label', 'Bloomberg CM'),
                'usd_spot': usd_data.get('spot'), 'usd_pips': usd_data.get('pips'),
                'usd_rate': usd_data.get('rate'), 'usd_days': usd_data.get('days'),
                'weights': weights, 'funding_rate': funding_rate,
                'spread': spread, 'final_rate': final_rate,
                'model': selected_model
            }


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

        # Get today's date to highlight the active row
        today_str = datetime.now().strftime("%Y-%m-%d")

        for _, r in df2.head(400).iterrows():
            row_date = str(r.get("date", ""))
            # Highlight today's row (the one used in calculations) with orange
            style = "active" if row_date == today_str else "normal"
            self.table.add_row([r.get(c, "") for c in cols], style=style)


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

        # ============================================================================
        # CALCULATION MODEL SELECTION
        # ============================================================================
        model_frame = tk.Frame(container, bg=THEME["bg_panel"])
        model_frame.pack(fill="x", padx=pad, pady=(10, 15))

        tk.Label(model_frame, text="CALCULATION MODEL:", fg=THEME["muted"],
                bg=THEME["bg_panel"],
                font=("Segoe UI", CURRENT_MODE["body"], "bold")).pack(side="left", padx=(0, 15))

        self.calc_model = tk.StringVar(value="swedbank")  # Default: Swedbank Calc Model

        # Swedbank Calc Model (default) - uses Excel CM rates
        swedbank_radio = tk.Radiobutton(
            model_frame,
            text="Swedbank Calc Model (Excel CM Rates)",
            variable=self.calc_model,
            value="swedbank",
            command=self._on_model_change,
            bg=THEME["bg_panel"],
            fg=THEME["text"],
            selectcolor=THEME["bg_card"],
            activebackground=THEME["bg_panel"],
            activeforeground=THEME["accent"],
            font=("Segoe UI", CURRENT_MODE["body"])
        )
        swedbank_radio.pack(side="left", padx=10)

        # Nore Calc Model - uses Bloomberg CM rates
        nore_radio = tk.Radiobutton(
            model_frame,
            text="Nore Calc Model (Bloomberg CM)",
            variable=self.calc_model,
            value="nore",
            command=self._on_model_change,
            bg=THEME["bg_panel"],
            fg=THEME["text"],
            selectcolor=THEME["bg_card"],
            activebackground=THEME["bg_panel"],
            activeforeground=THEME["accent"],
            font=("Segoe UI", CURRENT_MODE["body"])
        )
        nore_radio.pack(side="left", padx=10)

        # Weights display
        self.weights_frame = tk.Frame(container, bg=THEME["bg_panel"])
        self.weights_frame.pack(fill="x", padx=pad, pady=(0, 10))

        self.weights_label = tk.Label(self.weights_frame, text="VIKTER:  USD = 45%  |  EUR = 5%  |  NOK = 50%",
                                      fg=THEME["accent"], bg=THEME["bg_panel"],
                                      font=("Segoe UI", CURRENT_MODE["body"], "bold"))
        self.weights_label.pack(side="left")

        # ============================================================================
        # SUMMARY CARDS - Show weighted results at a glance
        # ============================================================================
        summary_frame = tk.Frame(container, bg=THEME["bg_panel"])
        summary_frame.pack(fill="x", padx=pad, pady=(10, 15))

        tk.Label(summary_frame, text="FUNDING RATES (WEIGHTED)", fg=THEME["muted"],
                bg=THEME["bg_panel"],
                font=("Segoe UI", CURRENT_MODE["small"], "bold")).pack(anchor="w", pady=(0, 8))

        cards_frame = tk.Frame(summary_frame, bg=THEME["bg_panel"])
        cards_frame.pack(fill="x")
        for i in range(4):
            cards_frame.grid_columnconfigure(i, weight=1, uniform="card")

        self.summary_cards = {}
        tenors = [("1M", "1m"), ("2M", "2m"), ("3M", "3m"), ("6M", "6m")]
        for i, (label, key) in enumerate(tenors):
            card = SummaryCard(cards_frame, label, "-")
            card.grid(row=0, column=i, sticky="ew", padx=(0 if i == 0 else 5, 0))
            self.summary_cards[key] = card

        # ============================================================================
        # COLLAPSIBLE SECTION 1: Bloomberg CM + Excel Days
        # ============================================================================
        self.section1 = CollapsibleSection(container, "DETALJER: BLOOMBERG CM + EXCEL DAGAR",
                                           expanded=False, accent_color=THEME["good"])
        self.section1.pack(fill="x", padx=pad, pady=(10, 5))

        sec1_content = self.section1.content

        # USDNOK Table (Section 1)
        tk.Label(sec1_content, text="USDNOK", fg=THEME["muted"], bg=THEME["bg_panel"],
                 font=("Segoe UI", CURRENT_MODE["small"], "bold")).pack(anchor="w", pady=(5, 0))

        self.usd_table_bbg = DataTableTree(sec1_content, columns=[
            "TENOR", "USD RATE", "BBG DAYS", "EXC DAYS", "PIPS BBG", "PIPS EXC", "IMPLIED", "NOK CM"
        ], col_widths=[50, 70, 70, 70, 80, 80, 80, 70], height=4)
        self.usd_table_bbg.pack(fill="x", pady=(0, 5))

        # EURNOK Table (Section 1)
        tk.Label(sec1_content, text="EURNOK", fg=THEME["muted"], bg=THEME["bg_panel"],
                 font=("Segoe UI", CURRENT_MODE["small"], "bold")).pack(anchor="w")

        self.eur_table_bbg = DataTableTree(sec1_content, columns=[
            "TENOR", "EUR RATE", "BBG DAYS", "EXC DAYS", "PIPS BBG", "PIPS EXC", "IMPLIED", "NOK CM"
        ], col_widths=[50, 70, 70, 70, 80, 80, 80, 70], height=4)
        self.eur_table_bbg.pack(fill="x", pady=(0, 5))

        # Weighted (Section 1)
        tk.Label(sec1_content, text="VIKTAD (BBG CM)", fg=THEME["accent"], bg=THEME["bg_panel"],
                 font=("Segoe UI", CURRENT_MODE["small"], "bold")).pack(anchor="w")

        self.weighted_table_bbg = DataTableTree(sec1_content, columns=[
            "TENOR", "USD IMPL", "× 45%", "EUR IMPL", "× 5%", "NOK CM", "× 50%", "TOTAL"
        ], col_widths=[50, 70, 60, 70, 60, 70, 60, 80], height=4)
        self.weighted_table_bbg.pack(fill="x", pady=(0, 10))

        # ============================================================================
        # COLLAPSIBLE SECTION 2: Excel CM + Bloomberg Days
        # ============================================================================
        self.section2 = CollapsibleSection(container, "DETALJER: EXCEL CM + BLOOMBERG DAGAR",
                                           expanded=False, accent_color=THEME["warn"])
        self.section2.pack(fill="x", padx=pad, pady=(5, pad))

        sec2_content = self.section2.content

        # USDNOK Table (Section 2)
        tk.Label(sec2_content, text="USDNOK", fg=THEME["muted"], bg=THEME["bg_panel"],
                 font=("Segoe UI", CURRENT_MODE["small"], "bold")).pack(anchor="w", pady=(5, 0))

        self.usd_table_exc = DataTableTree(sec2_content, columns=[
            "TENOR", "USD RATE", "BBG DAYS", "PIPS BBG", "IMPLIED", "NOK CM"
        ], col_widths=[50, 70, 70, 90, 90, 70], height=4)
        self.usd_table_exc.pack(fill="x", pady=(0, 5))

        # EURNOK Table (Section 2)
        tk.Label(sec2_content, text="EURNOK", fg=THEME["muted"], bg=THEME["bg_panel"],
                 font=("Segoe UI", CURRENT_MODE["small"], "bold")).pack(anchor="w")

        self.eur_table_exc = DataTableTree(sec2_content, columns=[
            "TENOR", "EUR RATE", "BBG DAYS", "PIPS BBG", "IMPLIED", "NOK CM"
        ], col_widths=[50, 70, 70, 90, 90, 70], height=4)
        self.eur_table_exc.pack(fill="x", pady=(0, 5))

        # Weighted (Section 2)
        tk.Label(sec2_content, text="VIKTAD (EXCEL CM)", fg=THEME["accent"], bg=THEME["bg_panel"],
                 font=("Segoe UI", CURRENT_MODE["small"], "bold")).pack(anchor="w")

        self.weighted_table_exc = DataTableTree(sec2_content, columns=[
            "TENOR", "USD IMPL", "× 45%", "EUR IMPL", "× 5%", "NOK CM", "× 50%", "TOTAL"
        ], col_widths=[50, 70, 60, 70, 60, 70, 60, 80], height=4)
        self.weighted_table_exc.pack(fill="x", pady=(0, 10))

    def _on_model_change(self):
        """Called when calculation model selection changes."""
        model = self.calc_model.get()
        log.info(f"[NOK Implied] Calculation model changed to: {model}")
        # Note: Recalculation is triggered manually via Recalculate button
    
    def _get_ticker_val(self, ticker):
        """Get price value from cached market data."""
        data = self.app.cached_market_data or {}
        inf = data.get(ticker)
        if inf:
            return float(inf.get("price", 0.0))
        return None

    def _get_pips_from_excel(self, cell_address):
        """Get pips directly from Excel recon file with extensive debugging."""
        from openpyxl.utils import coordinate_to_tuple
        excel_data = self.app.cached_excel_data or {}
        
        log.info(f"[_get_pips_from_excel] Looking for cell {cell_address}")
        log.info(f"[_get_pips_from_excel] Excel data keys count: {len(excel_data)}")
        
        coord_tuple = coordinate_to_tuple(cell_address)
        log.info(f"[_get_pips_from_excel] Converted to tuple: {coord_tuple}")
        
        val = excel_data.get(coord_tuple, None)
        
        if val is None:
            log.info(f"[_get_pips_from_excel] [ERROR] Cell {cell_address} ({coord_tuple}) not found in Excel data")
            # Print first few keys to debug
            sample_keys = list(excel_data.keys())[:10]
            log.info(f"[_get_pips_from_excel] Sample keys (first 10): {sample_keys}")
        else:
            log.info(f"[_get_pips_from_excel] [OK] Found {cell_address} = {val}")
        
        if val is not None:
            result = safe_float(val, None)
            log.info(f"[_get_pips_from_excel] Parsed to: {result}")
            return result
        return None

    def _get_weights(self):
        """Get weights from Excel engine or use defaults."""
        weights = {"USD": 0.445, "EUR": 0.055, "NOK": 0.50}
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
        log.info("========== NOK Implied Page UPDATE STARTED ==========")
        log.info(f"[NOK Implied Page] cached_excel_data length: {len(self.app.cached_excel_data)}")
        log.info(f"[NOK Implied Page] cached_market_data length: {len(self.app.cached_market_data or {})}")
        
        # Check if Excel data is loaded
        if not self.app.cached_excel_data or len(self.app.cached_excel_data) < 10:
            log.info(f"[NOK Implied Page] ❌ Excel data not loaded or insufficient! Skipping update.")
            log.info(f"[NOK Implied Page] Excel data needs at least 10 cells, currently has: {len(self.app.cached_excel_data)}")
            # Optionally trigger reload
            if hasattr(self.app, 'excel_engine'):
                log.info(f"[NOK Implied Page] Attempting to check Excel engine recon_data...")
                if self.app.excel_engine.recon_data:
                    log.info(f"[NOK Implied Page] Excel engine has recon_data with {len(self.app.excel_engine.recon_data)} entries")
                    log.info(f"[NOK Implied Page] But cached_excel_data is not populated. This is a sync issue.")
                else:
                    log.info(f"[NOK Implied Page] Excel engine recon_data is also empty.")
            return
        
        log.info(f"[NOK Implied Page] [OK] Excel data loaded with {len(self.app.cached_excel_data)} cells")
        
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
            text=f"VIKTER:  USD = {weights['USD']*100:.3f}%  |  EUR = {weights['EUR']*100:.3f}%  |  NOK = {weights['NOK']*100:.3f}%"
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
        
        # Initialize calculation data storage for Dashboard
        if not hasattr(self.app, 'impl_calc_data'):
            self.app.impl_calc_data = {}

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

            log.debug(f"========== TENOR {t['tenor']} ==========")
            
            # Get pips directly from Bloomberg market data (FRESH DATA!)
            pips_bbg_usd = self._get_ticker_val(t["usd_fwd"])
            log.info(f"[NOK Implied] USD: pips from Bloomberg ({t['usd_fwd']}) = {pips_bbg_usd}")
            
            pips_bbg_eur = self._get_ticker_val(t["eur_fwd"])
            log.info(f"[NOK Implied] EUR: pips from Bloomberg ({t['eur_fwd']}) = {pips_bbg_eur}")

            # NOK CM (same for both sections)
            nok_cm = self._get_ticker_val(t["nok_cm"]) if t["nok_cm"] else None
            log.info(f"[NOK Implied] NOK CM: {nok_cm}")

            # ============ SECTION 1: Bloomberg CM + Bloomberg TPSF Days ============
            # USD: Use Bloomberg TPSF days directly (NO adjustment!)
            usd_rate_bbg = self._get_ticker_val(t["usd_rate_bbg"]) if t["usd_rate_bbg"] else None
            log.info(f"[NOK Implied] USD Bloomberg CM Rate: {usd_rate_bbg}")
            log.info(f"[NOK Implied] USD Spot: {usd_spot}")
            log.info(f"[NOK Implied] USD BBG TPSF Days: {bbg_days_usd}")
            log.info(f"[NOK Implied] CALLING calc_implied_yield for USD with BBG DAYS...")
            impl_usd_bbg = calc_implied_yield(usd_spot, pips_bbg_usd, usd_rate_bbg, bbg_days_usd) if bbg_days_usd else None

            # EUR: Use Bloomberg TPSF days directly (NO adjustment!)
            eur_rate_bbg = self._get_ticker_val(t["eur_rate_bbg"]) if t["eur_rate_bbg"] else None
            log.info(f"[NOK Implied] EUR Bloomberg CM Rate: {eur_rate_bbg}")
            log.info(f"[NOK Implied] EUR Spot: {eur_spot}")
            log.info(f"[NOK Implied] EUR BBG TPSF Days: {bbg_days_eur}")
            log.info(f"[NOK Implied] CALLING calc_implied_yield for EUR with BBG DAYS...")
            impl_eur_bbg = calc_implied_yield(eur_spot, pips_bbg_eur, eur_rate_bbg, bbg_days_eur) if bbg_days_eur else None

            # Add rows to Section 1 tables (using BBG TPSF days directly)
            self.usd_table_bbg.add_row([
                t["tenor"], fmt_rate(usd_rate_bbg),
                fmt_days(bbg_days_usd), fmt_days(excel_days),
                fmt_pips(pips_bbg_usd), fmt_pips(pips_bbg_usd),
                fmt_impl(impl_usd_bbg), fmt_rate(nok_cm)
            ], style="normal")

            self.eur_table_bbg.add_row([
                t["tenor"], fmt_rate(eur_rate_bbg),
                fmt_days(bbg_days_eur), fmt_days(excel_days),
                fmt_pips(pips_bbg_eur), fmt_pips(pips_bbg_eur),
                fmt_impl(impl_eur_bbg), fmt_rate(nok_cm)
            ], style="normal")

            implied_data_bbg.append({
                "tenor": t["tenor"], "impl_usd": impl_usd_bbg, "impl_eur": impl_eur_bbg, "nok_cm": nok_cm
            })
            
            # Store calculation data for Dashboard funding rates
            # NORE MODEL (Bloomberg CM) - using BBG days
            self.app.impl_calc_data[f"usd_{t['key']}"] = {
                "spot": usd_spot, "pips": pips_bbg_usd, "rate": usd_rate_bbg, 
                "days": bbg_days_usd, "implied": impl_usd_bbg, "nok_cm": nok_cm,
                "rate_label": "Bloomberg CM"
            }
            self.app.impl_calc_data[f"eur_{t['key']}"] = {
                "spot": eur_spot, "pips": pips_bbg_eur, "rate": eur_rate_bbg, 
                "days": bbg_days_eur, "implied": impl_eur_bbg, "nok_cm": nok_cm,
                "rate_label": "Bloomberg CM"
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
            
            # ALSO store NIBOR MODEL data (Internal Basket Rates)
            self.app.impl_calc_data[f"usd_{t['key']}_nibor"] = {
                "spot": usd_spot, "pips": pips_bbg_usd, "rate": usd_rate_exc, 
                "days": bbg_days_usd, "implied": impl_usd_exc, "nok_cm": nok_cm,
                "rate_label": "Internal Basket"
            }
            self.app.impl_calc_data[f"eur_{t['key']}_nibor"] = {
                "spot": eur_spot, "pips": pips_bbg_eur, "rate": eur_rate_exc, 
                "days": bbg_days_eur, "implied": impl_eur_exc, "nok_cm": nok_cm,
                "rate_label": "Internal Basket"
            }

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

        # Add weighted rows for Section 2 and update summary cards
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

            # Update summary cards with the weighted totals (using Excel CM data - Section 2)
            tenor_key = d["tenor"].lower()
            if tenor_key in self.summary_cards:
                if total is not None:
                    self.summary_cards[tenor_key].set_value(f"{total:.2f}%")
                else:
                    self.summary_cards[tenor_key].set_value("-")


class WeightsPage(tk.Frame):
    """Weights history page - shows all historical weights from Wheights.xlsx."""

    def __init__(self, master, app):
        super().__init__(master, bg=THEME["bg_panel"])
        self.app = app
        pad = CURRENT_MODE["pad"]

        top = tk.Frame(self, bg=THEME["bg_panel"])
        top.pack(fill="x", padx=pad, pady=(pad, 10))

        tk.Label(top, text="WEIGHTS HISTORY", fg=THEME["muted"], bg=THEME["bg_panel"],
                 font=("Segoe UI", CURRENT_MODE["h2"], "bold")).pack(side="left")

        OnyxButtonTK(top, "Refresh Weights", command=self.update, variant="default").pack(side="right")

        # Info label
        info_frame = tk.Frame(self, bg=THEME["bg_panel"])
        info_frame.pack(fill="x", padx=pad, pady=(0, 10))
        
        tk.Label(info_frame, text="📊 All weights from Wheights.xlsx (latest first)",
                fg=THEME["muted"], bg=THEME["bg_panel"],
                font=("Segoe UI", CURRENT_MODE["small"], "italic")).pack(anchor="w")

        # Table with weights history
        self.table = DataTableTree(self, columns=["DATE", "USD", "EUR", "NOK", "SUM", "STATUS"],
                                   col_widths=[150, 120, 120, 120, 120, 150], height=22)
        self.table.pack(fill="both", expand=True, padx=pad, pady=(0, pad))

    def update(self):
        """Update weights table with all historical data."""
        from config import WEIGHTS_FILE
        
        self.table.clear()
        
        if not hasattr(self.app, 'excel_engine'):
            self.table.add_row(["ERROR", "-", "-", "-", "-", "Excel engine not available"], style="bad")
            return
        
        # Get all weights history
        weights_history = self.app.excel_engine.get_all_weights_history(WEIGHTS_FILE)
        
        if not weights_history:
            self.table.add_row(["NO DATA", "-", "-", "-", "-", "Could not load weights file"], style="bad")
            return
        
        # Display all weights (newest first)
        for i, w in enumerate(weights_history):
            date_str = w["date"].strftime("%Y-%m-%d")
            usd_str = f"{w['USD']:.4f}" if w['USD'] is not None else "-"
            eur_str = f"{w['EUR']:.4f}" if w['EUR'] is not None else "-"
            nok_str = f"{w['NOK']:.4f}" if w['NOK'] is not None else "-"
            
            # Calculate sum
            try:
                total = w['USD'] + w['EUR'] + w['NOK']
                sum_str = f"{total:.4f}"
                
                # Check if sum is close to 1.0
                is_valid = abs(total - 1.0) < 0.0001
                status = "✓ Valid" if is_valid else f"⚠ Sum ≠ 1.0"
                style = "good" if is_valid else "warn"
            except (TypeError, ValueError):
                sum_str = "ERROR"
                status = "✗ Invalid"
                style = "bad"
            
            # Mark first row (latest) differently
            if i == 0:
                status = "✓ LATEST (Active)"
                style = "good"
            
            self.table.add_row([date_str, usd_str, eur_str, nok_str, sum_str, status], style=style)


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
        self.table.add_row(["Publication Delay", "24h (T+1)", "License", "Active"], style="normal")
        self.table.add_row(["Calculation Agent", "GRSS", "System", "Active"], style="normal")
        self.table.add_row(["Calculation Agent", "GRSS", "System", "Active"], style="normal")
        self.table.add_row(["Algorithm", "Waterfall Level 1", "Manual", "Info"], style="section")


class HistoryPage(tk.Frame):
    """History page showing saved NIBOR snapshots with change tracking."""

    def __init__(self, master, app):
        super().__init__(master, bg=THEME["bg_panel"])
        self.app = app
        pad = CURRENT_MODE["pad"]

        # Header
        top = tk.Frame(self, bg=THEME["bg_panel"])
        top.pack(fill="x", padx=pad, pady=(pad, 10))

        tk.Label(top, text="NIBOR HISTORY", fg=THEME["muted"], bg=THEME["bg_panel"],
                 font=("Segoe UI", CURRENT_MODE["h2"], "bold")).pack(side="left")

        btn_frame = tk.Frame(top, bg=THEME["bg_panel"])
        btn_frame.pack(side="right")

        OnyxButtonTK(btn_frame, "Save Snapshot", command=self._save_now, variant="accent").pack(side="left", padx=5)
        OnyxButtonTK(btn_frame, "Refresh", command=self.update, variant="default").pack(side="left")

        # Info label
        info_frame = tk.Frame(self, bg=THEME["bg_panel"])
        info_frame.pack(fill="x", padx=pad, pady=(0, 10))

        tk.Label(info_frame, text="Saved NIBOR calculations with daily changes (click row for details)",
                fg=THEME["muted"], bg=THEME["bg_panel"],
                font=("Segoe UI", CURRENT_MODE["small"], "italic")).pack(anchor="w")

        # Main content area - split horizontally
        content = tk.Frame(self, bg=THEME["bg_panel"])
        content.pack(fill="both", expand=True, padx=pad, pady=(0, pad))

        # Left: Rates table
        left_frame = tk.Frame(content, bg=THEME["bg_panel"])
        left_frame.pack(side="left", fill="both", expand=True)

        self.table = DataTableTree(
            left_frame,
            columns=["DATE", "1M", "CHG", "2M", "CHG", "3M", "CHG", "6M", "CHG", "MODEL", "USER"],
            col_widths=[100, 65, 50, 65, 50, 65, 50, 65, 50, 80, 80],
            height=18
        )
        self.table.pack(fill="both", expand=True)
        self.table.tree.bind("<<TreeviewSelect>>", self._on_row_select)

        # Right: Detail panel
        right_frame = tk.Frame(content, bg=THEME["bg_card"], width=280,
                              highlightthickness=1, highlightbackground=THEME["border"])
        right_frame.pack(side="right", fill="y", padx=(15, 0))
        right_frame.pack_propagate(False)

        tk.Label(right_frame, text="SNAPSHOT DETAILS", fg=THEME["muted"], bg=THEME["bg_card"],
                 font=("Segoe UI", CURRENT_MODE["small"], "bold")).pack(anchor="w", padx=12, pady=(12, 8))

        self.detail_text = tk.Text(right_frame, bg=THEME["bg_card"], fg=THEME["text"],
                                   font=("Consolas", 9), relief="flat", wrap="word",
                                   highlightthickness=0)
        self.detail_text.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self.detail_text.config(state="disabled")

        # Store history data for selection lookup
        self._history_data = {}

    def _save_now(self):
        """Save current state as a snapshot."""
        try:
            date_key = save_snapshot(self.app)
            log.info(f"Snapshot saved: {date_key}")
            self.update()
        except Exception as e:
            log.error(f"Failed to save snapshot: {e}")

    def _format_chg(self, chg):
        """Format change value with sign."""
        if chg is None:
            return "-"
        if chg > 0:
            return f"+{chg:.2f}"
        elif chg < 0:
            return f"{chg:.2f}"
        return "0.00"

    def update(self):
        """Update the history table."""
        self.table.clear()
        self._history_data = load_history()

        table_data = get_rates_table_data(limit=50)

        if not table_data:
            self.table.add_row(["-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-"], style="normal")
            self._show_detail("No snapshots saved yet.\n\nClick 'Save Snapshot' to save current NIBOR calculation.")
            return

        for row in table_data:
            values = [
                row['date'],
                f"{row['1m']:.2f}" if row['1m'] is not None else "-",
                self._format_chg(row['1m_chg']),
                f"{row['2m']:.2f}" if row['2m'] is not None else "-",
                self._format_chg(row['2m_chg']),
                f"{row['3m']:.2f}" if row['3m'] is not None else "-",
                self._format_chg(row['3m_chg']),
                f"{row['6m']:.2f}" if row['6m'] is not None else "-",
                self._format_chg(row['6m_chg']),
                row.get('model', '-'),
                row.get('user', '-')
            ]
            self.table.add_row(values, style="normal")

        # Show first row details
        if table_data:
            self._show_snapshot_detail(table_data[0]['date'])

    def _on_row_select(self, event):
        """Handle row selection to show details."""
        selection = self.table.tree.selection()
        if selection:
            item = self.table.tree.item(selection[0])
            values = item['values']
            if values:
                date_key = str(values[0])
                self._show_snapshot_detail(date_key)

    def _show_snapshot_detail(self, date_key: str):
        """Show detailed info for a snapshot."""
        snapshot = self._history_data.get(date_key)
        if not snapshot:
            self._show_detail(f"No details available for {date_key}")
            return

        lines = []
        lines.append(f"Date: {date_key}")
        lines.append(f"Time: {snapshot.get('timestamp', '-')[11:19]}")
        lines.append(f"User: {snapshot.get('user', '-')}")
        lines.append(f"Machine: {snapshot.get('machine', '-')}")
        lines.append(f"Model: {snapshot.get('model', '-')}")
        lines.append("")

        # Weights
        weights = snapshot.get('weights', {})
        if weights:
            lines.append("WEIGHTS:")
            lines.append(f"  USD: {weights.get('USD', '-')}")
            lines.append(f"  EUR: {weights.get('EUR', '-')}")
            lines.append(f"  NOK: {weights.get('NOK', '-')}")
            lines.append("")

        # Rates detail
        rates = snapshot.get('rates', {})
        if rates:
            lines.append("RATES BREAKDOWN:")
            for tenor in ['1m', '2m', '3m', '6m']:
                t_data = rates.get(tenor, {})
                lines.append(f"  {tenor.upper()}:")
                lines.append(f"    Funding: {t_data.get('funding', '-')}")
                lines.append(f"    Spread:  {t_data.get('spread', '-')}")
                lines.append(f"    NIBOR:   {t_data.get('nibor', '-')}")
                lines.append(f"    EUR Impl:{t_data.get('eur_impl', '-')}")
                lines.append(f"    USD Impl:{t_data.get('usd_impl', '-')}")
                lines.append(f"    NOK CM:  {t_data.get('nok_cm', '-')}")
            lines.append("")

        # Alerts
        alerts = snapshot.get('alerts', [])
        if alerts:
            lines.append("ALERTS:")
            for a in alerts:
                lines.append(f"  - {a}")

        self._show_detail("\n".join(lines))

    def _show_detail(self, text: str):
        """Update detail panel text."""
        self.detail_text.config(state="normal")
        self.detail_text.delete("1.0", "end")
        self.detail_text.insert("1.0", text)
        self.detail_text.config(state="disabled")
