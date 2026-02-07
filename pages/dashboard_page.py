"""
DashboardPage for Nibor Calculation Terminal.
"""
import tkinter as tk
from tkinter import ttk
from datetime import datetime, timedelta

from ctk_compat import ctk, CTK_AVAILABLE

from config import THEME, FONTS, CURRENT_MODE, RULES_DB, MARKET_STRUCTURE, ALERTS_BOX_HEIGHT, CTK_CORNER_RADIUS, RADII, get_logger, get_market_structure, get_ticker

log = get_logger("ui_pages")
from ui_components import OnyxButtonTK, MetricChipTK, DataTableTree, SummaryCard, CollapsibleSection, RatesActionBar
from ui.components.drawers import CalculationDrawer, CompactCalculationDrawer
from ui.components.cards import MetricCard
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

from pages._common import BaseFrame, ToolTip


class DashboardPage(BaseFrame):
    """Main dashboard with Command Center sidebar and clean layout (CTk Edition)."""

    def __init__(self, master, app):
        if CTK_AVAILABLE:
            super().__init__(master, fg_color=THEME["bg_panel"], corner_radius=0)
        else:
            super().__init__(master, bg=THEME["bg_panel"])
        self.app = app

        # Initialize blink tracking
        self._blink_widgets = {}

        # Initialize match data for all tenors (ensures button state works on first update)
        self._match_data = {}

        # Track if a fresh calculation has been performed (not just loaded from last approved)
        self._calculation_performed = False

        # Track loading state to avoid validation during loading
        self._is_loading = False

        # ====================================================================
        # NAVIGATION REMOVED - Now in main.py (visible on ALL pages)
        # ====================================================================
        # The Command Center sidebar has been moved to main.py so it's
        # always visible across all pages. DashboardPage now only contains
        # the dashboard content itself.
        # ====================================================================

        # ====================================================================
        # DASHBOARD CONTENT (CTk if available) - Aligned with sidebar
        # ====================================================================
        if CTK_AVAILABLE:
            content = ctk.CTkFrame(self, fg_color="transparent")
        else:
            content = tk.Frame(self, bg=THEME["bg_panel"])
        content.pack(fill="both", expand=True, padx=12, pady=(0, 6))
        self._content = content

        # Drawer will be created as separate window when needed
        self._drawer = None
        self._drawer_window = None

        # Bind ESC to close drawer (use toplevel window, not bind_all which CTk disallows)
        self.winfo_toplevel().bind("<Escape>", self._close_drawer_on_escape, add="+")

        # Default calculation model (Swedbank Calc)
        self.calc_model_var = tk.StringVar(value="swedbank")

        # ====================================================================
        # NIBOR RATES CARD - Premium Hero Card (Main Feature)
        # ====================================================================

        # Outer wrapper for accent border effect (left accent stripe)
        card_wrapper = tk.Frame(content, bg=THEME["accent"])
        card_wrapper.pack(fill="x", pady=(0, 0))
        self._card_wrapper = card_wrapper  # Store for historical mode styling

        # Main card container with white surface
        if CTK_AVAILABLE:
            nibor_card = ctk.CTkFrame(
                card_wrapper,
                fg_color=THEME["bg_card"],
                corner_radius=0,  # Wrapper handles the accent
                border_width=0
            )
        else:
            nibor_card = tk.Frame(
                card_wrapper,
                bg=THEME["bg_card"]
            )
        # Left accent stripe (4px orange) + white card
        nibor_card.pack(fill="x", padx=(4, 0), pady=0)

        # Card inner padding container
        card_content = tk.Frame(nibor_card, bg=THEME["bg_card"])
        card_content.pack(fill="x", padx=24, pady=16)

        # ----------------------------------------------------------------
        # CARD HEADER ROW: Title | Dev Badge | View History link (right)
        # ----------------------------------------------------------------
        header_row = tk.Frame(card_content, bg=THEME["bg_card"])
        header_row.pack(fill="x", pady=(0, 10))
        self._header_row = header_row  # Store for historical badge
        self._historical_badge = None  # Will be created when needed

        # Left side: Title with accent underline effect
        title_container = tk.Frame(header_row, bg=THEME["bg_card"])
        title_container.pack(side="left")

        tk.Label(
            title_container,
            text="NIBOR RATES",
            fg=THEME["text"],
            bg=THEME["bg_card"],
            font=("Segoe UI Semibold", 20)
        ).pack(anchor="w")

        # Dev/Prod badge REMOVED - now in global header (top left)

        # Right side: View History link
        if MATPLOTLIB_AVAILABLE and TrendPopup:
            history_link = tk.Label(
                header_row,
                text="View History →",
                fg=THEME["accent"],
                bg=THEME["bg_card"],
                font=("Segoe UI", 11),
                cursor="hand2"
            )
            history_link.pack(side="right")
            history_link.bind("<Button-1>", lambda e: self._show_trend_popup())
            history_link.bind("<Enter>", lambda e: history_link.config(fg=THEME["accent_hover"]))
            history_link.bind("<Leave>", lambda e: history_link.config(fg=THEME["accent"]))

        # Header separator line
        tk.Frame(card_content, bg=THEME["border"], height=1).pack(fill="x", pady=(0, 12))

        # Calculate button container (button added by main.py)
        self.validation_btn_container = tk.Frame(card_content, bg=THEME["bg_card"])
        self.validation_btn_container.pack(fill="x", pady=(0, 16))

        # 1W toggle - small, above the table
        self._1w_toggle_frame = tk.Frame(card_content, bg=THEME["bg_card"])
        self._1w_toggle_frame.pack(fill="x", pady=(0, 8), padx=18)

        self._1w_indicator = tk.Label(
            self._1w_toggle_frame,
            text="▶",
            font=("Segoe UI", 9),
            fg=THEME["text_light"],
            bg=THEME["bg_card"],
            cursor="hand2"
        )
        self._1w_indicator.pack(side="left")

        self._1w_toggle_label = tk.Label(
            self._1w_toggle_frame,
            text="1W",
            font=("Segoe UI", 10),
            fg=THEME["text_light"],
            bg=THEME["bg_card"],
            cursor="hand2"
        )
        self._1w_toggle_label.pack(side="left", padx=(4, 0))

        self._1w_badge = tk.Label(
            self._1w_toggle_frame,
            text="Not Available",
            font=("Segoe UI", 9),
            fg=THEME["text_light"],
            bg=THEME["chip"],
            padx=8,
            pady=2,
            cursor="hand2"
        )
        self._1w_badge.pack(side="left", padx=(8, 0))

        # Table frame for grid layout - FULL WIDTH
        funding_frame = tk.Frame(card_content, bg=THEME["bg_card"])
        funding_frame.pack(fill="x")
        self._funding_frame = funding_frame  # Store reference for 1W row

        # Configure columns to expand proportionally
        col_weights = [1, 2, 1, 2, 1, 0, 2]  # TENOR, FUNDING, SPREAD, NIBOR, CHG, sep, CONTRIB
        for i, w in enumerate(col_weights):
            funding_frame.grid_columnconfigure(i, weight=w, uniform="cols" if w > 0 else None)

        # ================================================================
        # TABLE HEADER - Nordic Light premium styling
        # ================================================================
        header_text_color = THEME["text_muted"]  # Muted text for headers
        header_bg = THEME["table_header_bg"]     # Subtle header background
        row_separator_color = THEME["border"]     # Subtle border

        # Main headers with premium styling - wider columns with better hierarchy
        headers = [
            ("TENOR", 12, "center"),
            ("FUNDING RATE", 20, "center"),
            ("SPREAD", 12, "center"),
            ("NIBOR", 20, "center"),
            ("CHG", 14, "center"),
        ]
        for col, (text, width, anchor) in enumerate(headers):
            # Keep headers consistent. (Per request: no special background/border.)
            tk.Label(
                funding_frame,
                text=text,
                fg=THEME["text"],
                bg=header_bg,
                font=("Segoe UI Semibold", 11),
                width=width,
                pady=12,
                padx=18,
                anchor=anchor,
            ).grid(row=0, column=col, sticky="nsew")

        # Vertical separator between main cols and contribution
        tk.Frame(funding_frame, bg=row_separator_color, width=1).grid(row=0, column=5, rowspan=20, sticky="ns", padx=12)

        # Contribution header - wider
        tk.Label(funding_frame, text="NIBOR Contribution",
                fg=header_text_color,
                bg=header_bg,
                font=("Segoe UI Semibold", 10),
                width=20, pady=10, padx=16,
                anchor="center").grid(row=0, column=6, sticky="nsew")

        # Header bottom separator
        tk.Frame(funding_frame, bg=row_separator_color, height=1).grid(row=1, column=0, columnspan=7, sticky="ew")

        # ================================================================
        # DATA ROWS - Nordic Light with row hover effects
        # ================================================================
        self.funding_cells = {}

        # Only active tenors in main table (1W is handled separately above)
        tenors = [
            {"key": "1m", "label": "1M", "excel_row": 30, "excel_col": 27},
            {"key": "2m", "label": "2M", "excel_row": 31, "excel_col": 27},
            {"key": "3m", "label": "3M", "excel_row": 32, "excel_col": 27},
            {"key": "6m", "label": "6M", "excel_row": 33, "excel_col": 27}
        ]

        row_bg = THEME["bg_card"]         # Card white background
        hover_bg = THEME["row_hover"]     # Subtle hover state

        # Create hidden 1W row (shown when toggle is clicked)
        self._1w_row_frame = tk.Frame(funding_frame, bg=row_bg)
        self._1w_row_visible = False

        # 1W row content
        tk.Label(self._1w_row_frame, text="1W",
                fg=THEME["text_light"], bg=row_bg,
                font=("Segoe UI Semibold", 13),
                width=12, anchor="center", pady=14, padx=18
        ).grid(row=0, column=0, sticky="nsew")

        for col, val in enumerate(["N/A", "—", "N/A", "—"], start=1):
            # Keep 1W row clean as well (no special background/border).
            # If you later want orange numbers here too, we can re-add only fg for the NIBOR cell.
            tk.Label(
                self._1w_row_frame,
                text=val,
                fg=THEME["text_light"],
                bg=row_bg,
                font=("Consolas", 12),
                anchor="center",
                pady=14,
                padx=16,
            ).grid(row=0, column=col, sticky="nsew")

        # Separator and contribution for 1W
        tk.Frame(self._1w_row_frame, bg=row_separator_color, width=1).grid(row=0, column=5, sticky="ns", padx=12)
        tk.Label(self._1w_row_frame, text="—",
                fg=THEME["text_light"], bg=row_bg,
                font=("Consolas", 11), anchor="center", pady=14, padx=16
        ).grid(row=0, column=6, sticky="nsew")

        # Configure 1W row columns
        for i, w in enumerate(col_weights):
            self._1w_row_frame.grid_columnconfigure(i, weight=w, uniform="cols" if w > 0 else None)

        # 1W row separator
        self._1w_separator = tk.Frame(funding_frame, bg=row_separator_color, height=1)

        # Toggle function for 1W
        def toggle_1w_row(e=None):
            if self._1w_row_visible:
                self._1w_row_frame.grid_forget()
                self._1w_separator.grid_forget()
                self._1w_indicator.config(text="▶")
                self._1w_row_visible = False
            else:
                self._1w_row_frame.grid(row=2, column=0, columnspan=7, sticky="nsew")
                self._1w_separator.grid(row=3, column=0, columnspan=7, sticky="ew")
                self._1w_indicator.config(text="▼")
                self._1w_row_visible = True

        # Bind toggle to all 1W toggle elements
        for widget in [self._1w_indicator, self._1w_toggle_label, self._1w_badge]:
            widget.bind("<Button-1>", toggle_1w_row)

        self.funding_cells["1w"] = {}

        # Start row index after potential 1W row
        start_row = 4

        for i, tenor in enumerate(tenors):
            row_idx = start_row + (i * 2)  # Leave room for separator rows

            # Collect all widgets in this row for hover effect
            row_widgets = []

            # TENOR label - bold, larger, more padding
            tenor_lbl = tk.Label(funding_frame, text=tenor["label"], fg=THEME["text"],
                    bg=row_bg, font=("Segoe UI Semibold", 13),
                    width=12, anchor="center", pady=14, padx=18)
            tenor_lbl.grid(row=row_idx, column=0, sticky="nsew")
            row_widgets.append(tenor_lbl)

            cells = {}

            # FUNDING RATE - monospace, centered, clickable, more padding
            funding_lbl = tk.Label(funding_frame, text="—",
                                  fg=THEME["text"], bg=row_bg,
                                  font=("Consolas", 12),
                                  width=20, anchor="center", cursor="hand2", pady=14, padx=18)
            funding_lbl.grid(row=row_idx, column=1, sticky="nsew")
            funding_lbl.bind("<Button-1>", lambda e, t=tenor["key"]: self._show_funding_details(t, show_spread=False))
            row_widgets.append(funding_lbl)
            cells["funding"] = funding_lbl
            ToolTip(funding_lbl, lambda t=tenor["key"]: self._get_funding_tooltip(t))

            # SPREAD - monospace, centered, muted, more padding
            spread_lbl = tk.Label(funding_frame, text="—",
                                 fg=THEME["text_muted"], bg=row_bg,
                                 font=("Consolas", 12),
                                 width=12, anchor="center", pady=14, padx=18)
            spread_lbl.grid(row=row_idx, column=2, sticky="nsew")
            row_widgets.append(spread_lbl)
            cells["spread"] = spread_lbl

            # NIBOR - keep it simple: orange numbers only (no highlight background / border).
            final_lbl = tk.Label(
                funding_frame,
                text="—",
                fg=THEME["accent"],
                bg=row_bg,
                font=("Consolas", 18, "bold"),
                width=20,
                anchor="center",
                cursor="hand2",
                pady=14,
                padx=20,
            )
            final_lbl.grid(row=row_idx, column=3, sticky="nsew")
            final_lbl.bind("<Button-1>", lambda e, t=tenor["key"]: self._show_funding_details(t, show_spread=True))
            row_widgets.append(final_lbl)
            cells["final"] = final_lbl
            ToolTip(final_lbl, lambda t=tenor["key"]: self._get_nibor_tooltip(t))

            # CHG - monospace, centered (color set dynamically), more padding
            chg_lbl = tk.Label(funding_frame, text="—",
                              fg=THEME["text_muted"], bg=row_bg,
                              font=("Consolas", 12),
                              width=14, anchor="center", pady=14, padx=18)
            chg_lbl.grid(row=row_idx, column=4, sticky="nsew")
            row_widgets.append(chg_lbl)
            cells["chg"] = chg_lbl
            ToolTip(chg_lbl, lambda t=tenor["key"]: self._get_chg_tooltip(t))

            # NIBOR Contribution - Larger pill badge
            pill_container = tk.Frame(funding_frame, bg=row_bg)
            pill_container.grid(row=row_idx, column=6, sticky="nsew", pady=10, padx=16)
            row_widgets.append(pill_container)

            # Create pill badge - larger
            pill_badge = tk.Frame(pill_container, bg=THEME["chip"])
            pill_badge.pack(anchor="center", expand=True)
            pill_label = tk.Label(pill_badge, text="—",
                                  fg=THEME["text_muted"], bg=THEME["chip"],
                                  font=("Segoe UI", 12), padx=14, pady=5)
            pill_label.pack()

            cells["nibor_contrib"] = pill_label
            cells["nibor_contrib_badge"] = pill_badge
            cells["nibor_contrib_container"] = pill_container
            cells["row_bg"] = row_bg
            cells["row_widgets"] = row_widgets  # Store for hover effect

            # Make NIBOR Contribution clickable - opens reconciliation drawer
            pill_badge.config(cursor="hand2")
            pill_label.config(cursor="hand2")
            pill_badge.bind("<Button-1>", lambda e, t=tenor["key"]: self._open_drawer_for_tenor(t))
            pill_label.bind("<Button-1>", lambda e, t=tenor["key"]: self._open_drawer_for_tenor(t))

            # Bind row hover effect to all widgets
            def make_hover_enter(widgets, hbg):
                def handler(e):
                    for w in widgets:
                        if isinstance(w, (tk.Label, tk.Frame)):
                            w.config(bg=hbg)
                return handler

            def make_hover_leave(widgets, rbg):
                def handler(e):
                    for w in widgets:
                        if isinstance(w, (tk.Label, tk.Frame)):
                            w.config(bg=rbg)
                return handler

            for w in row_widgets:
                w.bind("<Enter>", make_hover_enter(row_widgets, hover_bg), add="+")
                w.bind("<Leave>", make_hover_leave(row_widgets, row_bg), add="+")

            # Subtle row separator
            tk.Frame(funding_frame, bg=row_separator_color, height=1).grid(row=row_idx+1, column=0, columnspan=7, sticky="ew")

            cells["excel_row"] = tenor["excel_row"]
            cells["excel_col"] = tenor["excel_col"]

            self.funding_cells[tenor["key"]] = cells

        # ====================================================================
        # VALIDATION CHECKS BAR - 6 check categories with ✓/✕ status
        # ====================================================================
        tk.Frame(card_content, bg=THEME["border"], height=1).pack(fill="x", pady=(20, 0))

        checks_bar = tk.Frame(card_content, bg=THEME["bg_card"])
        checks_bar.pack(fill="x", pady=(12, 12))

        # Validation checks label
        tk.Label(checks_bar, text="Validation:",
                fg=THEME["text_muted"],
                bg=THEME["bg_card"],
                font=("Segoe UI", 10)).pack(side="left", padx=(0, 16))

        # Store check badges for updates
        self.validation_checks = {}

        # Define the 6 check categories
        check_categories = [
            ("bloomberg", "Bloomberg"),
            ("excel_cells", "Excel Cells"),
            ("weights", "Weights"),
            ("days", "Days"),
            ("nibor_contrib", "Implied NOK"),
            ("spreads", "Spreads"),
        ]

        for check_id, check_label in check_categories:
            # Create clickable badge
            badge_frame = tk.Frame(checks_bar, bg=THEME["chip"], cursor="hand2")
            badge_frame.pack(side="left", padx=(0, 8))

            # Status icon (✓ or ✕) — slightly larger than label for emphasis
            status_icon = tk.Label(badge_frame, text="—",
                                   fg=THEME["text_muted"],
                                   bg=THEME["chip"],
                                   font=("Segoe UI", 14))
            status_icon.pack(side="left", padx=(8, 4), pady=6)

            # Label
            label = tk.Label(badge_frame, text=check_label,
                            fg=THEME["text_muted"],
                            bg=THEME["chip"],
                            font=("Segoe UI", 10))
            label.pack(side="left", padx=(0, 10), pady=6)

            # Store references
            self.validation_checks[check_id] = {
                "frame": badge_frame,
                "icon": status_icon,
                "label": label,
                "status": None,  # None=pending, True=OK, False=Failed
                "alerts": []     # List of alert messages
            }

            # Bind click to show popup
            def make_click_handler(cid):
                return lambda e: self._show_validation_popup(cid)

            badge_frame.bind("<Button-1>", make_click_handler(check_id))
            status_icon.bind("<Button-1>", make_click_handler(check_id))
            label.bind("<Button-1>", make_click_handler(check_id))

            # Hover effect
            def make_hover_enter(frame):
                return lambda e: frame.config(bg=THEME["chip2"]) or [w.config(bg=THEME["chip2"]) for w in frame.winfo_children()]

            def make_hover_leave(frame, check_id):
                def handler(e):
                    # Always use chip background
                    bg = THEME["chip"]
                    frame.config(bg=bg)
                    for w in frame.winfo_children():
                        w.config(bg=bg)
                return handler

            badge_frame.bind("<Enter>", make_hover_enter(badge_frame))
            badge_frame.bind("<Leave>", make_hover_leave(badge_frame, check_id))
            for w in badge_frame.winfo_children():
                w.bind("<Enter>", make_hover_enter(badge_frame))
                w.bind("<Leave>", make_hover_leave(badge_frame, check_id))

        # Summary on right side - X/Y format with larger text
        self.validation_summary_lbl = tk.Label(checks_bar, text="",
                                               fg=THEME["text_muted"],
                                               bg=THEME["bg_card"],
                                               font=("Segoe UI Semibold", 13))
        self.validation_summary_lbl.pack(side="right")

        # ====================================================================
        # ACTION BAR - Premium action bar with metadata and buttons
        # ====================================================================
        if CTK_AVAILABLE:
            self.action_bar = RatesActionBar(
                card_content,
                on_rerun_checks=self._on_rerun_checks,
                on_confirm_rates=self._on_confirm_rates,
            )
            self.action_bar.pack(fill="x", pady=(10, 10))
            # Reference for backwards compatibility
            self.confirm_rates_btn = self.action_bar.confirm_btn
        else:
            # Fallback for non-CTK
            confirm_btn_frame = tk.Frame(card_content, bg=THEME["bg_card"])
            confirm_btn_frame.pack(anchor="center", pady=(15, 10))
            self.confirm_rates_btn = tk.Button(
                confirm_btn_frame,
                text="Confirm rates",
                command=self._on_confirm_rates,
                fg="white",
                bg=THEME["accent"],
                activebackground=THEME["accent_hover"],
                activeforeground="white",
                font=("Segoe UI Semibold", 13),
                relief="flat",
                cursor="hand2",
                width=24,
                height=2,
                state="disabled"
            )
            self.confirm_rates_btn.pack()
            self.action_bar = None

    def _on_dashboard_model_change(self):
        """Handle calculation model change on Dashboard."""
        model = self.calc_model_var.get()
        log.info(f"[Dashboard] Calculation model changed to: {model}")
        # Store selected model in app
        self.app.selected_calc_model = model
        # Trigger re-update of funding rates table
        self._update_funding_rates_with_validation()

    def _on_rerun_checks(self):
        """Handle Re-run checks button click - runs all validations."""
        log.info("[Dashboard] Re-run checks clicked")

        # Re-run the validation update
        self._update_funding_rates_with_validation()

        # Show toast if available
        if hasattr(self.app, 'toast'):
            self.app.toast.info("Validation checks re-run")

    def _on_confirm_rates(self):
        """Handle Confirm rates button click."""
        from history import confirm_rates

        # Guard against double-click while confirmation is in progress
        if getattr(self, '_confirming', False):
            log.debug("[Dashboard] Confirm already in progress, ignoring click")
            return
        self._confirming = True

        log.info("[Dashboard] Confirm rates button clicked")

        # Set loading state on action bar
        if self.action_bar:
            self.action_bar.set_loading(True)
        else:
            self.confirm_rates_btn.configure(state="disabled", text="Confirming...")

        def do_confirm():
            try:
                success, message = confirm_rates(self.app)

                # Update UI on main thread
                def update_ui():
                    self._confirming = False
                    if self.action_bar:
                        self.action_bar.set_loading(False)
                        if success:
                            self.action_bar.flash_confirmed()
                    else:
                        self.confirm_rates_btn.configure(state="normal", text="Confirm rates")

                    if success:
                        # Show toast notification
                        if hasattr(self.app, 'toast'):
                            self.app.toast.success(message, duration=4000)
                        log.info(f"[Dashboard] {message}")
                    else:
                        # Show error toast
                        if hasattr(self.app, 'toast'):
                            self.app.toast.error(message, duration=5000)
                        log.error(f"[Dashboard] {message}")

                self.after(0, update_ui)

            except Exception as e:
                def show_error():
                    self._confirming = False
                    if self.action_bar:
                        self.action_bar.set_loading(False)
                    else:
                        self.confirm_rates_btn.configure(state="normal", text="Confirm rates")
                    error_msg = f"Error confirming rates: {e}"
                    if hasattr(self.app, 'toast'):
                        self.app.toast.error(error_msg, duration=5000)
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

    # ================================================================
    # DATA MODE TOGGLE (TEST/PROD)
    # ================================================================
    def _create_mode_toggle_ctk(self, parent):
        """Create Dev/Prod toggle button using CustomTkinter."""
        from settings import get_settings
        settings = get_settings()
        dev_mode = settings.get("development_mode", False)

        # Container frame
        mode_frame = ctk.CTkFrame(parent, fg_color="transparent")
        mode_frame.pack(side="left", padx=(30, 0))

        # Mode indicator/button - cleaner design
        mode_text = "Dev" if dev_mode else "Prod"
        mode_color = THEME["warning"] if dev_mode else THEME["success"]  # Orange for Dev, Green for Prod

        self._mode_btn = ctk.CTkButton(
            mode_frame,
            text=mode_text,
            fg_color=mode_color,
            hover_color=THEME["bg_hover"],
            text_color="white",
            font=("Segoe UI Semibold", 12, "bold"),
            width=70,
            height=30,
            corner_radius=15,
            command=self._toggle_data_mode
        )
        self._mode_btn.pack(side="left")

    def _create_mode_toggle_tk(self, parent):
        """Create Dev/Prod toggle button using tkinter."""
        from settings import get_settings
        settings = get_settings()
        dev_mode = settings.get("development_mode", False)

        # Container frame
        mode_frame = tk.Frame(parent, bg=THEME["bg_panel"])
        mode_frame.pack(side="left", padx=(30, 0))

        # Mode indicator/button - cleaner pill design
        mode_text = "Dev" if dev_mode else "Prod"
        mode_color = THEME["warning"] if dev_mode else THEME["success"]  # Orange for Dev, Green for Prod

        self._mode_btn = tk.Label(
            mode_frame,
            text=f"  {mode_text}  ",
            fg="white",
            bg=mode_color,
            font=("Segoe UI Semibold", 11, "bold"),
            cursor="hand2",
            padx=15,
            pady=5
        )
        self._mode_btn.pack(side="left")
        self._mode_btn.bind("<Button-1>", lambda e: self._toggle_data_mode())
        self._mode_btn.bind("<Enter>", lambda e: self._mode_btn.config(bg=THEME["bg_hover"]))
        self._mode_btn.bind("<Leave>", lambda e: self._update_mode_button_color())

    def _toggle_data_mode(self):
        """Toggle between Dev and Prod mode and reload data."""
        from settings import get_settings
        settings = get_settings()

        # Get current mode and flip it
        current_mode = settings.get("development_mode", False)
        new_mode = not current_mode

        # Save new setting
        settings.set("development_mode", new_mode, save=True)

        # Update button appearance
        self._update_mode_button_color()

        # Show feedback
        mode_text = "Dev" if new_mode else "Prod"
        log.info(f"[Dashboard] Switched to {mode_text} mode")

        # Trigger data reload
        if hasattr(self.app, 'refresh_data'):
            self.app.refresh_data()

        # Show toast notification if available
        if hasattr(self.app, 'toast'):
            self.app.toast.show(f"Switched to {mode_text} mode - Reloading data...", "info")

    def _update_mode_button_color(self):
        """Update the mode button color based on current setting."""
        from settings import get_settings
        settings = get_settings()
        dev_mode = settings.get("development_mode", False)

        mode_text = "Dev" if dev_mode else "Prod"
        mode_color = THEME["warning"] if dev_mode else THEME["success"]  # Orange for Dev, Green for Prod

        if hasattr(self, '_mode_btn'):
            if CTK_AVAILABLE and isinstance(self._mode_btn, ctk.CTkButton):
                self._mode_btn.configure(text=mode_text, fg_color=mode_color)
            else:
                self._mode_btn.config(text=f"  {mode_text}  ", bg=mode_color)

    def _create_mode_badge(self, parent):
        """Create compact Dev/Prod pill badge in card header (Nordic Light style)."""
        from settings import get_settings
        settings = get_settings()
        dev_mode = settings.get("development_mode", False)

        # Pill badge colors
        mode_text = "Dev" if dev_mode else "Prod"
        mode_bg = THEME["warning"] if dev_mode else THEME["success"]

        # Create compact pill badge
        self._mode_btn = tk.Label(
            parent,
            text=mode_text,
            fg="white",
            bg=mode_bg,
            font=("Segoe UI Semibold", 9),
            padx=10,
            pady=2,
            cursor="hand2"
        )
        self._mode_btn.pack(side="left", padx=(12, 0))

        # Click to toggle
        self._mode_btn.bind("<Button-1>", lambda e: self._toggle_data_mode())
        self._mode_btn.bind("<Enter>", lambda e: self._mode_btn.config(bg=THEME["bg_hover"], fg=THEME["text"]))
        self._mode_btn.bind("<Leave>", lambda e: self._update_mode_button_color())

    def _show_trend_popup(self):
        """Show popup with NIBOR trend history chart."""
        if not TrendPopup:
            return

        # ÄNDRING: Vi hämtar inte data här längre, och skickar inte med det.
        # Popupen hämtar sin egen data (både fixing och contribution).

        popup = TrendPopup(self.winfo_toplevel())
        popup.grab_set()

    def _show_validation_popup(self, check_id):
        """Show popup with validation alerts for a specific check category."""
        if check_id not in self.validation_checks:
            return

        check = self.validation_checks[check_id]
        check_names = {
            "bloomberg": "Bloomberg Data",
            "excel_cells": "Excel Cells",
            "weights": "Weights",
            "days": "Days",
            "nibor_contrib": "Implied NOK",
            "spreads": "Spreads"
        }
        check_name = check_names.get(check_id, check_id)

        # Create popup
        popup = tk.Toplevel(self.winfo_toplevel())
        popup.title(f"Validation: {check_name}")
        popup.configure(bg=THEME["bg_panel"])

        # Size based on content type
        if check_id == "excel_cells":
            popup.geometry("700x500")
        else:
            popup.geometry("600x500")

        popup.resizable(True, True)
        popup.transient(self.winfo_toplevel())
        popup.grab_set()

        # Header with status
        header_frame = tk.Frame(popup, bg=THEME["bg_card"])
        header_frame.pack(fill="x")

        status = check.get("status")
        if status is True:
            status_icon = "✓"
            status_text = "ALL CHECKS PASSED"
            status_color = THEME["success"]
            header_bg = "#0d2818"
        elif status is False:
            status_icon = "✕"
            status_text = "VALIDATION FAILED"
            status_color = THEME["danger"]
            header_bg = "#2a1215"
        else:
            status_icon = "—"
            status_text = "PENDING"
            status_color = THEME["text_muted"]
            header_bg = THEME["chip"]

        header_frame.configure(bg=header_bg)

        tk.Label(header_frame,
                text=f"{status_icon}  {check_name}",
                font=("Segoe UI", 18),
                fg=status_color, bg=header_bg).pack(pady=(24, 6))

        tk.Label(header_frame,
                text=status_text,
                font=("Segoe UI", 12),
                fg=status_color, bg=header_bg).pack(pady=(0, 24))

        # Special handling for detailed tables
        if check_id == "nibor_contrib" and hasattr(self, '_excel_cells_details'):
            self._show_nibor_contrib_table(popup)
        elif check_id == "excel_cells" and hasattr(self, '_excel_cells_details'):
            self._show_excel_cells_table(popup)
        elif check_id == "bloomberg" and hasattr(self, '_excel_cells_details'):
            self._show_bloomberg_table(popup)
        elif check_id == "spreads" and hasattr(self, '_spreads_details'):
            self._show_spreads_table(popup)
        elif check_id == "days" and hasattr(self, '_days_details'):
            self._show_days_table(popup)
        else:
            # Standard alerts list for other checks
            alerts = check.get("alerts", [])

            if alerts:
                alerts_frame = tk.Frame(popup, bg=THEME["bg_panel"])
                alerts_frame.pack(fill="both", expand=True, padx=24, pady=12)

                tk.Label(alerts_frame,
                        text=f"Issues ({len(alerts)})",
                        font=("Segoe UI", 12),
                        fg=THEME["text"], bg=THEME["bg_panel"]).pack(anchor="w", pady=(0, 12))

                canvas = tk.Canvas(alerts_frame, bg=THEME["bg_panel"], highlightthickness=0)
                scrollbar = tk.Scrollbar(alerts_frame, orient="vertical", command=canvas.yview)
                scroll_frame = tk.Frame(canvas, bg=THEME["bg_panel"])

                scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
                canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
                canvas.configure(yscrollcommand=scrollbar.set)

                canvas.pack(side="left", fill="both", expand=True)
                scrollbar.pack(side="right", fill="y")

                for i, alert in enumerate(alerts):
                    row_bg = THEME["bg_card"] if i % 2 == 0 else THEME["row_odd"]
                    alert_card = tk.Frame(scroll_frame, bg=row_bg,
                                          highlightthickness=1, highlightbackground=THEME["border"])
                    alert_card.pack(fill="x", pady=3, padx=2)

                    # Status indicator
                    tk.Label(alert_card,
                            text="Fail",
                            font=("Segoe UI", 11),
                            fg=THEME["danger"], bg=row_bg,
                            anchor="w").pack(side="left", padx=(16, 12), pady=12)

                    # Alert message
                    tk.Label(alert_card,
                            text=alert,
                            font=("Segoe UI", 11),
                            fg=THEME["text"], bg=row_bg,
                            anchor="w", wraplength=450, justify="left").pack(side="left", padx=(0, 16), pady=12, anchor="w")
            else:
                success_frame = tk.Frame(popup, bg=THEME["bg_panel"])
                success_frame.pack(fill="both", expand=True, padx=24, pady=24)

                if status is True:
                    tk.Label(success_frame,
                            text="All validation checks passed",
                            font=("Segoe UI", 14),
                            fg=THEME["success"], bg=THEME["bg_panel"]).pack(expand=True)
                else:
                    tk.Label(success_frame,
                            text="No validation data yet",
                            font=("Segoe UI", 14),
                            fg=THEME["text_muted"], bg=THEME["bg_panel"]).pack(expand=True)

        # Close button
        btn_frame = tk.Frame(popup, bg=THEME["bg_panel"])
        btn_frame.pack(fill="x", padx=24, pady=20)

        close_btn = tk.Button(btn_frame,
                             text="Close",
                             font=("Segoe UI", 12),
                             fg="white", bg=THEME["accent"],
                             activebackground=THEME["accent_hover"],
                             activeforeground="white",
                             relief="flat", cursor="hand2",
                             padx=32, pady=10,
                             command=popup.destroy)
        close_btn.pack(side="right")

        popup.focus_set()

    def _show_nibor_contrib_table(self, popup):
        """Show Implied NOK validation (EUR Implied, USD Implied)."""
        content = tk.Frame(popup, bg=THEME["bg_panel"])
        content.pack(fill="both", expand=True, padx=24, pady=12)

        # Get implied NOK checks from excel_cells_details
        implied_nok_checks = []
        if hasattr(self, '_excel_cells_details'):
            implied_nok_checks = [c for c in self._excel_cells_details if c.get("check_type") == "implied_nok"]

        implied_failed = [c for c in implied_nok_checks if not c.get("matched")]
        implied_passed = [c for c in implied_nok_checks if c.get("matched")]

        # Theme-compatible colors for dark mode
        FAIL_HEADER_BG = "#2a1215"          # Dark red background
        FAIL_HEADER_FG = THEME["danger"]    # Bright red text
        FAIL_BORDER = THEME["border"]
        PASS_HEADER_BG = "#0d2818"          # Dark green background
        PASS_HEADER_FG = THEME["success"]   # Bright green text
        PASS_BORDER = THEME["border"]

        # Summary bar
        total_failed = len(implied_failed)
        total_passed = len(implied_passed)

        summary_frame = tk.Frame(content, bg=THEME["bg_card"], highlightthickness=1, highlightbackground=THEME["border"])
        summary_frame.pack(fill="x", pady=(0, 16))

        summary_inner = tk.Frame(summary_frame, bg=THEME["bg_card"])
        summary_inner.pack(fill="x", padx=16, pady=12)

        tk.Label(summary_inner,
                text=f"Total: {len(implied_nok_checks)} checks",
                font=("Segoe UI", 11),
                fg=THEME["text"], bg=THEME["bg_card"]).pack(side="left")

        if total_failed > 0:
            tk.Label(summary_inner,
                    text=f"{total_failed} failed",
                    font=("Segoe UI", 11),
                    fg=THEME["danger"], bg=THEME["bg_card"]).pack(side="left", padx=(20, 0))

        tk.Label(summary_inner,
                text=f"{total_passed} passed",
                font=("Segoe UI", 11),
                fg=THEME["success"], bg=THEME["bg_card"]).pack(side="left", padx=(20, 0))

        # Scrollable container
        canvas = tk.Canvas(content, bg=THEME["bg_panel"], highlightthickness=0)
        scrollbar = tk.Scrollbar(content, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=THEME["bg_panel"])

        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas_window = canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        def on_canvas_configure(e):
            canvas.itemconfig(canvas_window, width=e.width)
        canvas.bind("<Configure>", on_canvas_configure)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Mousewheel scrolling
        def on_mousewheel(e):
            canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", on_mousewheel)

        # Collapsible state - ALL collapsed by default
        self._implied_nok_expanded = {
            "implied_failed": False, "implied_passed": False
        }

        # Column widths for grid alignment
        COL_WIDTHS = [5, 4, 14, 8, 10, 2, 10, 9]

        # Helper to create table header
        def create_table_header(parent, columns):
            header_row = tk.Frame(parent, bg=THEME["table_header_bg"])
            header_row.pack(fill="x")
            for col, (text, width) in enumerate(zip(columns, COL_WIDTHS)):
                tk.Label(header_row, text=text, font=("Segoe UI", 9),
                        fg=THEME["text_muted"], bg=THEME["table_header_bg"],
                        width=width, anchor="center").pack(side="left", padx=2, pady=5)
            tk.Frame(parent, bg=THEME["border"], height=1).pack(fill="x")

        # Helper to create a check row
        def create_check_row(parent, check, row_idx):
            field = check.get("field", "")
            tenor = check.get("tenor", "")
            cell = check.get("cell", "")
            gui_val = check.get("gui_value")
            excel_val = check.get("excel_value")
            decimals = check.get("decimals", 4)
            matched = check.get("matched", False)

            row_bg = THEME["bg_card"] if row_idx % 2 == 0 else THEME["row_odd"]
            check_row = tk.Frame(parent, bg=row_bg)
            check_row.pack(fill="x")

            # Status
            status_text = "OK" if matched else "Fail"
            status_color = THEME["success"] if matched else THEME["danger"]
            tk.Label(check_row, text=status_text, font=("Segoe UI", 9),
                    fg=status_color, bg=row_bg, width=COL_WIDTHS[0], anchor="center").pack(side="left", padx=2, pady=3)

            # Tenor
            tk.Label(check_row, text=tenor, font=("Segoe UI", 9),
                    fg=THEME["text"], bg=row_bg, width=COL_WIDTHS[1], anchor="center").pack(side="left", padx=2, pady=3)

            # Field name
            tk.Label(check_row, text=field, font=("Segoe UI", 9),
                    fg=THEME["text"], bg=row_bg, width=COL_WIDTHS[2], anchor="w").pack(side="left", padx=2, pady=3)

            # Cell reference
            tk.Label(check_row, text=cell, font=("Consolas", 9),
                    fg=THEME["text_muted"], bg=row_bg, width=COL_WIDTHS[3], anchor="center").pack(side="left", padx=2, pady=3)

            # GUI value
            val1_str = f"{gui_val:.{decimals}f}" if gui_val is not None else "—"
            tk.Label(check_row, text=val1_str, font=("Consolas", 9),
                    fg=THEME["text"], bg=row_bg, width=COL_WIDTHS[4], anchor="center").pack(side="left", padx=2, pady=3)

            # Comparison indicator
            cmp_text = "=" if matched else "!="
            cmp_color = THEME["success"] if matched else THEME["danger"]
            tk.Label(check_row, text=cmp_text, font=("Consolas", 9),
                    fg=cmp_color, bg=row_bg, width=COL_WIDTHS[5], anchor="center").pack(side="left", padx=2, pady=3)

            # Excel value
            val2_str = f"{excel_val:.{decimals}f}" if excel_val is not None else "—"
            tk.Label(check_row, text=val2_str, font=("Consolas", 9),
                    fg=THEME["text"], bg=row_bg, width=COL_WIDTHS[6], anchor="center").pack(side="left", padx=2, pady=3)

            # Difference
            diff_str = ""
            if not matched and gui_val is not None and excel_val is not None:
                try:
                    diff = float(gui_val) - float(excel_val)
                    diff_str = f"{diff:+.{decimals}f}"
                except (ValueError, TypeError):
                    pass
            tk.Label(check_row, text=diff_str, font=("Consolas", 9),
                    fg=THEME["danger"], bg=row_bg, width=COL_WIDTHS[7], anchor="center").pack(side="left", padx=2, pady=3)

        # Helper to create collapsible section
        def create_section(parent, title, items, section_key, header_bg, header_fg, border_color,
                          columns, initially_expanded=False):
            if not items:
                return

            section = tk.Frame(parent, bg=THEME["bg_panel"])
            section.pack(fill="x", pady=(0, 6))

            # Header
            header = tk.Frame(section, bg=header_bg, cursor="hand2", highlightthickness=1, highlightbackground=border_color)
            header.pack(fill="x")

            expand_lbl = tk.Label(header, text="▼" if initially_expanded else "▶",
                                 font=("Segoe UI", 9), fg=header_fg, bg=header_bg)
            expand_lbl.pack(side="left", padx=(12, 4), pady=6)

            tk.Label(header, text=title, font=("Segoe UI", 10),
                    fg=header_fg, bg=header_bg).pack(side="left", pady=6)

            count_text = f"({len(items)})"
            tk.Label(header, text=count_text, font=("Segoe UI", 9),
                    fg=THEME["text_muted"], bg=header_bg).pack(side="right", padx=12, pady=6)

            # Container
            container = tk.Frame(section, bg=THEME["bg_card"],
                                highlightthickness=1, highlightbackground=border_color)

            # Table header
            create_table_header(container, columns)

            # Rows
            sorted_items = sorted(items, key=lambda x: (x.get("tenor", ""), x.get("field", "")))
            for i, item in enumerate(sorted_items):
                create_check_row(container, item, i)

            if initially_expanded:
                container.pack(fill="x")

            self._implied_nok_expanded[section_key] = initially_expanded

            # Toggle function
            def toggle(e=None):
                self._implied_nok_expanded[section_key] = not self._implied_nok_expanded[section_key]
                if self._implied_nok_expanded[section_key]:
                    container.pack(fill="x")
                    expand_lbl.config(text="▼")
                else:
                    container.pack_forget()
                    expand_lbl.config(text="▶")

            header.bind("<Button-1>", toggle)
            for child in header.winfo_children():
                child.bind("<Button-1>", toggle)

        # Column definitions
        implied_columns = ["Status", "Tenor", "Field", "Cell", "GUI", "", "Excel", "Diff"]

        # ═══════════════════════════════════════════════════════════════
        # Implied NOK (EUR Implied, USD Implied)
        # ═══════════════════════════════════════════════════════════════
        if implied_nok_checks:
            tk.Label(scroll_frame, text="Implied NOK",
                    font=("Segoe UI", 11),
                    fg=THEME["text"], bg=THEME["bg_panel"]).pack(anchor="w", pady=(0, 2))
            tk.Label(scroll_frame, text="GUI calculated implied rates vs Excel implied rates",
                    font=("Segoe UI", 9), fg=THEME["text_muted"],
                    bg=THEME["bg_panel"]).pack(anchor="w", pady=(0, 6))

            if implied_failed:
                create_section(scroll_frame, "Failed", implied_failed, "implied_failed",
                              FAIL_HEADER_BG, FAIL_HEADER_FG, FAIL_BORDER,
                              implied_columns, initially_expanded=False)
            if implied_passed:
                create_section(scroll_frame, "Passed", implied_passed, "implied_passed",
                              PASS_HEADER_BG, PASS_HEADER_FG, PASS_BORDER,
                              implied_columns, initially_expanded=False)
        else:
            tk.Label(scroll_frame,
                    text="All Implied NOK checks passed",
                    font=("Segoe UI", 11),
                    fg=THEME["success"], bg=THEME["bg_panel"]).pack(pady=20)

    def _show_excel_cells_table(self, popup):
        """Show professional Excel Cells validation with Cell Checks and Internal Rates vs ECP sections."""
        content = tk.Frame(popup, bg=THEME["bg_panel"])
        content.pack(fill="both", expand=True, padx=24, pady=12)

        if not hasattr(self, '_excel_cells_details') or not self._excel_cells_details:
            tk.Label(content,
                    text="No Excel cell data available",
                    font=("Segoe UI", 12),
                    fg=THEME["text_muted"], bg=THEME["bg_panel"]).pack(pady=30)
            return

        # Separate checks by category (Excel Cells shows Nore vs Swedbank and Internal vs ECP only)
        # Cell Checks (GUI vs Excel) are shown under Bloomberg validation
        ecp_checks = [c for c in self._excel_cells_details if c.get("check_type") == "internal_vs_ecp"]
        nore_checks = [c for c in self._excel_cells_details if c.get("check_type") == "nore_vs_swedbank"]

        ecp_failed = [c for c in ecp_checks if not c.get("matched")]
        ecp_passed = [c for c in ecp_checks if c.get("matched")]
        nore_failed = [c for c in nore_checks if not c.get("matched")]
        nore_passed = [c for c in nore_checks if c.get("matched")]

        # Theme-compatible colors for dark mode
        FAIL_HEADER_BG = "#2a1215"          # Dark red background
        FAIL_HEADER_FG = THEME["danger"]    # Bright red text
        FAIL_BORDER = THEME["border"]
        PASS_HEADER_BG = "#0d2818"          # Dark green background
        PASS_HEADER_FG = THEME["success"]   # Bright green text
        PASS_BORDER = THEME["border"]

        # Summary bar
        summary_frame = tk.Frame(content, bg=THEME["bg_card"], highlightthickness=1, highlightbackground=THEME["border"])
        summary_frame.pack(fill="x", pady=(0, 16))

        summary_inner = tk.Frame(summary_frame, bg=THEME["bg_card"])
        summary_inner.pack(fill="x", padx=16, pady=12)

        total_checks = len(ecp_checks) + len(nore_checks)
        total_failed = len(ecp_failed) + len(nore_failed)
        total_passed = len(ecp_passed) + len(nore_passed)

        tk.Label(summary_inner,
                text=f"Total: {total_checks} checks",
                font=("Segoe UI", 11),
                fg=THEME["text"], bg=THEME["bg_card"]).pack(side="left")

        if total_failed > 0:
            tk.Label(summary_inner,
                    text=f"{total_failed} failed",
                    font=("Segoe UI", 11),
                    fg=THEME["danger"], bg=THEME["bg_card"]).pack(side="left", padx=(20, 0))

        tk.Label(summary_inner,
                text=f"{total_passed} passed",
                font=("Segoe UI", 11),
                fg=THEME["success"], bg=THEME["bg_card"]).pack(side="left", padx=(20, 0))

        # Scrollable container
        canvas = tk.Canvas(content, bg=THEME["bg_panel"], highlightthickness=0)
        scrollbar = tk.Scrollbar(content, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=THEME["bg_panel"])

        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas_window = canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        def on_canvas_configure(e):
            canvas.itemconfig(canvas_window, width=e.width)
        canvas.bind("<Configure>", on_canvas_configure)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Mousewheel scrolling
        def on_mousewheel(e):
            canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", on_mousewheel)

        # Collapsible state - ALL collapsed by default
        self._excel_cells_expanded = {
            "ecp_failed": False, "ecp_passed": False,
            "nore_failed": False, "nore_passed": False
        }

        # Column widths for grid alignment (compact)
        COL_WIDTHS = [5, 4, 14, 8, 10, 2, 10, 9]

        # Helper to create table header with grid
        def create_table_header(parent, columns):
            header_row = tk.Frame(parent, bg=THEME["table_header_bg"])
            header_row.pack(fill="x")
            for col, (text, width) in enumerate(zip(columns, COL_WIDTHS)):
                tk.Label(header_row, text=text, font=("Segoe UI", 9),
                        fg=THEME["text_muted"], bg=THEME["table_header_bg"],
                        width=width, anchor="center").pack(side="left", padx=2, pady=5)
            tk.Frame(parent, bg=THEME["border"], height=1).pack(fill="x")

        # Helper to create a check row with grid alignment
        def create_check_row(parent, check, row_idx, show_diff=True):
            field = check.get("field", "")
            tenor = check.get("tenor", "")
            cell = check.get("cell", "")
            gui_val = check.get("gui_value")
            excel_val = check.get("excel_value")
            ref_val = check.get("ref_value")
            decimals = check.get("decimals", 4)
            matched = check.get("matched", False)

            row_bg = THEME["bg_card"] if row_idx % 2 == 0 else THEME["row_odd"]
            check_row = tk.Frame(parent, bg=row_bg)
            check_row.pack(fill="x")

            # Status
            status_text = "OK" if matched else "Fail"
            status_color = THEME["success"] if matched else THEME["danger"]
            tk.Label(check_row, text=status_text, font=("Segoe UI", 9),
                    fg=status_color, bg=row_bg, width=COL_WIDTHS[0], anchor="center").pack(side="left", padx=2, pady=3)

            # Tenor
            tk.Label(check_row, text=tenor, font=("Segoe UI", 9),
                    fg=THEME["text"], bg=row_bg, width=COL_WIDTHS[1], anchor="center").pack(side="left", padx=2, pady=3)

            # Field name
            tk.Label(check_row, text=field, font=("Segoe UI", 9),
                    fg=THEME["text"], bg=row_bg, width=COL_WIDTHS[2], anchor="w").pack(side="left", padx=2, pady=3)

            # Cell reference
            tk.Label(check_row, text=cell, font=("Consolas", 9),
                    fg=THEME["text_muted"], bg=row_bg, width=COL_WIDTHS[3], anchor="center").pack(side="left", padx=2, pady=3)

            # Value 1 (GUI or Internal Rate)
            val1 = gui_val if gui_val is not None else ref_val
            val1_str = f"{val1:.{decimals}f}" if val1 is not None else "—"
            tk.Label(check_row, text=val1_str, font=("Consolas", 9),
                    fg=THEME["text"], bg=row_bg, width=COL_WIDTHS[4], anchor="center").pack(side="left", padx=2, pady=3)

            # Comparison indicator
            if check.get("check_type") == "internal_vs_ecp":
                cmp_text = ">=" if matched else "<"
            else:
                cmp_text = "=" if matched else "!="
            cmp_color = THEME["success"] if matched else THEME["danger"]
            tk.Label(check_row, text=cmp_text, font=("Consolas", 9),
                    fg=cmp_color, bg=row_bg, width=COL_WIDTHS[5], anchor="center").pack(side="left", padx=2, pady=3)

            # Value 2 (Excel or ECP Rate)
            val2 = excel_val
            val2_str = f"{val2:.{decimals}f}" if val2 is not None else "—"
            tk.Label(check_row, text=val2_str, font=("Consolas", 9),
                    fg=THEME["text"], bg=row_bg, width=COL_WIDTHS[6], anchor="center").pack(side="left", padx=2, pady=3)

            # Difference (only for failures with numeric values)
            diff_str = ""
            if show_diff and not matched and val1 is not None and val2 is not None:
                try:
                    diff = float(val1) - float(val2)
                    diff_str = f"{diff:+.{decimals}f}"
                except (ValueError, TypeError):
                    pass
            tk.Label(check_row, text=diff_str, font=("Consolas", 9),
                    fg=THEME["danger"], bg=row_bg, width=COL_WIDTHS[7], anchor="center").pack(side="left", padx=2, pady=3)

        # Helper to create collapsible section
        def create_section(parent, title, items, section_key, header_bg, header_fg, border_color,
                          columns, initially_expanded=False):
            if not items:
                return

            section = tk.Frame(parent, bg=THEME["bg_panel"])
            section.pack(fill="x", pady=(0, 6))

            # Header (compact)
            header = tk.Frame(section, bg=header_bg, cursor="hand2", highlightthickness=1, highlightbackground=border_color)
            header.pack(fill="x")

            expand_lbl = tk.Label(header, text="▼" if initially_expanded else "▶",
                                 font=("Segoe UI", 9), fg=header_fg, bg=header_bg)
            expand_lbl.pack(side="left", padx=(12, 4), pady=6)

            tk.Label(header, text=title, font=("Segoe UI", 10),
                    fg=header_fg, bg=header_bg).pack(side="left", pady=6)

            count_text = f"({len(items)})"
            tk.Label(header, text=count_text, font=("Segoe UI", 9),
                    fg=THEME["text_muted"], bg=header_bg).pack(side="right", padx=12, pady=6)

            # Container
            container = tk.Frame(section, bg=THEME["bg_card"],
                                highlightthickness=1, highlightbackground=border_color)

            # Table header
            create_table_header(container, columns)

            # Sort by tenor then field
            sorted_items = sorted(items, key=lambda x: (x.get("tenor", ""), x.get("field", "")))
            for i, check in enumerate(sorted_items):
                create_check_row(container, check, i)

            if initially_expanded:
                container.pack(fill="x")

            self._excel_cells_expanded[section_key] = initially_expanded

            # Toggle function
            def toggle(e=None):
                self._excel_cells_expanded[section_key] = not self._excel_cells_expanded[section_key]
                if self._excel_cells_expanded[section_key]:
                    container.pack(fill="x")
                    expand_lbl.config(text="▼")
                else:
                    container.pack_forget()
                    expand_lbl.config(text="▶")

            header.bind("<Button-1>", toggle)
            for child in header.winfo_children():
                child.bind("<Button-1>", toggle)

        # Column definitions
        ecp_columns = ["Status", "Tenor", "Field", "Cell", "Internal", "", "ECP Rate", "Diff"]
        nore_columns = ["Status", "Tenor", "Field", "Cells", "Nore", "", "Swedbank", "Diff"]

        # ═══════════════════════════════════════════════════════════════
        # DISPLAY ORDER: Nore vs Swedbank first, then Internal vs ECP
        # Cell Checks (GUI vs Excel) are shown under Bloomberg validation
        # ═══════════════════════════════════════════════════════════════

        section_shown = False

        # ═══════════════════════════════════════════════════════════════
        # SECTION 1: Nore Nibor Calculation Model vs Swedbank Estimated Spread
        # ═══════════════════════════════════════════════════════════════
        if nore_checks:
            tk.Label(scroll_frame, text="Nore vs Swedbank Calculation Model",
                    font=("Segoe UI", 11),
                    fg=THEME["text"], bg=THEME["bg_panel"]).pack(anchor="w", pady=(0, 2))
            tk.Label(scroll_frame, text="Bloomberg row 6-10 vs calculated row 29-33",
                    font=("Segoe UI", 9), fg=THEME["text_muted"],
                    bg=THEME["bg_panel"]).pack(anchor="w", pady=(0, 6))

            if nore_failed:
                create_section(scroll_frame, "Failed", nore_failed, "nore_failed",
                              FAIL_HEADER_BG, FAIL_HEADER_FG, FAIL_BORDER,
                              nore_columns, initially_expanded=False)
            if nore_passed:
                create_section(scroll_frame, "Passed", nore_passed, "nore_passed",
                              PASS_HEADER_BG, PASS_HEADER_FG, PASS_BORDER,
                              nore_columns, initially_expanded=False)
            section_shown = True

        # ═══════════════════════════════════════════════════════════════
        # SECTION 2: Internal Rates vs ECP
        # ═══════════════════════════════════════════════════════════════
        if ecp_checks:
            if section_shown:
                tk.Frame(scroll_frame, bg=THEME["border"], height=1).pack(fill="x", pady=(4, 10))

            tk.Label(scroll_frame, text="Internal Rates vs ECP", font=("Segoe UI", 11),
                    fg=THEME["text"], bg=THEME["bg_panel"]).pack(anchor="w", pady=(0, 2))
            tk.Label(scroll_frame, text="Internal rates must be >= ECP rates",
                    font=("Segoe UI", 9), fg=THEME["text_muted"],
                    bg=THEME["bg_panel"]).pack(anchor="w", pady=(0, 6))

            if ecp_failed:
                create_section(scroll_frame, "Failed", ecp_failed, "ecp_failed",
                              FAIL_HEADER_BG, FAIL_HEADER_FG, FAIL_BORDER,
                              ecp_columns, initially_expanded=False)
            if ecp_passed:
                create_section(scroll_frame, "Passed", ecp_passed, "ecp_passed",
                              PASS_HEADER_BG, PASS_HEADER_FG, PASS_BORDER,
                              ecp_columns, initially_expanded=False)
            section_shown = True

        # Unbind mousewheel on popup close
        def on_popup_destroy(e):
            try:
                canvas.unbind_all("<MouseWheel>")
            except Exception:
                pass
        popup.bind("<Destroy>", on_popup_destroy)

    def _show_bloomberg_table(self, popup):
        """Show Bloomberg Data Check (GUI vs Excel) under Bloomberg validation."""
        content = tk.Frame(popup, bg=THEME["bg_panel"])
        content.pack(fill="both", expand=True, padx=24, pady=12)

        if not hasattr(self, '_excel_cells_details') or not self._excel_cells_details:
            tk.Label(content,
                    text="No cell check data available",
                    font=("Segoe UI", 12),
                    fg=THEME["text_muted"], bg=THEME["bg_panel"]).pack(pady=30)
            return

        # Get only cell_check type (GUI vs Excel)
        cell_checks = [c for c in self._excel_cells_details if c.get("check_type") == "cell_check"]

        if not cell_checks:
            tk.Label(content,
                    text="No cell check data available",
                    font=("Segoe UI", 12),
                    fg=THEME["text_muted"], bg=THEME["bg_panel"]).pack(pady=30)
            return

        cell_failed = [c for c in cell_checks if not c.get("matched")]
        cell_passed = [c for c in cell_checks if c.get("matched")]

        # Theme-compatible colors for dark mode
        FAIL_HEADER_BG = "#2a1215"          # Dark red background
        FAIL_HEADER_FG = THEME["danger"]    # Bright red text
        FAIL_BORDER = THEME["border"]
        PASS_HEADER_BG = "#0d2818"          # Dark green background
        PASS_HEADER_FG = THEME["success"]   # Bright green text
        PASS_BORDER = THEME["border"]

        # Summary bar
        summary_frame = tk.Frame(content, bg=THEME["bg_card"], highlightthickness=1, highlightbackground=THEME["border"])
        summary_frame.pack(fill="x", pady=(0, 12))

        summary_inner = tk.Frame(summary_frame, bg=THEME["bg_card"])
        summary_inner.pack(fill="x", padx=16, pady=10)

        tk.Label(summary_inner,
                text=f"Total: {len(cell_checks)} checks",
                font=("Segoe UI", 10),
                fg=THEME["text"], bg=THEME["bg_card"]).pack(side="left")

        if cell_failed:
            tk.Label(summary_inner,
                    text=f"{len(cell_failed)} failed",
                    font=("Segoe UI", 10),
                    fg=THEME["danger"], bg=THEME["bg_card"]).pack(side="left", padx=(16, 0))

        tk.Label(summary_inner,
                text=f"{len(cell_passed)} passed",
                font=("Segoe UI", 10),
                fg=THEME["success"], bg=THEME["bg_card"]).pack(side="left", padx=(16, 0))

        # Scrollable container
        canvas = tk.Canvas(content, bg=THEME["bg_panel"], highlightthickness=0)
        scrollbar = tk.Scrollbar(content, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=THEME["bg_panel"])

        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas_window = canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        def on_canvas_configure(e):
            canvas.itemconfig(canvas_window, width=e.width)
        canvas.bind("<Configure>", on_canvas_configure)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        def on_mousewheel(e):
            canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", on_mousewheel)

        # Collapsible state
        self._bloomberg_expanded = {"failed": False, "passed": False}

        COL_WIDTHS = [5, 4, 14, 6, 10, 2, 10, 9]
        cell_columns = ["Status", "Tenor", "Field", "Cell", "GUI", "", "Excel", "Diff"]

        def create_table_header(parent):
            header_row = tk.Frame(parent, bg=THEME["table_header_bg"])
            header_row.pack(fill="x")
            for text, width in zip(cell_columns, COL_WIDTHS):
                tk.Label(header_row, text=text, font=("Segoe UI", 9),
                        fg=THEME["text_muted"], bg=THEME["table_header_bg"],
                        width=width, anchor="center").pack(side="left", padx=2, pady=5)
            tk.Frame(parent, bg=THEME["border"], height=1).pack(fill="x")

        def create_check_row(parent, check, row_idx):
            field = check.get("field", "")
            tenor = check.get("tenor", "")
            cell = check.get("cell", "")
            gui_val = check.get("gui_value")
            excel_val = check.get("excel_value")
            decimals = check.get("decimals", 4)
            matched = check.get("matched", False)

            row_bg = THEME["bg_card"] if row_idx % 2 == 0 else THEME["row_odd"]
            check_row = tk.Frame(parent, bg=row_bg)
            check_row.pack(fill="x")

            status_text = "OK" if matched else "Fail"
            status_color = THEME["success"] if matched else THEME["danger"]
            tk.Label(check_row, text=status_text, font=("Segoe UI", 9),
                    fg=status_color, bg=row_bg, width=COL_WIDTHS[0], anchor="center").pack(side="left", padx=2, pady=3)

            tk.Label(check_row, text=tenor, font=("Segoe UI", 9),
                    fg=THEME["text"], bg=row_bg, width=COL_WIDTHS[1], anchor="center").pack(side="left", padx=2, pady=3)

            tk.Label(check_row, text=field, font=("Segoe UI", 9),
                    fg=THEME["text"], bg=row_bg, width=COL_WIDTHS[2], anchor="w").pack(side="left", padx=2, pady=3)

            tk.Label(check_row, text=cell, font=("Consolas", 9),
                    fg=THEME["text_muted"], bg=row_bg, width=COL_WIDTHS[3], anchor="center").pack(side="left", padx=2, pady=3)

            gui_str = f"{gui_val:.{decimals}f}" if gui_val is not None else "—"
            tk.Label(check_row, text=gui_str, font=("Consolas", 9),
                    fg=THEME["text"], bg=row_bg, width=COL_WIDTHS[4], anchor="center").pack(side="left", padx=2, pady=3)

            cmp_text = "=" if matched else "!="
            cmp_color = THEME["success"] if matched else THEME["danger"]
            tk.Label(check_row, text=cmp_text, font=("Consolas", 9),
                    fg=cmp_color, bg=row_bg, width=COL_WIDTHS[5], anchor="center").pack(side="left", padx=2, pady=3)

            excel_str = f"{excel_val:.{decimals}f}" if excel_val is not None else "—"
            tk.Label(check_row, text=excel_str, font=("Consolas", 9),
                    fg=THEME["text"], bg=row_bg, width=COL_WIDTHS[6], anchor="center").pack(side="left", padx=2, pady=3)

            diff_str = ""
            if not matched and gui_val is not None and excel_val is not None:
                try:
                    diff = float(gui_val) - float(excel_val)
                    diff_str = f"{diff:+.{decimals}f}"
                except (ValueError, TypeError):
                    pass
            tk.Label(check_row, text=diff_str, font=("Consolas", 9),
                    fg=THEME["danger"], bg=row_bg, width=COL_WIDTHS[7], anchor="center").pack(side="left", padx=2, pady=3)

        def create_section(parent, title, items, section_key, header_bg, header_fg, border_color):
            if not items:
                return

            section = tk.Frame(parent, bg=THEME["bg_panel"])
            section.pack(fill="x", pady=(0, 6))

            header = tk.Frame(section, bg=header_bg, cursor="hand2", highlightthickness=1, highlightbackground=border_color)
            header.pack(fill="x")

            expand_lbl = tk.Label(header, text="▶", font=("Segoe UI", 9), fg=header_fg, bg=header_bg)
            expand_lbl.pack(side="left", padx=(12, 4), pady=6)

            tk.Label(header, text=title, font=("Segoe UI", 10), fg=header_fg, bg=header_bg).pack(side="left", pady=6)

            tk.Label(header, text=f"({len(items)})", font=("Segoe UI", 9),
                    fg=THEME["text_muted"], bg=header_bg).pack(side="right", padx=12, pady=6)

            container = tk.Frame(section, bg=THEME["bg_card"], highlightthickness=1, highlightbackground=border_color)
            create_table_header(container)

            sorted_items = sorted(items, key=lambda x: (x.get("tenor", ""), x.get("field", "")))
            for i, check in enumerate(sorted_items):
                create_check_row(container, check, i)

            self._bloomberg_expanded[section_key] = False

            def toggle(e=None):
                self._bloomberg_expanded[section_key] = not self._bloomberg_expanded[section_key]
                if self._bloomberg_expanded[section_key]:
                    container.pack(fill="x")
                    expand_lbl.config(text="▼")
                else:
                    container.pack_forget()
                    expand_lbl.config(text="▶")

            header.bind("<Button-1>", toggle)
            for child in header.winfo_children():
                child.bind("<Button-1>", toggle)

        # Section title
        tk.Label(scroll_frame, text="Bloomberg Data Check", font=("Segoe UI", 11),
                fg=THEME["text"], bg=THEME["bg_panel"]).pack(anchor="w", pady=(0, 2))
        tk.Label(scroll_frame, text="GUI calculated values vs Excel values",
                font=("Segoe UI", 9), fg=THEME["text_muted"],
                bg=THEME["bg_panel"]).pack(anchor="w", pady=(0, 6))

        if cell_failed:
            create_section(scroll_frame, "Failed", cell_failed, "failed",
                          FAIL_HEADER_BG, FAIL_HEADER_FG, FAIL_BORDER)
        if cell_passed:
            create_section(scroll_frame, "Passed", cell_passed, "passed",
                          PASS_HEADER_BG, PASS_HEADER_FG, PASS_BORDER)

        def on_popup_destroy(e):
            try:
                canvas.unbind_all("<MouseWheel>")
            except Exception:
                pass
        popup.bind("<Destroy>", on_popup_destroy)

    def _show_spreads_table(self, popup):
        """Show Spreads validation - check if spreads are within allowed intervals."""
        content = tk.Frame(popup, bg=THEME["bg_panel"])
        content.pack(fill="both", expand=True, padx=24, pady=12)

        if not hasattr(self, '_spreads_details') or not self._spreads_details:
            tk.Label(content,
                    text="No spread data available",
                    font=("Segoe UI", 12),
                    fg=THEME["text_muted"], bg=THEME["bg_panel"]).pack(pady=30)
            return

        spreads_failed = [s for s in self._spreads_details if not s.get("matched")]
        spreads_passed = [s for s in self._spreads_details if s.get("matched")]

        # Check if all passed
        all_passed = len(spreads_failed) == 0 and len(spreads_passed) > 0

        if all_passed:
            # Show simple success message - no details
            success_frame = tk.Frame(content, bg=THEME["bg_card"], highlightthickness=1, highlightbackground=THEME["border"])
            success_frame.pack(pady=(0, 16))

            inner = tk.Frame(success_frame, bg=THEME["bg_card"])
            inner.pack(padx=20, pady=20)

            tk.Label(inner,
                    text="✓  All spreads are within the allowed interval",
                    font=("Segoe UI", 12),
                    fg=THEME["success"], bg=THEME["bg_card"]).pack()

            # Centered table with interval info
            table_frame = tk.Frame(content, bg=THEME["bg_panel"])
            table_frame.pack(pady=(10, 0))

            # Table
            table = tk.Frame(table_frame, bg=THEME["bg_card"], highlightthickness=1, highlightbackground=THEME["border"])
            table.pack()

            # Header row
            header = tk.Frame(table, bg=THEME["table_header_bg"])
            header.pack(fill="x")

            tk.Label(header, text="Spread Swedbank model", font=("Segoe UI", 9),
                    fg=THEME["text_muted"], bg=THEME["table_header_bg"],
                    width=22, anchor="w").pack(side="left", padx=8, pady=6)
            tk.Label(header, text="Min Max", font=("Segoe UI", 9),
                    fg=THEME["text_muted"], bg=THEME["table_header_bg"],
                    width=12, anchor="center").pack(side="left", padx=8, pady=6)

            tk.Frame(table, bg=THEME["border"], height=1).pack(fill="x")

            # Row 1: 1W
            row1 = tk.Frame(table, bg=THEME["bg_card"])
            row1.pack(fill="x")
            tk.Label(row1, text="1W", font=("Segoe UI", 10),
                    fg=THEME["text"], bg=THEME["bg_card"],
                    width=8, anchor="w").pack(side="left", padx=8, pady=6)
            tk.Label(row1, text="15bp +/- 5bp", font=("Segoe UI", 9),
                    fg=THEME["text_muted"], bg=THEME["bg_card"],
                    width=14, anchor="w").pack(side="left", pady=6)
            tk.Label(row1, text="0,10 - 0,20", font=("Consolas", 10),
                    fg=THEME["text"], bg=THEME["bg_card"],
                    width=12, anchor="center").pack(side="left", padx=8, pady=6)

            # Row 2: 1-6 month
            row2 = tk.Frame(table, bg=THEME["row_odd"])
            row2.pack(fill="x")
            tk.Label(row2, text="1-6 month", font=("Segoe UI", 10),
                    fg=THEME["text"], bg=THEME["row_odd"],
                    width=8, anchor="w").pack(side="left", padx=8, pady=6)
            tk.Label(row2, text="20bp +/- 5bp", font=("Segoe UI", 9),
                    fg=THEME["text_muted"], bg=THEME["row_odd"],
                    width=14, anchor="w").pack(side="left", pady=6)
            tk.Label(row2, text="0,15 - 0,25", font=("Consolas", 10),
                    fg=THEME["text"], bg=THEME["row_odd"],
                    width=12, anchor="center").pack(side="left", padx=8, pady=6)
        else:
            # Show failed spreads with details
            FAIL_HEADER_BG = "#2a1215"          # Dark red background
            FAIL_HEADER_FG = THEME["danger"]    # Bright red text

            tk.Label(content,
                    text="Spreads Outside Allowed Interval",
                    font=("Segoe UI", 11),
                    fg=THEME["text"], bg=THEME["bg_panel"]).pack(anchor="w", pady=(0, 8))

            # Table for failed spreads
            table = tk.Frame(content, bg=THEME["bg_card"], highlightthickness=1, highlightbackground=THEME["border"])
            table.pack(fill="x")

            # Header
            header = tk.Frame(table, bg=FAIL_HEADER_BG)
            header.pack(fill="x")

            headers = [("Tenor", 8), ("Cell", 6), ("Value", 10), ("Interval", 14), ("Status", 8)]
            for text, width in headers:
                tk.Label(header, text=text, font=("Segoe UI", 9),
                        fg=THEME["text_muted"], bg=FAIL_HEADER_BG,
                        width=width, anchor="center").pack(side="left", padx=2, pady=6)

            tk.Frame(table, bg=THEME["border"], height=1).pack(fill="x")

            # Rows for failed spreads
            for i, spread in enumerate(spreads_failed):
                row_bg = THEME["bg_card"] if i % 2 == 0 else THEME["row_odd"]
                row = tk.Frame(table, bg=row_bg)
                row.pack(fill="x")

                tenor = spread.get("tenor", "")
                cell = spread.get("cell", "")
                value = spread.get("value")
                min_val = spread.get("min", 0)
                max_val = spread.get("max", 0)

                value_str = f"{value:.4f}" if value is not None else "—"
                interval_str = f"{min_val:.2f} - {max_val:.2f}"

                tk.Label(row, text=tenor, font=("Segoe UI", 9),
                        fg=THEME["text"], bg=row_bg, width=8, anchor="center").pack(side="left", padx=2, pady=4)
                tk.Label(row, text=cell, font=("Consolas", 9),
                        fg=THEME["text_muted"], bg=row_bg, width=6, anchor="center").pack(side="left", padx=2, pady=4)
                tk.Label(row, text=value_str, font=("Consolas", 9),
                        fg=FAIL_HEADER_FG, bg=row_bg, width=10, anchor="center").pack(side="left", padx=2, pady=4)
                tk.Label(row, text=interval_str, font=("Consolas", 9),
                        fg=THEME["text"], bg=row_bg, width=14, anchor="center").pack(side="left", padx=2, pady=4)
                tk.Label(row, text="Fail", font=("Segoe UI", 9),
                        fg=FAIL_HEADER_FG, bg=row_bg, width=8, anchor="center").pack(side="left", padx=2, pady=4)

    def _show_days_table(self, popup):
        """Show Days validation - check C7-C10 against Nibor Days file."""
        content = tk.Frame(popup, bg=THEME["bg_panel"])
        content.pack(fill="both", expand=True, padx=24, pady=12)

        if not hasattr(self, '_days_details') or not self._days_details:
            tk.Label(content,
                    text="No days data available",
                    font=("Segoe UI", 12),
                    fg=THEME["text_muted"], bg=THEME["bg_panel"]).pack(pady=30)
            return

        days_failed = [d for d in self._days_details if not d.get("matched")]
        days_passed = [d for d in self._days_details if d.get("matched")]

        # Check if all passed
        all_passed = len(days_failed) == 0 and len(days_passed) > 0

        if all_passed:
            # Show simple success message - no table needed
            from datetime import datetime
            today_str = datetime.now().strftime("%Y-%m-%d")

            success_frame = tk.Frame(content, bg=THEME["bg_card"], highlightthickness=1, highlightbackground=THEME["border"])
            success_frame.pack(pady=(0, 16))

            inner = tk.Frame(success_frame, bg=THEME["bg_card"])
            inner.pack(padx=30, pady=25)

            tk.Label(inner,
                    text="✓  All tenor days match the Nibor Days file",
                    font=("Segoe UI", 12),
                    fg=THEME["success"], bg=THEME["bg_card"]).pack()

            tk.Label(inner,
                    text=f"Validated for {today_str}",
                    font=("Segoe UI", 10),
                    fg=THEME["text_muted"], bg=THEME["bg_card"]).pack(pady=(8, 0))
        else:
            # Show failed days
            FAIL_HEADER_BG = "#2a1215"          # Dark red background
            FAIL_HEADER_FG = THEME["danger"]    # Bright red text

            from datetime import datetime
            today_str = datetime.now().strftime("%Y-%m-%d")

            tk.Label(content,
                    text=f"Days Mismatch for {today_str}",
                    font=("Segoe UI", 11),
                    fg=THEME["text"], bg=THEME["bg_panel"]).pack(anchor="w", pady=(0, 8))

            # Table
            table = tk.Frame(content, bg=THEME["bg_card"], highlightthickness=1, highlightbackground=THEME["border"])
            table.pack(fill="x")

            # Header
            header = tk.Frame(table, bg=FAIL_HEADER_BG)
            header.pack(fill="x")

            for text, width in [("Tenor", 8), ("Cell", 8), ("Excel", 10), ("Nibor Days", 12), ("Status", 8)]:
                tk.Label(header, text=text, font=("Segoe UI", 9),
                        fg=THEME["text_muted"], bg=FAIL_HEADER_BG,
                        width=width, anchor="center").pack(side="left", padx=4, pady=6)

            tk.Frame(table, bg=THEME["border"], height=1).pack(fill="x")

            # Data rows - show all with status
            for i, day in enumerate(self._days_details):
                matched = day.get("matched", False)
                row_bg = THEME["bg_card"] if i % 2 == 0 else THEME["row_odd"]
                row = tk.Frame(table, bg=row_bg)
                row.pack(fill="x")

                tenor = day.get("tenor", "")
                cell = day.get("cell", "")
                excel_val = day.get("excel_value")
                nibor_val = day.get("nibor_value")

                excel_str = str(excel_val) if excel_val is not None else "—"
                nibor_str = str(nibor_val) if nibor_val is not None else "—"

                status_text = "OK" if matched else "Fail"
                status_color = THEME["success"] if matched else FAIL_HEADER_FG
                value_color = THEME["text"] if matched else FAIL_HEADER_FG

                tk.Label(row, text=tenor, font=("Segoe UI", 10),
                        fg=THEME["text"], bg=row_bg, width=8, anchor="center").pack(side="left", padx=4, pady=6)
                tk.Label(row, text=cell, font=("Consolas", 10),
                        fg=THEME["text_muted"], bg=row_bg, width=8, anchor="center").pack(side="left", padx=4, pady=6)
                tk.Label(row, text=excel_str, font=("Consolas", 10),
                        fg=value_color, bg=row_bg, width=10, anchor="center").pack(side="left", padx=4, pady=6)
                tk.Label(row, text=nibor_str, font=("Consolas", 10),
                        fg=value_color, bg=row_bg, width=12, anchor="center").pack(side="left", padx=4, pady=6)
                tk.Label(row, text=status_text, font=("Segoe UI", 10),
                        fg=status_color, bg=row_bg, width=8, anchor="center").pack(side="left", padx=4, pady=6)

    def _update_validation_check(self, check_id, status, alerts=None):
        """Update a validation check badge status.

        Args:
            check_id: One of 'bloomberg', 'excel_cells', 'weights', 'days', 'nibor_contrib', 'spreads'
            status: True=OK, False=Failed, None=Pending
            alerts: List of alert messages (for failed checks)
        """
        if check_id not in self.validation_checks:
            return

        check = self.validation_checks[check_id]
        check["status"] = status
        check["alerts"] = alerts or []

        frame = check["frame"]
        icon = check["icon"]
        label = check["label"]

        if status is True:
            # Green success - only icon and text colored
            icon.config(text="✓", fg=THEME["success"])
            label.config(fg=THEME["success"])
        elif status is False:
            # Red failure - only icon and text colored
            icon.config(text="✕", fg=THEME["danger"])
            label.config(fg=THEME["danger"])
        else:
            # Pending
            icon.config(text="—", fg=THEME["text_muted"])
            label.config(fg=THEME["text_muted"])

        # Always use chip background
        bg = THEME["chip"]
        frame.config(bg=bg)
        icon.config(bg=bg)
        label.config(bg=bg)

        # Update summary
        self._update_validation_summary()

    def _update_validation_summary(self):
        """Update the validation summary label with X/Y format counting all individual checks."""
        # Count all individual checks from the detail lists
        total_checks = 0
        passed_checks = 0

        # Excel cells details (includes cell_check, implied_nok, internal_vs_ecp, nore_vs_swedbank)
        if hasattr(self, '_excel_cells_details') and self._excel_cells_details:
            for check in self._excel_cells_details:
                total_checks += 1
                if check.get("matched"):
                    passed_checks += 1

        # Spreads details
        if hasattr(self, '_spreads_details') and self._spreads_details:
            for check in self._spreads_details:
                total_checks += 1
                if check.get("matched"):
                    passed_checks += 1

        # Days details
        if hasattr(self, '_days_details') and self._days_details:
            for check in self._days_details:
                total_checks += 1
                if check.get("matched"):
                    passed_checks += 1

        # Weights - count from validation check alerts (1 check per weight)
        weights_check = self.validation_checks.get("weights", {})
        if weights_check.get("status") is not None:
            # 3 weight checks (EUR, USD, NOK)
            total_checks += 3
            if weights_check.get("status") is True:
                passed_checks += 3

        # If no checks have run yet, show nothing
        if total_checks == 0:
            self.validation_summary_lbl.config(text="", fg=THEME["text_muted"])
            return

        if passed_checks == total_checks:
            # All passed
            self.validation_summary_lbl.config(
                text=f"{passed_checks}/{total_checks}",
                fg=THEME["success"]
            )
        else:
            # Some failed
            self.validation_summary_lbl.config(
                text=f"{passed_checks}/{total_checks}",
                fg=THEME["danger"]
            )

    def _show_match_popup(self, tenor_key):
        """Show popup with detailed match criteria for NIBOR contribution."""
        if not hasattr(self, '_match_data') or tenor_key not in self._match_data:
            return

        data = self._match_data[tenor_key]

        # Create popup window
        popup = tk.Toplevel(self.winfo_toplevel())
        popup.title(f"NIBOR Match Details - {data['tenor']}")
        popup.configure(bg=THEME["bg_panel"])
        popup.geometry("500x400")
        popup.resizable(False, False)

        # Center on parent
        popup.transient(self.winfo_toplevel())
        popup.grab_set()

        # Header
        header_frame = tk.Frame(popup, bg=THEME["bg_card"])
        header_frame.pack(fill="x", padx=0, pady=0)

        status_color = THEME["success"] if data.get('all_matched') else THEME["danger"]
        status_text = "✓ ALL MATCHED" if data.get('all_matched') else "✕ MISMATCH FOUND"

        tk.Label(header_frame,
                text=f"NIBOR Contribution Match - {data['tenor']}",
                font=("Segoe UI Semibold", 14),
                fg=THEME["text"], bg=THEME["bg_card"]).pack(pady=(15, 5))

        tk.Label(header_frame,
                text=status_text,
                font=("Segoe UI Semibold", 12),
                fg=status_color, bg=THEME["bg_card"]).pack(pady=(0, 15))

        # GUI Rate display
        gui_frame = tk.Frame(popup, bg=THEME["bg_panel"])
        gui_frame.pack(fill="x", padx=20, pady=10)

        tk.Label(gui_frame,
                text="GUI NIBOR Rate:",
                font=("Segoe UI", 11),
                fg=THEME["muted"], bg=THEME["bg_panel"]).pack(side="left")

        gui_rate = data.get('gui_rate')
        tk.Label(gui_frame,
                text=f"{gui_rate:.4f}%" if gui_rate else "N/A",
                font=("Consolas", 12, "bold"),
                fg=THEME["accent"], bg=THEME["bg_panel"]).pack(side="right")

        # Separator
        tk.Frame(popup, bg=THEME["border"], height=1).pack(fill="x", padx=20, pady=5)

        # Criteria list
        criteria_frame = tk.Frame(popup, bg=THEME["bg_panel"])
        criteria_frame.pack(fill="both", expand=True, padx=20, pady=10)

        tk.Label(criteria_frame,
                text="Matchningskriterier:",
                font=("Segoe UI Semibold", 11),
                fg=THEME["text"], bg=THEME["bg_panel"]).pack(anchor="w", pady=(0, 10))

        for i, criterion in enumerate(data.get('criteria', []), 1):
            # Criterion card
            card = tk.Frame(criteria_frame, bg=THEME["bg_card"], highlightbackground=THEME["border"], highlightthickness=1)
            card.pack(fill="x", pady=5)

            # Status indicator
            match_status = criterion.get('matched', False)
            status_icon = "✓" if match_status else "✕"
            status_fg = THEME["success"] if match_status else THEME["danger"]

            # Header row
            header_row = tk.Frame(card, bg=THEME["bg_card"])
            header_row.pack(fill="x", padx=10, pady=(8, 4))

            tk.Label(header_row,
                    text=f"{status_icon} Kriterium {i}: {criterion.get('name', '')}",
                    font=("Segoe UI", 12),
                    fg=status_fg, bg=THEME["bg_card"]).pack(side="left")

            tk.Label(header_row,
                    text=f"({criterion.get('description', '')})",
                    font=("Segoe UI", 9),
                    fg=THEME["muted"], bg=THEME["bg_card"]).pack(side="right")

            # Values row
            values_row = tk.Frame(card, bg=THEME["bg_card"])
            values_row.pack(fill="x", padx=10, pady=(0, 8))

            gui_val = criterion.get('gui_value')
            excel_val = criterion.get('excel_value')
            decimals = 4 if "4 dec" in criterion.get('description', '') else 2

            gui_text = f"{gui_val:.{decimals}f}" if gui_val is not None else "N/A"
            excel_text = f"{excel_val:.{decimals}f}" if excel_val is not None else "N/A"

            tk.Label(values_row,
                    text=f"GUI: {gui_text}",
                    font=("Consolas", 10),
                    fg=THEME["text"], bg=THEME["bg_card"]).pack(side="left")

            tk.Label(values_row,
                    text="vs",
                    font=("Segoe UI", 9),
                    fg=THEME["muted"], bg=THEME["bg_card"]).pack(side="left", padx=10)

            tk.Label(values_row,
                    text=f"Excel ({criterion.get('excel_cell', '')}): {excel_text}",
                    font=("Consolas", 10),
                    fg=THEME["text"], bg=THEME["bg_card"]).pack(side="left")

        # Close button
        btn_frame = tk.Frame(popup, bg=THEME["bg_panel"])
        btn_frame.pack(fill="x", padx=20, pady=15)

        close_btn = tk.Button(btn_frame,
                             text="Stäng",
                             font=("Segoe UI", 10),
                             fg=THEME["text"],
                             bg=THEME["bg_card"],
                             activebackground=THEME["bg_card_2"],
                             activeforeground=THEME["text"],
                             relief="flat",
                             cursor="hand2",
                             padx=20, pady=8,
                             command=popup.destroy)
        close_btn.pack(side="right")

        # Focus popup
        popup.focus_set()

    def _show_funding_details(self, tenor_key, show_spread: bool = True):
        """Show compact calculation drawer for the selected tenor.

        Opens a compact popup showing calculation breakdown with collapsible sections.

        Args:
            tenor_key: The tenor (1m, 2m, 3m, 6m)
            show_spread: If True, shows NIBOR (with spread). If False, shows Funding Rate only.
        """
        # Close any existing compact drawer
        if hasattr(self, '_compact_drawer') and self._compact_drawer:
            try:
                self._compact_drawer.destroy()
            except tk.TclError:
                pass
            self._compact_drawer = None

        # Only open drawer if a fresh calculation has been performed (not just last approved data)
        if not getattr(self, '_calculation_performed', False):
            log.info(f"[Dashboard] No calculation performed yet - run calculation first")
            return

        if not hasattr(self.app, 'funding_calc_data') or not self.app.funding_calc_data.get(tenor_key):
            log.info(f"[Dashboard] No calculation data for {tenor_key}")
            return

        data = self.app.funding_calc_data.get(tenor_key, {})
        if not data or not data.get('final_rate'):
            log.info(f"[Dashboard] No funding data found for {tenor_key}")
            return

        # Open the compact calculation drawer
        self._compact_drawer = CompactCalculationDrawer(
            self,
            tenor_key,
            data,
            on_close=lambda: setattr(self, '_compact_drawer', None),
            show_spread=show_spread
        )

    def _apply_state(self, card, state: str, subtext: str = "—"):
        s = (state or "WAIT").upper()

        if s == "OK":
            card._icon.configure(text="●", fg=THEME["success"])
            card._status.configure(text="OK", fg=THEME["success"])
            card.configure(highlightbackground=THEME["success"])
        elif s == "PENDING":
            card._icon.configure(text="●", fg=THEME["yellow"])
            card._status.configure(text="PENDING", fg=THEME["yellow"])
            card.configure(highlightbackground=THEME["yellow"])
        elif s == "ALERT":
            card._icon.configure(text="●", fg=THEME["warning"])
            card._status.configure(text="ALERT", fg=THEME["warning"])
            card.configure(highlightbackground=THEME["warning"])
        elif s == "FAIL":
            card._icon.configure(text="●", fg=THEME["danger"])
            card._status.configure(text="ERROR", fg=THEME["danger"])
            card.configure(highlightbackground=THEME["danger"])
        else:
            card._icon.configure(text="●", fg=THEME["muted2"])
            card._status.configure(text="WAITING...", fg=THEME["text"])
            card.configure(highlightbackground=THEME["border"])

        card._sub.configure(text=subtext)

    def update(self):
        """Update all dashboard elements."""
        # Skip update if in loading state - wait for set_loading(False)
        if getattr(self, '_is_loading', False):
            return

        # Update historical mode visual indicator
        self._update_historical_mode()

        # Update funding rates and calculations
        try:
            self._update_funding_rates_with_validation()
        except Exception as e:
            log.error(f"[Dashboard] Error in _update_funding_rates_with_validation: {e}")

        # Populate horizontal status bar
        try:
            self._populate_status_badges()
        except Exception as e:
            log.error(f"[Dashboard] Error in _populate_status_badges: {e}")

    def _update_historical_mode(self):
        """Show/hide historical data indicator based on app state."""
        from ui.theme import COLORS
        is_historical = getattr(self.app, '_showing_last_approved', False)

        if is_historical:
            # Change card accent to warning color (amber)
            self._card_wrapper.configure(bg=COLORS.WARNING)

            # Show HISTORICAL badge if not already visible
            if not self._historical_badge:
                self._historical_badge = tk.Label(
                    self._header_row,
                    text="HISTORICAL",
                    fg=COLORS.WARNING,
                    bg=COLORS.WARNING_BG,
                    font=("Segoe UI Semibold", 9),
                    padx=8, pady=2
                )
                self._historical_badge.pack(side="left", padx=(12, 0))
        else:
            # Restore normal accent color
            self._card_wrapper.configure(bg=THEME["accent"])

            # Remove HISTORICAL badge if present
            if self._historical_badge:
                self._historical_badge.destroy()
                self._historical_badge = None

    def set_loading(self, loading: bool):
        """Show loading state on dashboard cells."""
        from ui.theme import COLORS

        # Track loading state
        self._is_loading = loading

        for tenor_key in ["1m", "2m", "3m", "6m"]:
            cells = self.funding_cells.get(tenor_key, {})
            if loading:
                # Set all values to "--" with muted color
                for key in ["funding", "spread", "final", "chg", "nibor_contrib"]:
                    lbl = cells.get(key)
                    if lbl:
                        lbl.configure(text="--", fg=COLORS.TEXT_MUTED)

        # Don't update funding rates when loading - just show empty state
        if loading:
            # Also reset validation badges to neutral state
            for check_id, check in self.validation_checks.items():
                check["status"] = None
                check["alerts"] = []
                check["icon"].configure(text="—", fg=THEME["text_muted"])
                check["label"].configure(fg=THEME["text_muted"])
                check["frame"].configure(bg=THEME["chip"])
                check["icon"].configure(bg=THEME["chip"])
                check["label"].configure(bg=THEME["chip"])

            # Reset validation summary
            self.validation_summary_lbl.config(text="", fg=THEME["text_muted"])
            return

        # When loading=False, update() will be called to populate real values
        # Update funding rates with Excel validation (cards are in global header, updated by main.py)
        try:
            self._update_funding_rates_with_validation()
        except Exception as e:
            log.error(f"[Dashboard] Error in _update_funding_rates_with_validation: {e}")
    
    def _populate_status_badges(self):
        """Populate horizontal status bar with current system status."""
        # Skip if frame doesn't exist (status badges moved to main header)
        if not hasattr(self, 'status_badges_frame') or not self.status_badges_frame:
            return
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

            # Pill badge colors
            if is_ok:
                icon = "✓"
                text_color = THEME["success"]  # Green
                bg_color = "#DCFCE7"    # Light green bg
            else:
                icon = "✕"
                text_color = THEME["danger"]  # Red
                bg_color = "#FEE2E2"    # Light red bg

            # Create pill-shaped badge
            if CTK_AVAILABLE:
                badge = ctk.CTkFrame(self.status_badges_frame, fg_color=bg_color,
                                    corner_radius=16)
                badge.pack(side="left", padx=4, pady=6)

                badge_label = ctk.CTkLabel(badge, text=f"{icon} {name}",
                                           text_color=text_color,
                                           font=("Segoe UI", 12),
                                           cursor="hand2")
                badge_label.pack(padx=12, pady=6)
            else:
                badge = tk.Frame(self.status_badges_frame, bg=bg_color,
                                cursor="hand2")
                badge.pack(side="left", padx=4, pady=6)

                badge_label = tk.Label(badge, text=f"{icon} {name}",
                                       fg=text_color, bg=bg_color,
                                       font=("Segoe UI", 12),
                                       padx=12, pady=6)
                badge_label.pack()

            # Store reference
            self.status_badges[key] = (badge_label, badge)
        
        # Update summary
        total = len(statuses)
        color = THEME["success"] if ok_count == total else (
            THEME["warning"] if ok_count > total // 2 else THEME["danger"]
        )
        if CTK_AVAILABLE:
            self.status_summary_lbl.configure(
                text=f"({ok_count}/{total} OK)",
                text_color=color
            )
        else:
            self.status_summary_lbl.config(
                text=f"({ok_count}/{total} OK)",
                fg=color
            )
    
    def _update_connection_cards(self):
        """Update Excel and Bloomberg connection status in top-right cards."""
        # Excel
        if hasattr(self.app, 'excel_ok') and self.app.excel_ok:
            self.excel_conn_lbl.config(text="CONNECTED", fg=THEME["success"])
            if hasattr(self.app, 'excel_last_update'):
                self.excel_time_lbl.config(text=f"Last updated: {self.app.excel_last_update}")
        else:
            self.excel_conn_lbl.config(text="DISCONNECTED", fg=THEME["danger"])
            self.excel_time_lbl.config(text="Last updated: --")
        
        # Bloomberg
        if hasattr(self.app, 'bbg_ok') and self.app.bbg_ok:
            self.bbg_conn_lbl.config(text="CONNECTED", fg=THEME["success"])
            if hasattr(self.app, 'bbg_last_update'):
                self.bbg_time_lbl.config(text=f"Last updated: {self.app.bbg_last_update}")
        else:
            self.bbg_conn_lbl.config(text="DISCONNECTED", fg=THEME["danger"])
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
                fg=THEME["danger"]
            )
        else:
            self.alerts_count_lbl.config(
                text="● ALL OK",
                fg=THEME["success"]
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

        # Mark that a fresh calculation has been performed
        self._calculation_performed = True

        # Get selected calculation model (default: swedbank)
        selected_model = self.calc_model_var.get() if hasattr(self, 'calc_model_var') else "swedbank"
        log.info(f"[Dashboard._update_funding_rates_with_validation] Using model: {selected_model}")

        weights = self._get_weights()
        self.app.funding_calc_data = {}

        # Excel cells for NIBOR Contribution reconciliation (from latest sheet)
        # 3 criteria for matching:
        # 1. GUI vs Z30-Z33 (4 decimals)
        # 2. GUI vs AA7-AA10 (2 decimals) - input row
        # 3. GUI vs AA30-AA33 (2 decimals) - output row
        EXCEL_Z_CELLS = {"1m": "Z30", "2m": "Z31", "3m": "Z32", "6m": "Z33"}
        EXCEL_AA_INPUT_CELLS = {"1m": "AA7", "2m": "AA8", "3m": "AA9", "6m": "AA10"}
        EXCEL_AA_OUTPUT_CELLS = {"1m": "AA30", "2m": "AA31", "3m": "AA32", "6m": "AA33"}

        # Store match data for popup
        if not hasattr(self, '_match_data'):
            self._match_data = {}

        # Get previous sheet rates for CHG calculation (from Excel second-to-last sheet)
        try:
            prev_rates = self.app.excel_engine.get_previous_sheet_nibor_rates()
        except Exception as e:
            log.warning(f"[Dashboard] Failed to get previous sheet rates for CHG: {e}")
            prev_rates = None

        alert_messages = []

        for tenor_key in ["1m", "2m", "3m", "6m"]:
          try:
            # Select data based on model choice
            if selected_model == "swedbank":
                # Use Internal Basket Rates (Excel CM - nibor suffix)
                eur_data = self.app.impl_calc_data.get(f"eur_{tenor_key}_nibor", {})
                usd_data = self.app.impl_calc_data.get(f"usd_{tenor_key}_nibor", {})
                log.info(f"[Dashboard] {tenor_key}: Using Swedbank Calc, eur_data={bool(eur_data)}, usd_data={bool(usd_data)}")
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
            log.info(f"[Dashboard] {tenor_key}: cells keys = {list(cells.keys())}")

            # Update display cells
            if "funding" in cells:
                cells["funding"].config(text=f"{funding_rate:.2f}%" if funding_rate else "N/A")
            if "spread" in cells:
                # NO % sign in spread column
                cells["spread"].config(text=f"{spread:.2f}")
            if "final" in cells:
                cells["final"].config(text=f"{final_rate:.2f}%" if final_rate else "N/A", fg=THEME["accent"])

            # CHG (Change from previous sheet in Excel - AA30-AA33)
            # Nordic Light: green positive with ▲, red negative with ▼, gray near-zero with —
            if "chg" in cells:
                chg_lbl = cells["chg"]
                prev_nibor = None
                if prev_rates and tenor_key in prev_rates:
                    prev_nibor = prev_rates[tenor_key].get('nibor')

                if final_rate is not None and prev_nibor is not None:
                    chg = final_rate - prev_nibor
                    # Near-zero threshold (less than 0.005 rounds to 0.00)
                    if abs(chg) < 0.005:
                        chg_text = "— 0.00"  # Dash for no significant change
                        chg_color = THEME["text_muted"]  # Gray for near-zero
                    elif chg > 0:
                        chg_text = f"▲ +{chg:.2f}"  # Up arrow for positive
                        chg_color = THEME["success"]  # Green for positive
                    else:
                        chg_text = f"▼ {chg:.2f}"   # Down arrow for negative
                        chg_color = THEME["danger"]   # Red for negative
                    chg_lbl.config(text=chg_text, fg=chg_color)
                else:
                    chg_lbl.config(text="—", fg=THEME["text_muted"])

            # ================================================================
            # RECON COL 1: NIBOR Contrib - 3 criteria matching
            # ================================================================
            if "nibor_contrib" in cells:
                z_cell = EXCEL_Z_CELLS.get(tenor_key)
                aa_input_cell = EXCEL_AA_INPUT_CELLS.get(tenor_key)
                aa_output_cell = EXCEL_AA_OUTPUT_CELLS.get(tenor_key)

                # Store match details for popup
                match_details = {
                    'tenor': tenor_key.upper(),
                    'gui_rate': final_rate,
                    'criteria': []
                }

                all_matched = True
                errors = []

                has_excel = hasattr(self.app, 'excel_engine') and self.app.excel_engine is not None

                if final_rate is None:
                    all_matched = False
                    errors.append("GUI rate not calculated")
                elif not has_excel:
                    all_matched = False
                    errors.append("Excel engine not loaded")
                else:
                    # Criterion 1: GUI vs Z30-Z33 (4 decimals)
                    if z_cell:
                        excel_z = self.app.excel_engine.get_recon_value(z_cell)
                        criterion_1 = {
                            'name': f'GUI vs {z_cell}',
                            'description': '4 decimaler',
                            'gui_value': round(final_rate, 4) if final_rate else None,
                            'excel_cell': z_cell,
                            'excel_value': None,
                            'matched': False
                        }
                        if excel_z is not None:
                            try:
                                excel_z = float(excel_z)
                                gui_4dec = round(final_rate, 4)
                                excel_4dec = round(excel_z, 4)
                                criterion_1['excel_value'] = excel_4dec
                                criterion_1['matched'] = (gui_4dec == excel_4dec)
                                if not criterion_1['matched']:
                                    all_matched = False
                                    errors.append(f"{z_cell}: GUI {gui_4dec:.4f} ≠ Excel {excel_4dec:.4f}")
                            except (ValueError, TypeError):
                                all_matched = False
                                errors.append(f"{z_cell}: parse error")
                        else:
                            all_matched = False
                            errors.append(f"{z_cell}: Excel value missing")
                        match_details['criteria'].append(criterion_1)

                    # Criterion 2: GUI vs AA7-AA10 (2 decimals) - input row
                    if aa_input_cell:
                        excel_aa_input = self.app.excel_engine.get_recon_value(aa_input_cell)
                        criterion_2 = {
                            'name': f'GUI vs {aa_input_cell}',
                            'description': '2 decimaler (input)',
                            'gui_value': round(final_rate, 2) if final_rate else None,
                            'excel_cell': aa_input_cell,
                            'excel_value': None,
                            'matched': False
                        }
                        if excel_aa_input is not None:
                            try:
                                excel_aa_input = float(excel_aa_input)
                                gui_2dec = round(final_rate, 2)
                                excel_2dec = round(excel_aa_input, 2)
                                criterion_2['excel_value'] = excel_2dec
                                criterion_2['matched'] = (gui_2dec == excel_2dec)
                                if not criterion_2['matched']:
                                    all_matched = False
                                    errors.append(f"{aa_input_cell}: GUI {gui_2dec:.2f} ≠ Excel {excel_2dec:.2f}")
                            except (ValueError, TypeError):
                                all_matched = False
                                errors.append(f"{aa_input_cell}: parse error")
                        else:
                            all_matched = False
                            errors.append(f"{aa_input_cell}: Excel value missing")
                        match_details['criteria'].append(criterion_2)

                    # Criterion 3: GUI vs AA30-AA33 (2 decimals) - output row
                    if aa_output_cell:
                        excel_aa_output = self.app.excel_engine.get_recon_value(aa_output_cell)
                        criterion_3 = {
                            'name': f'GUI vs {aa_output_cell}',
                            'description': '2 decimaler (output)',
                            'gui_value': round(final_rate, 2) if final_rate else None,
                            'excel_cell': aa_output_cell,
                            'excel_value': None,
                            'matched': False
                        }
                        if excel_aa_output is not None:
                            try:
                                excel_aa_output = float(excel_aa_output)
                                gui_2dec = round(final_rate, 2)
                                excel_2dec = round(excel_aa_output, 2)
                                criterion_3['excel_value'] = excel_2dec
                                criterion_3['matched'] = (gui_2dec == excel_2dec)
                                if not criterion_3['matched']:
                                    all_matched = False
                                    errors.append(f"{aa_output_cell}: GUI {gui_2dec:.2f} ≠ Excel {excel_2dec:.2f}")
                            except (ValueError, TypeError):
                                all_matched = False
                                errors.append(f"{aa_output_cell}: parse error")
                        else:
                            all_matched = False
                            errors.append(f"{aa_output_cell}: Excel value missing")
                        match_details['criteria'].append(criterion_3)

                # Store match data for popup
                match_details['all_matched'] = all_matched
                match_details['errors'] = errors
                self._match_data[tenor_key] = match_details

                # Professional pill badge status display
                lbl = cells["nibor_contrib"]
                badge = cells.get("nibor_contrib_badge")

                # Make label clickable for popup
                # Unbind first to prevent multiple popups
                try:
                    lbl.unbind("<Button-1>")
                except tk.TclError:
                    pass

                # Check if CTK widget (CTkLabel) or regular tk widget
                is_ctk_widget = CTK_AVAILABLE and 'ctk' in str(type(lbl).__module__).lower()

                if is_ctk_widget:
                    lbl.configure(cursor="hand2")
                    if badge:
                        badge.configure(cursor="hand2")
                        badge.bind("<Button-1>", lambda e, tk=tenor_key: self._open_drawer_for_tenor(tk))
                else:
                    lbl.config(cursor="hand2")
                    if badge:
                        badge.config(cursor="hand2")
                        badge.bind("<Button-1>", lambda e, tk=tenor_key: self._open_drawer_for_tenor(tk))
                lbl.bind("<Button-1>", lambda e, tk=tenor_key: self._open_drawer_for_tenor(tk))

                # Always use chip background - only text/icon colored
                chip_bg = THEME["chip"]
                if all_matched and match_details['criteria']:
                    # Matched - Green text with checkmark icon
                    matched_fg = THEME["success"]
                    if is_ctk_widget:
                        badge.configure(fg_color=chip_bg)
                        lbl.configure(text="✓ Matched", text_color=matched_fg)
                    else:
                        lbl.config(text="✓ Matched", fg=matched_fg, bg=chip_bg,
                                  font=("Segoe UI", 12), padx=14, pady=5)
                        if badge:
                            badge.config(bg=chip_bg)
                    self._stop_blink(lbl)
                elif errors:
                    # Failed - Red text with cross icon
                    failed_fg = THEME["danger"]
                    if is_ctk_widget:
                        badge.configure(fg_color=chip_bg)
                        lbl.configure(text="✕ Failed", text_color=failed_fg)
                    else:
                        lbl.config(text="✕ Failed", fg=failed_fg, bg=chip_bg,
                                  font=("Segoe UI", 12), padx=14, pady=5)
                        if badge:
                            badge.config(bg=chip_bg)
                    self._start_blink(lbl)
                    for err in errors:
                        alert_messages.append(f"{tenor_key.upper()} Contrib: {err}")
                else:
                    # Pending - Neutral pill with dash
                    pending_fg = THEME["text_muted"]
                    if is_ctk_widget:
                        badge.configure(fg_color=chip_bg)
                        lbl.configure(text="—", text_color=pending_fg)
                    else:
                        lbl.config(text="—", fg=pending_fg, bg=chip_bg,
                                  font=("Segoe UI", 12), padx=14, pady=5)
                        if badge:
                            badge.config(bg=chip_bg)
                    self._stop_blink(lbl)
            
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
          except Exception as e:
            log.error(f"[Dashboard] Error updating tenor {tenor_key}: {e}")

        # Show/hide alerts
        self._update_alerts(alert_messages)

        # Run recon checks and update validation icons
        self._update_recon_validation()

        # Enable/disable Confirm button based on matching status
        self._update_confirm_button_state()

        # Update action bar timestamp and data source
    def _on_alerts_configure(self, event=None):
        """Legacy method - no longer used (alerts now in validation checks)."""
        pass

    def _update_confirm_button_state(self):
        """Enable Confirm button only if all tenors are matched."""
        if not hasattr(self, 'confirm_rates_btn') and not hasattr(self, 'action_bar'):
            return

        # Check if all tenors (1m, 2m, 3m, 6m) are matched
        tenors_to_check = ["1m", "2m", "3m", "6m"]
        all_matched = True

        # First check that all tenors have been evaluated
        if len(self._match_data) < len(tenors_to_check):
            all_matched = False
            log.info(f"[Dashboard] Confirm button DISABLED - only {len(self._match_data)}/{len(tenors_to_check)} tenors evaluated")
        else:
            for tenor in tenors_to_check:
                match_data = self._match_data.get(tenor, {})
                if not match_data.get('all_matched', False):
                    all_matched = False
                    log.info(f"[Dashboard] Tenor {tenor} not matched")
                    break

        # Update button state
        try:
            if self.action_bar:
                # Use action bar's set_ready method
                self.action_bar.set_ready(all_matched)
                if all_matched:
                    log.info("[Dashboard] Confirm button ENABLED - all tenors matched")
            elif hasattr(self, 'confirm_rates_btn'):
                # Fallback for non-CTK
                if all_matched:
                    self.confirm_rates_btn.configure(state="normal")
                    log.info("[Dashboard] Confirm button ENABLED - all tenors matched")
                else:
                    self.confirm_rates_btn.configure(state="disabled")
        except Exception as e:
            log.error(f"[Dashboard] Error updating confirm button state: {e}")

    def _update_alerts(self, messages):
        """Update validation checks based on alert messages.

        Routes alerts to appropriate validation check categories based on message content.
        Messages can be either:
        - Simple strings (treated as critical)
        - Tuples of (message, priority) where priority is 'warning' or 'critical'
        """
        if not hasattr(self, 'validation_checks'):
            return

        # Categorize alerts by check type
        categorized_alerts = {
            "bloomberg": [],
            "excel_cells": [],
            "weights": [],
            "days": [],
            "nibor_contrib": [],
            "spreads": [],
        }

        for msg_item in messages:
            if isinstance(msg_item, tuple):
                msg, priority = msg_item
            else:
                msg = msg_item

            msg_lower = msg.lower()

            # Route to appropriate category
            if "contrib" in msg_lower or "z30" in msg_lower or "aa30" in msg_lower:
                categorized_alerts["nibor_contrib"].append(msg)
            elif "spread" in msg_lower:
                categorized_alerts["spreads"].append(msg)
            elif "weight" in msg_lower:
                categorized_alerts["weights"].append(msg)
            elif "day" in msg_lower:
                categorized_alerts["days"].append(msg)
            elif "bloomberg" in msg_lower or "ticker" in msg_lower:
                categorized_alerts["bloomberg"].append(msg)
            else:
                # Default to excel_cells for cell mismatches
                categorized_alerts["excel_cells"].append(msg)

        # Update each validation check
        for check_id, alerts in categorized_alerts.items():
            if alerts:
                self._update_validation_check(check_id, False, alerts)
            else:
                # If no alerts in this category, mark as OK
                # (only if we have data - check nibor_contrib based on _match_data)
                if check_id == "nibor_contrib":
                    # Only mark OK if we have all tenors matched
                    tenors_to_check = ["1m", "2m", "3m", "6m"]
                    all_matched = all(
                        self._match_data.get(t, {}).get('all_matched', False)
                        for t in tenors_to_check
                    ) if len(self._match_data) >= len(tenors_to_check) else None
                    if all_matched is not None:
                        self._update_validation_check(check_id, all_matched, [])
                else:
                    # For other categories, mark OK if no alerts
                    self._update_validation_check(check_id, True, [])

    def _update_recon_validation(self):
        """Run recon checks for all tenors and update NIBOR Contrib and Excel Cells validation."""
        from config import RECON_CELL_MAPPING

        if not hasattr(self, 'validation_checks'):
            return

        # Helper to read Excel value safely
        def read_excel_cell(cell):
            try:
                if hasattr(self.app, 'excel_engine') and self.app.excel_engine:
                    return self.app.excel_engine.get_recon_value(cell)
            except Exception:
                pass
            return None

        # Collect detailed diffs per tenor (same checks as drawer)
        # Store full details for the popup display
        self._recon_diff_details = []  # List of dicts with full diff info

        # NEW: Collect ALL Excel cell checks for Excel Cells popup
        self._excel_cells_details = []  # List of all checks (matched and failed)

        # Input fields to check - same as drawer recon
        input_fields = [
            ("NOK ECP", "NOK_ECP", "nok_cm", 2),
            ("EUR ECP", "EUR_RATE", "eur_rate", 2),
            ("USD ECP", "USD_RATE", "usd_rate", 2),
            ("EURNOK Spot", "EUR_SPOT", "eur_spot", 4),
            ("EURNOK Pips", "EUR_PIPS", "eur_pips", 2),
            ("USDNOK Spot", "USD_SPOT", "usd_spot", 4),
            ("USDNOK Pips", "USD_PIPS", "usd_pips", 2),
        ]

        # Output fields
        output_fields = [
            ("EUR Implied", "EUR_IMPLIED", "eur_impl", 4),
            ("USD Implied", "USD_IMPLIED", "usd_impl", 4),
        ]

        excel_cells_failed = []
        bloomberg_failed = []  # Track cell_check failures for Bloomberg validation
        implied_nok_failed = []  # Track implied NOK failures for NIBOR Contribution

        for tenor_key in ["1m", "2m", "3m", "6m"]:
            data = getattr(self.app, 'funding_calc_data', {}).get(tenor_key, {})
            if not data:
                continue

            # Check input fields
            for label, mapping_key, data_key, decimals in input_fields:
                cell = RECON_CELL_MAPPING.get(mapping_key, {}).get(tenor_key)
                if not cell:
                    continue

                gui_value = data.get(data_key)
                excel_value = read_excel_cell(cell)

                # Compare values
                matched = False
                gui_rounded = None
                excel_rounded = None
                if gui_value is not None and excel_value is not None:
                    try:
                        gui_rounded = round(float(gui_value), decimals)
                        excel_rounded = round(float(excel_value), decimals)
                        matched = (gui_rounded == excel_rounded)
                        if not matched:
                            self._recon_diff_details.append({
                                "tenor": tenor_key.upper(),
                                "component": label,
                                "gui_value": gui_rounded,
                                "excel_value": excel_rounded,
                                "decimals": decimals
                            })
                            bloomberg_failed.append(f"{tenor_key.upper()} {label}: {gui_rounded} ≠ {excel_rounded}")
                    except (ValueError, TypeError) as e:
                        log.debug(f"Float parse failed for {label} in {tenor_key}: gui={gui_value}, excel={excel_value}: {e}")

                # Store ALL checks for Excel Cells popup
                self._excel_cells_details.append({
                    "tenor": tenor_key.upper(),
                    "field": label,
                    "cell": cell,
                    "gui_value": gui_rounded if gui_rounded is not None else gui_value,
                    "excel_value": excel_rounded if excel_rounded is not None else excel_value,
                    "decimals": decimals,
                    "matched": matched,
                    "is_input": True,
                    "check_type": "cell_check"
                })

            # Check output fields (Implied NOK - goes to NIBOR Contribution)
            for label, mapping_key, data_key, decimals in output_fields:
                cell = RECON_CELL_MAPPING.get(mapping_key, {}).get(tenor_key)
                if not cell:
                    continue

                gui_value = data.get(data_key)
                excel_value = read_excel_cell(cell)

                matched = False
                gui_rounded = None
                excel_rounded = None
                if gui_value is not None and excel_value is not None:
                    try:
                        gui_rounded = round(float(gui_value), decimals)
                        excel_rounded = round(float(excel_value), decimals)
                        matched = (gui_rounded == excel_rounded)
                        if not matched:
                            implied_nok_failed.append(f"{tenor_key.upper()} {label}: {gui_rounded} ≠ {excel_rounded}")
                    except (ValueError, TypeError):
                        pass

                self._excel_cells_details.append({
                    "tenor": tenor_key.upper(),
                    "field": label,
                    "cell": cell,
                    "gui_value": gui_rounded if gui_rounded is not None else gui_value,
                    "excel_value": excel_rounded if excel_rounded is not None else excel_value,
                    "decimals": decimals,
                    "matched": matched,
                    "is_input": False,
                    "check_type": "implied_nok"
                })

        # ═══════════════════════════════════════════════════════════════
        # Internal Rates vs ECP checks (rules 129-136 from RULES_DB)
        # Internal rates must be >= ECP rates
        # ═══════════════════════════════════════════════════════════════
        ecp_checks = [
            # (tenor, internal_cell, ecp_cell, currency, label)
            ("1M", "M30", "M7", "EUR", "EUR 1M Internal vs ECP"),
            ("2M", "M31", "M8", "EUR", "EUR 2M Internal vs ECP"),
            ("3M", "M32", "M9", "EUR", "EUR 3M Internal vs ECP"),
            ("6M", "M33", "M10", "EUR", "EUR 6M Internal vs ECP"),
            ("1M", "R30", "R7", "USD", "USD 1M Internal vs ECP"),
            ("2M", "R31", "R8", "USD", "USD 2M Internal vs ECP"),
            ("3M", "R32", "R9", "USD", "USD 3M Internal vs ECP"),
            ("6M", "R33", "R10", "USD", "USD 6M Internal vs ECP"),
        ]

        for tenor, internal_cell, ecp_cell, currency, label in ecp_checks:
            internal_val = read_excel_cell(internal_cell)
            ecp_val = read_excel_cell(ecp_cell)

            matched = False
            internal_rounded = None
            ecp_rounded = None
            decimals = 4

            if internal_val is not None and ecp_val is not None:
                try:
                    internal_rounded = round(float(internal_val), decimals)
                    ecp_rounded = round(float(ecp_val), decimals)
                    # Internal rate must be >= ECP rate
                    matched = internal_rounded >= ecp_rounded
                    if not matched:
                        excel_cells_failed.append(f"{label}: {internal_rounded:.4f} < {ecp_rounded:.4f}")
                except (ValueError, TypeError):
                    pass

            self._excel_cells_details.append({
                "tenor": tenor,
                "field": f"{currency} Internal vs ECP",
                "cell": internal_cell,
                "gui_value": internal_rounded,  # Internal rate
                "excel_value": ecp_rounded,  # ECP rate
                "ref_value": internal_rounded,  # For display
                "decimals": decimals,
                "matched": matched,
                "check_type": "internal_vs_ecp"
            })

        # ═══════════════════════════════════════════════════════════════
        # Nore Nibor Calculation Model vs Swedbank Estimated Spread Calculation Model
        # Row 6-10 (Nore/Bloomberg) vs Row 29-33 (Swedbank calc model)
        # From RULES_DB rules 1-105
        # ═══════════════════════════════════════════════════════════════
        nore_vs_swedbank_columns = [
            # (column, field_name, decimals)
            # Removed: A, B, D, E, F, G, H, I, J, AB, AC (text or not needed)
            ("C", "Tenor Days", 0),
            ("K", "NOK ECP Rate", 4),
            ("L", "NOK ECP Adj", 4),
            ("N", "EURNOK Spot", 4),
            ("O", "EURNOK Pips", 2),
            ("Q", "EUR Implied", 4),
            ("S", "USDNOK Spot", 4),
            ("T", "USDNOK Pips", 2),
            ("V", "USD Implied", 4),
            ("W", "Weighted Avg", 4),
        ]

        tenor_rows = [
            ("1W", 6, 29),
            ("1M", 7, 30),
            ("2M", 8, 31),
            ("3M", 9, 32),
            ("6M", 10, 33),
        ]

        for col, field_name, decimals in nore_vs_swedbank_columns:
            for tenor, nore_row, swedbank_row in tenor_rows:
                nore_cell = f"{col}{nore_row}"
                swedbank_cell = f"{col}{swedbank_row}"

                nore_val = read_excel_cell(nore_cell)
                swedbank_val = read_excel_cell(swedbank_cell)

                matched = False
                nore_rounded = None
                swedbank_rounded = None

                if nore_val is not None and swedbank_val is not None:
                    try:
                        if decimals == 0:
                            # Integer comparison
                            nore_rounded = int(float(nore_val)) if nore_val else 0
                            swedbank_rounded = int(float(swedbank_val)) if swedbank_val else 0
                            matched = (nore_rounded == swedbank_rounded)
                        else:
                            nore_rounded = round(float(nore_val), decimals)
                            swedbank_rounded = round(float(swedbank_val), decimals)
                            matched = abs(nore_rounded - swedbank_rounded) < (10 ** -decimals)
                        if not matched:
                            excel_cells_failed.append(f"{tenor} {field_name}: {nore_cell}≠{swedbank_cell}")
                    except (ValueError, TypeError):
                        pass

                self._excel_cells_details.append({
                    "tenor": tenor,
                    "field": field_name,
                    "cell": f"{nore_cell}:{swedbank_cell}",
                    "gui_value": nore_rounded,  # Nore value
                    "excel_value": swedbank_rounded,  # Swedbank value
                    "decimals": decimals if decimals > 0 else 0,
                    "matched": matched,
                    "check_type": "nore_vs_swedbank"
                })

        # Update Implied NOK validation icon
        if implied_nok_failed:
            self._update_validation_check("nibor_contrib", False, implied_nok_failed)
        else:
            # Only mark OK if we have data
            if getattr(self.app, 'funding_calc_data', {}):
                self._update_validation_check("nibor_contrib", True, [])

        # Update Excel Cells validation icon (Nore vs Swedbank + Internal vs ECP)
        if self._excel_cells_details:
            if excel_cells_failed:
                self._update_validation_check("excel_cells", False, excel_cells_failed)
            else:
                self._update_validation_check("excel_cells", True, [])

        # Update Bloomberg validation icon (GUI vs Excel cell checks)
        if bloomberg_failed:
            self._update_validation_check("bloomberg", False, bloomberg_failed)
        else:
            # Mark OK if we have funding calc data
            if getattr(self.app, 'funding_calc_data', {}):
                self._update_validation_check("bloomberg", True, [])

        # ═══════════════════════════════════════════════════════════════
        # Spreads validation - check Y6 (0.10-0.20) and Y7-Y10 (0.15-0.25)
        # ═══════════════════════════════════════════════════════════════
        self._spreads_details = []
        spreads_failed = []

        spread_checks = [
            # (cell, tenor, min_val, max_val)
            ("Y6", "1W", 0.10, 0.20),
            ("Y7", "1M", 0.15, 0.25),
            ("Y8", "2M", 0.15, 0.25),
            ("Y9", "3M", 0.15, 0.25),
            ("Y10", "6M", 0.15, 0.25),
        ]

        for cell, tenor, min_val, max_val in spread_checks:
            spread_val = read_excel_cell(cell)
            matched = False
            spread_rounded = None

            if spread_val is not None:
                try:
                    spread_rounded = round(float(spread_val), 4)
                    matched = min_val <= spread_rounded <= max_val
                    if not matched:
                        spreads_failed.append(f"{tenor} ({cell}): {spread_rounded:.4f} not in [{min_val:.2f}-{max_val:.2f}]")
                except (ValueError, TypeError):
                    pass

            self._spreads_details.append({
                "tenor": tenor,
                "cell": cell,
                "value": spread_rounded,
                "min": min_val,
                "max": max_val,
                "matched": matched
            })

        # Update Spreads validation icon
        if spreads_failed:
            self._update_validation_check("spreads", False, spreads_failed)
        else:
            # Only mark OK if we have Excel data
            if hasattr(self.app, 'excel_engine') and self.app.excel_engine:
                self._update_validation_check("spreads", True, [])

        # ═══════════════════════════════════════════════════════════════
        # Days validation - check C7-C10 against Nibor Days file for today
        # ═══════════════════════════════════════════════════════════════
        self._days_details = []
        days_failed = []

        # Get today's days from Nibor Days file
        from datetime import datetime
        today_str = datetime.now().strftime("%Y-%m-%d")
        nibor_days = {}
        if hasattr(self.app, 'excel_engine') and self.app.excel_engine:
            nibor_days = self.app.excel_engine.get_days_for_date(today_str) or {}

        # Cells to check: C7=1M, C8=2M, C9=3M, C10=6M
        days_checks = [
            ("C7", "1M", "1m"),
            ("C8", "2M", "2m"),
            ("C9", "3M", "3m"),
            ("C10", "6M", "6m"),
        ]

        for cell, tenor_label, tenor_key in days_checks:
            excel_val = read_excel_cell(cell)
            nibor_val = nibor_days.get(tenor_key) or nibor_days.get(f"{tenor_key}_Days")

            matched = False
            excel_days = None
            nibor_days_val = None

            if excel_val is not None:
                try:
                    excel_days = int(float(excel_val))
                except (ValueError, TypeError):
                    pass

            if nibor_val is not None:
                try:
                    nibor_days_val = int(float(nibor_val))
                except (ValueError, TypeError):
                    pass

            if excel_days is not None and nibor_days_val is not None:
                matched = excel_days == nibor_days_val
                if not matched:
                    days_failed.append(f"{tenor_label} ({cell}): Excel={excel_days}, Nibor Days={nibor_days_val}")

            self._days_details.append({
                "tenor": tenor_label,
                "cell": cell,
                "excel_value": excel_days,
                "nibor_value": nibor_days_val,
                "matched": matched
            })

        # Update Days validation icon
        if days_failed:
            self._update_validation_check("days", False, days_failed)
        else:
            # Only mark OK if we have both Excel and Nibor Days data
            if nibor_days and hasattr(self.app, 'excel_engine') and self.app.excel_engine:
                self._update_validation_check("days", True, [])

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
        # Only show tooltip if a fresh calculation has been performed
        if not getattr(self, '_calculation_performed', False):
            return None

        calc_data = getattr(self.app, 'funding_calc_data', {})
        tenor_data = calc_data.get(tenor_key, {})
        final_rate = tenor_data.get('final_rate')
        if final_rate is not None:
            return f"NIBOR {tenor_key.upper()}: {final_rate:.4f}%"
        return None

    def _get_chg_tooltip(self, tenor_key):
        """Get previous NIBOR rate and date for CHG tooltip (from Excel second-to-last sheet)."""
        # Only show tooltip if a fresh calculation has been performed (not just last approved data)
        if not getattr(self, '_calculation_performed', False):
            return None  # No calculation done yet

        # Check if excel engine is available
        if not hasattr(self.app, 'excel_engine') or self.app.excel_engine is None:
            return None

        try:
            prev_rates = self.app.excel_engine.get_previous_sheet_nibor_rates()
        except Exception:
            return None

        if not prev_rates or tenor_key not in prev_rates:
            return None

        prev_nibor = prev_rates[tenor_key].get('nibor')
        if prev_nibor is None:
            return None

        # Get the date from the sheet name
        prev_date = prev_rates.get("_date", "")

        # Build clear tooltip text
        lines = [f"Comparing with: {prev_nibor:.2f}%"]
        if prev_date:
            lines.append(f"Date: {prev_date}")
        return "\n".join(lines)

    def _get_funding_tooltip(self, tenor_key):
        """Get Funding Rate breakdown: EUR/USD implied (4 dec), NOK (2 dec)."""
        # Only show tooltip if a fresh calculation has been performed
        if not getattr(self, '_calculation_performed', False):
            return None

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
            lines.append(f"  NOK ECP:      {nok_cm:.2f}%")

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
                cells["final"].config(text=f"{final_rate:.2f}%" if final_rate else "N/A", fg=THEME["accent"])

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

    # ====================================================================
    # CALCULATION DRAWER METHODS
    # ====================================================================

    def _on_drawer_close(self):
        """Callback when drawer is closed."""
        # Hide the drawer window
        if hasattr(self, '_drawer_window') and self._drawer_window:
            self._drawer_window.withdraw()
        log.info("[Dashboard] Drawer closed")

    def _on_drawer_rerun(self, tenor_key: str):
        """Callback when re-run button is clicked in drawer."""
        log.info(f"[Dashboard] Re-running checks for tenor: {tenor_key}")
        # Refresh data and re-update the drawer
        self._update_funding_rates_with_validation()
        # Re-open drawer with updated data
        if tenor_key and hasattr(self, '_drawer'):
            self._open_drawer_for_tenor(tenor_key)

    def _close_drawer_on_escape(self, event=None):
        """Close drawer when ESC key is pressed."""
        if self._drawer and self._drawer.is_visible():
            self._drawer.close()
            return "break"  # Prevent event propagation

    def _on_main_window_configure(self, event=None):
        """Update drawer position when main window moves or resizes."""
        if not self._drawer_window or not self._drawer_window.winfo_exists():
            return
        if not self._drawer_window.winfo_viewable():
            return

        # Get main window position and size
        root = self.winfo_toplevel()
        main_x = root.winfo_x()
        main_y = root.winfo_y()
        main_width = root.winfo_width()
        main_height = root.winfo_height()

        # Position drawer to the right of main window
        drawer_x = main_x + main_width + 2
        drawer_width = 450

        # Update drawer position and height
        self._drawer_window.geometry(f"{drawer_width}x{main_height}+{drawer_x}+{main_y}")

    def _open_drawer_for_tenor(self, tenor_key: str):
        """Open the calculation drawer for a specific tenor."""
        from config import RECON_CELL_MAPPING

        # Only open drawer if a fresh calculation has been performed (not just last approved data)
        if not getattr(self, '_calculation_performed', False):
            log.info(f"[Dashboard] No calculation performed yet - run calculation first")
            return

        if not hasattr(self.app, 'funding_calc_data') or not self.app.funding_calc_data.get(tenor_key):
            log.info(f"[Dashboard] No calculation data for {tenor_key}")
            return

        data = self.app.funding_calc_data.get(tenor_key)
        if not data or not data.get('final_rate'):
            log.info(f"[Dashboard] No funding data found for {tenor_key}")
            return

        # Add match data to the data dict
        match_data = self._match_data.get(tenor_key, {})
        data_with_match = dict(data)
        data_with_match['match_data'] = match_data

        # Build reconciliation data by reading Excel cells
        recon_data = []
        all_inputs_match = True

        # Helper to read Excel value safely
        def read_excel_cell(cell):
            try:
                if hasattr(self.app, 'excel_engine') and self.app.excel_engine:
                    return self.app.excel_engine.get_recon_value(cell)
            except Exception as e:
                log.warning(f"[Drawer] Could not read Excel cell {cell}: {e}")
            return None

        # Input fields to check (must all match before checking outputs)
        # Format: (display_label, mapping_key, data_key, decimals)
        input_fields = [
            ("NOK ECP", "NOK_ECP", "nok_cm", 2),
            ("EUR ECP", "EUR_RATE", "eur_rate", 2),
            ("USD ECP", "USD_RATE", "usd_rate", 2),
            ("EURNOK", "EUR_SPOT", "eur_spot", 4),
            ("EURNOK", "EUR_PIPS", "eur_pips", 2),
            ("USDNOK", "USD_SPOT", "usd_spot", 4),
            ("USDNOK", "USD_PIPS", "usd_pips", 2),
        ]

        for label, mapping_key, data_key, decimals in input_fields:
            cell = RECON_CELL_MAPPING.get(mapping_key, {}).get(tenor_key)
            if not cell:
                continue

            gui_value = data.get(data_key)
            excel_value = read_excel_cell(cell)

            # Compare values
            matched = False
            if gui_value is not None and excel_value is not None:
                try:
                    gui_rounded = round(float(gui_value), decimals)
                    excel_rounded = round(float(excel_value), decimals)
                    matched = (gui_rounded == excel_rounded)
                except (ValueError, TypeError):
                    pass

            if not matched:
                all_inputs_match = False

            recon_data.append({
                "label": label,
                "cell": cell,
                "gui_value": gui_value,
                "excel_value": excel_value,
                "decimals": decimals,
                "matched": matched,
                "is_input": True
            })

        # Output fields (only check if all inputs match)
        output_fields = [
            ("EUR Implied", "EUR_IMPLIED", "eur_impl", 4),
            ("USD Implied", "USD_IMPLIED", "usd_impl", 4),
        ]

        for label, mapping_key, data_key, decimals in output_fields:
            cell = RECON_CELL_MAPPING.get(mapping_key, {}).get(tenor_key)
            if not cell:
                continue

            gui_value = data.get(data_key)
            excel_value = read_excel_cell(cell) if all_inputs_match else None

            # Compare values (only if inputs matched)
            matched = False
            skipped = not all_inputs_match
            if not skipped and gui_value is not None and excel_value is not None:
                try:
                    gui_rounded = round(float(gui_value), decimals)
                    excel_rounded = round(float(excel_value), decimals)
                    matched = (gui_rounded == excel_rounded)
                except (ValueError, TypeError):
                    pass

            recon_data.append({
                "label": label,
                "cell": cell,
                "gui_value": gui_value,
                "excel_value": excel_value,
                "decimals": decimals,
                "matched": matched,
                "is_input": False,
                "skipped": skipped
            })

        data_with_match['recon_data'] = recon_data
        data_with_match['all_inputs_match'] = all_inputs_match

        # Show drawer in a separate window positioned next to main window
        root = self.winfo_toplevel()
        root.update_idletasks()

        drawer_width = 450
        drawer_height = root.winfo_height()

        # Position drawer window to the right of main window
        main_x = root.winfo_x()
        main_y = root.winfo_y()
        main_width = root.winfo_width()
        drawer_x = main_x + main_width + 2  # 2px gap

        # Create or reuse drawer window
        if not self._drawer_window or not self._drawer_window.winfo_exists():
            self._drawer_window = tk.Toplevel(root)
            self._drawer_window.title("")
            self._drawer_window.configure(bg=THEME["bg_card"])
            self._drawer_window.resizable(False, True)
            self._drawer_window.protocol("WM_DELETE_WINDOW", self._on_drawer_close)

            # Create the drawer widget in this window
            self._drawer = CalculationDrawer(
                self._drawer_window,
                width=drawer_width,
                on_close=self._on_drawer_close,
                on_rerun=self._on_drawer_rerun
            )
            self._drawer.pack(fill="both", expand=True)

            # Bind main window move/resize to update drawer position
            root.bind("<Configure>", self._on_main_window_configure, add="+")

        # Position and size the drawer window
        self._drawer_window.geometry(f"{drawer_width}x{drawer_height}+{drawer_x}+{main_y}")
        self._drawer_window.deiconify()
        self._drawer_window.lift()

        self._drawer.show_for_tenor(tenor_key, data_with_match)
        log.info(f"[Dashboard] Opened drawer for tenor: {tenor_key}")


