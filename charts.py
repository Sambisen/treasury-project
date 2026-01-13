"""
Chart components for Nibor Calculation Terminal.
Provides trend graphs and comparison views using matplotlib.
"""
import tkinter as tk
from tkinter import ttk
from datetime import datetime, timedelta
import math

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

# Tenor colors mapping
TENOR_COLORS = {
    '1w': '#a855f7',  # Purple
    '1m': '#e94560',  # Red
    '2m': '#4ade80',  # Green
    '3m': '#3b82f6',  # Blue (Default)
    '6m': '#f59e0b'   # Orange
}

class TrendChart(tk.Frame):
    """Interactive trend chart with robust state management via Variable Tracing."""

    def __init__(self, master, height=250):
        super().__init__(master, bg=THEME["bg_card"], highlightthickness=1,
                         highlightbackground=THEME["border"])
        self.height = height
        
        # --- DATA STATE ---
        self._contrib_data = [] 
        self._fixing_data = []
        
        # --- UI STATE VARIABLES ---
        # Vi skapar variablerna här och lägger till en "trace" (bevakning) på dem.
        # Detta garanterar att _redraw kallas så fort värdet ändras.
        
        # 1. Source (Swedbank vs Fixing)
        self._source_var = tk.StringVar(value="contribution")
        self._source_var.trace_add("write", self._on_trace_change)
        
        # 2. Time Range (1M, 3M, 1Y...)
        self._range_var = tk.StringVar(value="3M")
        # Range uppdateras via vanliga knappar, så vi behöver ingen trace här, 
        # men vi sparar den för state.
        
        # 3. Tenor Checkboxes (1W, 1M, 2M, 3M, 6M)
        self._tenor_vars = {
            '1w': tk.BooleanVar(value=False),
            '1m': tk.BooleanVar(value=False),
            '2m': tk.BooleanVar(value=False),
            '3m': tk.BooleanVar(value=True), # Default ON
            '6m': tk.BooleanVar(value=False)
        }
        
        # Lägg till trace på varje tenor-variabel
        for var in self._tenor_vars.values():
            var.trace_add("write", self._on_trace_change)
        
        self._range_btns = {}

        if not MATPLOTLIB_AVAILABLE:
            tk.Label(self, text="Matplotlib missing", fg="white", bg=THEME["bg_card"]).pack(pady=20)
            return

        # ==========================
        # 1. CONTROLS HEADER
        # ==========================
        controls_frame = tk.Frame(self, bg=THEME["bg_card"])
        controls_frame.pack(fill="x", padx=10, pady=(10, 5))

        # --- LEFT: Source Selection ---
        source_frame = tk.Frame(controls_frame, bg=THEME["bg_card"])
        source_frame.pack(side="left")
        
        # Notera: Inget 'command=' här, vi förlitar oss på trace
        for text, val in [("Swedbank", "contribution"), ("Fixing", "fixing")]:
            rb = tk.Radiobutton(source_frame, text=text, variable=self._source_var, value=val,
                               bg=THEME["bg_card"], fg=THEME["text"],
                               selectcolor=THEME["bg_card"], activebackground=THEME["bg_card"],
                               activeforeground=THEME["accent"], font=("Segoe UI", 9))
            rb.pack(side="left", padx=5)

        # --- CENTER: Time Range Buttons ---
        range_frame = tk.Frame(controls_frame, bg=THEME["bg_card"])
        range_frame.pack(side="left", padx=30)
        
        for label in ["1M", "3M", "1Y", "MAX"]:
            btn = tk.Button(range_frame, text=label, 
                           command=lambda l=label: self._set_range(l),
                           font=("Segoe UI", 8, "bold"),
                           relief="flat", bd=0, padx=8, pady=2, cursor="hand2")
            btn.pack(side="left", padx=1)
            self._range_btns[label] = btn
        
        self._update_range_buttons_ui()

        # --- RIGHT: Tenor Checkboxes ---
        cb_frame = tk.Frame(controls_frame, bg=THEME["bg_card"])
        cb_frame.pack(side="right")
        
        for tenor in ['1w', '1m', '2m', '3m', '6m']:
            color = TENOR_COLORS.get(tenor, '#fff')
            # Inget 'command=' här heller, trace sköter det
            cb = tk.Checkbutton(cb_frame, text=tenor.upper(), 
                               variable=self._tenor_vars[tenor],
                               bg=THEME["bg_card"], fg=color,
                               selectcolor=THEME["bg_card"],
                               activebackground=THEME["bg_card"],
                               activeforeground=color,
                               font=("Segoe UI", 9, "bold"))
            cb.pack(side="left", padx=4)

        # ==========================
        # 2. CHART CANVAS
        # ==========================
        self.fig = Figure(figsize=(8, height/100), dpi=100, facecolor=THEME["bg_card"])
        self.ax = self.fig.add_subplot(111)
        self._style_axes()

        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def _on_trace_change(self, *args):
        """Called automatically when any variable changes."""
        # print(f"DEBUG: Variable changed! Redrawing...") 
        self._redraw()

    def _set_range(self, range_val):
        """Handle range button click."""
        self._range_var.set(range_val)
        self._update_range_buttons_ui()
        self._redraw()

    def _update_range_buttons_ui(self):
        """Update visual state of range buttons."""
        current = self._range_var.get()
        for label, btn in self._range_btns.items():
            if label == current:
                btn.config(bg=THEME["accent"], fg="white")
            else:
                btn.config(bg=THEME["bg_card_2"], fg=THEME["muted"])

    def _process_data(self, raw_data):
        """Normalize keys and convert dates."""
        processed = []
        if not raw_data:
            return processed
            
        print(f"[Chart] Processing {len(raw_data)} rows...")
        
        # Helper to normalize keys
        def normalize_key(k):
            k = str(k).lower().strip()
            if k in ['1 week', '1week', '1 w']: return '1w'
            if k in ['1 month', '1month', '1 m', '1m_days']: return '1m'
            if k in ['2 months', '2months', '2 month', '2 m', '2m_days']: return '2m'
            if k in ['3 months', '3months', '3 month', '3 m', '3m_days']: return '3m'
            if k in ['6 months', '6months', '6 month', '6 m', '6m_days']: return '6m'
            return k

        for row in raw_data:
            try:
                new_row = {}
                for k, v in row.items():
                    norm_k = normalize_key(k)
                    new_row[norm_k] = v
                
                # Handle Date
                date_val = new_row.get('date') or new_row.get('timestamp')
                if date_val:
                    d_str = str(date_val).split("T")[0].split(" ")[0]
                    new_row['dt'] = datetime.strptime(d_str, "%Y-%m-%d").date()
                    processed.append(new_row)
            except Exception:
                continue
        
        processed.sort(key=lambda x: x['dt'])
        return processed

    def set_data(self, contribution_data: list, fixing_data: list):
        """Load data from backend."""
        print("[Chart] Setting data in chart component...")
        self._contrib_data = self._process_data(contribution_data)
        self._fixing_data = self._process_data(fixing_data)
        self._redraw()

    def _style_axes(self):
        """Apply dark theme styling."""
        self.ax.set_facecolor(THEME["bg_card"])
        self.ax.tick_params(axis='x', colors=THEME["muted"], labelsize=8)
        self.ax.tick_params(axis='y', colors=THEME["muted"], labelsize=8)
        for spine in self.ax.spines.values():
            spine.set_color(THEME["border"])
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)
        self.ax.grid(True, alpha=0.15, color=THEME["border"], linestyle='--')

    def _redraw(self):
        """Main drawing logic."""
        if not MATPLOTLIB_AVAILABLE:
            return

        self.ax.clear()
        self._style_axes()

        # 1. Get current states
        source = self._source_var.get()
        time_range = self._range_var.get()
        
        # print(f"DEBUG: Redrawing. Source={source}, Range={time_range}")
        
        # 2. Choose Data Source
        if source == "fixing":
            data_source = self._fixing_data
            title = "NIBOR FIXING (Official)"
            color_title = "#4ade80"
        else:
            data_source = self._contrib_data
            title = "SWEDBANK (Internal)"
            color_title = THEME["accent"]

        self.ax.set_title(title, color=color_title, loc='left', fontsize=10, pad=10)

        if not data_source:
            self.ax.text(0.5, 0.5, "NO DATA", ha='center', va='center', 
                        color=THEME["muted"], transform=self.ax.transAxes)
            self.canvas.draw()
            return

        # 3. Filter Time Range
        if time_range == "MAX":
            plot_data = data_source
        else:
            today = datetime.now().date()
            cutoff = today # Default fallback
            
            if time_range == "1M":
                cutoff = today - timedelta(days=30)
            elif time_range == "3M":
                cutoff = today - timedelta(days=90)
            elif time_range == "1Y":
                cutoff = today - timedelta(days=365)
            else:
                cutoff = today - timedelta(days=90)
            
            plot_data = [d for d in data_source if d['dt'] >= cutoff]

        if not plot_data:
            self.ax.text(0.5, 0.5, f"NO DATA FOR {time_range}", ha='center', va='center', 
                        color=THEME["muted"], transform=self.ax.transAxes)
            self.canvas.draw()
            return

        dates = [d['dt'] for d in plot_data]
        has_lines = False

        # 4. Plot Lines based on Checked Boxes
        tenors = ['1w', '1m', '2m', '3m', '6m']
        for tenor in tenors:
            # Skip 1W for contribution if empty (usually is)
            if source == "contribution" and tenor == '1w':
                # Check if data exists just in case
                if not any(row.get('1w') for row in plot_data):
                    continue

            # If checked
            if self._tenor_vars[tenor].get():
                rates = []
                for row in plot_data:
                    val = row.get(tenor)
                    # Convert to float, handle None
                    try:
                        rates.append(float(val) if val is not None and val != "" else float('nan'))
                    except (ValueError, TypeError):
                        rates.append(float('nan'))
                
                # Only plot if we have at least one valid number
                valid_points = [r for r in rates if not math.isnan(r)]
                if valid_points:
                    self.ax.plot(dates, rates, 
                               color=TENOR_COLORS.get(tenor, '#fff'), 
                               linewidth=1.5, label=tenor.upper())
                    has_lines = True

        # Formatting
        self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%d %b'))
        
        # Adaptive ticks
        if time_range == "1M":
            self.ax.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=mdates.MO))
        elif time_range == "3M":
            self.ax.xaxis.set_major_locator(mdates.DayLocator(interval=14))
        else:
            self.ax.xaxis.set_major_locator(mdates.AutoDateLocator())

        self.fig.autofmt_xdate(rotation=0, ha='center')
        
        if has_lines:
            self.ax.legend(loc='upper left', fontsize=8, framealpha=0.9,
                          facecolor=THEME["bg_card"], labelcolor=THEME["text"])
        else:
             self.ax.text(0.5, 0.5, "SELECT TENOR", ha='center', va='center', 
                        color=THEME["muted"], transform=self.ax.transAxes)

        self.fig.tight_layout()
        self.canvas.draw()


class TrendPopup(tk.Toplevel):
    """Popup wrapper for TrendChart."""

    def __init__(self, parent):
        super().__init__(parent)
        self.title("NIBOR Trend Analysis")
        self.geometry("900x550")
        self.configure(bg=THEME["bg_main"])
        self.transient(parent)

        # Center
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - 900) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - 550) // 2
        self.geometry(f"+{x}+{y}")

        # Header
        header = tk.Frame(self, bg=THEME["bg_main"])
        header.pack(fill="x", padx=20, pady=(15, 5))

        tk.Label(header, text="📈 NIBOR ANALYTICS", 
                 fg=THEME["accent"], bg=THEME["bg_main"],
                 font=("Segoe UI", 16, "bold")).pack(side="left")

        close_btn = tk.Label(header, text="✕", font=("Segoe UI", 14),
                            fg=THEME["muted"], bg=THEME["bg_main"], cursor="hand2")
        close_btn.pack(side="right")
        close_btn.bind("<Button-1>", lambda e: self.destroy())
        close_btn.bind("<Enter>", lambda e: close_btn.config(fg=THEME["accent"]))
        close_btn.bind("<Leave>", lambda e: close_btn.config(fg=THEME["muted"]))

        if MATPLOTLIB_AVAILABLE:
            self.chart = TrendChart(self, height=400)
            self.chart.pack(fill="both", expand=True, padx=15, pady=(0, 15))
            
            # Start loading data immediately
            # Using .after to allow UI to render first
            self.after(100, self._load_data)
        else:
            tk.Label(self, text="Matplotlib missing", fg="white", bg=THEME["bg_main"]).pack()

        self.bind("<Escape>", lambda e: self.destroy())
        self.focus_set()

    def _load_data(self):
        from history import get_rates_table_data, get_fixing_table_data
        contrib = get_rates_table_data(limit=500)
        fixing = get_fixing_table_data(limit=500)
        
        if self.chart:
            self.chart.set_data(contribution_data=contrib, fixing_data=fixing)


class ComparisonView(tk.Toplevel):
    """Side-by-side comparison view for two dates."""

    def __init__(self, parent, history_data: dict, date1: str, date2: str):
        super().__init__(parent)
        self.title(f"Compare: {date1} vs {date2}")
        self.geometry("700x550")
        self.configure(bg=THEME["bg_main"])
        self.transient(parent)

        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - 700) // 2
        y = parent.winfo_y() + (parent.winfo_height() - 550) // 2
        self.geometry(f"+{x}+{y}")

        snap1 = history_data.get(date1, {})
        snap2 = history_data.get(date2, {})

        header = tk.Frame(self, bg=THEME["bg_main"])
        header.pack(fill="x", padx=20, pady=15)

        tk.Label(header, text="NIBOR COMPARISON", fg=THEME["accent"], bg=THEME["bg_main"],
                 font=("Segoe UI", 14, "bold")).pack()

        content = tk.Frame(self, bg=THEME["bg_main"])
        content.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        col_header = tk.Frame(content, bg=THEME["bg_main"])
        col_header.pack(fill="x", pady=(0, 10))

        tk.Label(col_header, text="", width=15, bg=THEME["bg_main"]).pack(side="left")
        tk.Label(col_header, text=date1, width=15, fg=THEME["accent"], bg=THEME["bg_main"],
                 font=("Segoe UI", 11, "bold")).pack(side="left", padx=10)
        tk.Label(col_header, text=date2, width=15, fg="#4ade80", bg=THEME["bg_main"],
                 font=("Segoe UI", 11, "bold")).pack(side="left", padx=10)
        tk.Label(col_header, text="DIFF", width=10, fg=THEME["muted"], bg=THEME["bg_main"],
                 font=("Segoe UI", 11, "bold")).pack(side="left", padx=10)

        tk.Frame(content, bg=THEME["border"], height=2).pack(fill="x", pady=5)

        canvas = tk.Canvas(content, bg=THEME["bg_main"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(content, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=THEME["bg_main"])

        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self._add_section_header(scroll_frame, "NIBOR RATES")
        rates1 = snap1.get('rates', {})
        rates2 = snap2.get('rates', {})

        for tenor in ['1m', '2m', '3m', '6m']:
            r1 = rates1.get(tenor, {}).get('nibor')
            r2 = rates2.get(tenor, {}).get('nibor')
            self._add_comparison_row(scroll_frame, tenor.upper(), r1, r2)

        self._add_section_header(scroll_frame, "WEIGHTS")
        w1 = snap1.get('weights', {})
        w2 = snap2.get('weights', {})
        for curr in ['USD', 'EUR', 'NOK']:
            v1 = w1.get(curr)
            v2 = w2.get(curr)
            self._add_comparison_row(scroll_frame, curr, v1, v2, is_pct=True)

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

        btn_frame = tk.Frame(self, bg=THEME["bg_main"])
        btn_frame.pack(fill="x", padx=20, pady=10)
        tk.Button(btn_frame, text="Close", command=self.destroy,
                  bg=THEME["chip2"], fg=THEME["text"], font=("Segoe UI", 10),
                  relief="flat", padx=20, pady=8, cursor="hand2").pack(side="right")

    def _add_section_header(self, parent, text: str):
        frame = tk.Frame(parent, bg=THEME["bg_card"])
        frame.pack(fill="x", pady=(15, 5))
        tk.Label(frame, text=text, fg=THEME["muted"], bg=THEME["bg_card"],
                 font=("Segoe UI", 10, "bold")).pack(side="left", padx=10, pady=5)

    def _add_comparison_row(self, parent, label: str, val1, val2, is_pct=False):
        row = tk.Frame(parent, bg=THEME["bg_main"])
        row.pack(fill="x", pady=2)
        tk.Label(row, text=label, width=15, anchor="w", fg=THEME["text"],
                 bg=THEME["bg_main"], font=("Segoe UI", 10)).pack(side="left")

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

        if val1 is not None and val2 is not None:
            diff = val2 - val1
            if is_pct: diff_str = f"{diff*100:+.2f}%"
            else: diff_str = f"{diff:+.4f}"
            diff_color = THEME["good"] if diff >= 0 else THEME["bad"]
        else:
            diff_str = "-"
            diff_color = THEME["muted"]

        tk.Label(row, text=diff_str, width=10, anchor="center", fg=diff_color,
                 bg=THEME["bg_main"], font=("Consolas", 10, "bold")).pack(side="left", padx=10)