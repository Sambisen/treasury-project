"""
Page classes for Nibor Calculation Terminal.
Contains all specific page views.
"""
import tkinter as tk
from tkinter import ttk
from datetime import datetime, timedelta

from config import THEME, FONTS, CURRENT_MODE, RULES_DB, MARKET_STRUCTURE, ALERTS_BOX_HEIGHT, get_logger

log = get_logger("ui_pages")
from ui_components import OnyxButtonTK, MetricChipTK, DataTableTree, SummaryCard, CollapsibleSection
from utils import safe_float
from calculations import calc_implied_yield
from history import (
    save_snapshot, get_rates_table_data, get_snapshot, load_history,
    get_previous_day_rates, get_fixing_table_data, get_fixing_history_for_charts
)

# Import chart components (optional - graceful fallback if matplotlib not available)
try:
    from charts import TrendChart, TrendPopup, ComparisonView, MATPLOTLIB_AVAILABLE
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    TrendChart = None
    TrendPopup = None
    ComparisonView = None


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
        header_row = tk.Frame(content, bg=THEME["bg_panel"])
        header_row.pack(anchor="center", pady=(10, 15))

        tk.Label(header_row, text="🇳🇴 NIBOR RATES (LIVE)",
                fg=THEME["accent_secondary"],
                bg=THEME["bg_panel"],
                font=FONTS["h2"]).pack(side="left")

        # Trend icon - opens popup with history chart
        if MATPLOTLIB_AVAILABLE and TrendPopup:
            trend_icon = tk.Label(header_row, text="📈",
                                 fg=THEME["muted"],
                                 bg=THEME["bg_panel"],
                                 font=("Segoe UI", 16),
                                 cursor="hand2")
            trend_icon.pack(side="left", padx=(10, 0))
            trend_icon.bind("<Button-1>", lambda e: self._show_trend_popup())
            trend_icon.bind("<Enter>", lambda e: trend_icon.config(fg=THEME["accent"]))
            trend_icon.bind("<Leave>", lambda e: trend_icon.config(fg=THEME["muted"]))
            ToolTip(trend_icon, lambda: "Click to view NIBOR trend history")

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

            # CHG (Change from last saved snapshot)
            chg_lbl = tk.Label(funding_frame, text="-",
                              fg=THEME["muted"], bg=THEME["bg_card"],
                              font=("Consolas", CURRENT_MODE["body"]),
                              width=8, anchor="center")
            chg_lbl.grid(row=row_idx, column=4, padx=5, pady=6, sticky="ew")
            cells["chg"] = chg_lbl

            # Tooltip showing previous NIBOR rate for sanity check
            tenor_key_chg = tenor["key"]
            ToolTip(chg_lbl, lambda t=tenor_key_chg: self._get_chg_tooltip(t))

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
        # CONFIRM RATES BUTTON - Below the NIBOR Rates table
        # ====================================================================
        confirm_btn_frame = tk.Frame(content, bg=THEME["bg_panel"])
        confirm_btn_frame.pack(anchor="center", pady=(15, 0))

        self.confirm_rates_btn = OnyxButtonTK(
            confirm_btn_frame,
            "Confirm rates",
            command=self._on_confirm_rates,
            variant="primary"
        )
        self.confirm_rates_btn.pack()

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

    def _on_confirm_rates(self):
        """Handle Confirm rates button click."""
        from history import confirm_rates
        from tkinter import messagebox

        log.info("[Dashboard] Confirm rates button clicked")

        # Disable button during operation
        self.confirm_rates_btn.configure(state="disabled", text="Confirming...")

        def do_confirm():
            try:
                success, message = confirm_rates(self.app)

                # Update UI on main thread
                def update_ui():
                    self.confirm_rates_btn.configure(state="normal", text="Confirm rates")

                    if success:
                        # Show success message
                        messagebox.showinfo(
                            "Rates Confirmed",
                            message
                        )
                        # Show toast notification if available
                        if hasattr(self.app, 'toast'):
                            self.app.toast.success(message)
                        log.info(f"[Dashboard] {message}")
                    else:
                        # Show error message
                        messagebox.showerror(
                            "Confirmation Failed",
                            message
                        )
                        if hasattr(self.app, 'toast'):
                            self.app.toast.error(message)
                        log.error(f"[Dashboard] {message}")

                self.after(0, update_ui)

            except Exception as e:
                def show_error():
                    self.confirm_rates_btn.configure(state="normal", text="Confirm rates")
                    error_msg = f"Error confirming rates: {e}"
                    messagebox.showerror("Error", error_msg)
                    log.error(f"[Dashboard] {error_msg}")

                self.after(0, show_error)

        # Run in background thread to avoid blocking UI
        import threading
        threading.Thread(target=do_confirm, daemon=True).start()

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

    def _show_trend_popup(self):
        """Show popup with NIBOR trend history chart."""
        if not TrendPopup:
            return

        # ÄNDRING: Vi hämtar inte data här längre, och skickar inte med det.
        # Popupen hämtar sin egen data (både fixing och contribution).
        
        popup = TrendPopup(self.winfo_toplevel())
        popup.grab_set()
        
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

            # CHG (Change from last saved snapshot)
            if "chg" in cells:
                prev_nibor = None
                if prev_rates and tenor_key in prev_rates:
                    prev_nibor = prev_rates[tenor_key].get('nibor')

                if final_rate is not None and prev_nibor is not None:
                    chg = final_rate - prev_nibor
                    if chg > 0:
                        chg_text = f"+{chg:.2f}"
                        chg_color = THEME["good"]  # Green for increase
                    elif chg < 0:
                        chg_text = f"{chg:.2f}"
                        chg_color = THEME["bad"]   # Red for decrease
                    else:
                        chg_text = "0.00"
                        chg_color = THEME["muted"]
                    cells["chg"].config(text=chg_text, fg=chg_color)
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

    def _get_chg_tooltip(self, tenor_key):
        """Get previous NIBOR rate and date for CHG tooltip."""
        from history import get_previous_day_rates, load_history

        prev_rates = get_previous_day_rates()
        if not prev_rates or tenor_key not in prev_rates:
            return "No previous data"

        prev_nibor = prev_rates[tenor_key].get('nibor')
        if prev_nibor is None:
            return "No previous rate"

        # Get the date of the previous snapshot
        history = load_history()
        dates = sorted(history.keys(), reverse=True)
        today = datetime.now().strftime("%Y-%m-%d")

        prev_date = None
        for d in dates:
            if d < today:
                prev_date = d
                break

        if prev_date:
            return f"Prev: {prev_nibor:.2f}%\nDate: {prev_date}"
        else:
            return f"Prev: {prev_nibor:.2f}%"

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

        OnyxButtonTK(btn_frame, "Confirm Nibor", command=self._confirm_nibor, variant="accent").pack(side="left", padx=5)
        OnyxButtonTK(btn_frame, "Save Snapshot", command=self._save_now, variant="default").pack(side="left", padx=5)
        OnyxButtonTK(btn_frame, "Refresh", command=self.update, variant="default").pack(side="left")

        # View toggle (Contribution vs Fixing)
        view_frame = tk.Frame(self, bg=THEME["bg_panel"])
        view_frame.pack(fill="x", padx=pad, pady=(10, 5))

        tk.Label(view_frame, text="View:", fg=THEME["muted"], bg=THEME["bg_panel"],
                font=("Segoe UI", CURRENT_MODE["body"])).pack(side="left")

        self.history_view_var = tk.StringVar(value="fixing")

        contribution_radio = tk.Radiobutton(
            view_frame, text="Swedbank Contribution",
            variable=self.history_view_var, value="contribution",
            command=self._on_view_change,
            bg=THEME["bg_panel"], fg=THEME["text"],
            selectcolor=THEME["bg_card"],
            activebackground=THEME["bg_panel"],
            activeforeground=THEME["accent"],
            font=FONTS["body"]
        )
        contribution_radio.pack(side="left", padx=(10, 5))

        fixing_radio = tk.Radiobutton(
            view_frame, text="NIBOR Fixing",
            variable=self.history_view_var, value="fixing",
            command=self._on_view_change,
            bg=THEME["bg_panel"], fg=THEME["text"],
            selectcolor=THEME["bg_card"],
            activebackground=THEME["bg_panel"],
            activeforeground=THEME["accent"],
            font=FONTS["body"]
        )
        fixing_radio.pack(side="left", padx=5)

        # Entry count label
        self._entry_count_lbl = tk.Label(view_frame, text="",
                                         fg=THEME["muted"], bg=THEME["bg_panel"],
                                         font=("Segoe UI", CURRENT_MODE["small"]))
        self._entry_count_lbl.pack(side="right")

        # Trend chart (collapsible)
        if MATPLOTLIB_AVAILABLE and TrendChart:
            chart_section = CollapsibleSection(self, "Trend Graph", expanded=False, accent_color=THEME["accent"])
            chart_section.pack(fill="x", padx=pad, pady=(0, 10))
            self.trend_chart = TrendChart(chart_section.content, height=200)
            self.trend_chart.pack(fill="x", pady=5)
        else:
            self.trend_chart = None

        # Info label
        info_frame = tk.Frame(self, bg=THEME["bg_panel"])
        info_frame.pack(fill="x", padx=pad, pady=(0, 10))

        tk.Label(info_frame, text="Saved NIBOR calculations with daily changes (click row for details)",
                fg=THEME["muted"], bg=THEME["bg_panel"],
                font=("Segoe UI", CURRENT_MODE["small"], "italic")).pack(anchor="w")

        # Search frame
        search_frame = tk.Frame(self, bg=THEME["bg_panel"])
        search_frame.pack(fill="x", padx=pad, pady=(0, 10))

        tk.Label(search_frame, text="Sök datum:", fg=THEME["text"], bg=THEME["bg_panel"],
                font=("Segoe UI", CURRENT_MODE["body"])).pack(side="left")

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self._on_search_change)
        self.search_entry = tk.Entry(search_frame, textvariable=self.search_var,
                                     bg=THEME["bg_card"], fg=THEME["text"],
                                     insertbackground=THEME["text"],
                                     font=("Consolas", CURRENT_MODE["body"]),
                                     width=15, relief="flat",
                                     highlightthickness=1, highlightbackground=THEME["border"])
        self.search_entry.pack(side="left", padx=(8, 8))

        OnyxButtonTK(search_frame, "Rensa", command=self._clear_search, variant="default").pack(side="left")

        # Export buttons frame
        export_frame = tk.Frame(self, bg=THEME["bg_panel"])
        export_frame.pack(fill="x", padx=pad, pady=(0, 10))

        OnyxButtonTK(export_frame, "Export Selected", command=self._export_selected, variant="accent").pack(side="left", padx=(0, 5))
        OnyxButtonTK(export_frame, "Export PDF", command=self._export_pdf, variant="default").pack(side="left", padx=5)
        OnyxButtonTK(export_frame, "Compare", command=self._compare_selected, variant="default").pack(side="left", padx=5)
        OnyxButtonTK(export_frame, "Select All", command=self._select_all, variant="default").pack(side="left", padx=5)
        OnyxButtonTK(export_frame, "Deselect All", command=self._deselect_all, variant="default").pack(side="left", padx=5)

        self._selected_label = tk.Label(export_frame, text="0 selected", fg=THEME["muted"], bg=THEME["bg_panel"],
                                        font=("Segoe UI", CURRENT_MODE["small"]))
        self._selected_label.pack(side="left", padx=15)

        # Store all table data for filtering
        self._all_table_data = []
        self._selected_dates = set()  # Track selected dates

        # Main content area - split horizontally
        content = tk.Frame(self, bg=THEME["bg_panel"])
        content.pack(fill="both", expand=True, padx=pad, pady=(0, pad))

        # Left: Rates table
        left_frame = tk.Frame(content, bg=THEME["bg_panel"])
        left_frame.pack(side="left", fill="both", expand=True)

        # Table for contribution view (default columns)
        self._contribution_columns = ["SEL", "DATE", "1M", "CHG", "2M", "CHG", "3M", "CHG", "6M", "CHG", "MODEL", "USER"]
        self._contribution_widths = [30, 90, 60, 45, 60, 45, 60, 45, 60, 45, 75, 70]

        # Table for fixing view (includes 1W, no MODEL/USER)
        self._fixing_columns = ["SEL", "DATE", "1W", "CHG", "1M", "CHG", "2M", "CHG", "3M", "CHG", "6M", "CHG"]
        self._fixing_widths = [30, 90, 55, 45, 55, 45, 55, 45, 55, 45, 55, 45]

        # Start with fixing view
        self.table = DataTableTree(
            left_frame,
            columns=self._fixing_columns,
            col_widths=self._fixing_widths,
            height=18
        )
        self.table.pack(fill="both", expand=True)
        self.table.tree.bind("<<TreeviewSelect>>", self._on_row_select)
        self.table.tree.bind("<Button-1>", self._on_table_click)

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

    def _confirm_nibor(self):
        """Confirm NIBOR: save snapshot AND write stamp to Excel."""
        import tkinter.messagebox as messagebox

        # First save to log
        try:
            date_key = save_snapshot(self.app)
            log.info(f"Snapshot saved: {date_key}")
        except Exception as e:
            log.error(f"Failed to save snapshot: {e}")
            messagebox.showerror("Error", f"Failed to save snapshot: {e}")
            return

        # Then write stamp to Excel
        if hasattr(self.app, 'excel_engine') and self.app.excel_engine:
            success, msg = self.app.excel_engine.write_confirmation_stamp()
            if success:
                log.info(f"Confirmation stamp written: {msg}")
                messagebox.showinfo("Nibor Confirmed", f"✓ NIBOR confirmed and logged!\n\n{msg}")
            else:
                log.error(f"Failed to write stamp: {msg}")
                messagebox.showwarning("Warning", f"Snapshot saved but Excel stamp failed:\n\n{msg}")
        else:
            messagebox.showwarning("Warning", "Snapshot saved but Excel engine not available for stamp.")

        # Refresh the table
        self.update()

    def _format_chg(self, chg):
        """Format change value with sign."""
        if chg is None:
            return "-"
        if chg > 0:
            return f"+{chg:.2f}"
        elif chg < 0:
            return f"{chg:.2f}"
        return "0.00"

    def _on_view_change(self):
        """Handle view toggle between Contribution and Fixing."""
        self.update()

    def update(self):
        """Update the history table based on selected view."""
        self.table.clear()
        self._history_data = load_history()
        view = self.history_view_var.get()

        if view == "fixing":
            # Get fixing history (up to 500 entries for full history)
            table_data = get_fixing_table_data(limit=500)
            self._all_table_data = table_data

            # Update entry count
            self._entry_count_lbl.config(text=f"{len(table_data)} fixing entries")

            # Update trend chart with fixing data
            if self.trend_chart:
                chart_data = get_fixing_history_for_charts(limit=90)
                if chart_data:
                    self.trend_chart.set_data(chart_data, data_type="fixing")

            if not table_data:
                self.table.add_row(["", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-"], style="normal")
                self._show_detail("No NIBOR fixings saved yet.\n\nFixings are imported from Bloomberg BDH or Excel.")
                return

        else:  # contribution view
            table_data = get_rates_table_data(limit=50)
            self._all_table_data = table_data

            # Update entry count
            self._entry_count_lbl.config(text=f"{len(table_data)} contribution entries")

            # Update trend chart with contribution data
            if self.trend_chart and table_data:
                self.trend_chart.set_data(table_data, data_type="contribution")

            if not table_data:
                self.table.add_row(["", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-"], style="normal")
                self._show_detail("No snapshots saved yet.\n\nClick 'Save Snapshot' to save current NIBOR calculation.")
                return

        # Apply search filter if active
        search_text = self.search_var.get().strip()
        if search_text:
            self._filter_table(search_text)
        else:
            self._populate_table(table_data)

    def _populate_table(self, table_data, highlight_single=False):
        """Populate table with data based on current view."""
        self.table.clear()
        view = self.history_view_var.get()

        if not table_data:
            empty_cols = 12 if view == "fixing" else 12
            self.table.add_row([""] + ["-"] * (empty_cols - 1), style="normal")
            return

        for row in table_data:
            # Check if this date is selected
            is_selected = row['date'] in self._selected_dates
            checkbox = "☑" if is_selected else "☐"

            if view == "fixing":
                # Fixing view: SEL, DATE, 1W, CHG, 1M, CHG, 2M, CHG, 3M, CHG, 6M, CHG
                values = [
                    checkbox,
                    row['date'],
                    f"{row['1w']:.2f}" if row.get('1w') is not None else "-",
                    self._format_chg(row.get('1w_chg')),
                    f"{row['1m']:.2f}" if row.get('1m') is not None else "-",
                    self._format_chg(row.get('1m_chg')),
                    f"{row['2m']:.2f}" if row.get('2m') is not None else "-",
                    self._format_chg(row.get('2m_chg')),
                    f"{row['3m']:.2f}" if row.get('3m') is not None else "-",
                    self._format_chg(row.get('3m_chg')),
                    f"{row['6m']:.2f}" if row.get('6m') is not None else "-",
                    self._format_chg(row.get('6m_chg')),
                ]
            else:
                # Contribution view: SEL, DATE, 1M, CHG, 2M, CHG, 3M, CHG, 6M, CHG, MODEL, USER
                values = [
                    checkbox,
                    row['date'],
                    f"{row['1m']:.2f}" if row.get('1m') is not None else "-",
                    self._format_chg(row.get('1m_chg')),
                    f"{row['2m']:.2f}" if row.get('2m') is not None else "-",
                    self._format_chg(row.get('2m_chg')),
                    f"{row['3m']:.2f}" if row.get('3m') is not None else "-",
                    self._format_chg(row.get('3m_chg')),
                    f"{row['6m']:.2f}" if row.get('6m') is not None else "-",
                    self._format_chg(row.get('6m_chg')),
                    row.get('model', '-'),
                    row.get('user', '-')
                ]

            self.table.add_row(values, style="normal")

        self._update_selected_count()

        # If single result from search, highlight in orange and select it
        if highlight_single and len(table_data) == 1:
            items = self.table.tree.get_children()
            if items:
                # Configure orange tag for highlighting
                self.table.tree.tag_configure("search_match", background="#FF8C00", foreground="white")
                self.table.tree.item(items[0], tags=("search_match",))
                self.table.tree.selection_set(items[0])
                self._show_snapshot_detail(table_data[0]['date'])
        elif table_data:
            # Show first row details
            self._show_snapshot_detail(table_data[0]['date'])

    def _on_search_change(self, *args):
        """Handle search text change."""
        search_text = self.search_var.get().strip()
        if search_text:
            self._filter_table(search_text)
        else:
            # Reset to show all data
            self._populate_table(self._all_table_data)

    def _filter_table(self, search_text: str):
        """Filter table by date search."""
        if not self._all_table_data:
            return

        # Filter rows where date contains search text
        filtered = [row for row in self._all_table_data if search_text in row['date']]
        self._populate_table(filtered, highlight_single=True)

    def _clear_search(self):
        """Clear search and show all data."""
        self.search_var.set("")
        self._populate_table(self._all_table_data)

    def _on_row_select(self, event):
        """Handle row selection to show details."""
        selection = self.table.tree.selection()
        if selection:
            item = self.table.tree.item(selection[0])
            values = item['values']
            if values and len(values) > 1:
                date_key = str(values[1])  # Date is now column 1 (after checkbox)
                self._show_snapshot_detail(date_key)

    def _on_table_click(self, event):
        """Handle click on table - toggle checkbox if clicked on SEL column."""
        region = self.table.tree.identify_region(event.x, event.y)
        if region != "cell":
            return

        column = self.table.tree.identify_column(event.x)
        if column != "#1":  # First column (SEL)
            return

        item = self.table.tree.identify_row(event.y)
        if not item:
            return

        values = self.table.tree.item(item, 'values')
        if not values or len(values) < 2:
            return

        date_key = str(values[1])  # Date is column 1

        # Toggle selection
        if date_key in self._selected_dates:
            self._selected_dates.remove(date_key)
        else:
            self._selected_dates.add(date_key)

        # Update the checkbox display
        new_checkbox = "☑" if date_key in self._selected_dates else "☐"
        new_values = list(values)
        new_values[0] = new_checkbox
        self.table.tree.item(item, values=new_values)

        self._update_selected_count()

    def _update_selected_count(self):
        """Update the selected count label."""
        count = len(self._selected_dates)
        self._selected_label.config(text=f"{count} selected")

    def _select_all(self):
        """Select all visible rows."""
        for item in self.table.tree.get_children():
            values = self.table.tree.item(item, 'values')
            if values and len(values) > 1:
                date_key = str(values[1])
                self._selected_dates.add(date_key)
                new_values = list(values)
                new_values[0] = "☑"
                self.table.tree.item(item, values=new_values)
        self._update_selected_count()

    def _deselect_all(self):
        """Deselect all rows."""
        self._selected_dates.clear()
        for item in self.table.tree.get_children():
            values = self.table.tree.item(item, 'values')
            if values:
                new_values = list(values)
                new_values[0] = "☐"
                self.table.tree.item(item, values=new_values)
        self._update_selected_count()

    def _export_selected(self):
        """Export selected snapshots to Excel."""
        import tkinter.messagebox as messagebox
        import tkinter.filedialog as filedialog

        if not self._selected_dates:
            messagebox.showwarning("No Selection", "Please select at least one date to export.")
            return

        # Ask for save location
        filename = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
            title="Export NIBOR History",
            initialfile=f"nibor_export_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
        )

        if not filename:
            return

        try:
            self._do_export(filename)
            messagebox.showinfo("Export Complete", f"Exported {len(self._selected_dates)} snapshots to:\n{filename}")
        except Exception as e:
            log.error(f"Export failed: {e}")
            messagebox.showerror("Export Failed", f"Error exporting data:\n{e}")

    def _do_export(self, filename: str):
        """Perform the actual export to Excel - one sheet per selected date."""
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
        from openpyxl.utils import get_column_letter

        wb = Workbook()
        # Remove default sheet
        wb.remove(wb.active)

        # Styles
        header_fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
        section_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF", size=10)
        section_font = Font(bold=True, color="FFFFFF", size=11)
        label_font = Font(bold=True, size=10)
        value_font = Font(size=10)
        thin_border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )

        # Create a sheet for each selected date
        for date_key in sorted(self._selected_dates, reverse=True):
            snapshot = self._history_data.get(date_key, {})
            if not snapshot:
                continue

            # Create sheet with date as name
            ws = wb.create_sheet(title=date_key)

            row = 1

            # === HEADER INFO ===
            ws.cell(row=row, column=1, value="NIBOR SNAPSHOT").font = Font(bold=True, size=14)
            row += 2

            # Basic info
            info_data = [
                ("Date:", date_key),
                ("Time:", snapshot.get('timestamp', '-')[11:19] if snapshot.get('timestamp') else '-'),
                ("User:", snapshot.get('user', '-')),
                ("Machine:", snapshot.get('machine', '-')),
                ("Model:", snapshot.get('model', '-')),
            ]
            for label, value in info_data:
                ws.cell(row=row, column=1, value=label).font = label_font
                ws.cell(row=row, column=2, value=value).font = value_font
                row += 1

            row += 1

            # === WEIGHTS ===
            ws.cell(row=row, column=1, value="WEIGHTS").font = section_font
            ws.cell(row=row, column=1).fill = section_fill
            ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=2)
            row += 1

            weights = snapshot.get('weights', {})
            for curr in ['USD', 'EUR', 'NOK']:
                ws.cell(row=row, column=1, value=f"{curr}:").font = label_font
                val = weights.get(curr)
                ws.cell(row=row, column=2, value=val if val else '-').font = value_font
                if val:
                    ws.cell(row=row, column=2).number_format = '0.00%'
                row += 1

            row += 1

            # === NIBOR RATES ===
            ws.cell(row=row, column=1, value="NIBOR RATES").font = section_font
            ws.cell(row=row, column=1).fill = section_fill
            ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=4)
            row += 1

            # Header row
            rate_headers = ["Tenor", "NIBOR", "Funding", "Spread"]
            for col, h in enumerate(rate_headers, 1):
                cell = ws.cell(row=row, column=col, value=h)
                cell.font = header_font
                cell.fill = header_fill
                cell.border = thin_border
            row += 1

            rates = snapshot.get('rates', {})
            for tenor in ['1m', '2m', '3m', '6m']:
                t_data = rates.get(tenor, {})
                row_data = [
                    tenor.upper(),
                    t_data.get('nibor'),
                    t_data.get('funding'),
                    t_data.get('spread'),
                ]
                for col, val in enumerate(row_data, 1):
                    cell = ws.cell(row=row, column=col, value=val if val is not None else '-')
                    cell.border = thin_border
                    if col > 1 and val is not None:
                        cell.number_format = '0.0000'
                        cell.alignment = Alignment(horizontal="right")
                row += 1

            row += 1

            # === IMPLIED RATES ===
            ws.cell(row=row, column=1, value="IMPLIED RATES").font = section_font
            ws.cell(row=row, column=1).fill = section_fill
            ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=4)
            row += 1

            # Header row
            impl_headers = ["Tenor", "EUR Implied", "USD Implied", "NOK CM"]
            for col, h in enumerate(impl_headers, 1):
                cell = ws.cell(row=row, column=col, value=h)
                cell.font = header_font
                cell.fill = header_fill
                cell.border = thin_border
            row += 1

            for tenor in ['1m', '2m', '3m', '6m']:
                t_data = rates.get(tenor, {})
                impl_row = [
                    tenor.upper(),
                    t_data.get('eur_impl'),
                    t_data.get('usd_impl'),
                    t_data.get('nok_cm'),
                ]
                for col, val in enumerate(impl_row, 1):
                    cell = ws.cell(row=row, column=col, value=val if val is not None else '-')
                    cell.border = thin_border
                    if col > 1 and val is not None:
                        cell.number_format = '0.0000'
                        cell.alignment = Alignment(horizontal="right")
                row += 1

            row += 1

            # === EXCEL CM RATES ===
            excel_cm = snapshot.get('excel_cm_rates', {})
            if excel_cm:
                ws.cell(row=row, column=1, value="EXCEL CM RATES (används)").font = section_font
                ws.cell(row=row, column=1).fill = section_fill
                ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=3)
                row += 1

                # Header
                for col, h in enumerate(["Tenor", "EUR", "USD"], 1):
                    cell = ws.cell(row=row, column=col, value=h)
                    cell.font = header_font
                    cell.fill = header_fill
                    cell.border = thin_border
                row += 1

                for tenor in ['1M', '2M', '3M', '6M']:
                    eur = excel_cm.get(f'EUR_{tenor}')
                    usd = excel_cm.get(f'USD_{tenor}')
                    ws.cell(row=row, column=1, value=tenor).border = thin_border
                    cell_eur = ws.cell(row=row, column=2, value=eur if eur else '-')
                    cell_eur.border = thin_border
                    if eur:
                        cell_eur.number_format = '0.0000'
                    cell_usd = ws.cell(row=row, column=3, value=usd if usd else '-')
                    cell_usd.border = thin_border
                    if usd:
                        cell_usd.number_format = '0.0000'
                    row += 1

                row += 1

            # === BLOOMBERG MARKET DATA ===
            market_data = snapshot.get('market_data', {})
            if market_data:
                ws.cell(row=row, column=1, value="BLOOMBERG MARKET DATA").font = section_font
                ws.cell(row=row, column=1).fill = section_fill
                ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=3)
                row += 1

                # Header
                for col, h in enumerate(["Ticker", "Value"], 1):
                    cell = ws.cell(row=row, column=col, value=h)
                    cell.font = header_font
                    cell.fill = header_fill
                    cell.border = thin_border
                row += 1

                # Sort tickers for consistent output
                for ticker in sorted(market_data.keys()):
                    val = market_data[ticker]
                    ws.cell(row=row, column=1, value=ticker).border = thin_border
                    cell_val = ws.cell(row=row, column=2, value=val if val else '-')
                    cell_val.border = thin_border
                    if val is not None:
                        cell_val.number_format = '0.0000'
                    row += 1

                row += 1

            # === ALERTS ===
            alerts = snapshot.get('alerts', [])
            if alerts:
                ws.cell(row=row, column=1, value="ALERTS").font = section_font
                ws.cell(row=row, column=1).fill = PatternFill(start_color="C00000", end_color="C00000", fill_type="solid")
                row += 1
                for alert in alerts:
                    ws.cell(row=row, column=1, value=f"• {alert}")
                    row += 1

            # Auto-width columns
            ws.column_dimensions['A'].width = 25
            ws.column_dimensions['B'].width = 15
            ws.column_dimensions['C'].width = 12
            ws.column_dimensions['D'].width = 12
            ws.column_dimensions['E'].width = 12
            ws.column_dimensions['F'].width = 12
            ws.column_dimensions['G'].width = 12

        wb.save(filename)
        log.info(f"Exported {len(self._selected_dates)} snapshots to {filename}")

    def _compare_selected(self):
        """Compare two selected dates side by side."""
        import tkinter.messagebox as messagebox

        if len(self._selected_dates) != 2:
            messagebox.showinfo("Select Two Dates",
                               "Please select exactly 2 dates to compare.\n\n"
                               "Click the checkbox (☐) in the SEL column to select dates.")
            return

        if not ComparisonView:
            messagebox.showwarning("Not Available",
                                  "Comparison view requires matplotlib.\n"
                                  "Install with: pip install matplotlib")
            return

        dates = sorted(self._selected_dates)
        ComparisonView(self.winfo_toplevel(), self._history_data, dates[0], dates[1])

    def _export_pdf(self):
        """Export selected snapshots to PDF."""
        import tkinter.messagebox as messagebox
        import tkinter.filedialog as filedialog

        if not self._selected_dates:
            messagebox.showwarning("No Selection", "Please select at least one date to export.")
            return

        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib import colors
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        except ImportError:
            messagebox.showwarning("Not Available",
                                  "PDF export requires reportlab.\n"
                                  "Install with: pip install reportlab")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
            title="Export NIBOR History to PDF",
            initialfile=f"nibor_report_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
        )

        if not filename:
            return

        try:
            self._do_pdf_export(filename)
            messagebox.showinfo("Export Complete", f"Exported {len(self._selected_dates)} snapshots to:\n{filename}")
        except Exception as e:
            log.error(f"PDF export failed: {e}")
            messagebox.showerror("Export Failed", f"Error exporting PDF:\n{e}")

    def _do_pdf_export(self, filename: str):
        """Perform the PDF export."""
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import mm
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak

        doc = SimpleDocTemplate(filename, pagesize=A4,
                               topMargin=20*mm, bottomMargin=20*mm,
                               leftMargin=15*mm, rightMargin=15*mm)
        styles = getSampleStyleSheet()
        elements = []

        # Title style
        title_style = ParagraphStyle('Title', parent=styles['Heading1'],
                                    fontSize=16, spaceAfter=10,
                                    textColor=colors.HexColor('#1F4E79'))
        section_style = ParagraphStyle('Section', parent=styles['Heading2'],
                                      fontSize=12, spaceAfter=6, spaceBefore=12,
                                      textColor=colors.HexColor('#4472C4'))
        normal_style = styles['Normal']

        for i, date_key in enumerate(sorted(self._selected_dates, reverse=True)):
            snapshot = self._history_data.get(date_key, {})
            if not snapshot:
                continue

            if i > 0:
                elements.append(PageBreak())

            # Title
            elements.append(Paragraph(f"NIBOR Snapshot: {date_key}", title_style))
            elements.append(Spacer(1, 5*mm))

            # Basic info
            info_data = [
                ["Time:", snapshot.get('timestamp', '-')[11:19] if snapshot.get('timestamp') else '-'],
                ["User:", snapshot.get('user', '-')],
                ["Machine:", snapshot.get('machine', '-')],
                ["Model:", snapshot.get('model', '-')],
            ]
            info_table = Table(info_data, colWidths=[30*mm, 60*mm])
            info_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ]))
            elements.append(info_table)
            elements.append(Spacer(1, 5*mm))

            # NIBOR Rates
            elements.append(Paragraph("NIBOR Rates", section_style))
            rates = snapshot.get('rates', {})
            rate_data = [["Tenor", "NIBOR", "Funding", "Spread"]]
            for tenor in ['1m', '2m', '3m', '6m']:
                t_data = rates.get(tenor, {})
                rate_data.append([
                    tenor.upper(),
                    f"{t_data.get('nibor'):.4f}" if t_data.get('nibor') else "-",
                    f"{t_data.get('funding'):.4f}" if t_data.get('funding') else "-",
                    f"{t_data.get('spread'):.4f}" if t_data.get('spread') else "-",
                ])

            rate_table = Table(rate_data, colWidths=[25*mm, 35*mm, 35*mm, 35*mm])
            rate_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1F4E79')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
            ]))
            elements.append(rate_table)

            # Weights
            weights = snapshot.get('weights', {})
            if weights:
                elements.append(Paragraph("Weights", section_style))
                weight_data = [["Currency", "Weight"]]
                for curr in ['USD', 'EUR', 'NOK']:
                    w = weights.get(curr)
                    weight_data.append([curr, f"{w*100:.2f}%" if w else "-"])
                w_table = Table(weight_data, colWidths=[30*mm, 40*mm])
                w_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4472C4')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
                ]))
                elements.append(w_table)

            # Alerts
            alerts = snapshot.get('alerts', [])
            if alerts:
                elements.append(Paragraph("Alerts", section_style))
                for alert in alerts:
                    elements.append(Paragraph(f"• {alert}", normal_style))

        doc.build(elements)
        log.info(f"PDF exported to {filename}")

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
            lines.append("NIBOR RATES:")
            for tenor in ['1m', '2m', '3m', '6m']:
                t_data = rates.get(tenor, {})
                nibor = t_data.get('nibor')
                if nibor is not None:
                    lines.append(f"  {tenor.upper()}: {nibor:.4f}")
            lines.append("")

            # Implied rates breakdown
            lines.append("IMPLIED RATES:")
            lines.append("        EUR Impl  USD Impl  NOK CM")
            for tenor in ['1m', '2m', '3m', '6m']:
                t_data = rates.get(tenor, {})
                eur_impl = t_data.get('eur_impl')
                usd_impl = t_data.get('usd_impl')
                nok_cm = t_data.get('nok_cm')
                eur_str = f"{eur_impl:.4f}" if eur_impl is not None else "   -   "
                usd_str = f"{usd_impl:.4f}" if usd_impl is not None else "   -   "
                nok_str = f"{nok_cm:.4f}" if nok_cm is not None else "   -   "
                lines.append(f"  {tenor.upper()}:  {eur_str}  {usd_str}  {nok_str}")
            lines.append("")

        # Excel CM rates (used for calculation)
        excel_cm = snapshot.get('excel_cm_rates', {})
        if excel_cm:
            lines.append("EXCEL CM RATES (används):")
            for tenor in ['1M', '2M', '3M', '6M']:
                eur = excel_cm.get(f'EUR_{tenor}')
                usd = excel_cm.get(f'USD_{tenor}')
                eur_str = f"{eur:.4f}" if eur is not None else "-"
                usd_str = f"{usd:.4f}" if usd is not None else "-"
                lines.append(f"  {tenor}: EUR {eur_str}  USD {usd_str}")
            lines.append("")

        # Bloomberg market data
        market_data = snapshot.get('market_data', {})
        if market_data:
            lines.append("BLOOMBERG DATA:")
            # Show key rates first
            key_tickers = [
                ('NOK F033 Curncy', 'USDNOK Spot'),
                ('NKEU F033 Curncy', 'EURNOK Spot'),
            ]
            for ticker, label in key_tickers:
                val = market_data.get(ticker)
                if val is not None:
                    lines.append(f"  {label}: {val:.4f}")

            # Show CM rates from Bloomberg
            lines.append("  --- BBG CM (referens) ---")
            for tenor in ['1M', '2M', '3M', '6M']:
                eur_ticker = f'EUCM{tenor} SWET Curncy'
                usd_ticker = f'USCM{tenor} SWET Curncy'
                eur = market_data.get(eur_ticker)
                usd = market_data.get(usd_ticker)
                eur_str = f"{eur:.4f}" if eur is not None else "-"
                usd_str = f"{usd:.4f}" if usd is not None else "-"
                lines.append(f"  {tenor}: EUR {eur_str}  USD {usd_str}")
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


class AuditLogPage(tk.Frame):
    """
    Professional Audit Log page with search, filtering, live updates, and persistence.

    Features:
    - Real-time log streaming with live indicator
    - Search functionality
    - Level and date filtering
    - Auto-save to JSON
    - Right-click context menu
    - Pause/Resume auto-scroll
    - Export to TXT/JSON
    - Visual icons per log level
    """

    # Log level icons and colors
    LEVEL_CONFIG = {
        'INFO': {'icon': 'ℹ️', 'color': '#3b82f6', 'bg': '#1e3a5f'},
        'WARNING': {'icon': '⚠️', 'color': '#f59e0b', 'bg': '#3d3520'},
        'ERROR': {'icon': '❌', 'color': '#ef4444', 'bg': '#3d1e1e'},
        'ACTION': {'icon': '✓', 'color': '#4ade80', 'bg': '#1e3d2e'},
        'DEBUG': {'icon': '🔧', 'color': '#8b5cf6', 'bg': '#2d1f4e'},
        'SYSTEM': {'icon': '⚙️', 'color': '#6b7280', 'bg': '#2d2d44'},
    }

    def __init__(self, master, app):
        super().__init__(master, bg=THEME["bg_panel"])
        self.app = app
        pad = CURRENT_MODE["pad"]

        # State
        self._log_entries = []
        self._filtered_entries = []
        self._auto_scroll = True
        self._live_indicator_state = False
        self._new_entries_count = 0
        self._log_file_path = None

        # Try to load saved logs
        self._init_log_file()

        # ================================================================
        # HEADER ROW
        # ================================================================
        header = tk.Frame(self, bg=THEME["bg_panel"])
        header.pack(fill="x", padx=pad, pady=(pad, 10))

        # Left: Title with live indicator
        title_frame = tk.Frame(header, bg=THEME["bg_panel"])
        title_frame.pack(side="left")

        tk.Label(title_frame, text="AUDIT LOG", fg=THEME["muted"], bg=THEME["bg_panel"],
                 font=("Segoe UI", CURRENT_MODE["h2"], "bold")).pack(side="left")

        # Live indicator dot (pulses when new logs arrive)
        self._live_dot = tk.Label(title_frame, text="●", fg="#666666", bg=THEME["bg_panel"],
                                  font=("Segoe UI", 12))
        self._live_dot.pack(side="left", padx=(10, 0))

        self._live_label = tk.Label(title_frame, text="LIVE", fg="#666666", bg=THEME["bg_panel"],
                                    font=("Segoe UI", 8, "bold"))
        self._live_label.pack(side="left", padx=(3, 0))

        # Right: Action buttons
        btn_frame = tk.Frame(header, bg=THEME["bg_panel"])
        btn_frame.pack(side="right")

        # Pause/Resume button
        self._pause_btn = OnyxButtonTK(btn_frame, "⏸ Pause", command=self._toggle_auto_scroll, variant="default")
        self._pause_btn.pack(side="left", padx=3)

        OnyxButtonTK(btn_frame, "📋 Copy", command=self._copy_to_clipboard, variant="default").pack(side="left", padx=3)
        OnyxButtonTK(btn_frame, "💾 Export", command=self._show_export_menu, variant="default").pack(side="left", padx=3)
        OnyxButtonTK(btn_frame, "🗑 Clear", command=self._clear_log, variant="danger").pack(side="left", padx=3)

        # ================================================================
        # SEARCH AND FILTER ROW
        # ================================================================
        filter_row = tk.Frame(self, bg=THEME["bg_panel"])
        filter_row.pack(fill="x", padx=pad, pady=(0, 10))

        # Search box
        search_frame = tk.Frame(filter_row, bg=THEME["bg_card"], highlightthickness=1,
                               highlightbackground=THEME["border"])
        search_frame.pack(side="left")

        tk.Label(search_frame, text="🔍", fg=THEME["muted"], bg=THEME["bg_card"],
                font=("Segoe UI", 10)).pack(side="left", padx=(8, 4), pady=4)

        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", lambda *args: self._apply_filter())
        self._search_entry = tk.Entry(search_frame, textvariable=self._search_var,
                                      bg=THEME["bg_card"], fg=THEME["text"],
                                      insertbackground=THEME["text"],
                                      font=("Segoe UI", 10), relief="flat",
                                      width=25)
        self._search_entry.pack(side="left", padx=(0, 8), pady=4)
        self._search_entry.bind("<Escape>", lambda e: self._clear_search())

        # Clear search button
        clear_search_btn = tk.Label(search_frame, text="✕", fg=THEME["muted"], bg=THEME["bg_card"],
                                   font=("Segoe UI", 10), cursor="hand2")
        clear_search_btn.pack(side="left", padx=(0, 8))
        clear_search_btn.bind("<Button-1>", lambda e: self._clear_search())

        # Level filter pills
        level_frame = tk.Frame(filter_row, bg=THEME["bg_panel"])
        level_frame.pack(side="left", padx=(15, 0))

        tk.Label(level_frame, text="Level:", fg=THEME["muted"], bg=THEME["bg_panel"],
                font=("Segoe UI", 9)).pack(side="left", padx=(0, 5))

        self._filter_var = tk.StringVar(value="ALL")
        levels = ["ALL", "INFO", "WARNING", "ERROR", "ACTION", "SYSTEM"]

        for level in levels:
            color = self.LEVEL_CONFIG.get(level, {}).get('color', THEME["text"])
            if level == "ALL":
                color = THEME["text"]

            rb = tk.Radiobutton(level_frame, text=level, variable=self._filter_var, value=level,
                               bg=THEME["bg_panel"], fg=color,
                               selectcolor=THEME["bg_card"],
                               activebackground=THEME["bg_panel"],
                               activeforeground=color,
                               font=("Segoe UI", 9, "bold"),
                               command=self._apply_filter)
            rb.pack(side="left", padx=2)

        # Date filter (right side)
        date_frame = tk.Frame(filter_row, bg=THEME["bg_panel"])
        date_frame.pack(side="right")

        tk.Label(date_frame, text="Time:", fg=THEME["muted"], bg=THEME["bg_panel"],
                font=("Segoe UI", 9)).pack(side="left", padx=(0, 5))

        self._time_filter_var = tk.StringVar(value="ALL")
        for label, value in [("All", "ALL"), ("1h", "1H"), ("15m", "15M"), ("5m", "5M")]:
            rb = tk.Radiobutton(date_frame, text=label, variable=self._time_filter_var, value=value,
                               bg=THEME["bg_panel"], fg=THEME["text"],
                               selectcolor=THEME["bg_card"],
                               activebackground=THEME["bg_panel"],
                               font=("Segoe UI", 9),
                               command=self._apply_filter)
            rb.pack(side="left", padx=2)

        # ================================================================
        # STATS BAR
        # ================================================================
        stats_frame = tk.Frame(self, bg=THEME["bg_card"], highlightthickness=1,
                              highlightbackground=THEME["border"])
        stats_frame.pack(fill="x", padx=pad, pady=(0, 10))

        # Stats with icons
        self._stats_labels = {}
        stats_config = [
            ("total", "📊 Total:", THEME["text"]),
            ("info", "ℹ️ Info:", "#3b82f6"),
            ("warning", "⚠️ Warnings:", "#f59e0b"),
            ("error", "❌ Errors:", "#ef4444"),
            ("action", "✓ Actions:", "#4ade80"),
        ]

        for key, label, color in stats_config:
            frame = tk.Frame(stats_frame, bg=THEME["bg_card"])
            frame.pack(side="left", padx=12, pady=6)

            tk.Label(frame, text=label, fg=THEME["muted"], bg=THEME["bg_card"],
                    font=("Segoe UI", 9)).pack(side="left")

            lbl = tk.Label(frame, text="0", fg=color, bg=THEME["bg_card"],
                          font=("Segoe UI", 10, "bold"))
            lbl.pack(side="left", padx=(3, 0))
            self._stats_labels[key] = lbl

        # Showing X of Y label
        self._showing_label = tk.Label(stats_frame, text="", fg=THEME["muted"],
                                       bg=THEME["bg_card"], font=("Segoe UI", 9))
        self._showing_label.pack(side="right", padx=12, pady=6)

        # ================================================================
        # LOG LIST (using Treeview for better performance)
        # ================================================================
        log_container = tk.Frame(self, bg=THEME["bg_card"], highlightthickness=1,
                                highlightbackground=THEME["border"])
        log_container.pack(fill="both", expand=True, padx=pad, pady=(0, pad))

        # Create treeview with columns
        columns = ("time", "level", "message")
        self._tree = ttk.Treeview(log_container, columns=columns, show="headings",
                                  selectmode="extended")

        # Configure columns
        self._tree.heading("time", text="TIME", anchor="w")
        self._tree.heading("level", text="LEVEL", anchor="w")
        self._tree.heading("message", text="MESSAGE", anchor="w")

        self._tree.column("time", width=150, minwidth=120)
        self._tree.column("level", width=100, minwidth=80)
        self._tree.column("message", width=600, minwidth=200)

        # Scrollbars
        y_scroll = ttk.Scrollbar(log_container, orient="vertical", command=self._tree.yview)
        x_scroll = ttk.Scrollbar(log_container, orient="horizontal", command=self._tree.xview)
        self._tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)

        # Pack
        self._tree.pack(side="left", fill="both", expand=True)
        y_scroll.pack(side="right", fill="y")

        # Configure tags for row colors
        for level, config in self.LEVEL_CONFIG.items():
            self._tree.tag_configure(level.lower(), background=config['bg'], foreground=config['color'])

        # Alternating row colors for readability
        self._tree.tag_configure("even", background=THEME["bg_card"])
        self._tree.tag_configure("odd", background=THEME["bg_card_2"])

        # Bind events
        self._tree.bind("<Double-1>", self._on_double_click)
        self._tree.bind("<Button-3>", self._show_context_menu)  # Right-click
        self._tree.bind("<Control-c>", lambda e: self._copy_selected())

        # Context menu
        self._context_menu = tk.Menu(self, tearoff=0, bg=THEME["bg_card"], fg=THEME["text"],
                                     activebackground=THEME["accent"], activeforeground="white")
        self._context_menu.add_command(label="📋 Copy", command=self._copy_selected)
        self._context_menu.add_command(label="🔍 View Details", command=self._view_selected_details)
        self._context_menu.add_separator()
        self._context_menu.add_command(label="🗑 Delete Selected", command=self._delete_selected)

        # ================================================================
        # FOOTER STATUS BAR
        # ================================================================
        footer = tk.Frame(self, bg=THEME["bg_card_2"], height=24)
        footer.pack(fill="x", padx=pad, pady=(0, pad))
        footer.pack_propagate(False)

        # Auto-save status
        self._autosave_label = tk.Label(footer, text="💾 Auto-save: ON", fg=THEME["muted"],
                                        bg=THEME["bg_card_2"], font=("Segoe UI", 8))
        self._autosave_label.pack(side="left", padx=10, pady=4)

        # Log file path
        self._filepath_label = tk.Label(footer, text="", fg=THEME["muted"],
                                        bg=THEME["bg_card_2"], font=("Segoe UI", 8))
        self._filepath_label.pack(side="left", padx=10, pady=4)

        # Session duration
        self._session_start = datetime.now()
        self._session_label = tk.Label(footer, text="Session: 0:00:00", fg=THEME["muted"],
                                       bg=THEME["bg_card_2"], font=("Segoe UI", 8))
        self._session_label.pack(side="right", padx=10, pady=4)

        # Start timers
        self._update_session_timer()
        self._pulse_live_indicator()

        # Add initial entries
        self._add_system_start_entry()

    def _init_log_file(self):
        """Initialize log file for auto-save."""
        try:
            from config import NIBOR_LOG_PATH
            log_dir = NIBOR_LOG_PATH / "audit_logs"
            log_dir.mkdir(parents=True, exist_ok=True)

            today = datetime.now().strftime("%Y-%m-%d")
            self._log_file_path = log_dir / f"audit_{today}.json"

            # Load existing entries from today's log
            if self._log_file_path.exists():
                import json
                with open(self._log_file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for entry in data:
                        entry['timestamp'] = datetime.fromisoformat(entry['timestamp'])
                    self._log_entries = data
        except Exception as e:
            log.error(f"Failed to init log file: {e}")

    def _auto_save(self):
        """Auto-save logs to JSON file."""
        if not self._log_file_path:
            return

        try:
            import json
            data = []
            for entry in self._log_entries:
                data.append({
                    'timestamp': entry['timestamp'].isoformat(),
                    'level': entry['level'],
                    'message': entry['message'],
                    'source': entry.get('source', 'app')
                })

            with open(self._log_file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            log.error(f"Auto-save failed: {e}")

    def _add_system_start_entry(self):
        """Add system startup entries."""
        import getpass
        import platform

        self.add_entry("SYSTEM", "═" * 50)
        self.add_entry("SYSTEM", "Nibor Calculation Terminal - Session Started")
        self.add_entry("SYSTEM", f"User: {getpass.getuser()} @ {platform.node()}")
        self.add_entry("SYSTEM", f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.add_entry("SYSTEM", "═" * 50)
        self.add_entry("INFO", "Ready for NIBOR calculations")

    def add_entry(self, level: str, message: str, timestamp=None, source: str = "app"):
        """Add a log entry."""
        ts = timestamp or datetime.now()
        entry = {
            'timestamp': ts,
            'level': level.upper(),
            'message': message,
            'source': source
        }
        self._log_entries.append(entry)
        self._new_entries_count += 1

        # Update display
        self._update_stats()
        self._apply_filter()

        # Trigger live indicator pulse
        self._trigger_live_pulse()

        # Auto-save periodically (every 10 entries)
        if len(self._log_entries) % 10 == 0:
            self._auto_save()

    def _trigger_live_pulse(self):
        """Trigger the live indicator to pulse."""
        self._live_indicator_state = True
        self._live_dot.config(fg="#4ade80")
        self._live_label.config(fg="#4ade80")

        # Reset after 500ms
        self.after(500, self._reset_live_indicator)

    def _reset_live_indicator(self):
        """Reset live indicator to idle state."""
        if not self._auto_scroll:
            self._live_dot.config(fg="#f59e0b")
            self._live_label.config(fg="#f59e0b", text="PAUSED")
        else:
            self._live_dot.config(fg="#666666")
            self._live_label.config(fg="#666666", text="LIVE")

    def _pulse_live_indicator(self):
        """Periodic pulse for live indicator."""
        if self._auto_scroll and self._new_entries_count > 0:
            self._new_entries_count = 0
        self.after(2000, self._pulse_live_indicator)

    def _update_session_timer(self):
        """Update session duration display."""
        elapsed = datetime.now() - self._session_start
        hours, remainder = divmod(int(elapsed.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        self._session_label.config(text=f"Session: {hours}:{minutes:02d}:{seconds:02d}")
        self.after(1000, self._update_session_timer)

    def _update_stats(self):
        """Update statistics display."""
        total = len(self._log_entries)
        counts = {'info': 0, 'warning': 0, 'error': 0, 'action': 0}

        for entry in self._log_entries:
            level = entry['level'].lower()
            if level in counts:
                counts[level] += 1

        self._stats_labels['total'].config(text=str(total))
        self._stats_labels['info'].config(text=str(counts['info']))
        self._stats_labels['warning'].config(text=str(counts['warning']))
        self._stats_labels['error'].config(text=str(counts['error']))
        self._stats_labels['action'].config(text=str(counts['action']))

    def _apply_filter(self):
        """Apply all filters and update display."""
        search_text = self._search_var.get().lower()
        level_filter = self._filter_var.get()
        time_filter = self._time_filter_var.get()

        # Calculate time threshold
        now = datetime.now()
        time_thresholds = {
            "ALL": None,
            "1H": now - timedelta(hours=1),
            "15M": now - timedelta(minutes=15),
            "5M": now - timedelta(minutes=5),
        }
        time_threshold = time_thresholds.get(time_filter)

        # Filter entries
        self._filtered_entries = []
        for entry in self._log_entries:
            # Level filter
            if level_filter != "ALL" and entry['level'] != level_filter:
                continue

            # Time filter
            if time_threshold and entry['timestamp'] < time_threshold:
                continue

            # Search filter
            if search_text and search_text not in entry['message'].lower():
                continue

            self._filtered_entries.append(entry)

        # Update treeview
        self._refresh_treeview()

        # Update showing label
        total = len(self._log_entries)
        shown = len(self._filtered_entries)
        if shown < total:
            self._showing_label.config(text=f"Showing {shown} of {total}")
        else:
            self._showing_label.config(text="")

    def _refresh_treeview(self):
        """Refresh the treeview with filtered entries."""
        # Clear existing
        for item in self._tree.get_children():
            self._tree.delete(item)

        # Add filtered entries
        for i, entry in enumerate(self._filtered_entries):
            level = entry['level']
            config = self.LEVEL_CONFIG.get(level, self.LEVEL_CONFIG['INFO'])

            time_str = entry['timestamp'].strftime("%Y-%m-%d %H:%M:%S")
            level_str = f"{config['icon']} {level}"

            # Determine tag
            tag = level.lower()

            self._tree.insert("", "end", values=(time_str, level_str, entry['message']), tags=(tag,))

        # Auto-scroll to bottom if enabled
        if self._auto_scroll and self._filtered_entries:
            children = self._tree.get_children()
            if children:
                self._tree.see(children[-1])

    def _toggle_auto_scroll(self):
        """Toggle auto-scroll."""
        self._auto_scroll = not self._auto_scroll
        if self._auto_scroll:
            self._pause_btn.config(text="⏸ Pause")
            self._live_label.config(text="LIVE", fg="#666666")
            self._live_dot.config(fg="#666666")
        else:
            self._pause_btn.config(text="▶ Resume")
            self._live_label.config(text="PAUSED", fg="#f59e0b")
            self._live_dot.config(fg="#f59e0b")

    def _clear_search(self):
        """Clear search field."""
        self._search_var.set("")
        self._search_entry.focus_set()

    def _copy_to_clipboard(self):
        """Copy all visible logs to clipboard."""
        lines = []
        for entry in self._filtered_entries:
            ts = entry['timestamp'].strftime("%Y-%m-%d %H:%M:%S")
            lines.append(f"[{ts}] [{entry['level']:8}] {entry['message']}")

        text = "\n".join(lines)
        self.clipboard_clear()
        self.clipboard_append(text)

        self.add_entry("ACTION", f"Copied {len(lines)} log entries to clipboard")

    def _copy_selected(self):
        """Copy selected entries to clipboard."""
        selection = self._tree.selection()
        if not selection:
            return

        lines = []
        for item in selection:
            values = self._tree.item(item, 'values')
            lines.append(f"[{values[0]}] {values[1]} {values[2]}")

        text = "\n".join(lines)
        self.clipboard_clear()
        self.clipboard_append(text)

    def _show_context_menu(self, event):
        """Show context menu on right-click."""
        # Select item under cursor
        item = self._tree.identify_row(event.y)
        if item:
            self._tree.selection_set(item)
            self._context_menu.post(event.x_root, event.y_root)

    def _on_double_click(self, event):
        """Handle double-click on entry."""
        self._view_selected_details()

    def _view_selected_details(self):
        """Show details popup for selected entry."""
        selection = self._tree.selection()
        if not selection:
            return

        # Get the entry data
        item = selection[0]
        idx = self._tree.index(item)
        if idx < len(self._filtered_entries):
            entry = self._filtered_entries[idx]
            self._show_entry_details(entry)

    def _show_entry_details(self, entry):
        """Show detailed popup for a log entry."""
        popup = tk.Toplevel(self)
        popup.title("Log Entry Details")
        popup.geometry("500x300")
        popup.configure(bg=THEME["bg_main"])
        popup.transient(self.winfo_toplevel())
        popup.grab_set()

        # Header with level icon
        config = self.LEVEL_CONFIG.get(entry['level'], self.LEVEL_CONFIG['INFO'])

        header = tk.Frame(popup, bg=config['bg'])
        header.pack(fill="x", padx=0, pady=0)

        tk.Label(header, text=f"  {config['icon']} {entry['level']}",
                fg=config['color'], bg=config['bg'],
                font=("Segoe UI", 14, "bold")).pack(side="left", pady=10)

        # Content
        content = tk.Frame(popup, bg=THEME["bg_main"])
        content.pack(fill="both", expand=True, padx=20, pady=15)

        # Timestamp
        tk.Label(content, text="Timestamp:", fg=THEME["muted"], bg=THEME["bg_main"],
                font=("Segoe UI", 10)).grid(row=0, column=0, sticky="w", pady=3)
        tk.Label(content, text=entry['timestamp'].strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
                fg=THEME["text"], bg=THEME["bg_main"],
                font=("Consolas", 10)).grid(row=0, column=1, sticky="w", padx=10, pady=3)

        # Level
        tk.Label(content, text="Level:", fg=THEME["muted"], bg=THEME["bg_main"],
                font=("Segoe UI", 10)).grid(row=1, column=0, sticky="w", pady=3)
        tk.Label(content, text=entry['level'], fg=config['color'], bg=THEME["bg_main"],
                font=("Segoe UI", 10, "bold")).grid(row=1, column=1, sticky="w", padx=10, pady=3)

        # Source
        tk.Label(content, text="Source:", fg=THEME["muted"], bg=THEME["bg_main"],
                font=("Segoe UI", 10)).grid(row=2, column=0, sticky="w", pady=3)
        tk.Label(content, text=entry.get('source', 'app'), fg=THEME["text"], bg=THEME["bg_main"],
                font=("Segoe UI", 10)).grid(row=2, column=1, sticky="w", padx=10, pady=3)

        # Message
        tk.Label(content, text="Message:", fg=THEME["muted"], bg=THEME["bg_main"],
                font=("Segoe UI", 10)).grid(row=3, column=0, sticky="nw", pady=3)

        msg_frame = tk.Frame(content, bg=THEME["bg_card"], highlightthickness=1,
                            highlightbackground=THEME["border"])
        msg_frame.grid(row=3, column=1, sticky="nsew", padx=10, pady=3)
        content.grid_rowconfigure(3, weight=1)
        content.grid_columnconfigure(1, weight=1)

        msg_text = tk.Text(msg_frame, bg=THEME["bg_card"], fg=THEME["text"],
                          font=("Consolas", 10), relief="flat", wrap="word", height=6)
        msg_text.pack(fill="both", expand=True, padx=8, pady=8)
        msg_text.insert("1.0", entry['message'])
        msg_text.config(state="disabled")

        # Buttons
        btn_frame = tk.Frame(popup, bg=THEME["bg_main"])
        btn_frame.pack(fill="x", padx=20, pady=(0, 15))

        tk.Button(btn_frame, text="📋 Copy", bg=THEME["accent"], fg="white",
                 font=("Segoe UI", 10), relief="flat", padx=15, pady=5,
                 command=lambda: self._copy_entry(entry)).pack(side="left")
        tk.Button(btn_frame, text="Close", bg=THEME["chip2"], fg=THEME["text"],
                 font=("Segoe UI", 10), relief="flat", padx=15, pady=5,
                 command=popup.destroy).pack(side="right")

        popup.bind("<Escape>", lambda e: popup.destroy())

    def _copy_entry(self, entry):
        """Copy single entry to clipboard."""
        ts = entry['timestamp'].strftime("%Y-%m-%d %H:%M:%S")
        text = f"[{ts}] [{entry['level']}] {entry['message']}"
        self.clipboard_clear()
        self.clipboard_append(text)

    def _delete_selected(self):
        """Delete selected entries."""
        selection = self._tree.selection()
        if not selection:
            return

        import tkinter.messagebox as messagebox
        if not messagebox.askyesno("Delete Entries", f"Delete {len(selection)} selected entries?"):
            return

        # Get indices to delete
        indices_to_delete = set()
        for item in selection:
            idx = self._tree.index(item)
            if idx < len(self._filtered_entries):
                # Find the original entry
                entry = self._filtered_entries[idx]
                if entry in self._log_entries:
                    indices_to_delete.add(self._log_entries.index(entry))

        # Delete in reverse order
        for idx in sorted(indices_to_delete, reverse=True):
            del self._log_entries[idx]

        self._update_stats()
        self._apply_filter()
        self.add_entry("ACTION", f"Deleted {len(indices_to_delete)} log entries")

    def _show_export_menu(self):
        """Show export options menu."""
        menu = tk.Menu(self, tearoff=0, bg=THEME["bg_card"], fg=THEME["text"])
        menu.add_command(label="📄 Export as TXT", command=lambda: self._export_log("txt"))
        menu.add_command(label="📋 Export as JSON", command=lambda: self._export_log("json"))
        menu.add_separator()
        menu.add_command(label="📂 Open Log Folder", command=self._open_log_folder)

        # Position near the button
        menu.post(self.winfo_rootx() + 400, self.winfo_rooty() + 50)

    def _export_log(self, format_type: str = "txt"):
        """Export log to file."""
        import tkinter.filedialog as filedialog

        if format_type == "json":
            filetypes = [("JSON files", "*.json"), ("All files", "*.*")]
            ext = ".json"
        else:
            filetypes = [("Text files", "*.txt"), ("All files", "*.*")]
            ext = ".txt"

        filename = filedialog.asksaveasfilename(
            defaultextension=ext,
            filetypes=filetypes,
            title="Export Audit Log",
            initialfile=f"audit_log_{datetime.now().strftime('%Y%m%d_%H%M')}{ext}"
        )

        if not filename:
            return

        try:
            if format_type == "json":
                import json
                data = []
                for entry in self._filtered_entries:
                    data.append({
                        'timestamp': entry['timestamp'].isoformat(),
                        'level': entry['level'],
                        'message': entry['message'],
                        'source': entry.get('source', 'app')
                    })
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
            else:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write("NIBOR CALCULATION TERMINAL - AUDIT LOG\n")
                    f.write(f"Exported: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("=" * 70 + "\n\n")

                    for entry in self._filtered_entries:
                        ts_str = entry['timestamp'].strftime("%Y-%m-%d %H:%M:%S")
                        f.write(f"[{ts_str}] [{entry['level']:8}] {entry['message']}\n")

            self.add_entry("ACTION", f"Log exported to {filename}")
        except Exception as e:
            log.error(f"Failed to export log: {e}")
            self.add_entry("ERROR", f"Export failed: {e}")

    def _open_log_folder(self):
        """Open the log folder in file explorer."""
        if self._log_file_path:
            import os
            folder = self._log_file_path.parent
            if folder.exists():
                os.startfile(folder)

    def _clear_log(self):
        """Clear all log entries."""
        import tkinter.messagebox as messagebox
        if messagebox.askyesno("Clear Log", "Are you sure you want to clear all log entries?"):
            self._log_entries.clear()
            self._update_stats()
            self._apply_filter()
            self.add_entry("SYSTEM", "Audit log cleared by user")

    def update(self):
        """Refresh the log display."""
        self._apply_filter()


class SettingsPage(tk.Frame):
    """
    Professional Settings page with category navigation and comprehensive options.
    """

    # Category configuration
    CATEGORIES = [
        ("appearance", "🎨", "Utseende"),
        ("data", "🔄", "Data & Refresh"),
        ("alerts", "🔔", "Alerts"),
        ("display", "📊", "Display"),
        ("connections", "🔌", "Connections"),
        ("history", "💾", "History"),
        ("shortcuts", "⌨️", "Shortcuts"),
        ("system", "🖥️", "System"),
        ("about", "ℹ️", "About"),
    ]

    def __init__(self, master, app):
        super().__init__(master, bg=THEME["bg_panel"])
        self.app = app
        pad = CURRENT_MODE["pad"]

        # Load settings
        from settings import get_settings, ACCENT_COLORS, FONT_SIZE_PRESETS
        self.settings = get_settings()
        self._pending_changes = {}  # Track unsaved changes
        self._widgets = {}  # Store widget references

        # ================================================================
        # HEADER
        # ================================================================
        header = tk.Frame(self, bg=THEME["bg_panel"])
        header.pack(fill="x", padx=pad, pady=(pad, 15))

        # Title with cogwheel
        title_frame = tk.Frame(header, bg=THEME["bg_panel"])
        title_frame.pack(side="left")

        # Animated cogwheel
        self._cog_angle = 0
        self._cog_label = tk.Label(title_frame, text="⚙", fg=THEME["accent"],
                                   bg=THEME["bg_panel"], font=("Segoe UI", 28))
        self._cog_label.pack(side="left", padx=(0, 10))

        tk.Label(title_frame, text="SETTINGS", fg=THEME["muted"], bg=THEME["bg_panel"],
                 font=("Segoe UI", CURRENT_MODE["h2"], "bold")).pack(side="left")

        # Action buttons
        btn_frame = tk.Frame(header, bg=THEME["bg_panel"])
        btn_frame.pack(side="right")

        OnyxButtonTK(btn_frame, "↺ Restore Defaults", command=self._restore_defaults,
                    variant="default").pack(side="left", padx=5)
        OnyxButtonTK(btn_frame, "📥 Import", command=self._import_settings,
                    variant="default").pack(side="left", padx=5)
        OnyxButtonTK(btn_frame, "📤 Export", command=self._export_settings,
                    variant="default").pack(side="left", padx=5)

        # ================================================================
        # MAIN CONTENT (Sidebar + Content Area)
        # ================================================================
        main = tk.Frame(self, bg=THEME["bg_panel"])
        main.pack(fill="both", expand=True, padx=pad, pady=(0, pad))

        # Left sidebar with categories
        sidebar = tk.Frame(main, bg=THEME["bg_card"], width=180,
                          highlightthickness=1, highlightbackground=THEME["border"])
        sidebar.pack(side="left", fill="y", padx=(0, 15))
        sidebar.pack_propagate(False)

        self._category_buttons = {}
        self._current_category = "appearance"

        for cat_id, icon, label in self.CATEGORIES:
            btn = tk.Frame(sidebar, bg=THEME["bg_card"], cursor="hand2")
            btn.pack(fill="x", padx=5, pady=2)

            btn_inner = tk.Frame(btn, bg=THEME["bg_card"])
            btn_inner.pack(fill="x", padx=8, pady=8)

            icon_lbl = tk.Label(btn_inner, text=icon, fg=THEME["muted"],
                               bg=THEME["bg_card"], font=("Segoe UI", 14))
            icon_lbl.pack(side="left")

            text_lbl = tk.Label(btn_inner, text=label, fg=THEME["text"],
                               bg=THEME["bg_card"], font=("Segoe UI", 10))
            text_lbl.pack(side="left", padx=(8, 0))

            # Store references
            self._category_buttons[cat_id] = {
                "frame": btn,
                "inner": btn_inner,
                "icon": icon_lbl,
                "text": text_lbl
            }

            # Bind events
            for widget in [btn, btn_inner, icon_lbl, text_lbl]:
                widget.bind("<Button-1>", lambda e, c=cat_id: self._select_category(c))
                widget.bind("<Enter>", lambda e, c=cat_id: self._on_category_hover(c, True))
                widget.bind("<Leave>", lambda e, c=cat_id: self._on_category_hover(c, False))

        # Right content area
        self._content_frame = tk.Frame(main, bg=THEME["bg_card"],
                                       highlightthickness=1,
                                       highlightbackground=THEME["border"])
        self._content_frame.pack(side="left", fill="both", expand=True)

        # Inner content with padding
        self._content_inner = tk.Frame(self._content_frame, bg=THEME["bg_card"])
        self._content_inner.pack(fill="both", expand=True, padx=20, pady=20)

        # ================================================================
        # FOOTER WITH SAVE/CANCEL
        # ================================================================
        footer = tk.Frame(self, bg=THEME["bg_panel"])
        footer.pack(fill="x", padx=pad, pady=(10, pad))

        # Unsaved changes indicator
        self._unsaved_label = tk.Label(footer, text="", fg="#f59e0b",
                                       bg=THEME["bg_panel"], font=("Segoe UI", 9))
        self._unsaved_label.pack(side="left")

        # Buttons
        btn_frame2 = tk.Frame(footer, bg=THEME["bg_panel"])
        btn_frame2.pack(side="right")

        self._cancel_btn = OnyxButtonTK(btn_frame2, "Cancel", command=self._cancel_changes,
                                        variant="default")
        self._cancel_btn.pack(side="left", padx=5)

        self._apply_btn = OnyxButtonTK(btn_frame2, "Apply", command=self._apply_changes,
                                       variant="default")
        self._apply_btn.pack(side="left", padx=5)

        self._save_btn = OnyxButtonTK(btn_frame2, "Save", command=self._save_changes,
                                      variant="accent")
        self._save_btn.pack(side="left", padx=5)

        # Select first category
        self._select_category("appearance")

        # Start cogwheel animation
        self._animate_cogwheel()

    def _animate_cogwheel(self):
        """Subtle cogwheel rotation animation."""
        # Only animate when there are pending changes
        if self._pending_changes:
            self._cog_angle = (self._cog_angle + 15) % 360
            # We can't actually rotate text, but we can pulse the color
            intensity = abs((self._cog_angle % 60) - 30) / 30
            r = int(233 * (0.7 + 0.3 * intensity))
            g = int(69 * (0.7 + 0.3 * intensity))
            b = int(96 * (0.7 + 0.3 * intensity))
            self._cog_label.config(fg=f"#{r:02x}{g:02x}{b:02x}")
        else:
            self._cog_label.config(fg=THEME["accent"])

        self.after(100, self._animate_cogwheel)

    def _select_category(self, category_id: str):
        """Select a category and show its settings."""
        self._current_category = category_id

        # Update button styles
        for cat_id, widgets in self._category_buttons.items():
            if cat_id == category_id:
                widgets["frame"].config(bg=THEME["accent"])
                widgets["inner"].config(bg=THEME["accent"])
                widgets["icon"].config(bg=THEME["accent"], fg="white")
                widgets["text"].config(bg=THEME["accent"], fg="white")
            else:
                widgets["frame"].config(bg=THEME["bg_card"])
                widgets["inner"].config(bg=THEME["bg_card"])
                widgets["icon"].config(bg=THEME["bg_card"], fg=THEME["muted"])
                widgets["text"].config(bg=THEME["bg_card"], fg=THEME["text"])

        # Clear content
        for widget in self._content_inner.winfo_children():
            widget.destroy()

        # Build content for selected category
        builder = getattr(self, f"_build_{category_id}", None)
        if builder:
            builder()

    def _on_category_hover(self, category_id: str, entering: bool):
        """Handle category button hover."""
        if category_id == self._current_category:
            return

        widgets = self._category_buttons[category_id]
        if entering:
            widgets["frame"].config(bg=THEME["bg_card_2"])
            widgets["inner"].config(bg=THEME["bg_card_2"])
            widgets["icon"].config(bg=THEME["bg_card_2"])
            widgets["text"].config(bg=THEME["bg_card_2"])
        else:
            widgets["frame"].config(bg=THEME["bg_card"])
            widgets["inner"].config(bg=THEME["bg_card"])
            widgets["icon"].config(bg=THEME["bg_card"])
            widgets["text"].config(bg=THEME["bg_card"])

    def _add_section_header(self, parent, text: str):
        """Add a section header."""
        frame = tk.Frame(parent, bg=THEME["bg_card"])
        frame.pack(fill="x", pady=(0, 15))

        tk.Label(frame, text=text, fg=THEME["accent"], bg=THEME["bg_card"],
                font=("Segoe UI", 12, "bold")).pack(side="left")

        tk.Frame(frame, bg=THEME["border"], height=1).pack(side="left", fill="x",
                                                            expand=True, padx=(15, 0), pady=8)

    def _add_setting_row(self, parent, label: str, description: str = None) -> tk.Frame:
        """Add a setting row and return the right-side frame for controls."""
        row = tk.Frame(parent, bg=THEME["bg_card"])
        row.pack(fill="x", pady=8)

        left = tk.Frame(row, bg=THEME["bg_card"])
        left.pack(side="left", fill="x", expand=True)

        tk.Label(left, text=label, fg=THEME["text"], bg=THEME["bg_card"],
                font=("Segoe UI", 10)).pack(anchor="w")

        if description:
            tk.Label(left, text=description, fg=THEME["muted"], bg=THEME["bg_card"],
                    font=("Segoe UI", 8)).pack(anchor="w")

        right = tk.Frame(row, bg=THEME["bg_card"])
        right.pack(side="right")

        return right

    def _create_toggle(self, parent, setting_key: str) -> tk.Frame:
        """Create a toggle switch."""
        frame = tk.Frame(parent, bg=THEME["bg_card"])

        current = self.settings.get(setting_key)
        var = tk.BooleanVar(value=current)

        def on_toggle():
            self._mark_changed(setting_key, var.get())

        # Custom toggle look
        toggle_frame = tk.Frame(frame, bg="#3d3d54" if not current else THEME["accent"],
                               width=44, height=24, highlightthickness=0)
        toggle_frame.pack()
        toggle_frame.pack_propagate(False)

        knob = tk.Frame(toggle_frame, bg="white", width=20, height=20)
        if current:
            knob.place(x=22, y=2)
        else:
            knob.place(x=2, y=2)

        def toggle_click(e=None):
            new_val = not var.get()
            var.set(new_val)
            if new_val:
                toggle_frame.config(bg=THEME["accent"])
                knob.place(x=22, y=2)
            else:
                toggle_frame.config(bg="#3d3d54")
                knob.place(x=2, y=2)
            on_toggle()

        toggle_frame.bind("<Button-1>", toggle_click)
        knob.bind("<Button-1>", toggle_click)
        toggle_frame.config(cursor="hand2")
        knob.config(cursor="hand2")

        self._widgets[setting_key] = {"var": var, "frame": toggle_frame, "knob": knob}
        return frame

    def _create_dropdown(self, parent, setting_key: str, options: list) -> tk.Frame:
        """Create a dropdown menu."""
        frame = tk.Frame(parent, bg=THEME["bg_card"])

        current = self.settings.get(setting_key)
        var = tk.StringVar(value=str(current))

        def on_change(*args):
            self._mark_changed(setting_key, var.get())

        var.trace_add("write", on_change)

        # Style the dropdown
        dropdown = ttk.Combobox(frame, textvariable=var, values=options,
                               state="readonly", width=15)
        dropdown.pack()

        self._widgets[setting_key] = {"var": var}
        return frame

    def _create_slider(self, parent, setting_key: str, min_val: int, max_val: int,
                       suffix: str = "") -> tk.Frame:
        """Create a slider with value display."""
        frame = tk.Frame(parent, bg=THEME["bg_card"])

        current = self.settings.get(setting_key)
        var = tk.IntVar(value=current)

        value_label = tk.Label(frame, text=f"{current}{suffix}", fg=THEME["text"],
                              bg=THEME["bg_card"], font=("Consolas", 10), width=6)
        value_label.pack(side="right", padx=(10, 0))

        def on_change(val):
            int_val = int(float(val))
            value_label.config(text=f"{int_val}{suffix}")
            self._mark_changed(setting_key, int_val)

        slider = ttk.Scale(frame, from_=min_val, to=max_val, variable=var,
                          orient="horizontal", length=150, command=on_change)
        slider.pack(side="right")

        self._widgets[setting_key] = {"var": var}
        return frame

    def _create_radio_group(self, parent, setting_key: str, options: list) -> tk.Frame:
        """Create a radio button group."""
        frame = tk.Frame(parent, bg=THEME["bg_card"])

        current = self.settings.get(setting_key)
        var = tk.StringVar(value=str(current))

        def on_change():
            self._mark_changed(setting_key, var.get())

        for value, label in options:
            rb = tk.Radiobutton(frame, text=label, variable=var, value=value,
                               bg=THEME["bg_card"], fg=THEME["text"],
                               selectcolor=THEME["bg_card_2"],
                               activebackground=THEME["bg_card"],
                               font=("Segoe UI", 9), command=on_change)
            rb.pack(side="left", padx=(0, 15))

        self._widgets[setting_key] = {"var": var}
        return frame

    def _create_color_picker(self, parent, setting_key: str, colors: dict) -> tk.Frame:
        """Create a color picker with predefined colors."""
        frame = tk.Frame(parent, bg=THEME["bg_card"])

        current = self.settings.get(setting_key)

        for color_name, color_hex in colors.items():
            color_frame = tk.Frame(frame, bg=color_hex, width=28, height=28,
                                  highlightthickness=2,
                                  highlightbackground=THEME["border"] if color_name != current else "white",
                                  cursor="hand2")
            color_frame.pack(side="left", padx=3)
            color_frame.pack_propagate(False)

            def on_click(e, name=color_name):
                self._mark_changed(setting_key, name)
                # Update visual selection
                for child in frame.winfo_children():
                    child.config(highlightbackground=THEME["border"])
                e.widget.config(highlightbackground="white")

            color_frame.bind("<Button-1>", on_click)

        return frame

    def _mark_changed(self, key: str, value):
        """Mark a setting as changed."""
        original = self.settings.get(key)
        if value != original:
            self._pending_changes[key] = value
        elif key in self._pending_changes:
            del self._pending_changes[key]

        # Update UI
        if self._pending_changes:
            self._unsaved_label.config(text=f"⚠ {len(self._pending_changes)} unsaved changes")
        else:
            self._unsaved_label.config(text="")

    # ================================================================
    # CATEGORY BUILDERS
    # ================================================================

    def _build_appearance(self):
        """Build Appearance settings."""
        from settings import ACCENT_COLORS

        self._add_section_header(self._content_inner, "Theme")

        # Theme toggle
        right = self._add_setting_row(self._content_inner, "Color Theme",
                                      "Choose between dark and light mode")
        self._create_radio_group(right, "theme", [("dark", "🌙 Dark"), ("light", "☀️ Light")]).pack()

        # Accent color
        right = self._add_setting_row(self._content_inner, "Accent Color",
                                      "Primary color for buttons and highlights")
        self._create_color_picker(right, "accent_color", ACCENT_COLORS).pack()

        self._add_section_header(self._content_inner, "Text")

        # Font size
        right = self._add_setting_row(self._content_inner, "Font Size",
                                      "Adjust text size throughout the app")
        self._create_radio_group(right, "font_size",
                                [("compact", "Compact"), ("normal", "Normal"), ("large", "Large")]).pack()

        # Animations
        right = self._add_setting_row(self._content_inner, "Animations",
                                      "Enable smooth transitions and effects")
        self._create_toggle(right, "animations").pack()

    def _build_data(self):
        """Build Data & Refresh settings."""
        self._add_section_header(self._content_inner, "Auto Refresh")

        # Auto-refresh toggle
        right = self._add_setting_row(self._content_inner, "Enable Auto-Refresh",
                                      "Automatically fetch new data at regular intervals")
        self._create_toggle(right, "auto_refresh").pack()

        # Refresh interval
        right = self._add_setting_row(self._content_inner, "Refresh Interval",
                                      "How often to fetch new data")
        self._create_dropdown(right, "refresh_interval",
                             ["30", "60", "120", "300", "600"]).pack()

        # Show countdown
        right = self._add_setting_row(self._content_inner, "Show Countdown Timer",
                                      "Display time until next refresh")
        self._create_toggle(right, "show_countdown").pack()

        self._add_section_header(self._content_inner, "Data Quality")

        # Stale warning
        right = self._add_setting_row(self._content_inner, "Stale Data Warning",
                                      "Warn when data is older than X minutes")
        self._create_slider(right, "stale_warning_minutes", 1, 30, " min").pack()

    def _build_alerts(self):
        """Build Alerts settings."""
        self._add_section_header(self._content_inner, "Rate Alerts")

        # Enable alerts
        right = self._add_setting_row(self._content_inner, "Enable Rate Alerts",
                                      "Get notified when NIBOR rates change significantly")
        self._create_toggle(right, "rate_alerts_enabled").pack()

        # Threshold
        right = self._add_setting_row(self._content_inner, "Alert Threshold",
                                      "Minimum change in basis points to trigger alert")
        self._create_slider(right, "rate_alert_threshold_bps", 1, 20, " bps").pack()

        self._add_section_header(self._content_inner, "Notification Types")

        # Sound
        right = self._add_setting_row(self._content_inner, "Sound Notifications",
                                      "Play a sound when alerts trigger")
        self._create_toggle(right, "sound_enabled").pack()

        # Toast
        right = self._add_setting_row(self._content_inner, "Toast Notifications",
                                      "Show popup notifications in-app")
        self._create_toggle(right, "toast_enabled").pack()

        # System tray
        right = self._add_setting_row(self._content_inner, "System Tray Alerts",
                                      "Show notifications in Windows system tray")
        self._create_toggle(right, "tray_alerts_enabled").pack()

    def _build_display(self):
        """Build Display settings."""
        self._add_section_header(self._content_inner, "Numbers")

        # Decimal places
        right = self._add_setting_row(self._content_inner, "Decimal Places",
                                      "Number of decimals for rate display")
        self._create_radio_group(right, "decimal_places",
                                [("2", "2"), ("4", "4"), ("6", "6")]).pack()

        # Show CHG column
        right = self._add_setting_row(self._content_inner, "Show Change Column",
                                      "Display daily change in rate tables")
        self._create_toggle(right, "show_chg_column").pack()

        self._add_section_header(self._content_inner, "Layout")

        # Start page
        right = self._add_setting_row(self._content_inner, "Start Page",
                                      "Which page to show when the app opens")
        self._create_dropdown(right, "start_page",
                             ["dashboard", "history", "nibor_days", "nok_implied"]).pack()

        # Compact mode
        right = self._add_setting_row(self._content_inner, "Compact Mode",
                                      "Use smaller margins and padding")
        self._create_toggle(right, "compact_mode").pack()

    def _build_connections(self):
        """Build Connections settings."""
        self._add_section_header(self._content_inner, "Bloomberg")

        # Auto-connect
        right = self._add_setting_row(self._content_inner, "Auto-Connect",
                                      "Automatically connect to Bloomberg on startup")
        self._create_toggle(right, "bloomberg_auto_connect").pack()

        # Timeout
        right = self._add_setting_row(self._content_inner, "Connection Timeout",
                                      "Maximum time to wait for Bloomberg response")
        self._create_slider(right, "bloomberg_timeout", 5, 60, "s").pack()

        self._add_section_header(self._content_inner, "Status Display")

        # Show connection status
        right = self._add_setting_row(self._content_inner, "Show Connection Status",
                                      "Display connection indicators in status bar")
        self._create_toggle(right, "show_connection_status").pack()

    def _build_history(self):
        """Build History settings."""
        self._add_section_header(self._content_inner, "Snapshots")

        # Auto-save
        right = self._add_setting_row(self._content_inner, "Auto-Save Snapshots",
                                      "Automatically save NIBOR snapshots")
        self._create_toggle(right, "auto_save_snapshots").pack()

        # Retention
        right = self._add_setting_row(self._content_inner, "History Retention",
                                      "How long to keep historical data")
        self._create_dropdown(right, "history_retention_days",
                             ["30", "60", "90", "180", "365"]).pack()

        self._add_section_header(self._content_inner, "Audit Log")

        # Log level
        right = self._add_setting_row(self._content_inner, "Log Level",
                                      "Minimum severity to record in audit log")
        self._create_dropdown(right, "audit_log_level",
                             ["all", "info", "warning", "error"]).pack()

        # Max entries
        right = self._add_setting_row(self._content_inner, "Max Log Entries",
                                      "Maximum number of log entries to keep")
        self._create_slider(right, "max_log_entries", 1000, 10000, "").pack()

    def _build_shortcuts(self):
        """Build Keyboard Shortcuts display."""
        self._add_section_header(self._content_inner, "Navigation")

        shortcuts_nav = [
            ("Ctrl + 1", "Go to Dashboard"),
            ("Ctrl + 2", "Go to History"),
            ("Ctrl + 3", "Go to Nibor Days"),
            ("Ctrl + H", "Go to History"),
            ("Ctrl + ,", "Open Settings"),
        ]

        for key, action in shortcuts_nav:
            row = tk.Frame(self._content_inner, bg=THEME["bg_card"])
            row.pack(fill="x", pady=4)

            key_frame = tk.Frame(row, bg=THEME["bg_card_2"], padx=8, pady=4)
            key_frame.pack(side="left")
            tk.Label(key_frame, text=key, fg=THEME["text"], bg=THEME["bg_card_2"],
                    font=("Consolas", 10, "bold")).pack()

            tk.Label(row, text=action, fg=THEME["muted"], bg=THEME["bg_card"],
                    font=("Segoe UI", 10)).pack(side="left", padx=(15, 0))

        self._add_section_header(self._content_inner, "Actions")

        shortcuts_action = [
            ("Ctrl + R", "Refresh Data"),
            ("Ctrl + S", "Save Snapshot"),
            ("Ctrl + E", "Export"),
            ("F5", "Refresh Data"),
            ("F11", "Toggle Fullscreen"),
            ("Escape", "Close Popup / Cancel"),
        ]

        for key, action in shortcuts_action:
            row = tk.Frame(self._content_inner, bg=THEME["bg_card"])
            row.pack(fill="x", pady=4)

            key_frame = tk.Frame(row, bg=THEME["bg_card_2"], padx=8, pady=4)
            key_frame.pack(side="left")
            tk.Label(key_frame, text=key, fg=THEME["text"], bg=THEME["bg_card_2"],
                    font=("Consolas", 10, "bold")).pack()

            tk.Label(row, text=action, fg=THEME["muted"], bg=THEME["bg_card"],
                    font=("Segoe UI", 10)).pack(side="left", padx=(15, 0))

    def _build_system(self):
        """Build System settings."""
        self._add_section_header(self._content_inner, "Window Behavior")

        # Minimize to tray
        right = self._add_setting_row(self._content_inner, "Minimize to System Tray",
                                      "Keep running in background when minimized")
        self._create_toggle(right, "minimize_to_tray").pack()

        # Start with Windows
        right = self._add_setting_row(self._content_inner, "Start with Windows",
                                      "Launch automatically when Windows starts")
        self._create_toggle(right, "start_with_windows").pack()

        # Confirm on close
        right = self._add_setting_row(self._content_inner, "Confirm on Close",
                                      "Ask for confirmation before closing")
        self._create_toggle(right, "confirm_on_close").pack()

        self._add_section_header(self._content_inner, "Language")

        # Language
        right = self._add_setting_row(self._content_inner, "Language",
                                      "Interface language")
        self._create_radio_group(right, "language",
                                [("sv", "🇸🇪 Svenska"), ("en", "🇬🇧 English")]).pack()

    def _build_about(self):
        """Build About section."""
        from config import APP_VERSION
        import getpass
        import platform

        # Center content
        center = tk.Frame(self._content_inner, bg=THEME["bg_card"])
        center.pack(expand=True)

        # Logo
        tk.Label(center, text="N", font=("Segoe UI", 64, "bold"),
                fg=THEME["accent"], bg=THEME["bg_card"]).pack(pady=(20, 10))

        # Title
        tk.Label(center, text="NIBOR CALCULATION TERMINAL",
                fg=THEME["text"], bg=THEME["bg_card"],
                font=("Segoe UI", 16, "bold")).pack()

        # Version
        tk.Label(center, text=f"Version {APP_VERSION}",
                fg=THEME["muted"], bg=THEME["bg_card"],
                font=("Segoe UI", 11)).pack(pady=(5, 20))

        # Separator
        tk.Frame(center, bg=THEME["border"], height=1, width=200).pack(pady=10)

        # Info
        info_frame = tk.Frame(center, bg=THEME["bg_card"])
        info_frame.pack(pady=10)

        info = [
            ("User", getpass.getuser()),
            ("Machine", platform.node()),
            ("Python", platform.python_version()),
            ("OS", f"{platform.system()} {platform.release()}"),
        ]

        for label, value in info:
            row = tk.Frame(info_frame, bg=THEME["bg_card"])
            row.pack(fill="x", pady=2)
            tk.Label(row, text=f"{label}:", fg=THEME["muted"], bg=THEME["bg_card"],
                    font=("Segoe UI", 9), width=10, anchor="e").pack(side="left")
            tk.Label(row, text=value, fg=THEME["text"], bg=THEME["bg_card"],
                    font=("Consolas", 9)).pack(side="left", padx=(10, 0))

        # Separator
        tk.Frame(center, bg=THEME["border"], height=1, width=200).pack(pady=15)

        # Copyright
        tk.Label(center, text="© 2025 Swedbank Treasury",
                fg=THEME["muted"], bg=THEME["bg_card"],
                font=("Segoe UI", 9)).pack()

        # Buttons
        btn_frame = tk.Frame(center, bg=THEME["bg_card"])
        btn_frame.pack(pady=20)

        OnyxButtonTK(btn_frame, "📂 Open Log Folder", command=self._open_log_folder,
                    variant="default").pack(side="left", padx=5)
        OnyxButtonTK(btn_frame, "📄 View License", command=self._show_license,
                    variant="default").pack(side="left", padx=5)

    # ================================================================
    # ACTIONS
    # ================================================================

    def _cancel_changes(self):
        """Cancel pending changes."""
        self._pending_changes.clear()
        self._unsaved_label.config(text="")
        self._select_category(self._current_category)  # Rebuild current view

    def _apply_changes(self):
        """Apply pending changes without saving to file."""
        for key, value in self._pending_changes.items():
            self.settings.set(key, value)
        self._pending_changes.clear()
        self._unsaved_label.config(text="✓ Changes applied")
        self.after(2000, lambda: self._unsaved_label.config(text=""))

    def _save_changes(self):
        """Apply and save changes to file."""
        for key, value in self._pending_changes.items():
            self.settings.set(key, value)
        self._pending_changes.clear()
        self.settings.save()
        self._unsaved_label.config(text="✓ Settings saved")
        self.after(2000, lambda: self._unsaved_label.config(text=""))

    def _restore_defaults(self):
        """Restore all settings to defaults."""
        import tkinter.messagebox as messagebox
        if messagebox.askyesno("Restore Defaults",
                               "Are you sure you want to restore all settings to defaults?"):
            self.settings.reset_to_defaults()
            self._pending_changes.clear()
            self._select_category(self._current_category)
            self._unsaved_label.config(text="✓ Defaults restored")

    def _import_settings(self):
        """Import settings from file."""
        import tkinter.filedialog as filedialog
        filepath = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json")],
            title="Import Settings"
        )
        if filepath:
            from pathlib import Path
            if self.settings.import_settings(Path(filepath)):
                self._select_category(self._current_category)
                self._unsaved_label.config(text="✓ Settings imported")

    def _export_settings(self):
        """Export settings to file."""
        import tkinter.filedialog as filedialog
        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
            title="Export Settings",
            initialfile="nibor_settings.json"
        )
        if filepath:
            from pathlib import Path
            if self.settings.export_settings(Path(filepath)):
                self._unsaved_label.config(text="✓ Settings exported")

    def _open_log_folder(self):
        """Open the log folder."""
        import os
        from config import NIBOR_LOG_PATH
        if NIBOR_LOG_PATH.exists():
            os.startfile(NIBOR_LOG_PATH)

    def _show_license(self):
        """Show license information."""
        popup = tk.Toplevel(self)
        popup.title("License")
        popup.geometry("500x400")
        popup.configure(bg=THEME["bg_main"])
        popup.transient(self.winfo_toplevel())

        tk.Label(popup, text="MIT License", fg=THEME["accent"], bg=THEME["bg_main"],
                font=("Segoe UI", 14, "bold")).pack(pady=20)

        license_text = """Copyright (c) 2025 Swedbank Treasury

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT."""

        text = tk.Text(popup, bg=THEME["bg_card"], fg=THEME["text"],
                      font=("Consolas", 9), relief="flat", wrap="word")
        text.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        text.insert("1.0", license_text)
        text.config(state="disabled")

        OnyxButtonTK(popup, "Close", command=popup.destroy, variant="default").pack(pady=(0, 20))

    def update(self):
        """Refresh the settings page."""
        pass
