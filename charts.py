"""
Chart components for Nibor Calculation Terminal.
Provides trend graphs and comparison views using matplotlib.
"""
import tkinter as tk
from tkinter import ttk
from datetime import datetime
from typing import Optional

try:
    import matplotlib
    matplotlib.use('TkAgg')
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
    import matplotlib.dates as mdates
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

from config import THEME, CURRENT_MODE


class TrendChart(tk.Frame):
    """Interactive trend chart for NIBOR history."""

    def __init__(self, master, height=250):
        super().__init__(master, bg=THEME["bg_card"], highlightthickness=1,
                        highlightbackground=THEME["border"])
        self.height = height
        self._tenor_vars = {}
        self._data = []

        if not MATPLOTLIB_AVAILABLE:
            tk.Label(self, text="Matplotlib not available - install with: pip install matplotlib",
                    fg=THEME["muted"], bg=THEME["bg_card"],
                    font=("Segoe UI", 10)).pack(pady=20)
            return

        # Header
        header = tk.Frame(self, bg=THEME["bg_card"])
        header.pack(fill="x", padx=10, pady=(10, 5))

        tk.Label(header, text="NIBOR TREND", fg=THEME["muted"], bg=THEME["bg_card"],
                font=("Segoe UI", CURRENT_MODE["small"], "bold")).pack(side="left")

        # Tenor checkboxes
        cb_frame = tk.Frame(header, bg=THEME["bg_card"])
        cb_frame.pack(side="right")

        tenors = [("1M", "#e94560"), ("2M", "#4ade80"), ("3M", "#3b82f6"), ("6M", "#f59e0b")]
        for tenor, color in tenors:
            var = tk.BooleanVar(value=True)
            self._tenor_vars[tenor.lower()] = var
            cb = tk.Checkbutton(cb_frame, text=tenor, variable=var,
                               bg=THEME["bg_card"], fg=color,
                               selectcolor=THEME["bg_card"],
                               activebackground=THEME["bg_card"],
                               activeforeground=color,
                               font=("Segoe UI", 9, "bold"),
                               command=self._redraw)
            cb.pack(side="left", padx=5)

        # Create matplotlib figure
        self.fig = Figure(figsize=(8, height/100), dpi=100, facecolor=THEME["bg_card"])
        self.ax = self.fig.add_subplot(111)
        self._style_axes()

        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def _style_axes(self):
        """Apply dark theme styling to axes."""
        self.ax.set_facecolor(THEME["bg_card"])
        self.ax.tick_params(colors=THEME["muted"], labelsize=8)
        self.ax.spines['bottom'].set_color(THEME["border"])
        self.ax.spines['left'].set_color(THEME["border"])
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)
        self.ax.grid(True, alpha=0.2, color=THEME["border"])

    def set_data(self, history_data: list):
        """
        Set history data for chart.

        Args:
            history_data: List of dicts with 'date', '1m', '2m', '3m', '6m' keys
        """
        self._data = history_data
        self._redraw()

    def _redraw(self):
        """Redraw the chart with current data and settings."""
        if not MATPLOTLIB_AVAILABLE or not self._data:
            return

        self.ax.clear()
        self._style_axes()

        # Parse dates
        dates = []
        rates = {'1m': [], '2m': [], '3m': [], '6m': []}

        for row in reversed(self._data):  # Oldest first
            try:
                d = datetime.strptime(row['date'], "%Y-%m-%d")
                dates.append(d)
                for tenor in rates:
                    val = row.get(tenor)
                    rates[tenor].append(val if val is not None else float('nan'))
            except (ValueError, KeyError):
                continue

        if not dates:
            self.canvas.draw()
            return

        # Plot each tenor
        colors = {'1m': '#e94560', '2m': '#4ade80', '3m': '#3b82f6', '6m': '#f59e0b'}

        for tenor, color in colors.items():
            if self._tenor_vars.get(tenor, tk.BooleanVar(value=True)).get():
                self.ax.plot(dates, rates[tenor], color=color, linewidth=1.5,
                           label=tenor.upper(), marker='o', markersize=3)

        # Format x-axis
        self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
        self.ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        self.fig.autofmt_xdate(rotation=45)

        # Labels
        self.ax.set_ylabel('Rate (%)', color=THEME["muted"], fontsize=9)
        self.ax.legend(loc='upper left', fontsize=8, framealpha=0.8,
                      facecolor=THEME["bg_card"], labelcolor=THEME["text"])

        self.fig.tight_layout()
        self.canvas.draw()


class TrendPopup(tk.Toplevel):
    """Popup window showing NIBOR trend chart."""

    def __init__(self, parent, history_data: list = None):
        super().__init__(parent)
        self.title("NIBOR Trend History")
        self.geometry("700x450")
        self.configure(bg=THEME["bg_main"])
        self.transient(parent)

        # Center on parent
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - 700) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - 450) // 2
        self.geometry(f"+{x}+{y}")

        # Header
        header = tk.Frame(self, bg=THEME["bg_main"])
        header.pack(fill="x", padx=20, pady=(15, 10))

        tk.Label(header, text="📈 NIBOR TREND HISTORY",
                fg=THEME["accent"], bg=THEME["bg_main"],
                font=("Segoe UI", 14, "bold")).pack(side="left")

        # Close button in header
        close_btn = tk.Label(header, text="✕", font=("Segoe UI", 16),
                            fg=THEME["muted"], bg=THEME["bg_main"], cursor="hand2")
        close_btn.pack(side="right")
        close_btn.bind("<Button-1>", lambda e: self.destroy())
        close_btn.bind("<Enter>", lambda e: close_btn.config(fg=THEME["accent"]))
        close_btn.bind("<Leave>", lambda e: close_btn.config(fg=THEME["muted"]))

        # Chart
        if MATPLOTLIB_AVAILABLE:
            self.chart = TrendChart(self, height=320)
            self.chart.pack(fill="both", expand=True, padx=15, pady=(0, 15))

            if history_data:
                self.chart.set_data(history_data)
        else:
            tk.Label(self, text="Matplotlib not available\nInstall with: pip install matplotlib",
                    fg=THEME["muted"], bg=THEME["bg_main"],
                    font=("Segoe UI", 12)).pack(expand=True)

        # Bind Escape to close
        self.bind("<Escape>", lambda e: self.destroy())
        self.focus_set()

    def set_data(self, history_data: list):
        """Update chart data."""
        if hasattr(self, 'chart') and self.chart:
            self.chart.set_data(history_data)


class ComparisonView(tk.Toplevel):
    """Side-by-side comparison view for two dates."""

    def __init__(self, parent, history_data: dict, date1: str, date2: str):
        super().__init__(parent)
        self.title(f"Compare: {date1} vs {date2}")
        self.geometry("700x550")
        self.configure(bg=THEME["bg_main"])
        self.transient(parent)

        # Center on parent
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - 700) // 2
        y = parent.winfo_y() + (parent.winfo_height() - 550) // 2
        self.geometry(f"+{x}+{y}")

        snap1 = history_data.get(date1, {})
        snap2 = history_data.get(date2, {})

        # Header
        header = tk.Frame(self, bg=THEME["bg_main"])
        header.pack(fill="x", padx=20, pady=15)

        tk.Label(header, text="NIBOR COMPARISON", fg=THEME["accent"], bg=THEME["bg_main"],
                font=("Segoe UI", 14, "bold")).pack()

        # Main content
        content = tk.Frame(self, bg=THEME["bg_main"])
        content.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # Column headers
        col_header = tk.Frame(content, bg=THEME["bg_main"])
        col_header.pack(fill="x", pady=(0, 10))

        tk.Label(col_header, text="", width=15, bg=THEME["bg_main"]).pack(side="left")
        tk.Label(col_header, text=date1, width=15, fg=THEME["accent"], bg=THEME["bg_main"],
                font=("Segoe UI", 11, "bold")).pack(side="left", padx=10)
        tk.Label(col_header, text=date2, width=15, fg="#4ade80", bg=THEME["bg_main"],
                font=("Segoe UI", 11, "bold")).pack(side="left", padx=10)
        tk.Label(col_header, text="DIFF", width=10, fg=THEME["muted"], bg=THEME["bg_main"],
                font=("Segoe UI", 11, "bold")).pack(side="left", padx=10)

        # Separator
        tk.Frame(content, bg=THEME["border"], height=2).pack(fill="x", pady=5)

        # Scrollable content
        canvas = tk.Canvas(content, bg=THEME["bg_main"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(content, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=THEME["bg_main"])

        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # NIBOR Rates section
        self._add_section_header(scroll_frame, "NIBOR RATES")

        rates1 = snap1.get('rates', {})
        rates2 = snap2.get('rates', {})

        for tenor in ['1m', '2m', '3m', '6m']:
            r1 = rates1.get(tenor, {}).get('nibor')
            r2 = rates2.get(tenor, {}).get('nibor')
            self._add_comparison_row(scroll_frame, tenor.upper(), r1, r2)

        # Weights section
        self._add_section_header(scroll_frame, "WEIGHTS")

        w1 = snap1.get('weights', {})
        w2 = snap2.get('weights', {})

        for curr in ['USD', 'EUR', 'NOK']:
            v1 = w1.get(curr)
            v2 = w2.get(curr)
            self._add_comparison_row(scroll_frame, curr, v1, v2, is_pct=True)

        # Implied rates section
        self._add_section_header(scroll_frame, "IMPLIED EUR")
        for tenor in ['1m', '2m', '3m', '6m']:
            r1 = rates1.get(tenor, {}).get('eur_impl')
            r2 = rates2.get(tenor, {}).get('eur_impl')
            self._add_comparison_row(scroll_frame, tenor.upper(), r1, r2)

        self._add_section_header(scroll_frame, "IMPLIED USD")
        for tenor in ['1m', '2m', '3m', '6m']:
            r1 = rates1.get(tenor, {}).get('usd_impl')
            r2 = rates2.get(tenor, {}).get('usd_impl')
            self._add_comparison_row(scroll_frame, tenor.upper(), r1, r2)

        # Close button
        btn_frame = tk.Frame(self, bg=THEME["bg_main"])
        btn_frame.pack(fill="x", padx=20, pady=10)

        tk.Button(btn_frame, text="Close", command=self.destroy,
                 bg=THEME["chip2"], fg=THEME["text"], font=("Segoe UI", 10),
                 relief="flat", padx=20, pady=8, cursor="hand2").pack(side="right")

    def _add_section_header(self, parent, text: str):
        """Add a section header."""
        frame = tk.Frame(parent, bg=THEME["bg_card"])
        frame.pack(fill="x", pady=(15, 5))

        tk.Label(frame, text=text, fg=THEME["muted"], bg=THEME["bg_card"],
                font=("Segoe UI", 10, "bold")).pack(side="left", padx=10, pady=5)

    def _add_comparison_row(self, parent, label: str, val1, val2, is_pct=False):
        """Add a comparison row."""
        row = tk.Frame(parent, bg=THEME["bg_main"])
        row.pack(fill="x", pady=2)

        tk.Label(row, text=label, width=15, anchor="w", fg=THEME["text"],
                bg=THEME["bg_main"], font=("Segoe UI", 10)).pack(side="left")

        # Format values
        if is_pct:
            v1_str = f"{val1*100:.2f}%" if val1 is not None else "-"
            v2_str = f"{val2*100:.2f}%" if val2 is not None else "-"
        else:
            v1_str = f"{val1:.4f}" if val1 is not None else "-"
            v2_str = f"{val2:.4f}" if val2 is not None else "-"

        tk.Label(row, text=v1_str, width=15, anchor="center", fg=THEME["accent"],
                bg=THEME["bg_main"], font=("Consolas", 10)).pack(side="left", padx=10)

        tk.Label(row, text=v2_str, width=15, anchor="center", fg="#4ade80",
                bg=THEME["bg_main"], font=("Consolas", 10)).pack(side="left", padx=10)

        # Calculate diff
        if val1 is not None and val2 is not None:
            diff = val2 - val1
            if is_pct:
                diff_str = f"{diff*100:+.2f}%"
            else:
                diff_str = f"{diff:+.4f}"
            diff_color = THEME["good"] if diff >= 0 else THEME["bad"]
        else:
            diff_str = "-"
            diff_color = THEME["muted"]

        tk.Label(row, text=diff_str, width=10, anchor="center", fg=diff_color,
                bg=THEME["bg_main"], font=("Consolas", 10, "bold")).pack(side="left", padx=10)


class AuditLogViewer(tk.Frame):
    """Audit log viewer showing all system events."""

    def __init__(self, master, app):
        super().__init__(master, bg=THEME["bg_panel"])
        self.app = app
        self._log_entries = []

        # Header
        header = tk.Frame(self, bg=THEME["bg_panel"])
        header.pack(fill="x", padx=15, pady=10)

        tk.Label(header, text="AUDIT LOG", fg=THEME["muted"], bg=THEME["bg_panel"],
                font=("Segoe UI", CURRENT_MODE["h2"], "bold")).pack(side="left")

        # Filter frame
        filter_frame = tk.Frame(header, bg=THEME["bg_panel"])
        filter_frame.pack(side="right")

        tk.Label(filter_frame, text="Filter:", fg=THEME["text"], bg=THEME["bg_panel"],
                font=("Segoe UI", 10)).pack(side="left", padx=(0, 5))

        self.filter_var = tk.StringVar(value="ALL")
        for level in ["ALL", "INFO", "WARNING", "ERROR"]:
            tk.Radiobutton(filter_frame, text=level, variable=self.filter_var, value=level,
                          bg=THEME["bg_panel"], fg=THEME["text"],
                          selectcolor=THEME["bg_card"],
                          command=self._apply_filter).pack(side="left", padx=3)

        # Log text area
        log_frame = tk.Frame(self, bg=THEME["bg_card"], highlightthickness=1,
                            highlightbackground=THEME["border"])
        log_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        self.log_text = tk.Text(log_frame, bg=THEME["bg_card"], fg=THEME["text"],
                               font=("Consolas", 9), relief="flat", wrap="word",
                               highlightthickness=0)
        self.log_text.pack(fill="both", expand=True, padx=10, pady=10)

        # Configure tags for different log levels
        self.log_text.tag_configure("info", foreground="#3b82f6")
        self.log_text.tag_configure("warning", foreground="#f59e0b")
        self.log_text.tag_configure("error", foreground="#ef4444")
        self.log_text.tag_configure("success", foreground="#4ade80")
        self.log_text.tag_configure("timestamp", foreground=THEME["muted"])

        self.log_text.config(state="disabled")

    def add_entry(self, level: str, message: str, timestamp: Optional[datetime] = None):
        """Add a log entry."""
        ts = timestamp or datetime.now()
        entry = {
            'timestamp': ts,
            'level': level.upper(),
            'message': message
        }
        self._log_entries.append(entry)
        self._apply_filter()

    def _apply_filter(self):
        """Apply the current filter to log display."""
        filter_level = self.filter_var.get()

        self.log_text.config(state="normal")
        self.log_text.delete("1.0", "end")

        for entry in self._log_entries:
            if filter_level != "ALL" and entry['level'] != filter_level:
                continue

            ts_str = entry['timestamp'].strftime("%Y-%m-%d %H:%M:%S")
            level = entry['level']
            msg = entry['message']

            self.log_text.insert("end", f"[{ts_str}] ", "timestamp")

            tag = level.lower() if level in ["INFO", "WARNING", "ERROR"] else "info"
            self.log_text.insert("end", f"[{level}] ", tag)
            self.log_text.insert("end", f"{msg}\n")

        self.log_text.config(state="disabled")
        self.log_text.see("end")

    def clear(self):
        """Clear all log entries."""
        self._log_entries.clear()
        self.log_text.config(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.config(state="disabled")
