"""
Page classes for Nibor Calculation Terminal.
Contains all specific page views.
CustomTkinter Edition - Modern UI with rounded corners.
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

# Use CTk frame as base if available
BaseFrame = ctk.CTkFrame if CTK_AVAILABLE else tk.Frame


class ToolTip:
    """Tooltip that follows cursor and stays visible while hovering."""
    def __init__(self, widget, text_func, delay=400):
        self.widget = widget
        self.text_func = text_func
        self.tooltip_window = None
        self._show_id = None
        self._delay = delay
        self._mouse_over = False
        # Use add="+" to not replace existing bindings
        widget.bind("<Enter>", self._on_enter, add="+")
        widget.bind("<Leave>", self._on_leave, add="+")
        widget.bind("<Motion>", self._on_motion, add="+")

    def _on_enter(self, event=None):
        """Mouse entered widget."""
        self._mouse_over = True
        self._schedule_show()

    def _on_leave(self, event=None):
        """Mouse left widget - check if really left."""
        self._mouse_over = False
        # Small delay before hiding to handle flicker
        self.widget.after(50, self._check_and_hide)

    def _on_motion(self, event=None):
        """Mouse moving over widget - update tooltip position."""
        if self.tooltip_window:
            x = self.widget.winfo_rootx() + event.x + 15
            y = self.widget.winfo_rooty() + event.y + 15
            self.tooltip_window.wm_geometry(f"+{x}+{y}")

    def _schedule_show(self):
        """Schedule tooltip to show after delay."""
        self._cancel_scheduled()
        self._show_id = self.widget.after(self._delay, self._do_show)

    def _cancel_scheduled(self):
        """Cancel any scheduled show."""
        if self._show_id:
            self.widget.after_cancel(self._show_id)
            self._show_id = None

    def _check_and_hide(self):
        """Hide only if mouse is really not over widget."""
        if not self._mouse_over:
            self._cancel_scheduled()
            self._do_hide()

    def _do_show(self):
        """Actually show the tooltip."""
        self._show_id = None
        if not self._mouse_over:
            return
        try:
            text = self.text_func()
        except Exception:
            text = None
        if text and self.tooltip_window is None:
            # Position near cursor
            try:
                x = self.widget.winfo_pointerx() + 15
                y = self.widget.winfo_pointery() + 15
            except Exception:
                x = self.widget.winfo_rootx() + 20
                y = self.widget.winfo_rooty() + 20
            self.tooltip_window = tk.Toplevel(self.widget)
            self.tooltip_window.wm_overrideredirect(True)
            self.tooltip_window.wm_geometry(f"+{x}+{y}")
            # Make tooltip non-interactive so it doesn't steal focus
            self.tooltip_window.wm_attributes("-topmost", True)
            label = tk.Label(
                self.tooltip_window,
                text=text,
                background=THEME["bg_card"],
                foreground=THEME["accent"],
                relief="solid",
                borderwidth=1,
                font=("Consolas", 10, "bold"),
                padx=8,
                pady=4
            )
            label.pack()

    def _do_hide(self):
        """Actually hide the tooltip."""
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None


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
            tk.Label(funding_frame, text=text,
                    fg=THEME["text"],  # Mörkare text för bättre kontrast
                    bg=header_bg,
                    font=("Segoe UI Semibold", 11),  # Något större font
                    width=width, pady=12, padx=18,  # Mer padding
                    anchor=anchor).grid(row=0, column=col, sticky="nsew")

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
            tk.Label(self._1w_row_frame, text=val,
                    fg=THEME["text_light"], bg=row_bg,
                    font=("Consolas", 12),
                    anchor="center", pady=14, padx=16
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

            # NIBOR - HERO COLUMN - EXTRA LARGE, bold, accent color, centered
            final_lbl = tk.Label(funding_frame, text="—",
                                fg=THEME["accent"], bg=row_bg,
                                font=("Consolas", 18, "bold"),
                                width=20, anchor="center", cursor="hand2", pady=14, padx=20)
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
                        if isinstance(w, tk.Label) or isinstance(w, tk.Frame):
                            w.config(bg=hbg)
                return handler

            def make_hover_leave(widgets, rbg, pill_bg):
                def handler(e):
                    for w in widgets:
                        if w == pill_container:
                            w.config(bg=rbg)
                        elif isinstance(w, tk.Label) or isinstance(w, tk.Frame):
                            w.config(bg=rbg)
                return handler

            for w in row_widgets:
                w.bind("<Enter>", make_hover_enter(row_widgets, hover_bg), add="+")
                w.bind("<Leave>", make_hover_leave(row_widgets, row_bg, THEME["chip"]), add="+")

            # Subtle row separator
            tk.Frame(funding_frame, bg=row_separator_color, height=1).grid(row=row_idx+1, column=0, columnspan=7, sticky="ew")

            cells["excel_row"] = tenor["excel_row"]
            cells["excel_col"] = tenor["excel_col"]

            self.funding_cells[tenor["key"]] = cells

        # ====================================================================
        # VALIDATION CHECKS BAR - 6 check categories with ✔/✖ status
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

            # Status icon (✔ or ✖)
            status_icon = tk.Label(badge_frame, text="—",
                                   fg=THEME["text_muted"],
                                   bg=THEME["chip"],
                                   font=("Segoe UI", 13))
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
                    check = self.validation_checks[check_id]
                    if check["status"] is True:
                        bg = "#E8F5E9"
                    elif check["status"] is False:
                        bg = "#FFEBEE"
                    else:
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

        # Summary on right side
        self.validation_summary_lbl = tk.Label(checks_bar, text="",
                                               fg=THEME["text_muted"],
                                               bg=THEME["bg_card"],
                                               font=("Segoe UI", 10))
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
        dev_mode = settings.get("development_mode", True)

        # Container frame
        mode_frame = ctk.CTkFrame(parent, fg_color="transparent")
        mode_frame.pack(side="left", padx=(30, 0))

        # Mode indicator/button - cleaner design
        mode_text = "Dev" if dev_mode else "Prod"
        mode_color = THEME["warning"] if dev_mode else THEME["good"]  # Orange for Dev, Green for Prod

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
        dev_mode = settings.get("development_mode", True)

        # Container frame
        mode_frame = tk.Frame(parent, bg=THEME["bg_panel"])
        mode_frame.pack(side="left", padx=(30, 0))

        # Mode indicator/button - cleaner pill design
        mode_text = "Dev" if dev_mode else "Prod"
        mode_color = THEME["warning"] if dev_mode else THEME["good"]  # Orange for Dev, Green for Prod

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
        current_mode = settings.get("development_mode", True)
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
        dev_mode = settings.get("development_mode", True)

        mode_text = "Dev" if dev_mode else "Prod"
        mode_color = THEME["warning"] if dev_mode else THEME["good"]  # Orange for Dev, Green for Prod

        if hasattr(self, '_mode_btn'):
            if CTK_AVAILABLE and isinstance(self._mode_btn, ctk.CTkButton):
                self._mode_btn.configure(text=mode_text, fg_color=mode_color)
            else:
                self._mode_btn.config(text=f"  {mode_text}  ", bg=mode_color)

    def _create_mode_badge(self, parent):
        """Create compact Dev/Prod pill badge in card header (Nordic Light style)."""
        from settings import get_settings
        settings = get_settings()
        dev_mode = settings.get("development_mode", True)

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
            status_icon = "✔"
            status_text = "ALL CHECKS PASSED"
            status_color = THEME["success"]
            header_bg = "#E8F5E9"
        elif status is False:
            status_icon = "✖"
            status_text = "VALIDATION FAILED"
            status_color = THEME["danger"]
            header_bg = "#FFEBEE"
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

        # Professional colors
        FAIL_HEADER_BG = "#F5F5F5"
        FAIL_HEADER_FG = "#B71C1C"
        FAIL_BORDER = "#E0E0E0"
        PASS_HEADER_BG = "#F5F5F5"
        PASS_HEADER_FG = "#1B5E20"
        PASS_BORDER = "#E0E0E0"

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
                    fg="#B71C1C", bg=THEME["bg_card"]).pack(side="left", padx=(20, 0))

        tk.Label(summary_inner,
                text=f"{total_passed} passed",
                font=("Segoe UI", 11),
                fg="#1B5E20", bg=THEME["bg_card"]).pack(side="left", padx=(20, 0))

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
            status_color = "#1B5E20" if matched else "#B71C1C"
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
            cmp_color = "#1B5E20" if matched else "#B71C1C"
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
                    fg="#B71C1C", bg=row_bg, width=COL_WIDTHS[7], anchor="center").pack(side="left", padx=2, pady=3)

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
                    fg="#1B5E20", bg=THEME["bg_panel"]).pack(pady=20)

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

        # Professional muted colors
        FAIL_HEADER_BG = "#F5F5F5"      # Light gray
        FAIL_HEADER_FG = "#B71C1C"      # Dark red
        FAIL_BORDER = "#E0E0E0"         # Gray border
        PASS_HEADER_BG = "#F5F5F5"      # Light gray
        PASS_HEADER_FG = "#1B5E20"      # Dark green
        PASS_BORDER = "#E0E0E0"         # Gray border

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
                    fg="#B71C1C", bg=THEME["bg_card"]).pack(side="left", padx=(20, 0))

        tk.Label(summary_inner,
                text=f"{total_passed} passed",
                font=("Segoe UI", 11),
                fg="#1B5E20", bg=THEME["bg_card"]).pack(side="left", padx=(20, 0))

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
            status_color = "#1B5E20" if matched else "#B71C1C"
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
            cmp_color = "#1B5E20" if matched else "#B71C1C"
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
                    fg="#B71C1C", bg=row_bg, width=COL_WIDTHS[7], anchor="center").pack(side="left", padx=2, pady=3)

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

        # Professional colors
        FAIL_HEADER_BG = "#F5F5F5"
        FAIL_HEADER_FG = "#B71C1C"
        FAIL_BORDER = "#E0E0E0"
        PASS_HEADER_BG = "#F5F5F5"
        PASS_HEADER_FG = "#1B5E20"
        PASS_BORDER = "#E0E0E0"

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
                    fg="#B71C1C", bg=THEME["bg_card"]).pack(side="left", padx=(16, 0))

        tk.Label(summary_inner,
                text=f"{len(cell_passed)} passed",
                font=("Segoe UI", 10),
                fg="#1B5E20", bg=THEME["bg_card"]).pack(side="left", padx=(16, 0))

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
            status_color = "#1B5E20" if matched else "#B71C1C"
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
            cmp_color = "#1B5E20" if matched else "#B71C1C"
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
                    fg="#B71C1C", bg=row_bg, width=COL_WIDTHS[7], anchor="center").pack(side="left", padx=2, pady=3)

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
            # Green success
            icon.config(text="✔", fg=THEME["success"])
            label.config(fg=THEME["success"])
            bg = "#E8F5E9"
        elif status is False:
            # Red failure
            icon.config(text="✖", fg=THEME["danger"])
            label.config(fg=THEME["danger"])
            bg = "#FFEBEE"
        else:
            # Pending
            icon.config(text="—", fg=THEME["text_muted"])
            label.config(fg=THEME["text_muted"])
            bg = THEME["chip"]

        frame.config(bg=bg)
        icon.config(bg=bg)
        label.config(bg=bg)

        # Update summary
        self._update_validation_summary()

    def _update_validation_summary(self):
        """Update the validation summary label."""
        total = len(self.validation_checks)
        ok_count = sum(1 for c in self.validation_checks.values() if c["status"] is True)
        failed_count = sum(1 for c in self.validation_checks.values() if c["status"] is False)

        if failed_count > 0:
            self.validation_summary_lbl.config(
                text=f"{failed_count} failed",
                fg=THEME["danger"]
            )
        elif ok_count == total:
            self.validation_summary_lbl.config(
                text=f"All OK",
                fg=THEME["success"]
            )
        else:
            self.validation_summary_lbl.config(
                text=f"{ok_count}/{total}",
                fg=THEME["text_muted"]
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

        status_color = THEME["good"] if data.get('all_matched') else THEME["bad"]
        status_text = "✔ ALL MATCHED" if data.get('all_matched') else "✖ MISMATCH FOUND"

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
            status_icon = "✔" if match_status else "✖"
            status_fg = THEME["good"] if match_status else THEME["bad"]

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
            except:
                pass
            self._compact_drawer = None

        # Get calculation data
        if not hasattr(self.app, 'funding_calc_data') or not self.app.funding_calc_data.get(tenor_key):
            self._update_funding_rates_with_validation()

        data = self.app.funding_calc_data.get(tenor_key, {})
        if not data:
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
            card._icon.configure(text="●", fg=THEME["good"])
            card._status.configure(text="OK", fg=THEME["good"])
            card.configure(highlightbackground=THEME["good"])
        elif s == "PENDING":
            card._icon.configure(text="●", fg=THEME["yellow"])
            card._status.configure(text="PENDING", fg=THEME["yellow"])
            card.configure(highlightbackground=THEME["yellow"])
        elif s == "ALERT":
            card._icon.configure(text="●", fg=THEME["warn"])
            card._status.configure(text="ALERT", fg=THEME["warn"])
            card.configure(highlightbackground=THEME["warn"])
        elif s == "FAIL":
            card._icon.configure(text="●", fg=THEME["bad"])
            card._status.configure(text="ERROR", fg=THEME["bad"])
            card.configure(highlightbackground=THEME["bad"])
        else:
            card._icon.configure(text="●", fg=THEME["muted2"])
            card._status.configure(text="WAITING...", fg=THEME["text"])
            card.configure(highlightbackground=THEME["border"])

        card._sub.configure(text=subtext)

    def update(self):
        """Update all dashboard elements."""
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
        for tenor_key in ["1m", "2m", "3m", "6m"]:
            cells = self.funding_cells.get(tenor_key, {})
            if loading:
                # Set all values to "--" with muted color
                for key in ["funding", "spread", "final", "chg", "nibor_contrib"]:
                    lbl = cells.get(key)
                    if lbl:
                        lbl.configure(text="--", fg=COLORS.TEXT_MUTED)
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
                icon = "✔"
                text_color = THEME["good"]  # Green
                bg_color = "#DCFCE7"    # Light green bg
            else:
                icon = "✖"
                text_color = THEME["bad"]  # Red
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
        color = THEME["good"] if ok_count == total else (
            THEME["warning"] if ok_count > total // 2 else THEME["bad"]
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
                text="● ALL OK",
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
                cells["final"].config(text=f"{final_rate:.2f}%" if final_rate else "N/A")

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
                except:
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

                if all_matched and match_details['criteria']:
                    # Matched - Green pill with checkmark icon (Nordic Light)
                    matched_bg = "#E8F5E9"  # Light green bg
                    matched_fg = THEME["success"]  # #1E8E3E
                    if is_ctk_widget:
                        badge.configure(fg_color=matched_bg)
                        lbl.configure(text="✔ Matched", text_color=matched_fg)
                    else:
                        lbl.config(text="✔ Matched", fg=matched_fg, bg=matched_bg,
                                  font=("Segoe UI", 12), padx=14, pady=5)
                        if badge:
                            badge.config(bg=matched_bg)
                    self._stop_blink(lbl)
                elif errors:
                    # Failed - Red pill with cross icon (Nordic Light)
                    failed_bg = "#FFEBEE"  # Light red bg
                    failed_fg = THEME["danger"]  # #D93025
                    if is_ctk_widget:
                        badge.configure(fg_color=failed_bg)
                        lbl.configure(text="✖ Failed", text_color=failed_fg)
                    else:
                        lbl.config(text="✖ Failed", fg=failed_fg, bg=failed_bg,
                                  font=("Segoe UI", 12), padx=14, pady=5)
                        if badge:
                            badge.config(bg=failed_bg)
                    self._start_blink(lbl)
                    for err in errors:
                        alert_messages.append(f"{tenor_key.upper()} Contrib: {err}")
                else:
                    # Pending - Neutral pill with dash
                    pending_bg = THEME["chip"]
                    pending_fg = THEME["text_muted"]
                    if is_ctk_widget:
                        badge.configure(fg_color=pending_bg)
                        lbl.configure(text="—", text_color=pending_fg)
                    else:
                        lbl.config(text="—", fg=pending_fg, bg=pending_bg,
                                  font=("Segoe UI", 12), padx=14, pady=5)
                        if badge:
                            badge.config(bg=pending_bg)
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
                    except (ValueError, TypeError):
                        pass

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
        """Get previous NIBOR rate and date for CHG tooltip (from Excel second-to-last sheet)."""
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

        # Auto-update if data not available
        if not hasattr(self.app, 'funding_calc_data') or not self.app.funding_calc_data.get(tenor_key):
            self._update_funding_rates_with_validation()

        data = self.app.funding_calc_data.get(tenor_key)
        if not data:
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

        # Failures only checkbox
        self.failures_only_var = tk.BooleanVar(value=True)
        self.failures_only_chk = ttk.Checkbutton(
            top, text="Failures only",
            variable=self.failures_only_var,
            command=self._on_filter_change
        )
        self.failures_only_chk.pack(side="right", padx=(0, 12))

        # Search field
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(
            top, textvariable=self.search_var,
            bg=THEME["bg_card"], fg=THEME["text"],
            insertbackground=THEME["text"],
            relief="flat", highlightthickness=1,
            highlightbackground=THEME["border"],
            highlightcolor=THEME["accent"],
            font=("Segoe UI", CURRENT_MODE["body"]),
            width=20
        )
        self.search_entry.pack(side="right", padx=(0, 12))
        tk.Label(top, text="Search:", fg=THEME["muted"], bg=THEME["bg_panel"],
                 font=("Segoe UI", CURRENT_MODE["body"])).pack(side="right", padx=(0, 4))

        # Debounce for search
        self._search_after_id = None
        self.search_var.trace_add("write", lambda *_: self._debounced_update())

        self.table = DataTableTree(self, columns=["CELL", "DESC", "MODEL", "MARKET/FILE", "DIFF", "STATUS"],
                                   col_widths=[110, 330, 170, 170, 140, 90], height=20)
        self.table.pack(fill="both", expand=True, padx=pad, pady=(0, pad))

    def _on_filter_change(self):
        """Handle filter checkbox change."""
        self.update()

    def _debounced_update(self):
        """Debounce search input to avoid excessive updates."""
        if self._search_after_id:
            self.after_cancel(self._search_after_id)
        self._search_after_id = self.after(200, self.update)

    def _matches_search(self, row: dict, query: str) -> bool:
        """Check if row matches search query (cell name or description)."""
        if row.get("style") == "section":
            return True  # Always show section headers
        values = row.get("values", [])
        # Search in CELL and DESC columns (first two)
        return any(query in str(v).lower() for v in values[:2])

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

        # Apply failures-only filter (in ALL mode when checkbox is checked)
        if self.failures_only_var.get() and self.app.recon_view_mode == "ALL":
            rows = [r for r in rows if r.get("style") in ("bad", "warn", "section")]

        # Apply search filter
        search_q = self.search_var.get().strip().lower()
        if search_q:
            rows = [r for r in rows if self._matches_search(r, search_q)]

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


class BackupNiborPage(tk.Frame):
    """Manual NIBOR calculation page - clean professional layout."""

    TENORS = ["1M", "2M", "3M", "6M"]

    def __init__(self, master, app):
        super().__init__(master, bg=THEME["bg_panel"])
        self.app = app
        self._all_entries = {}
        self._result_labels = {}
        self._calc_btn = None
        self._weight_warning = None

        self._build_ui()

    def _build_ui(self):
        """Build the calculator UI."""
        pad = 16

        # ================================================================
        # HEADER
        # ================================================================
        header = tk.Frame(self, bg=THEME["bg_panel"])
        header.pack(fill="x", padx=pad, pady=(pad, 12))

        tk.Label(header, text="BACKUP NIBOR CALCULATOR", fg=THEME["text"], bg=THEME["bg_panel"],
                 font=("Segoe UI", CURRENT_MODE["h2"], "bold")).pack(side="left")

        # ================================================================
        # TOP ROW: SPOTS + WEIGHTS
        # ================================================================
        top_row = tk.Frame(self, bg=THEME["bg_card"])
        top_row.pack(fill="x", padx=pad, pady=(0, 12))

        top_content = tk.Frame(top_row, bg=THEME["bg_card"])
        top_content.pack(fill="x", padx=20, pady=16)

        # SPOTS section
        spots_frame = tk.Frame(top_content, bg=THEME["bg_card"])
        spots_frame.pack(side="left")

        tk.Label(spots_frame, text="SPOTS", fg=THEME["accent"], bg=THEME["bg_card"],
                 font=("Segoe UI Semibold", 11)).pack(anchor="w")

        spots_row = tk.Frame(spots_frame, bg=THEME["bg_card"])
        spots_row.pack(anchor="w", pady=(8, 0))

        tk.Label(spots_row, text="EURNOK", fg=THEME["text"], bg=THEME["bg_card"],
                 font=("Segoe UI", 10)).pack(side="left")
        eur_spot = tk.Entry(spots_row, width=10, font=("Consolas", 12), bg=THEME["bg_card_2"],
                           fg=THEME["text"], insertbackground=THEME["text"], relief="flat")
        eur_spot.pack(side="left", padx=(8, 20), ipady=4)
        self._all_entries["eur_spot"] = eur_spot

        tk.Label(spots_row, text="USDNOK", fg=THEME["text"], bg=THEME["bg_card"],
                 font=("Segoe UI", 10)).pack(side="left")
        usd_spot = tk.Entry(spots_row, width=10, font=("Consolas", 12), bg=THEME["bg_card_2"],
                           fg=THEME["text"], insertbackground=THEME["text"], relief="flat")
        usd_spot.pack(side="left", padx=(8, 0), ipady=4)
        self._all_entries["usd_spot"] = usd_spot

        # Separator
        tk.Frame(top_content, bg=THEME["border"], width=1).pack(side="left", fill="y", padx=30)

        # WEIGHTS section
        weights_frame = tk.Frame(top_content, bg=THEME["bg_card"])
        weights_frame.pack(side="left")

        weights_header = tk.Frame(weights_frame, bg=THEME["bg_card"])
        weights_header.pack(anchor="w")

        tk.Label(weights_header, text="WEIGHTS", fg=THEME["accent"], bg=THEME["bg_card"],
                 font=("Segoe UI Semibold", 11)).pack(side="left")

        self._weight_warning = tk.Label(weights_header, text="", fg=THEME["bad"], bg=THEME["bg_card"],
                                        font=("Segoe UI", 9))
        self._weight_warning.pack(side="left", padx=(12, 0))

        weights_row = tk.Frame(weights_frame, bg=THEME["bg_card"])
        weights_row.pack(anchor="w", pady=(8, 0))

        tk.Label(weights_row, text="EUR", fg=THEME["text"], bg=THEME["bg_card"],
                 font=("Segoe UI", 10)).pack(side="left")
        eur_weight = tk.Entry(weights_row, width=5, font=("Consolas", 12), bg=THEME["bg_card_2"],
                             fg=THEME["text"], insertbackground=THEME["text"], relief="flat")
        eur_weight.pack(side="left", padx=(4, 0), ipady=4)
        tk.Label(weights_row, text="%", fg=THEME["text_muted"], bg=THEME["bg_card"],
                 font=("Segoe UI", 10)).pack(side="left", padx=(2, 16))
        self._all_entries["eur_weight"] = eur_weight

        tk.Label(weights_row, text="USD", fg=THEME["text"], bg=THEME["bg_card"],
                 font=("Segoe UI", 10)).pack(side="left")
        usd_weight = tk.Entry(weights_row, width=5, font=("Consolas", 12), bg=THEME["bg_card_2"],
                             fg=THEME["text"], insertbackground=THEME["text"], relief="flat")
        usd_weight.pack(side="left", padx=(4, 0), ipady=4)
        tk.Label(weights_row, text="%", fg=THEME["text_muted"], bg=THEME["bg_card"],
                 font=("Segoe UI", 10)).pack(side="left", padx=(2, 16))
        self._all_entries["usd_weight"] = usd_weight

        tk.Label(weights_row, text="NOK", fg=THEME["text"], bg=THEME["bg_card"],
                 font=("Segoe UI", 10)).pack(side="left")
        tk.Label(weights_row, text="50", fg=THEME["text_muted"], bg=THEME["bg_card"],
                 font=("Consolas", 12)).pack(side="left", padx=(4, 0))
        tk.Label(weights_row, text="% (fixed)", fg=THEME["text_muted"], bg=THEME["bg_card"],
                 font=("Segoe UI", 9)).pack(side="left", padx=(2, 0))

        # Must sum hint
        tk.Label(weights_row, text="Must sum to 100%", fg=THEME["text_muted"], bg=THEME["bg_card"],
                 font=("Segoe UI", 9)).pack(side="left", padx=(20, 0))

        # ================================================================
        # MIDDLE ROW: EUR + USD TABLES SIDE BY SIDE
        # ================================================================
        tables_row = tk.Frame(self, bg=THEME["bg_panel"])
        tables_row.pack(fill="both", expand=True, padx=pad, pady=(0, 12))

        tables_row.columnconfigure(0, weight=1, uniform="tables")
        tables_row.columnconfigure(1, weight=1, uniform="tables")

        # EUR TABLE
        eur_card = tk.Frame(tables_row, bg=THEME["bg_card"])
        eur_card.grid(row=0, column=0, sticky="nsew", padx=(0, 6))

        # EUR accent bar
        tk.Frame(eur_card, bg=THEME["accent"], height=4).pack(fill="x")

        eur_content = tk.Frame(eur_card, bg=THEME["bg_card"])
        eur_content.pack(fill="both", expand=True, padx=16, pady=12)

        tk.Label(eur_content, text="EUR", fg=THEME["accent"], bg=THEME["bg_card"],
                 font=("Segoe UI Semibold", 14)).pack(anchor="w")

        # EUR header row
        eur_hdr = tk.Frame(eur_content, bg=THEME["bg_card"])
        eur_hdr.pack(fill="x", pady=(12, 4))
        for txt, w in [("Tenor", 6), ("Days", 8), ("Pips", 10), ("Rate %", 10)]:
            tk.Label(eur_hdr, text=txt, fg=THEME["text_muted"], bg=THEME["bg_card"],
                     font=("Segoe UI", 9), width=w, anchor="w").pack(side="left", padx=2)

        # EUR tenor rows
        for tenor in self.TENORS:
            row = tk.Frame(eur_content, bg=THEME["bg_card"])
            row.pack(fill="x", pady=3)

            tk.Label(row, text=tenor, fg=THEME["text"], bg=THEME["bg_card"],
                     font=("Segoe UI Semibold", 11), width=6, anchor="w").pack(side="left", padx=2)

            days_e = tk.Entry(row, width=6, font=("Consolas", 11), bg=THEME["bg_card_2"],
                             fg=THEME["text"], insertbackground=THEME["text"], relief="flat")
            days_e.pack(side="left", padx=2, ipady=3)
            self._all_entries[f"eur_{tenor}_days"] = days_e

            pips_e = tk.Entry(row, width=8, font=("Consolas", 11), bg=THEME["bg_card_2"],
                             fg=THEME["text"], insertbackground=THEME["text"], relief="flat")
            pips_e.pack(side="left", padx=2, ipady=3)
            self._all_entries[f"eur_{tenor}_pips"] = pips_e

            rate_e = tk.Entry(row, width=8, font=("Consolas", 11), bg=THEME["bg_card_2"],
                             fg=THEME["text"], insertbackground=THEME["text"], relief="flat")
            rate_e.pack(side="left", padx=2, ipady=3)
            self._all_entries[f"eur_{tenor}_rate"] = rate_e

        # USD TABLE
        usd_card = tk.Frame(tables_row, bg=THEME["bg_card"])
        usd_card.grid(row=0, column=1, sticky="nsew", padx=(6, 0))

        # USD accent bar (different shade)
        tk.Frame(usd_card, bg="#4A90D9", height=4).pack(fill="x")

        usd_content = tk.Frame(usd_card, bg=THEME["bg_card"])
        usd_content.pack(fill="both", expand=True, padx=16, pady=12)

        tk.Label(usd_content, text="USD", fg="#4A90D9", bg=THEME["bg_card"],
                 font=("Segoe UI Semibold", 14)).pack(anchor="w")

        # USD header row
        usd_hdr = tk.Frame(usd_content, bg=THEME["bg_card"])
        usd_hdr.pack(fill="x", pady=(12, 4))
        for txt, w in [("Tenor", 6), ("Days", 8), ("Pips", 10), ("Rate %", 10)]:
            tk.Label(usd_hdr, text=txt, fg=THEME["text_muted"], bg=THEME["bg_card"],
                     font=("Segoe UI", 9), width=w, anchor="w").pack(side="left", padx=2)

        # USD tenor rows
        for tenor in self.TENORS:
            row = tk.Frame(usd_content, bg=THEME["bg_card"])
            row.pack(fill="x", pady=3)

            tk.Label(row, text=tenor, fg=THEME["text"], bg=THEME["bg_card"],
                     font=("Segoe UI Semibold", 11), width=6, anchor="w").pack(side="left", padx=2)

            days_e = tk.Entry(row, width=6, font=("Consolas", 11), bg=THEME["bg_card_2"],
                             fg=THEME["text"], insertbackground=THEME["text"], relief="flat")
            days_e.pack(side="left", padx=2, ipady=3)
            self._all_entries[f"usd_{tenor}_days"] = days_e

            pips_e = tk.Entry(row, width=8, font=("Consolas", 11), bg=THEME["bg_card_2"],
                             fg=THEME["text"], insertbackground=THEME["text"], relief="flat")
            pips_e.pack(side="left", padx=2, ipady=3)
            self._all_entries[f"usd_{tenor}_pips"] = pips_e

            rate_e = tk.Entry(row, width=8, font=("Consolas", 11), bg=THEME["bg_card_2"],
                             fg=THEME["text"], insertbackground=THEME["text"], relief="flat")
            rate_e.pack(side="left", padx=2, ipady=3)
            self._all_entries[f"usd_{tenor}_rate"] = rate_e

        # ================================================================
        # BOTTOM ROW: NOK + RESULTS
        # ================================================================
        bottom_row = tk.Frame(self, bg=THEME["bg_panel"])
        bottom_row.pack(fill="x", padx=pad, pady=(0, pad))

        bottom_row.columnconfigure(0, weight=1)
        bottom_row.columnconfigure(1, weight=2)

        # NOK (ECP) Card
        nok_card = tk.Frame(bottom_row, bg=THEME["bg_card"])
        nok_card.grid(row=0, column=0, sticky="nsew", padx=(0, 6))

        tk.Frame(nok_card, bg="#2ECC71", height=4).pack(fill="x")

        nok_content = tk.Frame(nok_card, bg=THEME["bg_card"])
        nok_content.pack(fill="both", expand=True, padx=16, pady=12)

        tk.Label(nok_content, text="NOK (ECP)", fg="#2ECC71", bg=THEME["bg_card"],
                 font=("Segoe UI Semibold", 14)).pack(anchor="w")

        nok_row = tk.Frame(nok_content, bg=THEME["bg_card"])
        nok_row.pack(fill="x", pady=(12, 0))

        for tenor in self.TENORS:
            tenor_frame = tk.Frame(nok_row, bg=THEME["bg_card"])
            tenor_frame.pack(side="left", padx=(0, 16))

            tk.Label(tenor_frame, text=tenor, fg=THEME["text_muted"], bg=THEME["bg_card"],
                     font=("Segoe UI", 9)).pack(anchor="w")
            nok_e = tk.Entry(tenor_frame, width=7, font=("Consolas", 11), bg=THEME["bg_card_2"],
                            fg=THEME["text"], insertbackground=THEME["text"], relief="flat")
            nok_e.pack(ipady=3)
            self._all_entries[f"nok_{tenor}_rate"] = nok_e

        # RESULTS Card
        results_card = tk.Frame(bottom_row, bg=THEME["bg_card"])
        results_card.grid(row=0, column=1, sticky="nsew", padx=(6, 0))

        tk.Frame(results_card, bg=THEME["accent"], height=4).pack(fill="x")

        results_content = tk.Frame(results_card, bg=THEME["bg_card"])
        results_content.pack(fill="both", expand=True, padx=16, pady=12)

        results_header = tk.Frame(results_content, bg=THEME["bg_card"])
        results_header.pack(fill="x")

        tk.Label(results_header, text="NIBOR RESULT", fg=THEME["accent"], bg=THEME["bg_card"],
                 font=("Segoe UI Semibold", 14)).pack(side="left")

        # Buttons
        btn_frame = tk.Frame(results_header, bg=THEME["bg_card"])
        btn_frame.pack(side="right")

        if CTK_AVAILABLE:
            self._calc_btn = ctk.CTkButton(btn_frame, text="CALCULATE", command=self._calculate,
                                          fg_color=THEME["bg_card_2"], text_color=THEME["text_muted"],
                                          font=("Segoe UI Semibold", 11), height=32, width=100,
                                          corner_radius=6, state="disabled")
            self._calc_btn.pack(side="left")

            ctk.CTkButton(btn_frame, text="CLEAR", command=self._clear_all,
                         fg_color="transparent", text_color=THEME["text_muted"],
                         font=("Segoe UI", 10), height=32, width=60,
                         corner_radius=6, border_width=1,
                         border_color=THEME["border"]).pack(side="left", padx=(8, 0))

        # Results row
        results_row = tk.Frame(results_content, bg=THEME["bg_card"])
        results_row.pack(fill="x", pady=(16, 0))

        for tenor in self.TENORS:
            tenor_frame = tk.Frame(results_row, bg=THEME["bg_card"])
            tenor_frame.pack(side="left", padx=(0, 24))

            tk.Label(tenor_frame, text=tenor, fg=THEME["text_muted"], bg=THEME["bg_card"],
                     font=("Segoe UI", 10)).pack(anchor="w")
            lbl = tk.Label(tenor_frame, text="—", fg=THEME["text"], bg=THEME["bg_card"],
                          font=("Consolas", 18, "bold"))
            lbl.pack(anchor="w")
            self._result_labels[tenor] = lbl

        # Bind validation to all entries
        for entry in self._all_entries.values():
            entry.bind("<KeyRelease>", self._validate_inputs)

    def _validate_inputs(self, event=None):
        """Check if all inputs are filled and validate weights."""
        all_filled = True

        # Check all entries have values
        for key, entry in self._all_entries.items():
            val = entry.get().strip()
            if not val:
                all_filled = False
                break
            # Check it's a valid number
            try:
                float(val.replace(",", "."))
            except ValueError:
                all_filled = False
                break

        # Validate weights sum to 100%
        weight_valid = False
        try:
            eur_w = float(self._all_entries["eur_weight"].get().replace(",", "."))
            usd_w = float(self._all_entries["usd_weight"].get().replace(",", "."))
            total = eur_w + usd_w + 50  # NOK is fixed at 50
            weight_valid = abs(total - 100) < 0.01

            if not weight_valid and (eur_w > 0 or usd_w > 0):
                self._weight_warning.configure(text=f"⚠ Sum = {total:.0f}%")
            else:
                self._weight_warning.configure(text="")
        except (ValueError, KeyError):
            self._weight_warning.configure(text="")

        # Enable/disable calculate button
        if self._calc_btn and CTK_AVAILABLE:
            if all_filled and weight_valid:
                self._calc_btn.configure(fg_color=THEME["accent"], text_color="white",
                                        state="normal")
            else:
                self._calc_btn.configure(fg_color=THEME["bg_card_2"], text_color=THEME["text_muted"],
                                        state="disabled")

    def _calculate(self):
        """Calculate NIBOR rates for all tenors."""
        from calculations import calc_implied_yield, calc_funding_rate

        # Get weights (as decimals)
        try:
            eur_w = float(self._all_entries["eur_weight"].get().replace(",", ".")) / 100
            usd_w = float(self._all_entries["usd_weight"].get().replace(",", ".")) / 100
            nok_w = 0.50
            weights = {"EUR": eur_w, "USD": usd_w, "NOK": nok_w}
        except ValueError:
            return

        # Get spots
        try:
            eur_spot = float(self._all_entries["eur_spot"].get().replace(",", "."))
            usd_spot = float(self._all_entries["usd_spot"].get().replace(",", "."))
        except ValueError:
            return

        # Calculate for each tenor
        for tenor in self.TENORS:
            try:
                # EUR implied
                eur_days = int(self._all_entries[f"eur_{tenor}_days"].get())
                eur_pips = float(self._all_entries[f"eur_{tenor}_pips"].get().replace(",", "."))
                eur_rate = float(self._all_entries[f"eur_{tenor}_rate"].get().replace(",", "."))
                eur_implied = calc_implied_yield(eur_spot, eur_pips, eur_rate, eur_days)

                # USD implied
                usd_days = int(self._all_entries[f"usd_{tenor}_days"].get())
                usd_pips = float(self._all_entries[f"usd_{tenor}_pips"].get().replace(",", "."))
                usd_rate = float(self._all_entries[f"usd_{tenor}_rate"].get().replace(",", "."))
                usd_implied = calc_implied_yield(usd_spot, usd_pips, usd_rate, usd_days)

                # NOK rate
                nok_rate = float(self._all_entries[f"nok_{tenor}_rate"].get().replace(",", "."))

                # Calculate weighted NIBOR
                if eur_implied is not None and usd_implied is not None:
                    nibor_rate = calc_funding_rate(eur_implied, usd_implied, nok_rate, weights)
                    if nibor_rate is not None:
                        self._result_labels[tenor].configure(text=f"{nibor_rate:.4f}%",
                                                            fg=THEME["good"])
                    else:
                        self._result_labels[tenor].configure(text="Error", fg=THEME["bad"])
                else:
                    self._result_labels[tenor].configure(text="Error", fg=THEME["bad"])

            except (ValueError, KeyError) as e:
                log.error(f"Calculation error for {tenor}: {e}")
                self._result_labels[tenor].configure(text="Error", fg=THEME["bad"])

        self.app.toast.success("Calculation complete")

    def _clear_all(self):
        """Clear all input fields."""
        for entry in self._all_entries.values():
            entry.delete(0, tk.END)

        for tenor in self.TENORS:
            self._result_labels[tenor].configure(text="—", fg=THEME["text"])

        self._weight_warning.configure(text="")
        self._validate_inputs()

    def update(self, *_):
        """Called when page is shown."""
        pass


# Alias for backwards compatibility
RulesPage = BackupNiborPage


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

        for group_name, items in get_market_structure().items():
            self.table.add_row([group_name, "", "", "", ""], style="section")
            for ticker, label in items:
                inf = data.get(ticker)
                price = f"{inf['price']:,.6f}" if inf else "-"
                chg = f"{inf['change']:+,.6f}" if inf else "-"
                tms = inf.get("time", "-") if inf else "-"
                self.table.add_row([group_name, label, price, chg, tms], style="normal")


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
            "TENOR", "USD RATE", "BBG DAYS", "EXC DAYS", "PIPS BBG", "PIPS EXC", "IMPLIED", "NOK ECP"
        ], col_widths=[50, 70, 70, 70, 80, 80, 80, 70], height=4)
        self.usd_table_bbg.pack(fill="x", pady=(0, 5))

        # EURNOK Table (Section 1)
        tk.Label(sec1_content, text="EURNOK", fg=THEME["muted"], bg=THEME["bg_panel"],
                 font=("Segoe UI", CURRENT_MODE["small"], "bold")).pack(anchor="w")

        self.eur_table_bbg = DataTableTree(sec1_content, columns=[
            "TENOR", "EUR RATE", "BBG DAYS", "EXC DAYS", "PIPS BBG", "PIPS EXC", "IMPLIED", "NOK ECP"
        ], col_widths=[50, 70, 70, 70, 80, 80, 80, 70], height=4)
        self.eur_table_bbg.pack(fill="x", pady=(0, 5))

        # Weighted (Section 1)
        tk.Label(sec1_content, text="VIKTAD (BBG CM)", fg=THEME["accent"], bg=THEME["bg_panel"],
                 font=("Segoe UI", CURRENT_MODE["small"], "bold")).pack(anchor="w")

        self.weighted_table_bbg = DataTableTree(sec1_content, columns=[
            "TENOR", "USD IMPL", "× 45%", "EUR IMPL", "× 5%", "NOK ECP", "× 50%", "TOTAL"
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
            "TENOR", "USD RATE", "BBG DAYS", "PIPS BBG", "IMPLIED", "NOK ECP"
        ], col_widths=[50, 70, 70, 90, 90, 70], height=4)
        self.usd_table_exc.pack(fill="x", pady=(0, 5))

        # EURNOK Table (Section 2)
        tk.Label(sec2_content, text="EURNOK", fg=THEME["muted"], bg=THEME["bg_panel"],
                 font=("Segoe UI", CURRENT_MODE["small"], "bold")).pack(anchor="w")

        self.eur_table_exc = DataTableTree(sec2_content, columns=[
            "TENOR", "EUR RATE", "BBG DAYS", "PIPS BBG", "IMPLIED", "NOK ECP"
        ], col_widths=[50, 70, 70, 90, 90, 70], height=4)
        self.eur_table_exc.pack(fill="x", pady=(0, 5))

        # Weighted (Section 2)
        tk.Label(sec2_content, text="VIKTAD (EXCEL CM)", fg=THEME["accent"], bg=THEME["bg_panel"],
                 font=("Segoe UI", CURRENT_MODE["small"], "bold")).pack(anchor="w")

        self.weighted_table_exc = DataTableTree(sec2_content, columns=[
            "TENOR", "USD IMPL", "× 45%", "EUR IMPL", "× 5%", "NOK ECP", "× 50%", "TOTAL"
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
        log.debug("========== NOK Implied Page UPDATE STARTED ==========")
        log.debug(f"[NOK Implied Page] cached_excel_data length: {len(self.app.cached_excel_data)}")
        log.debug(f"[NOK Implied Page] cached_market_data length: {len(self.app.cached_market_data or {})}")

        # Check if Excel data is loaded
        if not self.app.cached_excel_data or len(self.app.cached_excel_data) < 10:
            log.debug(f"[NOK Implied Page] Excel data not loaded or insufficient! Skipping update.")
            return

        log.debug(f"[NOK Implied Page] [OK] Excel data loaded with {len(self.app.cached_excel_data)} cells")
        
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
        log.debug(f"[NOK Implied Page] Excel CM rates loaded: {excel_cm}")

        # Spots - use dynamic tickers (F043 for Dev, F033 for Prod)
        usd_spot = self._get_ticker_val(get_ticker("NOK F033 Curncy"))
        eur_spot = self._get_ticker_val(get_ticker("NKEU F033 Curncy"))

        # Excel days from Nibor days file
        excel_days_data = self.app.current_days_data or {}

        # Tenor configuration - use dynamic tickers for forwards
        tenors = [
            {"tenor": "1M", "key": "1m",
             "usd_fwd": get_ticker("NK1M F033 Curncy"), "usd_rate_bbg": "USCM1M SWET Curncy", "usd_days_bbg": "NK1M TPSF Curncy",
             "eur_fwd": get_ticker("NKEU1M F033 Curncy"), "eur_rate_bbg": "EUCM1M SWET Curncy", "eur_days_bbg": "EURNOK1M TPSF Curncy",
             "nok_cm": "NKCM1M SWET Curncy", "usd_rate_exc": "USD_1M", "eur_rate_exc": "EUR_1M"},
            {"tenor": "2M", "key": "2m",
             "usd_fwd": get_ticker("NK2M F033 Curncy"), "usd_rate_bbg": "USCM2M SWET Curncy", "usd_days_bbg": "NK2M TPSF Curncy",
             "eur_fwd": get_ticker("NKEU2M F033 Curncy"), "eur_rate_bbg": "EUCM2M SWET Curncy", "eur_days_bbg": "EURNOK2M TPSF Curncy",
             "nok_cm": "NKCM2M SWET Curncy", "usd_rate_exc": "USD_2M", "eur_rate_exc": "EUR_2M"},
            {"tenor": "3M", "key": "3m",
             "usd_fwd": get_ticker("NK3M F033 Curncy"), "usd_rate_bbg": "USCM3M SWET Curncy", "usd_days_bbg": "NK3M TPSF Curncy",
             "eur_fwd": get_ticker("NKEU3M F033 Curncy"), "eur_rate_bbg": "EUCM3M SWET Curncy", "eur_days_bbg": "EURNOK3M TPSF Curncy",
             "nok_cm": "NKCM3M SWET Curncy", "usd_rate_exc": "USD_3M", "eur_rate_exc": "EUR_3M"},
            {"tenor": "6M", "key": "6m",
             "usd_fwd": get_ticker("NK6M F033 Curncy"), "usd_rate_bbg": "USCM6M SWET Curncy", "usd_days_bbg": "NK6M TPSF Curncy",
             "eur_fwd": get_ticker("NKEU6M F033 Curncy"), "eur_rate_bbg": "EUCM6M SWET Curncy", "eur_days_bbg": "EURNOK6M TPSF Curncy",
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

            # Get pips directly from Bloomberg market data
            pips_bbg_usd = self._get_ticker_val(t["usd_fwd"])
            pips_bbg_eur = self._get_ticker_val(t["eur_fwd"])

            # NOK ECP (same for both sections)
            nok_cm = self._get_ticker_val(t["nok_cm"]) if t["nok_cm"] else None

            # ============ SECTION 1: Bloomberg CM + Bloomberg TPSF Days ============
            usd_rate_bbg = self._get_ticker_val(t["usd_rate_bbg"]) if t["usd_rate_bbg"] else None
            impl_usd_bbg = calc_implied_yield(usd_spot, pips_bbg_usd, usd_rate_bbg, bbg_days_usd) if bbg_days_usd else None

            eur_rate_bbg = self._get_ticker_val(t["eur_rate_bbg"]) if t["eur_rate_bbg"] else None
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
    """Weights page with active weights cards and history table."""

    def __init__(self, master, app):
        super().__init__(master, bg=THEME["bg_panel"])
        self.app = app
        self.pad = CURRENT_MODE["pad"]

        # Header
        header = tk.Frame(self, bg=THEME["bg_panel"])
        header.pack(fill="x", padx=self.pad, pady=(self.pad, 16))

        tk.Label(header, text="CURRENCY WEIGHTS", fg=THEME["text"], bg=THEME["bg_panel"],
                 font=("Segoe UI", CURRENT_MODE["h2"], "bold")).pack(side="left")

        OnyxButtonTK(header, "Refresh", command=self.update, variant="default").pack(side="right")

        # Active weights section - 4 cards in a row
        self.cards_frame = tk.Frame(self, bg=THEME["bg_panel"])
        self.cards_frame.pack(fill="x", padx=self.pad, pady=(0, 12))

        # Configure grid for equal-width columns
        for i in range(4):
            self.cards_frame.columnconfigure(i, weight=1, uniform="weights")

        # Placeholder for cards (will be created in update)
        self._cards = []
        self._create_cards("--", "--", "--", "--", "default")

        # Active date label
        self.active_date_label = tk.Label(self, text="Active from: --", fg=THEME["muted"], bg=THEME["bg_panel"],
                                          font=("Segoe UI", CURRENT_MODE["small"]))
        self.active_date_label.pack(anchor="w", padx=self.pad, pady=(0, 16))

        # History section header
        history_header = tk.Frame(self, bg=THEME["bg_panel"])
        history_header.pack(fill="x", padx=self.pad, pady=(0, 8))

        tk.Label(history_header, text="WEIGHTS HISTORY", fg=THEME["muted"], bg=THEME["bg_panel"],
                 font=("Segoe UI", CURRENT_MODE["body"], "bold")).pack(side="left")

        # Table with weights history
        self.table = DataTableTree(self, columns=["DATE", "USD", "EUR", "NOK", "SUM", "STATUS"],
                                   col_widths=[140, 100, 100, 100, 100, 140], height=14)
        self.table.pack(fill="both", expand=True, padx=self.pad, pady=(0, self.pad))

    def _create_cards(self, usd_val, eur_val, nok_val, total_val, total_variant):
        """Create or recreate the metric cards."""
        # Destroy existing cards
        for card in self._cards:
            card.destroy()
        self._cards = []

        # Create new cards with current values
        usd_card = MetricCard(self.cards_frame, label="USD", value=usd_val, sublabel="US Dollar", variant="accent")
        usd_card.grid(row=0, column=0, padx=(0, 6), sticky="ew")
        self._cards.append(usd_card)

        eur_card = MetricCard(self.cards_frame, label="EUR", value=eur_val, sublabel="Euro", variant="default")
        eur_card.grid(row=0, column=1, padx=6, sticky="ew")
        self._cards.append(eur_card)

        nok_card = MetricCard(self.cards_frame, label="NOK", value=nok_val, sublabel="Norwegian Krone", variant="default")
        nok_card.grid(row=0, column=2, padx=6, sticky="ew")
        self._cards.append(nok_card)

        total_card = MetricCard(self.cards_frame, label="TOTAL", value=total_val, sublabel="Sum of weights", variant=total_variant)
        total_card.grid(row=0, column=3, padx=(6, 0), sticky="ew")
        self._cards.append(total_card)

    def update(self):
        """Update weights cards and table with all historical data."""
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

        # Update active weights cards with latest values
        latest = weights_history[0]

        # Format as percentages for cards
        usd_pct = f"{latest['USD']*100:.1f}%" if latest['USD'] is not None else "--"
        eur_pct = f"{latest['EUR']*100:.1f}%" if latest['EUR'] is not None else "--"
        nok_pct = f"{latest['NOK']*100:.1f}%" if latest['NOK'] is not None else "--"

        try:
            total = latest['USD'] + latest['EUR'] + latest['NOK']
            total_pct = f"{total*100:.1f}%"
            is_valid = abs(total - 1.0) < 0.0001
            total_variant = "success" if is_valid else "danger"
        except (TypeError, ValueError):
            total_pct = "ERROR"
            total_variant = "danger"

        # Recreate cards with new values
        self._create_cards(usd_pct, eur_pct, nok_pct, total_pct, total_variant)

        # Update active date
        date_str = latest["date"].strftime("%Y-%m-%d")
        self.active_date_label.config(text=f"Active from: {date_str}")

        # Display all weights in table (newest first)
        for i, w in enumerate(weights_history):
            date_str = w["date"].strftime("%Y-%m-%d")
            usd_str = f"{w['USD']*100:.2f}%" if w['USD'] is not None else "-"
            eur_str = f"{w['EUR']*100:.2f}%" if w['EUR'] is not None else "-"
            nok_str = f"{w['NOK']*100:.2f}%" if w['NOK'] is not None else "-"

            # Calculate sum
            try:
                total = w['USD'] + w['EUR'] + w['NOK']
                sum_str = f"{total*100:.2f}%"

                # Check if sum is close to 1.0
                is_valid = abs(total - 1.0) < 0.0001
                status = "Valid" if is_valid else "Sum != 100%"
                style = "good" if is_valid else "warn"
            except (TypeError, ValueError):
                sum_str = "ERROR"
                status = "Invalid"
                style = "bad"

            # Mark first row (latest) as active
            if i == 0:
                status = "ACTIVE"
                style = "good"

            self.table.add_row([date_str, usd_str, eur_str, nok_str, sum_str, status], style=style)


class MetaDataPage(tk.Frame):
    """Meta Data page - placeholder for future implementation."""

    def __init__(self, master, app):
        super().__init__(master, bg=THEME["bg_panel"])
        self.app = app
        self._build_ui()

    def _build_ui(self):
        # Header
        header = tk.Frame(self, bg=THEME["bg_panel"])
        header.pack(fill="x", padx=24, pady=(24, 16))

        tk.Label(
            header,
            text="Meta Data",
            font=("Segoe UI Semibold", 24),
            fg=THEME["text"],
            bg=THEME["bg_panel"]
        ).pack(side="left")

        # Placeholder content
        content = tk.Frame(self, bg=THEME["bg_panel"])
        content.pack(fill="both", expand=True, padx=24, pady=16)

        tk.Label(
            content,
            text="Coming soon...",
            font=("Segoe UI", 14),
            fg=THEME["text_muted"],
            bg=THEME["bg_panel"]
        ).pack(pady=40)

    def update(self):
        """Refresh the page."""
        pass


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
        'ACTION': {'icon': '✔', 'color': '#4ade80', 'bg': '#1e3d2e'},
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
            ("info", "ℹ️ Info:", "#2563EB"),  # Blue
            ("warning", "⚠️ Warnings:", THEME["warning"]),
            ("error", "❌ Errors:", THEME["bad"]),
            ("action", "✔ Actions:", THEME["good"]),
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
        self._live_dot.config(fg=THEME["good"])
        self._live_label.config(fg=THEME["good"])

        # Reset after 500ms
        self.after(500, self._reset_live_indicator)

    def _reset_live_indicator(self):
        """Reset live indicator to idle state."""
        if not self._auto_scroll:
            self._live_dot.config(fg=THEME["warning"])
            self._live_label.config(fg=THEME["warning"], text="PAUSED")
        else:
            self._live_dot.config(fg=THEME["muted"])
            self._live_label.config(fg=THEME["muted"], text="LIVE")

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
            self._live_label.config(text="LIVE", fg=THEME["muted"])
            self._live_dot.config(fg=THEME["muted"])
        else:
            self._pause_btn.config(text="▶ Resume")
            self._live_label.config(text="PAUSED", fg=THEME["warning"])
            self._live_dot.config(fg=THEME["warning"])

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


class NiborRoadmapPage(tk.Frame):
    """
    Nibor Roadmap page showing the data flow for NIBOR calculations.
    Three source cards: Bloomberg API, Weights, Estimated Market Rates.
    Compact overview with drawer for full details.
    """

    # Full detail texts for drawer
    DETAILS = {
        "bloomberg": {
            "title": "BLOOMBERG API",
            "icon": "📡",
            "time": "10:30 CET",
            "content": """SOURCE: BFIX (Bloomberg FX Fixings)

Transparent, replicable FX reference rates calculated as a Time-Weighted Average Price (TWAP) of BGN prices, generated half-hourly. Provides market snapshots for spots and forwards.

BGN (Bloomberg Generic) are real-time composite bid/ask FX rates sourced globally, processed by algorithms to create accurate, dealer-anonymous price points.

SPOTS
  USDNOK    NOK F033 Curncy
  EURNOK    NKEU F033 Curncy

FORWARDS
  USDNOK                      EURNOK
  1W    NK1W F033 Curncy      1W    NKEU1W F033 Curncy
  1M    NK1M F033 Curncy      1M    NKEU1M F033 Curncy
  2M    NK2M F033 Curncy      2M    NKEU2M F033 Curncy
  3M    NK3M F033 Curncy      3M    NKEU3M F033 Curncy
  6M    NK6M F033 Curncy      6M    NKEU6M F033 Curncy

DAYS TO MATURITY
  USDNOK                      EURNOK
  1W    NK1W TPSF Curncy      1W    EURNOK1W TPSF Curncy
  1M    NK1M TPSF Curncy      1M    EURNOK1M TPSF Curncy
  2M    NK2M TPSF Curncy      2M    EURNOK2M TPSF Curncy
  3M    NK3M TPSF Curncy      3M    EURNOK3M TPSF Curncy
  6M    NK6M TPSF Curncy      6M    EURNOK6M TPSF Curncy"""
        },
        "weights": {
            "title": "WEIGHTS",
            "icon": "⚖️",
            "time": "Monthly (before 10th bank day)",
            "content": """SOURCE: Weights.xlsx

FUNDING MIX

The funding mix is updated monthly (before 10th bank day) and consists of:

  • NOK: 50% (fixed)
  • USD: Based on previous month's funding basket
  • EUR: Based on previous month's funding basket

USD and EUR weights reflect the short-term funding composition in each currency from the previous month.

Contracts with maturities less than 30 days are excluded, as these are used for arbitrage and do not reflect actual funding."""
        },
        "estimated": {
            "title": "ESTIMATED MARKET RATES",
            "icon": "📊",
            "time": "10:30 CET",
            "content": """SOURCE: Nibor Fixing Workbook (Excel)

EUR & USD:
Swedbank committed price quotes on CDs/CPs denominated in NOK, combined with expert judgements based on Swedbank's weighted funding costs in USD and EUR. Actual transaction prices are preferred where available.

If Swedbank prices off-market due to limited interest related to the overall funding strategy, an estimation of prevailing market rates is applied instead, called expert judgement.

NOK:
Always uses ECP (Euro Commercial Paper) rate."""
        }
    }

    # Compact summaries for cards
    SUMMARIES = {
        "bloomberg": {
            "title": "BLOOMBERG API",
            "icon": "📡",
            "time": "10:30 CET",
            "lines": [
                "BFIX rates via",
                "TWAP of BGN",
                "prices.",
                "",
                "BGN = real-time",
                "composite FX",
                "rates.",
                "",
                "SPOTS",
                "USDNOK / EURNOK",
                "",
                "FORWARDS + DAYS",
                "per tenor"
            ]
        },
        "weights": {
            "title": "WEIGHTS",
            "icon": "⚖️",
            "time": "Monthly",
            "lines": [
                "(before 10th",
                "bank day)",
                "",
                "• NOK: 50%",
                "• USD/EUR: from",
                "  funding basket",
                "",
                "Excl. <30 day",
                "contracts",
                "",
                "Source:",
                "Weights.xlsx"
            ]
        },
        "estimated": {
            "title": "EST. MARKET",
            "icon": "📊",
            "time": "RATES 10:30 CET",
            "lines": [
                "",
                "EUR/USD:",
                "Swedbank quotes",
                "+ expert",
                "judgement",
                "",
                "NOK: ECP rate",
                "",
                "Source:",
                "Nibor Fixing",
                "Workbook"
            ]
        }
    }

    def __init__(self, master, app):
        super().__init__(master, bg=THEME["bg_panel"])
        self.app = app
        self.pad = CURRENT_MODE["pad"]
        self._card_frames = {}
        self._drawer = None
        self._drawer_overlay = None

        # Bind ESC to close drawer
        self.winfo_toplevel().bind("<Escape>", self._close_drawer_on_escape, add="+")

        self._build_ui()

    def _build_ui(self):
        """Build the main UI."""
        # ================================================================
        # HEADER
        # ================================================================
        header = tk.Frame(self, bg=THEME["bg_panel"])
        header.pack(fill="x", padx=self.pad, pady=(self.pad, 16))

        tk.Label(header, text="NIBOR ROADMAP", fg=THEME["text"], bg=THEME["bg_panel"],
                 font=("Segoe UI", CURRENT_MODE["h2"], "bold")).pack(side="left")

        tk.Label(header, text="Data Flow Overview", fg=THEME["muted"], bg=THEME["bg_panel"],
                 font=("Segoe UI", 12)).pack(side="left", padx=(16, 0))

        # ================================================================
        # MAIN CONTENT - Cards + Flow
        # ================================================================
        content = tk.Frame(self, bg=THEME["bg_panel"])
        content.pack(fill="both", expand=True, padx=self.pad)

        # Cards row
        cards_frame = tk.Frame(content, bg=THEME["bg_panel"])
        cards_frame.pack(fill="x", pady=(0, 0))

        # Equal width columns
        for i in range(3):
            cards_frame.columnconfigure(i, weight=1, uniform="cards")

        # Create the three cards
        self._create_card(cards_frame, 0, "bloomberg")
        self._create_card(cards_frame, 1, "weights")
        self._create_card(cards_frame, 2, "estimated")

        # ================================================================
        # FLOW ARROWS
        # ================================================================
        arrow_frame = tk.Frame(content, bg=THEME["bg_panel"])
        arrow_frame.pack(fill="x", pady=(12, 12))

        # Create canvas for smooth flow lines
        canvas = tk.Canvas(arrow_frame, bg=THEME["bg_panel"], height=50,
                          highlightthickness=0)
        canvas.pack(fill="x")

        # Draw flow lines after widget is mapped
        def draw_flow(event=None):
            canvas.delete("all")
            w = canvas.winfo_width()
            h = canvas.winfo_height()
            if w < 10:
                return

            # Three starting points (center of each card)
            x1 = w // 6
            x2 = w // 2
            x3 = 5 * w // 6
            mid_y = h // 2

            # Draw lines converging to center bottom
            color = THEME["muted"]
            canvas.create_line(x1, 0, x1, mid_y, x2, mid_y, fill=color, width=2)
            canvas.create_line(x3, 0, x3, mid_y, x2, mid_y, fill=color, width=2)
            canvas.create_line(x2, 0, x2, h, fill=color, width=2)

            # Arrow head
            canvas.create_polygon(
                x2 - 8, h - 12,
                x2 + 8, h - 12,
                x2, h,
                fill=THEME["accent"]
            )

        canvas.bind("<Configure>", draw_flow)
        self.after(100, draw_flow)

        # ================================================================
        # NIBOR CALCULATION BOX
        # ================================================================
        calc_container = tk.Frame(content, bg=THEME["bg_panel"])
        calc_container.pack(pady=(0, 20))

        # Accent border wrapper
        calc_border = tk.Frame(calc_container, bg=THEME["accent"], padx=3, pady=3)
        calc_border.pack()

        calc_box = tk.Frame(calc_border, bg=THEME["bg_card"], padx=50, pady=16)
        calc_box.pack()

        tk.Label(calc_box, text="NIBOR CALCULATION", fg=THEME["accent"],
                 bg=THEME["bg_card"], font=("Segoe UI Semibold", 18)).pack()

    def _create_card(self, parent, col, key):
        """Create a compact source card."""
        data = self.SUMMARIES[key]

        # Outer frame for hover border effect
        outer = tk.Frame(parent, bg=THEME["border"], padx=2, pady=2)
        outer.grid(row=0, column=col, padx=10, sticky="nsew")

        # Inner card
        inner = tk.Frame(outer, bg=THEME["bg_card"], cursor="hand2")
        inner.pack(fill="both", expand=True)

        # Content padding
        content = tk.Frame(inner, bg=THEME["bg_card"], padx=16, pady=14)
        content.pack(fill="both", expand=True)

        # Header row: icon + title
        header = tk.Frame(content, bg=THEME["bg_card"])
        header.pack(fill="x", pady=(0, 4))

        tk.Label(header, text=data["icon"], fg=THEME["accent"], bg=THEME["bg_card"],
                 font=("Segoe UI", 20)).pack(side="left")

        tk.Label(header, text=data["title"], fg=THEME["text"], bg=THEME["bg_card"],
                 font=("Segoe UI Semibold", 13)).pack(side="left", padx=(8, 0))

        # Time label
        tk.Label(content, text=data["time"], fg=THEME["accent"], bg=THEME["bg_card"],
                 font=("Segoe UI", 10)).pack(anchor="w", pady=(0, 8))

        # Summary lines
        for line in data["lines"]:
            if line == "":
                tk.Frame(content, bg=THEME["bg_card"], height=4).pack()
            else:
                tk.Label(content, text=line, fg=THEME["muted"], bg=THEME["bg_card"],
                         font=("Segoe UI", 10), anchor="w").pack(anchor="w")

        # Store references
        self._card_frames[key] = {"outer": outer, "inner": inner, "content": content}

        # Bind events
        widgets = [inner, content] + list(content.winfo_children())
        for widget in widgets:
            widget.bind("<Enter>", lambda e, k=key: self._on_card_enter(k))
            widget.bind("<Leave>", lambda e, k=key: self._on_card_leave(k))
            widget.bind("<Button-1>", lambda e, k=key: self._on_card_click(k))

            # Make children also have hand cursor
            try:
                widget.configure(cursor="hand2")
            except tk.TclError:
                pass

    def _on_card_enter(self, key):
        """Handle mouse enter on card."""
        self._card_frames[key]["outer"].configure(bg=THEME["accent"])

    def _on_card_leave(self, key):
        """Handle mouse leave on card."""
        self._card_frames[key]["outer"].configure(bg=THEME["border"])

    def _on_card_click(self, key):
        """Handle card click - open drawer."""
        self._open_drawer(key)

    def _open_drawer(self, key):
        """Open drawer with full details."""
        # Close existing drawer if any
        self._close_drawer()

        data = self.DETAILS[key]

        # Get root window
        root = self.winfo_toplevel()
        root_width = root.winfo_width()
        root_height = root.winfo_height()

        # Create overlay (semi-transparent click-to-close area)
        self._drawer_overlay = tk.Frame(root, bg="black")
        self._drawer_overlay.place(x=0, y=0, relwidth=1, relheight=1)
        self._drawer_overlay.configure(bg=THEME["bg_main"])

        # Make overlay semi-transparent by using a lower opacity color
        # (Tkinter doesn't support true transparency, so we use a dark color)
        self._drawer_overlay.bind("<Button-1>", lambda e: self._close_drawer())

        # Drawer panel (right side)
        drawer_width = 480
        self._drawer = tk.Frame(root, bg=THEME["bg_card"], width=drawer_width)
        self._drawer.place(x=root_width - drawer_width, y=0, width=drawer_width, relheight=1)
        self._drawer.pack_propagate(False)

        # Drawer header
        header = tk.Frame(self._drawer, bg=THEME["bg_card"])
        header.pack(fill="x", padx=24, pady=(20, 16))

        # Close button
        close_btn = tk.Label(header, text="✕", fg=THEME["muted"], bg=THEME["bg_card"],
                            font=("Segoe UI", 16), cursor="hand2")
        close_btn.pack(side="right")
        close_btn.bind("<Button-1>", lambda e: self._close_drawer())
        close_btn.bind("<Enter>", lambda e: close_btn.configure(fg=THEME["accent"]))
        close_btn.bind("<Leave>", lambda e: close_btn.configure(fg=THEME["muted"]))

        # Title with icon
        tk.Label(header, text=f"{data['icon']}  {data['title']}", fg=THEME["accent"],
                 bg=THEME["bg_card"], font=("Segoe UI Semibold", 18)).pack(side="left")

        # Time badge
        time_frame = tk.Frame(header, bg=THEME["bg_panel"], padx=10, pady=4)
        time_frame.pack(side="left", padx=(16, 0))
        tk.Label(time_frame, text=data["time"], fg=THEME["text"], bg=THEME["bg_panel"],
                 font=("Segoe UI", 10)).pack()

        # Separator
        tk.Frame(self._drawer, bg=THEME["border"], height=1).pack(fill="x", padx=24)

        # Content
        content_frame = tk.Frame(self._drawer, bg=THEME["bg_card"])
        content_frame.pack(fill="both", expand=True, padx=24, pady=20)

        # Display content as formatted text
        text_widget = tk.Text(content_frame, bg=THEME["bg_card"], fg=THEME["text"],
                             font=("Consolas", 11), relief="flat", wrap="word",
                             highlightthickness=0, padx=0, pady=0)
        text_widget.pack(fill="both", expand=True)
        text_widget.insert("1.0", data["content"])
        text_widget.configure(state="disabled")

        # Accent bar on left edge of drawer
        accent_bar = tk.Frame(self._drawer, bg=THEME["accent"], width=4)
        accent_bar.place(x=0, y=0, width=4, relheight=1)

    def _close_drawer(self, event=None):
        """Close the drawer."""
        if self._drawer_overlay:
            self._drawer_overlay.destroy()
            self._drawer_overlay = None
        if self._drawer:
            self._drawer.destroy()
            self._drawer = None

    def _close_drawer_on_escape(self, event=None):
        """Close drawer on ESC key."""
        if self._drawer:
            self._close_drawer()

    def update(self):
        """Refresh the page (no dynamic data needed)."""
        pass
