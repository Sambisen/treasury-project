"""
AuditLogPage for Nibor Calculation Terminal.
"""
import tkinter as tk
from tkinter import ttk
from datetime import datetime, timedelta

from config import THEME, CURRENT_MODE, get_logger

log = get_logger("ui_pages")
from ui_components import OnyxButtonTK


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


