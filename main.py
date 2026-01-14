"""
Nibor Calculation Terminal - Main Application
Treasury Suite for NIBOR validation and monitoring.
CustomTkinter Edition - Modern UI with rounded corners and dark theme.
"""
import os
import threading
import time
from datetime import datetime
from tkinter import messagebox

import tkinter as tk
import customtkinter as ctk

from openpyxl.utils import coordinate_to_tuple

from config import (
    APP_VERSION, THEME, FONTS, CURRENT_MODE, set_mode,
    CTK_APPEARANCE, CTK_CORNER_RADIUS,
    APP_DIR, DATA_DIR, BASE_HISTORY_PATH, STIBOR_GRSS_PATH,
    DAY_FILES, RECON_FILE, WEIGHTS_FILE, CACHE_DIR,
    EXCEL_LOGO_CANDIDATES, BBG_LOGO_CANDIDATES,
    RULES_DB, RECON_MAPPING, DAYS_MAPPING, MARKET_STRUCTURE,
    WEIGHTS_FILE_CELLS, WEIGHTS_MODEL_CELLS, SWET_CM_RECON_MAPPING,
    ALL_REAL_TICKERS,
    setup_logging, get_logger
)

# Configure CustomTkinter appearance
ctk.set_appearance_mode(CTK_APPEARANCE)
ctk.set_default_color_theme("dark-blue")

# Initialize logging
setup_logging()
log = get_logger("main")

from utils import (
    fmt_ts, fmt_date, safe_float, to_date,
    business_day_index_in_month, calendar_days_since_month_start,
    LogoPipelineTK
)
from engines import ExcelEngine, BloombergEngine, blpapi
from ui_components import style_ttk, NavButtonTK, SourceCardTK, ConnectionStatusPanel, ConnectionStatusIndicator
from history import save_snapshot
from ui_pages import (
    DashboardPage, ReconPage, RulesPage, BloombergPage,
    NiborDaysPage, NokImpliedPage, WeightsPage, NiborMetaDataPage, HistoryPage,
    AuditLogPage, SettingsPage
)


class NiborTerminalCTK(ctk.CTk):
    """Main application window for Nibor Calculation Terminal (CustomTkinter)."""

    def __init__(self):
        super().__init__()

        set_mode("OFFICE")

        self.title(f"Nibor Calculation Terminal v{APP_VERSION}")
        self.geometry("1400x1050")
        self.minsize(1320, 950)
        self.configure(fg_color=THEME["bg_main"])

        style_ttk(self)

        self.logo_pipeline = LogoPipelineTK()
        self.engine = BloombergEngine(cache_ttl_sec=3.0)
        self.excel_engine = ExcelEngine()

        # Toast notification manager
        from toast import ToastManager
        self.toast = ToastManager(self)

        # System tray (optional)
        self._tray = None
        self._tray_enabled = False
        try:
            from system_tray import SystemTray, TRAY_AVAILABLE
            if TRAY_AVAILABLE:
                self._tray = SystemTray(self)
                self._tray.start()
                self._tray_enabled = True
                log.info("System tray initialized")
        except ImportError:
            log.warning("System tray not available - pystray not installed")

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
        self._setup_keyboard_shortcuts()

        # Set up window close handler for system tray
        self.protocol("WM_DELETE_WINDOW", self._on_window_close)

        self.after(250, self.refresh_data)

    def _setup_keyboard_shortcuts(self):
        """Setup global keyboard shortcuts."""
        # F5 = Refresh
        self.bind("<F5>", lambda e: self.refresh_data())

        # Ctrl+S = Save snapshot (when on history page)
        self.bind("<Control-s>", self._shortcut_save_snapshot)

        # Ctrl+E = Export (when on history page)
        self.bind("<Control-e>", self._shortcut_export)

        # Ctrl+H = Go to History page
        self.bind("<Control-h>", lambda e: self.show_page("history"))

        # Ctrl+D = Go to Dashboard
        self.bind("<Control-d>", lambda e: self.show_page("dashboard"))

        # Ctrl+R = Go to Nibor Recon
        self.bind("<Control-r>", lambda e: self.show_page("nibor_recon"))

        # Ctrl+N = Go to NOK Implied
        self.bind("<Control-n>", lambda e: self.show_page("nok_implied"))

        # Ctrl+comma = Settings
        self.bind("<Control-comma>", lambda e: self._show_settings_dialog())

        # Escape = Close any open dialog
        self.bind("<Escape>", self._close_toplevel_dialogs)

        # F1 = About
        self.bind("<F1>", lambda e: self._show_about_dialog())

        # Ctrl+M = Minimize to tray
        self.bind("<Control-m>", lambda e: self._minimize_to_tray())

    def _shortcut_save_snapshot(self, event=None):
        """Handle Ctrl+S shortcut."""
        if self._current_page == "history" and "history" in self._pages:
            self._pages["history"]._save_now()

    def _shortcut_export(self, event=None):
        """Handle Ctrl+E shortcut."""
        if self._current_page == "history" and "history" in self._pages:
            self._pages["history"]._export_selected()

    def _close_toplevel_dialogs(self, event=None):
        """Close any open toplevel dialogs."""
        for widget in self.winfo_children():
            if isinstance(widget, tk.Toplevel):
                widget.destroy()

    def _on_window_close(self):
        """Handle window close - minimize to tray or quit."""
        if self._tray_enabled:
            # Minimize to tray instead of closing
            self._minimize_to_tray()
        else:
            # Actually quit
            self._quit_app()

    def _minimize_to_tray(self):
        """Minimize to system tray."""
        if self._tray_enabled and self._tray:
            self.withdraw()
            self._tray.show_notification(
                "Nibor Calculation Terminal",
                "Minimized to tray. Click icon to restore."
            )
            log.info("Application minimized to system tray")
        else:
            # If tray not available, just minimize normally
            self.iconify()

    def _quit_app(self):
        """Quit the application."""
        log.info("Application shutting down")
        if self._tray:
            self._tray.stop()
        self.destroy()

    def build_ui(self):
        hpad = CURRENT_MODE["hpad"]

        # ====================================================================
        # GLOBAL HEADER - Visible on ALL pages
        # ====================================================================
        from PIL import Image, ImageTk

        global_header = ctk.CTkFrame(self, fg_color=THEME["bg_main"], corner_radius=0)
        global_header.pack(fill="x", padx=hpad, pady=(hpad, 5))

        # --- LEFT: Swedbank header image ---
        header_left = ctk.CTkFrame(global_header, fg_color="transparent")
        header_left.pack(side="left", anchor="n")

        image_path = r"C:\Users\p901sbf\OneDrive - Swedbank\GroupTreasury-ShortTermFunding - Documents\Referensräntor\Nibor\Bilder\Swed.png"

        if os.path.exists(image_path):
            try:
                img = Image.open(image_path)
                target_width = 350
                aspect_ratio = img.height / img.width
                target_height = int(target_width * aspect_ratio)
                img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)

                ctk_image = ctk.CTkImage(light_image=img, dark_image=img, size=(target_width, target_height))
                img_label = ctk.CTkLabel(header_left, image=ctk_image, text="")
                img_label.pack(anchor="w")
                log.info(f"Global Swedbank header loaded: {target_width}x{target_height}px")
            except Exception as e:
                log.warning(f"Failed to load Swedbank header: {e}")
                ctk.CTkLabel(header_left, text="ONYX TERMINAL",
                            text_color=THEME["text"],
                            font=("Segoe UI", 24, "bold")).pack()
        else:
            log.warning(f"Image not found: {image_path}")
            ctk.CTkLabel(header_left, text="ONYX TERMINAL",
                        text_color=THEME["text"],
                        font=("Segoe UI", 24, "bold")).pack()

        # ====================================================================
        # RIGHT SECTION: UPDATE button + Professional clock
        # ====================================================================
        header_right = ctk.CTkFrame(global_header, fg_color="transparent")
        header_right.pack(side="right", padx=(0, 20))

        # UPDATE button (to the left of clock) - Modern CTk button
        self.header_update_btn = ctk.CTkButton(
            header_right,
            text="UPDATE",
            command=self.refresh_data,
            fg_color=THEME["accent"],
            hover_color=THEME["accent_hover"],
            text_color=THEME["bg_panel"],
            font=("Segoe UI Semibold", 12),
            corner_radius=CTK_CORNER_RADIUS["button"],
            width=120,
            height=40
        )
        self.header_update_btn.pack(side="left", padx=(0, 20), pady=10)
        self.register_update_button(self.header_update_btn)

        # ====================================================================
        # PROFESSIONAL CLOCK - Rightmost corner (Modern rounded frame)
        # ====================================================================
        clock_frame = ctk.CTkFrame(header_right, fg_color=THEME["bg_card"],
                                   corner_radius=CTK_CORNER_RADIUS["frame"],
                                   border_width=1, border_color=THEME["border"])
        clock_frame.pack(side="right")

        clock_inner = ctk.CTkFrame(clock_frame, fg_color="transparent")
        clock_inner.pack(padx=20, pady=12)

        # Left side: Time and date
        time_section = ctk.CTkFrame(clock_inner, fg_color="transparent")
        time_section.pack(side="left", padx=(0, 15))

        # Small label "LOCAL TIME"
        ctk.CTkLabel(time_section, text="LOCAL TIME",
                    text_color=THEME["muted"],
                    font=("Segoe UI", 8)).pack(anchor="center")

        # Time display - unified size
        self._header_clock_time = ctk.CTkLabel(time_section, text="--:--:--",
                                               text_color=THEME["accent"],
                                               font=("Consolas", 22, "bold"))
        self._header_clock_time.pack(anchor="center")

        # Date label below time
        self._header_clock_date = ctk.CTkLabel(time_section, text="",
                                               text_color=THEME["muted"],
                                               font=("Segoe UI", 9))
        self._header_clock_date.pack(anchor="center")

        # Vertical separator
        sep_frame = ctk.CTkFrame(clock_inner, fg_color="transparent", width=1)
        sep_frame.pack(side="left", padx=10, fill="y")
        ctk.CTkFrame(sep_frame, fg_color=THEME["border"], width=1, height=60).pack(fill="y", expand=True, pady=5)

        # Right side: NIBOR Fixing countdown
        nibor_section = ctk.CTkFrame(clock_inner, fg_color="transparent")
        nibor_section.pack(side="left", padx=(15, 0))

        # NIBOR Fixing label
        ctk.CTkLabel(nibor_section, text="NIBOR FIXING",
                    text_color=THEME["muted"],
                    font=("Segoe UI", 8)).pack(anchor="center")

        # Fixing countdown - same size as clock
        self._nibor_fixing_status = ctk.CTkLabel(nibor_section, text="--:--:--",
                                                 text_color=THEME["accent_secondary"],
                                                 font=("Consolas", 22, "bold"))
        self._nibor_fixing_status.pack(anchor="center")

        # Fixing indicator text
        self._nibor_fixing_indicator = ctk.CTkLabel(nibor_section, text="",
                                                    text_color=THEME["muted"],
                                                    font=("Segoe UI", 9))
        self._nibor_fixing_indicator.pack(anchor="center")

        # Start the header clock update
        self._update_header_clock()

        # ====================================================================
        # STATUS BAR - Bottom of window
        # ====================================================================
        self._build_status_bar()

        # ====================================================================
        # BODY with Command Center Sidebar + Content
        # ====================================================================
        self.body = ctk.CTkFrame(self, fg_color=THEME["bg_main"], corner_radius=0)
        self.body.pack(fill="both", expand=True, padx=hpad, pady=(0, 5))

        # Configure grid layout: sidebar (0) | separator (1) | content (2)
        self.body.grid_columnconfigure(0, weight=0, minsize=220)  # Sidebar fixed
        self.body.grid_columnconfigure(1, weight=0, minsize=3)    # Separator fixed
        self.body.grid_columnconfigure(2, weight=1)               # Content expandable
        self.body.grid_rowconfigure(0, weight=1)

        # ====================================================================
        # COMMAND CENTER SIDEBAR - ALWAYS VISIBLE (Modern rounded design)
        # ====================================================================
        sidebar = ctk.CTkFrame(self.body, fg_color=THEME["bg_nav"], width=220,
                               corner_radius=CTK_CORNER_RADIUS["frame"])
        sidebar.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        sidebar.grid_propagate(False)

        # Sidebar title
        ctk.CTkLabel(sidebar, text="COMMAND CENTER",
                    text_color=THEME["text_light"],
                    font=("Segoe UI Semibold", 21)).pack(anchor="w", padx=20, pady=(20, 15))

        # Navigation buttons with line-art icons (icon, name, page_class)
        self.PAGES_CONFIG = [
            ("dashboard", "📊", "NIBOR", DashboardPage),
            ("nibor_recon", "✅", "Nibor Recon", ReconPage),
            ("nok_implied", "📈", "NOK Implied", NokImpliedPage),
            ("weights", "⚖️", "Weights", WeightsPage),
            ("history", "🕐", "History", HistoryPage),
            ("audit_log", "📋", "Audit Log", AuditLogPage),
            ("nibor_meta", "ℹ️", "Meta Data", NiborMetaDataPage),
            ("rules_logic", "📐", "Rules & Logic", RulesPage),
            ("bloomberg", "📡", "Bloomberg", BloombergPage),
            ("nibor_days", "📅", "Nibor Days", NiborDaysPage),
            ("settings", "⚙️", "Settings", SettingsPage),
        ]

        # Hover color: rgba(255,255,255,0.05) = #FFFFFF with 5% opacity on dark bg
        hover_color = "#1A1F2E"  # Approximation of white 5% on dark navy
        # Active bg: rgba(238,118,35,0.1) = orange with 10% opacity
        active_bg = "#1E1714"  # Approximation of orange 10% on dark navy

        for page_key, icon, page_name, _ in self.PAGES_CONFIG:
            # Container frame - 44px height as per spec
            btn_container = ctk.CTkFrame(sidebar, fg_color="transparent", height=44)
            btn_container.pack(fill="x", pady=0)
            btn_container.pack_propagate(False)

            # Active indicator (orange bar on left - 3px)
            indicator = ctk.CTkFrame(btn_container, fg_color="transparent", width=3, corner_radius=0)
            indicator.pack(side="left", fill="y")

            # Icon label (20x20px area, 16px gap to text)
            icon_label = ctk.CTkLabel(
                btn_container,
                text=icon,
                text_color=THEME["muted"],
                font=("Segoe UI", 23),
                width=28
            )
            icon_label.pack(side="left", padx=(12, 12))

            # Text button
            btn = ctk.CTkButton(
                btn_container,
                text=page_name,
                command=lambda pk=page_key: self.show_page(pk),
                fg_color="transparent",
                hover_color=hover_color,
                text_color=THEME["text"],
                font=("Segoe UI", 11),
                anchor="w",
                corner_radius=0,
                height=44
            )
            btn.pack(side="left", fill="x", expand=True)

            self._nav_buttons[page_key] = {
                "btn": btn,
                "indicator": indicator,
                "container": btn_container,
                "icon": icon_label,
                "hover_color": hover_color,
                "active_bg": active_bg
            }

        # Divider
        ctk.CTkFrame(sidebar, fg_color=THEME["border"], height=1).pack(fill="x", padx=20, pady=15)

        # Quick Access
        ctk.CTkLabel(sidebar, text="QUICK ACCESS",
                    text_color=THEME["text_light"],
                    font=("Segoe UI Semibold", 9)).pack(anchor="w", padx=20, pady=(0, 10))

        # History folder button
        history_btn = ctk.CTkButton(
            sidebar,
            text="📂  History",
            command=self.open_history_folder,
            fg_color="transparent",
            hover_color=THEME["bg_nav_sel"],
            text_color=THEME["muted"],
            font=("Segoe UI", 10),
            anchor="w",
            corner_radius=6,
            height=32
        )
        history_btn.pack(fill="x", padx=12, pady=2)

        # GRSS folder button
        grss_btn = ctk.CTkButton(
            sidebar,
            text="📂  GRSS",
            command=self.open_stibor_folder,
            fg_color="transparent",
            hover_color=THEME["bg_nav_sel"],
            text_color=THEME["muted"],
            font=("Segoe UI", 10),
            anchor="w",
            corner_radius=6,
            height=32
        )
        grss_btn.pack(fill="x", padx=12, pady=2)

        # Spacer
        ctk.CTkFrame(sidebar, fg_color="transparent").pack(fill="both", expand=True)

        # Subtle separator line
        separator = ctk.CTkFrame(self.body, fg_color=THEME["border"], width=1)
        separator.grid(row=0, column=1, sticky="ns")

        # ====================================================================
        # CONTENT AREA
        # ====================================================================
        self.content = ctk.CTkFrame(self.body, fg_color=THEME["bg_panel"], corner_radius=0)
        self.content.grid(row=0, column=2, sticky="nsew")
        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_columnconfigure(0, weight=1)

        for key, icon, name, page_class in self.PAGES_CONFIG:
            page_instance = page_class(self.content, self)
            self._pages[key] = page_instance
            page_instance.grid(row=0, column=0, sticky="nsew")
            page_instance.grid_remove()

        if self.PAGES_CONFIG:
            self.show_page(self.PAGES_CONFIG[0][0])

    def _update_header_clock(self):
        """Update the header clock and NIBOR fixing countdown every second."""
        now = datetime.now()

        # Swedish day and month names
        days_sv = ["Mån", "Tis", "Ons", "Tor", "Fre", "Lör", "Sön"]
        months_sv = ["", "jan", "feb", "mar", "apr", "maj", "jun",
                     "jul", "aug", "sep", "okt", "nov", "dec"]
        day_name = days_sv[now.weekday()]
        date_str = f"{day_name} {now.day} {months_sv[now.month]} {now.year}"

        # Update date and time (unified HH:MM:SS format) - CTk uses configure
        self._header_clock_date.configure(text=date_str)
        self._header_clock_time.configure(text=now.strftime("%H:%M:%S"))

        # NIBOR Fixing window: 11:00 - 11:30 CET (weekdays only)
        hour = now.hour
        minute = now.minute
        second = now.second
        weekday = now.weekday()
        current_seconds = hour * 3600 + minute * 60 + second

        fixing_start = 11 * 3600  # 11:00:00
        fixing_end = 11 * 3600 + 30 * 60  # 11:30:00

        if weekday >= 5:  # Weekend
            self._nibor_fixing_status.configure(text="— — —", text_color=THEME["muted"])
            self._nibor_fixing_indicator.configure(text="Weekend", text_color=THEME["muted"])
        elif current_seconds < fixing_start:
            # Before fixing window - countdown to open
            secs_until = fixing_start - current_seconds
            hrs = secs_until // 3600
            mins = (secs_until % 3600) // 60
            secs = secs_until % 60

            # Always show H:MM:SS format for consistency
            countdown_str = f"{hrs}:{mins:02d}:{secs:02d}"
            # Orange warning when less than 30 min
            color = THEME["warning"] if hrs == 0 and mins < 30 else THEME["muted"]
            self._nibor_fixing_status.configure(text=countdown_str, text_color=color)
            self._nibor_fixing_indicator.configure(text="until open", text_color=color)
        elif current_seconds < fixing_end:
            # FIXING WINDOW OPEN - countdown to close
            secs_left = fixing_end - current_seconds
            mins = secs_left // 60
            secs = secs_left % 60
            countdown_str = f"0:{mins:02d}:{secs:02d}"
            self._nibor_fixing_status.configure(text=countdown_str, text_color=THEME["good"])
            self._nibor_fixing_indicator.configure(text="● OPEN", text_color=THEME["good"])
        else:
            # After fixing window - closed
            self._nibor_fixing_status.configure(text="CLOSED", text_color=THEME["muted"])
            self._nibor_fixing_indicator.configure(text="until tomorrow", text_color=THEME["muted"])

        # Schedule next update
        self.after(1000, self._update_header_clock)

    def _build_status_bar(self):
        """Build the status bar at the bottom of the window."""
        from config import APP_VERSION

        status_bar = ctk.CTkFrame(self, fg_color=THEME["bg_nav"], height=36, corner_radius=0)
        status_bar.pack(side="bottom", fill="x")
        status_bar.pack_propagate(False)

        # Left side - connection status panel (still uses tk for compatibility)
        self.connection_panel = ConnectionStatusPanel(status_bar, bg=THEME["bg_nav"])
        self.connection_panel.pack(side="left", padx=15, pady=4)

        # Right side - version and user
        right_frame = ctk.CTkFrame(status_bar, fg_color="transparent")
        right_frame.pack(side="right", padx=15)

        # User info
        import getpass
        username = getpass.getuser()
        ctk.CTkLabel(right_frame, text=f"👤 {username}", text_color=THEME["muted"], font=("Segoe UI", 9)).pack(side="right", padx=(15, 0))

        # Separator
        ctk.CTkFrame(right_frame, fg_color=THEME["border"], width=1, height=18).pack(side="right", padx=12)

        # Version
        ctk.CTkLabel(right_frame, text=f"v{APP_VERSION}", text_color=THEME["text_light"], font=("Segoe UI", 9)).pack(side="right")

        # About button (clickable)
        about_btn = ctk.CTkButton(
            right_frame,
            text="ⓘ",
            command=self._show_about_dialog,
            fg_color="transparent",
            hover_color=THEME["bg_nav_sel"],
            text_color=THEME["muted"],
            font=("Segoe UI", 12),
            width=30,
            height=24,
            corner_radius=4
        )
        about_btn.pack(side="right", padx=(0, 8))

    def _update_status_bar(self):
        """Update status bar indicators using the new ConnectionStatusPanel."""
        # Bloomberg status with details
        if self.bbg_ok:
            bbg_details = {
                "Tickers": len(getattr(self, 'cached_market_data', {}) or {}),
                "API": "blpapi" if blpapi else "Mock"
            }
            self.connection_panel.set_bloomberg_status(
                ConnectionStatusIndicator.CONNECTED, bbg_details
            )
        else:
            self.connection_panel.set_bloomberg_status(
                ConnectionStatusIndicator.ERROR, {"Message": "Connection failed"}
            )

        # Excel status with details
        if self.excel_ok:
            excel_details = {
                "File": "eFX_Template.xlsx",
                "Cells": len(getattr(self, 'cached_excel_data', {}) or {})
            }
            self.connection_panel.set_excel_status(
                ConnectionStatusIndicator.CONNECTED, excel_details
            )
        else:
            self.connection_panel.set_excel_status(
                ConnectionStatusIndicator.DISCONNECTED, {"Message": "File not loaded"}
            )

        # Update data freshness timestamp
        self.connection_panel.set_data_time()

    def _show_about_dialog(self):
        """Show the About dialog with modern CTk styling."""
        from config import APP_VERSION
        import getpass
        import platform

        about_win = ctk.CTkToplevel(self)
        about_win.title("About Nibor Calculation Terminal")
        about_win.geometry("400x320")
        about_win.resizable(False, False)
        about_win.transient(self)
        about_win.grab_set()

        # Center on parent
        about_win.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() - 400) // 2
        y = self.winfo_y() + (self.winfo_height() - 320) // 2
        about_win.geometry(f"+{x}+{y}")

        # Content
        content = ctk.CTkFrame(about_win, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=30, pady=20)

        # Logo
        ctk.CTkLabel(content, text="N", font=("Segoe UI", 36, "bold"), text_color=THEME["accent"]).pack()

        # Title
        ctk.CTkLabel(content, text="NIBOR CALCULATION TERMINAL", font=("Segoe UI", 14, "bold"), text_color=THEME["text"]).pack(pady=(5, 0))

        # Subtitle
        ctk.CTkLabel(content, text="Treasury Reference Rate System", font=("Segoe UI", 10), text_color=THEME["muted"]).pack(pady=(2, 15))

        # Info
        info_frame = ctk.CTkFrame(content, fg_color="transparent")
        info_frame.pack(fill="x", pady=10)

        info_items = [
            ("Version:", APP_VERSION),
            ("User:", getpass.getuser()),
            ("Platform:", platform.system()),
            ("Python:", platform.python_version()),
        ]

        for label, value in info_items:
            row = ctk.CTkFrame(info_frame, fg_color="transparent")
            row.pack(fill="x", pady=2)
            ctk.CTkLabel(row, text=label, font=("Segoe UI", 9), text_color=THEME["text_light"], width=80, anchor="e").pack(side="left")
            ctk.CTkLabel(row, text=value, font=("Segoe UI", 9), text_color=THEME["muted"], anchor="w").pack(side="left", padx=5)

        # Footer
        ctk.CTkLabel(content, text="© 2025 Swedbank Treasury", font=("Segoe UI", 8), text_color=THEME["text_light"]).pack(side="bottom", pady=(15, 0))

        # Close button
        close_btn = ctk.CTkButton(
            content,
            text="Close",
            command=about_win.destroy,
            fg_color=THEME["bg_card_2"],
            hover_color=THEME["accent"],
            text_color=THEME["text"],
            font=("Segoe UI", 10),
            corner_radius=CTK_CORNER_RADIUS["button"],
            width=100,
            height=32
        )
        close_btn.pack(side="bottom")

    def _show_settings_dialog(self):
        """Show the Settings dialog with modern CTk styling."""
        settings_win = ctk.CTkToplevel(self)
        settings_win.title("Settings")
        settings_win.geometry("500x450")
        settings_win.resizable(False, False)
        settings_win.transient(self)
        settings_win.grab_set()

        # Center on parent
        settings_win.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() - 500) // 2
        y = self.winfo_y() + (self.winfo_height() - 450) // 2
        settings_win.geometry(f"+{x}+{y}")

        # Title
        ctk.CTkLabel(settings_win, text="⚙️ Settings", font=("Segoe UI", 16, "bold"),
                    text_color=THEME["text"]).pack(pady=(20, 15))

        # Content frame
        content = ctk.CTkFrame(settings_win, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=30)

        # Auto-refresh interval
        refresh_frame = ctk.CTkFrame(content, fg_color="transparent")
        refresh_frame.pack(fill="x", pady=10)

        ctk.CTkLabel(refresh_frame, text="Auto-refresh interval:", font=("Segoe UI", 10),
                    text_color=THEME["muted"]).pack(side="left")

        self.settings_refresh_var = tk.StringVar(value="Manual")
        refresh_options = ["Manual", "30 sec", "1 min", "5 min", "10 min"]
        refresh_menu = ctk.CTkOptionMenu(refresh_frame, variable=self.settings_refresh_var,
                                         values=refresh_options, width=120,
                                         fg_color=THEME["bg_card_2"], button_color=THEME["accent"],
                                         button_hover_color=THEME["accent_hover"])
        refresh_menu.pack(side="right")

        # Theme selection
        theme_frame = ctk.CTkFrame(content, fg_color="transparent")
        theme_frame.pack(fill="x", pady=10)

        ctk.CTkLabel(theme_frame, text="Theme:", font=("Segoe UI", 10),
                    text_color=THEME["muted"]).pack(side="left")

        self.settings_theme_var = tk.StringVar(value="Dark")
        theme_options = ["Dark", "Light"]
        theme_menu = ctk.CTkOptionMenu(theme_frame, variable=self.settings_theme_var,
                                       values=theme_options, width=120,
                                       fg_color=THEME["bg_card_2"], button_color=THEME["accent"],
                                       button_hover_color=THEME["accent_hover"])
        theme_menu.pack(side="right")

        # Auto-save snapshots
        autosave_frame = ctk.CTkFrame(content, fg_color="transparent")
        autosave_frame.pack(fill="x", pady=10)

        self.settings_autosave_var = tk.BooleanVar(value=True)
        autosave_check = ctk.CTkCheckBox(autosave_frame, text="Auto-save snapshots on data refresh",
                                         variable=self.settings_autosave_var,
                                         font=("Segoe UI", 10), text_color=THEME["muted"],
                                         fg_color=THEME["accent"], hover_color=THEME["accent_hover"])
        autosave_check.pack(side="left")

        # Show notifications
        notif_frame = ctk.CTkFrame(content, fg_color="transparent")
        notif_frame.pack(fill="x", pady=10)

        self.settings_notif_var = tk.BooleanVar(value=True)
        notif_check = ctk.CTkCheckBox(notif_frame, text="Show notifications for alerts",
                                      variable=self.settings_notif_var,
                                      font=("Segoe UI", 10), text_color=THEME["muted"],
                                      fg_color=THEME["accent"], hover_color=THEME["accent_hover"])
        notif_check.pack(side="left")

        # Keyboard shortcuts info
        shortcuts_label = ctk.CTkLabel(content, text="Keyboard Shortcuts", font=("Segoe UI", 9, "bold"),
                                       text_color=THEME["text_light"])
        shortcuts_label.pack(anchor="w", pady=(20, 10))

        shortcuts_frame = ctk.CTkFrame(content, fg_color=THEME["bg_card"],
                                       corner_radius=CTK_CORNER_RADIUS["frame"])
        shortcuts_frame.pack(fill="x")

        shortcuts = [
            ("F5", "Refresh data"),
            ("Ctrl+S", "Save snapshot"),
            ("Ctrl+E", "Export selected"),
            ("Ctrl+H", "History page"),
            ("Ctrl+D", "Dashboard"),
            ("Ctrl+,", "Settings"),
            ("F1", "About"),
            ("Esc", "Close dialogs"),
        ]

        for key, desc in shortcuts:
            row = ctk.CTkFrame(shortcuts_frame, fg_color="transparent")
            row.pack(fill="x", padx=10, pady=2)
            ctk.CTkLabel(row, text=key, font=("Consolas", 9), text_color=THEME["accent"], width=80, anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=desc, font=("Segoe UI", 9), text_color=THEME["muted"], anchor="w").pack(side="left")

        # Buttons
        btn_frame = ctk.CTkFrame(settings_win, fg_color="transparent")
        btn_frame.pack(side="bottom", pady=20)

        ctk.CTkButton(btn_frame, text="Close", command=settings_win.destroy,
                     fg_color=THEME["bg_card_2"], hover_color=THEME["accent"],
                     text_color=THEME["text"], font=("Segoe UI", 10),
                     corner_radius=CTK_CORNER_RADIUS["button"],
                     width=100, height=32).pack(side="right", padx=5)

    def register_update_button(self, btn):
        """Register a button (tk.Button or CTkButton) for update state management."""
        if btn not in self._update_buttons:
            self._update_buttons.append(btn)
            # CTkButton uses cget differently
            try:
                self._update_btn_original_text[id(btn)] = btn.cget("text")
            except Exception:
                self._update_btn_original_text[id(btn)] = "UPDATE"

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

        # Update navigation button highlighting with active indicator (CTk style)
        for btn_key, btn_data in self._nav_buttons.items():
            btn = btn_data["btn"] if isinstance(btn_data, dict) else btn_data
            indicator = btn_data.get("indicator") if isinstance(btn_data, dict) else None
            container = btn_data.get("container") if isinstance(btn_data, dict) else None
            icon = btn_data.get("icon") if isinstance(btn_data, dict) else None
            active_bg = btn_data.get("active_bg", "#1E1714") if isinstance(btn_data, dict) else "#1E1714"

            if btn_key == key:
                # Active state: orange text, orange left border (3px), subtle orange bg
                btn.configure(text_color=THEME["accent"], fg_color="transparent",
                             font=("Segoe UI Semibold", 11))
                if indicator:
                    indicator.configure(fg_color=THEME["accent"])
                if container:
                    container.configure(fg_color=active_bg)
                if icon:
                    icon.configure(text_color=THEME["accent"])
            else:
                # Inactive state
                btn.configure(text_color=THEME["text"], fg_color="transparent",
                             font=("Segoe UI", 11))
                if indicator:
                    indicator.configure(fg_color="transparent")
                if container:
                    container.configure(fg_color="transparent")
                if icon:
                    icon.configure(text_color=THEME["muted"])

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
            messagebox.showerror("Nibor Terminal", f"Folder missing: {folder_path}")

    def open_stibor_folder(self):
        if STIBOR_GRSS_PATH.exists():
            os.startfile(STIBOR_GRSS_PATH)
        else:
            messagebox.showerror("Nibor Terminal", f"Folder missing: {STIBOR_GRSS_PATH}")

    def refresh_data(self):
        if self._busy:
            return

        self.set_busy(True, text="FETCHING…")

        # Set connection indicators to "connecting" state
        self.connection_panel.set_bloomberg_status(ConnectionStatusIndicator.CONNECTING)
        self.connection_panel.set_excel_status(ConnectionStatusIndicator.CONNECTING)

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
        else:
            self.cached_excel_data = {}
            self.excel_ok = False
            log.error("Excel failed, cached_excel_data cleared")

        self.active_alerts = []
        self.status_spot = True
        self.status_fwds = True
        self.status_ecp = True
        self.status_days = True
        self.status_cells = True
        self.status_weights = True
        self.weights_state = "WAIT"

        _ = self.build_recon_rows(view="ALL")
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
        else:
            self.cached_market_data = dict(bbg_data) if bbg_data else {}
            self.bbg_ok = False
            self.group_health = self._compute_group_health(self.last_bbg_meta, self.cached_market_data)

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
        self._update_status_bar()
        self.refresh_ui()

        # Show success toast
        if self.bbg_ok and self.excel_ok:
            self.toast.success("Data refreshed successfully")
        elif self.bbg_ok or self.excel_ok:
            self.toast.warning("Partial data refresh - check connections")

        # Auto-save snapshot after successful data refresh
        if hasattr(self, 'funding_calc_data') and self.funding_calc_data:
            try:
                date_key = save_snapshot(self)
                log.info(f"Auto-saved snapshot: {date_key}")
            except Exception as e:
                log.error(f"Failed to auto-save snapshot: {e}")

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
    # Launch main application
    app = NiborTerminalCTK()

    # Import fixing history from Excel on startup
    try:
        from history import import_all_fixings_from_excel
        from pathlib import Path

        # Look for Excel file
        excel_candidates = [
            DATA_DIR / "Nibor history - wide.xlsx",
            DATA_DIR / "Referensräntor" / "Nibor" / "Nibor history - wide.xlsx",
            Path(__file__).parent / "data" / "Nibor history - wide.xlsx",
        ]

        for excel_path in excel_candidates:
            if excel_path.exists():
                log.info(f"[Startup] Found NIBOR history Excel: {excel_path}")
                total, saved = import_all_fixings_from_excel(excel_path)
                if saved > 0:
                    log.info(f"[Startup] Imported {saved} new fixing entries from Excel")
                break
        else:
            log.info("[Startup] NIBOR history Excel not found - skipping import")
    except Exception as e:
        log.warning(f"[Startup] Failed to import fixing history: {e}")

    app.mainloop()
