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

from config import THEME, CURRENT_MODE, FONTS

# Tenor colors mapping - Professional colors for light theme
TENOR_COLORS = {
    '1w': '#7C3AED',  # Purple (Violet-600)
    '1m': '#DC2626',  # Red-600
    '2m': '#059669',  # Emerald-600
    '3m': '#2563EB',  # Blue-600 (Default)
    '6m': '#D97706'   # Amber-600
}

# Tenor display names
TENOR_LABELS = {
    '1w': '1 Week',
    '1m': '1 Month',
    '2m': '2 Months',
    '3m': '3 Months',
    '6m': '6 Months'
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
        # 1. Source checkboxes (both can be selected)
        self._show_contrib_var = tk.BooleanVar(value=True)
        self._show_fixing_var = tk.BooleanVar(value=True)
        self._show_contrib_var.trace_add("write", self._on_trace_change)
        self._show_fixing_var.trace_add("write", self._on_trace_change)
        # Legacy variable for compatibility
        self._source_var = tk.StringVar(value="contribution")

        # 2. Time Range (1M, 3M, 1Y...)
        self._range_var = tk.StringVar(value="3M")

        # 3. Selected Tenor (single selection via dropdown)
        self._selected_tenor = tk.StringVar(value="3m")
        self._selected_tenor.trace_add("write", self._on_trace_change)

        # 4. Tenor Checkboxes (for multi-select mode)
        self._tenor_vars = {
            '1w': tk.BooleanVar(value=False),
            '1m': tk.BooleanVar(value=False),
            '2m': tk.BooleanVar(value=False),
            '3m': tk.BooleanVar(value=True),
            '6m': tk.BooleanVar(value=False)
        }

        for var in self._tenor_vars.values():
            var.trace_add("write", self._on_trace_change)

        self._range_btns = {}

        if not MATPLOTLIB_AVAILABLE:
            tk.Label(self, text="Matplotlib not installed",
                    fg=THEME["muted"], bg=THEME["bg_card"],
                    font=("Segoe UI", 11)).pack(pady=20)
            return

        # ==========================
        # 1. CONTROLS HEADER
        # ==========================
        controls_frame = tk.Frame(self, bg=THEME["bg_card"])
        controls_frame.pack(fill="x", padx=15, pady=(12, 8))

        # --- LEFT: Source Selection (checkboxes - both can be selected) ---
        source_frame = tk.Frame(controls_frame, bg=THEME["bg_card"])
        source_frame.pack(side="left")

        tk.Label(source_frame, text="Source:", fg=THEME["muted"], bg=THEME["bg_card"],
                font=("Segoe UI", 9)).pack(side="left", padx=(0, 8))

        # Swedbank checkbox (Orange line)
        swedbank_cb = tk.Checkbutton(source_frame, text="Swedbank",
                                     variable=self._show_contrib_var,
                                     bg=THEME["bg_card"], fg="#EE7623",
                                     selectcolor=THEME["bg_card"], activebackground=THEME["bg_card"],
                                     activeforeground="#EE7623", font=("Segoe UI", 10, "bold"))
        swedbank_cb.pack(side="left", padx=4)

        # Fixing checkbox (Black line)
        fixing_cb = tk.Checkbutton(source_frame, text="Fixing",
                                   variable=self._show_fixing_var,
                                   bg=THEME["bg_card"], fg="#000000",
                                   selectcolor=THEME["bg_card"], activebackground=THEME["bg_card"],
                                   activeforeground="#000000", font=("Segoe UI", 10, "bold"))
        fixing_cb.pack(side="left", padx=4)

        # --- CENTER: Time Range Buttons ---
        range_frame = tk.Frame(controls_frame, bg=THEME["bg_card"])
        range_frame.pack(side="left", padx=40)

        tk.Label(range_frame, text="Period:", fg=THEME["muted"], bg=THEME["bg_card"],
                font=("Segoe UI", 9)).pack(side="left", padx=(0, 8))

        for label in ["1M", "3M", "1Y", "MAX"]:
            btn = tk.Button(range_frame, text=label,
                           command=lambda l=label: self._set_range(l),
                           font=("Segoe UI", 9, "bold"),
                           relief="flat", bd=0, padx=10, pady=4, cursor="hand2")
            btn.pack(side="left", padx=2)
            self._range_btns[label] = btn

        self._update_range_buttons_ui()

        # --- RIGHT: Tenor Checkboxes (improved styling) ---
        cb_frame = tk.Frame(controls_frame, bg=THEME["bg_card"])
        cb_frame.pack(side="right")

        tk.Label(cb_frame, text="Tenors:", fg=THEME["muted"], bg=THEME["bg_card"],
                font=("Segoe UI", 9)).pack(side="left", padx=(0, 8))

        for tenor in ['1w', '1m', '2m', '3m', '6m']:
            color = TENOR_COLORS.get(tenor, THEME["text"])
            cb = tk.Checkbutton(cb_frame, text=tenor.upper(),
                               variable=self._tenor_vars[tenor],
                               bg=THEME["bg_card"], fg=color,
                               selectcolor=THEME["bg_card"],
                               activebackground=THEME["bg_card"],
                               activeforeground=color,
                               font=("Segoe UI", 9, "bold"),
                               cursor="hand2")
            cb.pack(side="left", padx=3)

        # ==========================
        # 2. CHART CANVAS
        # ==========================
        self.fig = Figure(figsize=(8, height/100), dpi=100, facecolor=THEME["bg_card"])
        self.ax = self.fig.add_subplot(111)
        self._style_axes()

        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=15, pady=(0, 12))

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
        """Apply light Swedbank theme styling."""
        self.ax.set_facecolor(THEME["bg_card"])
        self.ax.tick_params(axis='x', colors=THEME["text"], labelsize=9)
        self.ax.tick_params(axis='y', colors=THEME["text"], labelsize=9)
        for spine in self.ax.spines.values():
            spine.set_color(THEME["border"])
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)
        self.ax.grid(True, alpha=0.3, color=THEME["border"], linestyle='-', linewidth=0.5)

    def _redraw(self):
        """Main drawing logic - supports both Swedbank and Fixing simultaneously."""
        if not MATPLOTLIB_AVAILABLE:
            return

        self.ax.clear()
        self._style_axes()

        # 1. Get current states
        show_contrib = self._show_contrib_var.get()
        show_fixing = self._show_fixing_var.get()
        time_range = self._range_var.get()

        # Build title based on selected sources
        title_parts = []
        if show_contrib:
            title_parts.append("SWEDBANK")
        if show_fixing:
            title_parts.append("FIXING")
        title = " + ".join(title_parts) if title_parts else "NO SOURCE SELECTED"

        self.ax.set_title(title, color=THEME["text"], loc='left', fontsize=10, pad=10)

        if not show_contrib and not show_fixing:
            self.ax.text(0.5, 0.5, "SELECT A SOURCE", ha='center', va='center',
                        color=THEME["muted"], transform=self.ax.transAxes)
            self.canvas.draw()
            return

        # 2. Calculate time cutoff
        today = datetime.now().date()
        if time_range == "MAX":
            cutoff = None
        elif time_range == "1M":
            cutoff = today - timedelta(days=30)
        elif time_range == "3M":
            cutoff = today - timedelta(days=90)
        elif time_range == "1Y":
            cutoff = today - timedelta(days=365)
        else:
            cutoff = today - timedelta(days=90)

        has_lines = False

        # 3. Get selected tenor
        selected_tenors = [t for t, var in self._tenor_vars.items() if var.get()]
        if not selected_tenors:
            selected_tenors = ['3m']  # Default

        # 4. Plot Swedbank data (Orange line)
        if show_contrib and self._contrib_data:
            plot_data = self._contrib_data if cutoff is None else [d for d in self._contrib_data if d['dt'] >= cutoff]
            if plot_data:
                dates = [d['dt'] for d in plot_data]
                for tenor in selected_tenors:
                    if tenor == '1w':
                        continue  # Skip 1W for contribution
                    rates = []
                    for row in plot_data:
                        val = row.get(tenor)
                        try:
                            rates.append(float(val) if val is not None and val != "" else float('nan'))
                        except (ValueError, TypeError):
                            rates.append(float('nan'))
                    valid_points = [r for r in rates if not math.isnan(r)]
                    if valid_points:
                        label = f"Swedbank {tenor.upper()}"
                        self.ax.plot(dates, rates, color='#EE7623', linewidth=2, label=label)
                        has_lines = True

        # 5. Plot Fixing data (Black line)
        if show_fixing and self._fixing_data:
            plot_data = self._fixing_data if cutoff is None else [d for d in self._fixing_data if d['dt'] >= cutoff]
            if plot_data:
                dates = [d['dt'] for d in plot_data]
                for tenor in selected_tenors:
                    rates = []
                    for row in plot_data:
                        val = row.get(tenor)
                        try:
                            rates.append(float(val) if val is not None and val != "" else float('nan'))
                        except (ValueError, TypeError):
                            rates.append(float('nan'))
                    valid_points = [r for r in rates if not math.isnan(r)]
                    if valid_points:
                        label = f"Fixing {tenor.upper()}"
                        self.ax.plot(dates, rates, color='#000000', linewidth=2, label=label)
                        has_lines = True

        if not has_lines:
            self.ax.text(0.5, 0.5, f"NO DATA FOR {time_range}", ha='center', va='center',
                        color=THEME["muted"], transform=self.ax.transAxes)
            self.canvas.draw()
            return

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
    """Popup with trend chart - Light Nordic theme, professional design."""

    # Light Nordic color palette
    LIGHT_BG = "#FAFBFC"           # Very light gray background
    LIGHT_CARD = "#FFFFFF"         # Pure white cards
    LIGHT_BORDER = "#E1E4E8"       # Soft gray border
    LIGHT_TEXT = "#24292E"         # Dark text
    LIGHT_MUTED = "#6A737D"        # Muted gray text
    LIGHT_ACCENT = "#0366D6"       # Nordic blue accent
    SWEDBANK_ORANGE = "#EE7623"    # Swedbank orange
    FIXING_BLUE = "#1B4F72"        # Dark blue for fixing

    def __init__(self, parent):
        super().__init__(parent)
        self.title("NIBOR Rates History")
        self.geometry("1200x750")
        self.configure(bg=self.LIGHT_BG)
        self.transient(parent)
        self.minsize(1000, 650)

        # Data storage
        self._contrib_data = []
        self._fixing_data = []
        self._current_view = "chart"  # "chart" or "table"
        self._hover_annotation = None

        # Center window
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - 1200) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - 750) // 2
        self.geometry(f"+{max(0, x)}+{max(0, y)}")

        # ==========================
        # HEADER - Clean white design
        # ==========================
        header = tk.Frame(self, bg=self.LIGHT_CARD, highlightthickness=0)
        header.pack(fill="x", padx=0, pady=0)

        # Shadow effect
        tk.Frame(self, bg=self.LIGHT_BORDER, height=1).pack(fill="x")

        header_inner = tk.Frame(header, bg=self.LIGHT_CARD)
        header_inner.pack(fill="x", padx=24, pady=18)

        # Title with icon
        title_frame = tk.Frame(header_inner, bg=self.LIGHT_CARD)
        title_frame.pack(side="left")

        tk.Label(title_frame, text="📈  NIBOR RATES HISTORY",
                fg=self.LIGHT_TEXT, bg=self.LIGHT_CARD,
                font=("Segoe UI Semibold", 20)).pack(side="left")

        # View toggle buttons (Chart / Table) - Pill style
        view_frame = tk.Frame(header_inner, bg=self.LIGHT_CARD)
        view_frame.pack(side="left", padx=40)

        self._view_btns = {}
        for view_name, label in [("chart", "📊 Chart"), ("table", "📋 Table")]:
            btn = tk.Button(view_frame, text=label,
                           command=lambda v=view_name: self._switch_view(v),
                           font=("Segoe UI", 10, "bold"),
                           relief="flat", bd=0, padx=16, pady=8, cursor="hand2")
            btn.pack(side="left", padx=2)
            self._view_btns[view_name] = btn

        self._update_view_buttons()

        # Tenor dropdown (for table view)
        tenor_frame = tk.Frame(header_inner, bg=self.LIGHT_CARD)
        tenor_frame.pack(side="left", padx=20)

        tk.Label(tenor_frame, text="Tenor:", fg=self.LIGHT_MUTED, bg=self.LIGHT_CARD,
                font=("Segoe UI", 10)).pack(side="left", padx=(0, 8))

        self._tenor_var = tk.StringVar(value="3m")
        self._tenor_dropdown = ttk.Combobox(tenor_frame, textvariable=self._tenor_var,
                                           values=["1W", "1M", "2M", "3M", "6M"],
                                           state="readonly", width=8, font=("Segoe UI", 10))
        self._tenor_dropdown.pack(side="left")
        self._tenor_dropdown.set("3M")
        self._tenor_dropdown.bind("<<ComboboxSelected>>", self._on_tenor_change)

        # Source checkboxes (both selected by default)
        source_frame = tk.Frame(header_inner, bg=self.LIGHT_CARD)
        source_frame.pack(side="left", padx=20)

        tk.Label(source_frame, text="Source:", fg=self.LIGHT_MUTED, bg=self.LIGHT_CARD,
                font=("Segoe UI", 10)).pack(side="left", padx=(0, 8))

        # BOTH selected by default!
        self._show_contrib_var = tk.BooleanVar(value=True)
        self._show_fixing_var = tk.BooleanVar(value=True)

        contrib_check = tk.Checkbutton(
            source_frame, text="Swedbank",
            variable=self._show_contrib_var,
            command=self._on_source_change,
            bg=self.LIGHT_CARD, fg=self.SWEDBANK_ORANGE,
            selectcolor=self.LIGHT_CARD,
            activebackground=self.LIGHT_CARD,
            activeforeground=self.SWEDBANK_ORANGE,
            font=("Segoe UI", 10, "bold")
        )
        contrib_check.pack(side="left", padx=(0, 10))

        fixing_check = tk.Checkbutton(
            source_frame, text="Fixing",
            variable=self._show_fixing_var,
            command=self._on_source_change,
            bg=self.LIGHT_CARD, fg=self.FIXING_BLUE,
            selectcolor=self.LIGHT_CARD,
            activebackground=self.LIGHT_CARD,
            activeforeground=self.FIXING_BLUE,
            font=("Segoe UI", 10, "bold")
        )
        fixing_check.pack(side="left")

        # Close button - Elegant X
        close_btn = tk.Label(header_inner, text="✕", font=("Segoe UI", 18),
                            fg=self.LIGHT_MUTED, bg=self.LIGHT_CARD, cursor="hand2")
        close_btn.pack(side="right")
        close_btn.bind("<Button-1>", lambda e: self.destroy())
        close_btn.bind("<Enter>", lambda e: close_btn.config(fg="#DC2626"))
        close_btn.bind("<Leave>", lambda e: close_btn.config(fg=self.LIGHT_MUTED))

        # ==========================
        # CONTENT AREA - Light background
        # ==========================
        self._content_frame = tk.Frame(self, bg=self.LIGHT_BG)
        self._content_frame.pack(fill="both", expand=True, padx=24, pady=20)

        # Chart view - Custom light themed chart
        self._chart_frame = tk.Frame(self._content_frame, bg=self.LIGHT_BG)
        self.chart = None
        self._setup_light_chart()

        # Table view
        self._table_frame = tk.Frame(self._content_frame, bg=self.LIGHT_BG)
        self._create_rates_table()

        # Show chart by default
        self._chart_frame.pack(fill="both", expand=True)

        # ==========================
        # FOOTER - Clean white
        # ==========================
        tk.Frame(self, bg=self.LIGHT_BORDER, height=1).pack(fill="x", side="bottom")
        footer = tk.Frame(self, bg=self.LIGHT_CARD)
        footer.pack(fill="x", side="bottom")

        footer_inner = tk.Frame(footer, bg=self.LIGHT_CARD)
        footer_inner.pack(fill="x", padx=24, pady=12)

        self._status_label = tk.Label(footer_inner, text="Loading data...",
                                     fg=self.LIGHT_MUTED, bg=self.LIGHT_CARD,
                                     font=("Segoe UI", 9))
        self._status_label.pack(side="left")

        # Hover info label (shows when hovering over chart)
        self._hover_label = tk.Label(footer_inner, text="",
                                    fg=self.LIGHT_ACCENT, bg=self.LIGHT_CARD,
                                    font=("Segoe UI Semibold", 10))
        self._hover_label.pack(side="right")

        # Bindings
        self.bind("<Escape>", lambda e: self.destroy())
        self.focus_set()

        # Load data
        self.after(100, self._load_data)

    def _setup_light_chart(self):
        """Create a custom light-themed matplotlib chart with hover support."""
        if not MATPLOTLIB_AVAILABLE:
            tk.Label(self._chart_frame, text="Matplotlib not installed",
                    fg=self.LIGHT_MUTED, bg=self.LIGHT_BG).pack(pady=40)
            return

        # Chart container with subtle shadow
        chart_container = tk.Frame(self._chart_frame, bg=self.LIGHT_CARD,
                                  highlightthickness=1, highlightbackground=self.LIGHT_BORDER)
        chart_container.pack(fill="both", expand=True)

        # Controls bar inside chart
        controls = tk.Frame(chart_container, bg=self.LIGHT_CARD)
        controls.pack(fill="x", padx=20, pady=(15, 5))

        # Time range buttons
        range_frame = tk.Frame(controls, bg=self.LIGHT_CARD)
        range_frame.pack(side="left")

        tk.Label(range_frame, text="Period:", fg=self.LIGHT_MUTED, bg=self.LIGHT_CARD,
                font=("Segoe UI", 9)).pack(side="left", padx=(0, 10))

        self._range_var = tk.StringVar(value="3M")
        self._range_btns = {}
        for label in ["1M", "3M", "1Y", "MAX"]:
            btn = tk.Button(range_frame, text=label,
                           command=lambda l=label: self._set_range(l),
                           font=("Segoe UI", 9, "bold"),
                           relief="flat", bd=0, padx=14, pady=6, cursor="hand2")
            btn.pack(side="left", padx=2)
            self._range_btns[label] = btn

        self._update_range_buttons()

        # Tenor checkboxes
        tenor_frame = tk.Frame(controls, bg=self.LIGHT_CARD)
        tenor_frame.pack(side="right")

        tk.Label(tenor_frame, text="Tenors:", fg=self.LIGHT_MUTED, bg=self.LIGHT_CARD,
                font=("Segoe UI", 9)).pack(side="left", padx=(0, 10))

        self._tenor_vars = {}
        tenor_colors = {'1w': '#7C3AED', '1m': '#DC2626', '2m': '#059669', '3m': '#2563EB', '6m': '#D97706'}
        for tenor in ['1m', '2m', '3m', '6m']:
            var = tk.BooleanVar(value=(tenor == '3m'))  # 3M selected by default
            self._tenor_vars[tenor] = var
            color = tenor_colors.get(tenor, self.LIGHT_TEXT)
            cb = tk.Checkbutton(tenor_frame, text=tenor.upper(),
                               variable=var, command=self._redraw_chart,
                               bg=self.LIGHT_CARD, fg=color,
                               selectcolor=self.LIGHT_CARD,
                               activebackground=self.LIGHT_CARD,
                               activeforeground=color,
                               font=("Segoe UI", 9, "bold"), cursor="hand2")
            cb.pack(side="left", padx=4)

        # Matplotlib figure - LIGHT THEME
        self.fig = Figure(figsize=(10, 5), dpi=100, facecolor=self.LIGHT_CARD)
        self.ax = self.fig.add_subplot(111)
        self._style_light_axes()

        self.canvas = FigureCanvasTkAgg(self.fig, master=chart_container)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=15, pady=(5, 15))

        # Connect hover event
        self.canvas.mpl_connect('motion_notify_event', self._on_hover)

    def _create_rates_table(self):
        """Create the scrollable rates table - Light theme."""
        # Table container with border
        table_container = tk.Frame(self._table_frame, bg=self.LIGHT_CARD,
                                  highlightthickness=1, highlightbackground=self.LIGHT_BORDER)
        table_container.pack(fill="both", expand=True)

        # Header row
        header_frame = tk.Frame(table_container, bg="#F6F8FA")
        header_frame.pack(fill="x")

        headers = [("Date", 120), ("Source", 100), ("Rate (%)", 100), ("Change", 80)]
        for header_text, width in headers:
            tk.Label(header_frame, text=header_text, fg=self.LIGHT_TEXT, bg="#F6F8FA",
                    font=("Segoe UI", 10, "bold"), width=width//8, anchor="w").pack(
                        side="left", padx=15, pady=10)

        # Scrollable area
        canvas = tk.Canvas(table_container, bg=self.LIGHT_CARD, highlightthickness=0)
        scrollbar = ttk.Scrollbar(table_container, orient="vertical", command=canvas.yview)
        self._table_scroll_frame = tk.Frame(canvas, bg=self.LIGHT_CARD)

        self._table_scroll_frame.bind("<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self._table_scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Mouse wheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

    def _populate_table(self):
        """Fill the table with data for selected tenor and sources - Light theme."""
        # Clear existing rows
        for widget in self._table_scroll_frame.winfo_children():
            widget.destroy()

        tenor = self._tenor_var.get().lower()
        show_contrib = self._show_contrib_var.get()
        show_fixing = self._show_fixing_var.get()

        # Combine data from selected sources
        combined_data = []
        if show_contrib and self._contrib_data:
            for row in self._contrib_data:
                row['_source'] = 'Swedbank'
            combined_data.extend(self._contrib_data)
        if show_fixing and self._fixing_data:
            for row in self._fixing_data:
                row['_source'] = 'Fixing'
            combined_data.extend(self._fixing_data)

        if not combined_data:
            tk.Label(self._table_scroll_frame, text="No data available",
                    fg=self.LIGHT_MUTED, bg=self.LIGHT_CARD,
                    font=("Segoe UI", 11)).pack(pady=40)
            return

        # Sort by date descending
        sorted_data = sorted(combined_data, key=lambda x: x.get('dt', datetime.min.date()), reverse=True)

        prev_rate = None
        for i, row in enumerate(sorted_data):
            date_val = row.get('dt')
            rate_val = row.get(tenor)
            source_label = row.get('_source', '-')

            if date_val is None:
                continue

            # Alternate row colors - light theme
            bg_color = self.LIGHT_CARD if i % 2 == 0 else "#F6F8FA"

            row_frame = tk.Frame(self._table_scroll_frame, bg=bg_color)
            row_frame.pack(fill="x")

            # Date
            date_str = date_val.strftime("%Y-%m-%d") if hasattr(date_val, 'strftime') else str(date_val)
            tk.Label(row_frame, text=date_str, fg=self.LIGHT_TEXT, bg=bg_color,
                    font=("Consolas", 10), width=15, anchor="w").pack(side="left", padx=15, pady=8)

            # Source with color
            source_color = self.SWEDBANK_ORANGE if source_label == 'Swedbank' else self.FIXING_BLUE
            tk.Label(row_frame, text=source_label, fg=source_color, bg=bg_color,
                    font=("Segoe UI", 9, "bold"), width=10, anchor="w").pack(side="left", padx=10, pady=8)

            # Rate
            try:
                rate_float = float(rate_val) if rate_val is not None else None
                rate_str = f"{rate_float:.4f}%" if rate_float is not None else "-"
            except (ValueError, TypeError):
                rate_float = None
                rate_str = "-"

            tk.Label(row_frame, text=rate_str, fg=self.LIGHT_ACCENT, bg=bg_color,
                    font=("Consolas", 10, "bold"), width=12, anchor="w").pack(side="left", padx=15, pady=8)

            # Change
            if rate_float is not None and prev_rate is not None:
                change = rate_float - prev_rate
                change_str = f"{change:+.4f}"
                change_color = "#059669" if change >= 0 else "#DC2626"  # Green/Red
            else:
                change_str = "-"
                change_color = self.LIGHT_MUTED

            tk.Label(row_frame, text=change_str, fg=change_color, bg=bg_color,
                    font=("Consolas", 10), width=10, anchor="w").pack(side="left", padx=15, pady=8)

            prev_rate = rate_float

        self._status_label.config(text=f"📋 Showing {len(sorted_data)} entries for {tenor.upper()}")

    def _switch_view(self, view_name):
        """Switch between chart and table view."""
        self._current_view = view_name
        self._update_view_buttons()

        if view_name == "chart":
            self._table_frame.pack_forget()
            self._chart_frame.pack(fill="both", expand=True)
        else:
            self._chart_frame.pack_forget()
            self._table_frame.pack(fill="both", expand=True)
            self._populate_table()

    def _update_view_buttons(self):
        """Update visual state of view toggle buttons."""
        for view_name, btn in self._view_btns.items():
            if view_name == self._current_view:
                btn.config(bg=self.LIGHT_ACCENT, fg="white")
            else:
                btn.config(bg="#E1E4E8", fg=self.LIGHT_TEXT)

    def _on_tenor_change(self, event=None):
        """Handle tenor dropdown change."""
        if self._current_view == "table":
            self._populate_table()

    def _on_source_change(self, event=None):
        """Handle source checkbox change."""
        show_contrib = self._show_contrib_var.get()
        show_fixing = self._show_fixing_var.get()

        # Determine which source to show in chart (prefer contribution if both selected)
        if show_contrib and show_fixing:
            new_source = "both"
        elif show_contrib:
            new_source = "contribution"
        elif show_fixing:
            new_source = "fixing"
        else:
            new_source = "contribution"  # Default fallback

        # Update chart if visible
        if self.chart and hasattr(self.chart, '_source_var'):
            # For now, set to contribution or fixing (chart may need update to support both)
            if new_source == "both":
                self.chart._source_var.set("contribution")  # Show contribution in chart
            else:
                self.chart._source_var.set(new_source)

        # Update table if visible
        if self._current_view == "table":
            self._populate_table()

        # Update our custom chart
        self._redraw_chart()

    def _style_light_axes(self):
        """Apply light Nordic theme to chart axes."""
        self.ax.set_facecolor(self.LIGHT_CARD)
        self.ax.tick_params(axis='x', colors=self.LIGHT_TEXT, labelsize=9)
        self.ax.tick_params(axis='y', colors=self.LIGHT_TEXT, labelsize=9)
        for spine in self.ax.spines.values():
            spine.set_color(self.LIGHT_BORDER)
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)
        self.ax.grid(True, alpha=0.4, color=self.LIGHT_BORDER, linestyle='-', linewidth=0.5)

    def _set_range(self, range_val):
        """Handle range button click."""
        self._range_var.set(range_val)
        self._update_range_buttons()
        self._redraw_chart()

    def _update_range_buttons(self):
        """Update visual state of range buttons."""
        current = self._range_var.get()
        for label, btn in self._range_btns.items():
            if label == current:
                btn.config(bg=self.LIGHT_ACCENT, fg="white")
            else:
                btn.config(bg="#E1E4E8", fg=self.LIGHT_MUTED)

    def _redraw_chart(self):
        """Main chart drawing logic with light theme."""
        if not MATPLOTLIB_AVAILABLE or not hasattr(self, 'ax'):
            return

        self.ax.clear()
        self._style_light_axes()

        # Get current states
        show_contrib = self._show_contrib_var.get()
        show_fixing = self._show_fixing_var.get()
        time_range = self._range_var.get()

        # Build title
        title_parts = []
        if show_contrib:
            title_parts.append("SWEDBANK")
        if show_fixing:
            title_parts.append("FIXING")
        title = " + ".join(title_parts) if title_parts else "Select a source"

        self.ax.set_title(title, color=self.LIGHT_TEXT, loc='left', fontsize=11,
                         fontweight='semibold', pad=10)

        if not show_contrib and not show_fixing:
            self.ax.text(0.5, 0.5, "Select a source above", ha='center', va='center',
                        color=self.LIGHT_MUTED, fontsize=12, transform=self.ax.transAxes)
            self.canvas.draw()
            return

        # Calculate time cutoff
        today = datetime.now().date()
        if time_range == "MAX":
            cutoff = None
        elif time_range == "1M":
            cutoff = today - timedelta(days=30)
        elif time_range == "3M":
            cutoff = today - timedelta(days=90)
        elif time_range == "1Y":
            cutoff = today - timedelta(days=365)
        else:
            cutoff = today - timedelta(days=90)

        has_lines = False
        self._plot_lines = []  # Store for hover detection

        # Get selected tenors
        selected_tenors = [t for t, var in self._tenor_vars.items() if var.get()]
        if not selected_tenors:
            selected_tenors = ['3m']

        # Plot Swedbank data (Orange)
        if show_contrib and self._contrib_data:
            plot_data = self._contrib_data if cutoff is None else [d for d in self._contrib_data if d['dt'] >= cutoff]
            if plot_data:
                dates = [d['dt'] for d in plot_data]
                for tenor in selected_tenors:
                    rates = []
                    for row in plot_data:
                        val = row.get(tenor)
                        try:
                            rates.append(float(val) if val is not None and val != "" else float('nan'))
                        except (ValueError, TypeError):
                            rates.append(float('nan'))
                    valid_points = [r for r in rates if not math.isnan(r)]
                    if valid_points:
                        label = f"Swedbank {tenor.upper()}"
                        line, = self.ax.plot(dates, rates, color=self.SWEDBANK_ORANGE,
                                           linewidth=2.5, label=label, marker='o', markersize=3)
                        self._plot_lines.append((line, dates, rates, label, 'Swedbank'))
                        has_lines = True

        # Plot Fixing data (Dark blue)
        if show_fixing and self._fixing_data:
            plot_data = self._fixing_data if cutoff is None else [d for d in self._fixing_data if d['dt'] >= cutoff]
            if plot_data:
                dates = [d['dt'] for d in plot_data]
                for tenor in selected_tenors:
                    rates = []
                    for row in plot_data:
                        val = row.get(tenor)
                        try:
                            rates.append(float(val) if val is not None and val != "" else float('nan'))
                        except (ValueError, TypeError):
                            rates.append(float('nan'))
                    valid_points = [r for r in rates if not math.isnan(r)]
                    if valid_points:
                        label = f"Fixing {tenor.upper()}"
                        line, = self.ax.plot(dates, rates, color=self.FIXING_BLUE,
                                           linewidth=2.5, label=label, marker='s', markersize=3)
                        self._plot_lines.append((line, dates, rates, label, 'Fixing'))
                        has_lines = True

        if not has_lines:
            self.ax.text(0.5, 0.5, f"No data for {time_range}", ha='center', va='center',
                        color=self.LIGHT_MUTED, fontsize=12, transform=self.ax.transAxes)
            self.canvas.draw()
            return

        # Date formatting - INCLUDE YEAR for MAX and 1Y!
        if time_range in ["MAX", "1Y"]:
            self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%d %b %Y'))
        else:
            self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%d %b'))

        # Adaptive tick locator
        if time_range == "1M":
            self.ax.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=mdates.MO))
        elif time_range == "3M":
            self.ax.xaxis.set_major_locator(mdates.DayLocator(interval=14))
        elif time_range == "1Y":
            self.ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
        else:  # MAX
            self.ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))

        self.fig.autofmt_xdate(rotation=30, ha='right')

        # Y-axis formatting
        self.ax.set_ylabel('Rate (%)', color=self.LIGHT_TEXT, fontsize=10)
        self.ax.yaxis.set_major_formatter(lambda x, p: f'{x:.2f}%')

        # Legend - Professional style
        if has_lines:
            legend = self.ax.legend(loc='upper right', fontsize=9, framealpha=0.95,
                                   facecolor=self.LIGHT_CARD, edgecolor=self.LIGHT_BORDER,
                                   labelcolor=self.LIGHT_TEXT)
            legend.get_frame().set_linewidth(1)

        self.fig.tight_layout()
        self.canvas.draw()

    def _on_hover(self, event):
        """Handle mouse hover to show rate and date."""
        if event.inaxes != self.ax or not hasattr(self, '_plot_lines'):
            if hasattr(self, '_hover_label'):
                self._hover_label.config(text="")
            return

        # Find closest point
        closest_dist = float('inf')
        closest_info = None

        for line, dates, rates, label, source in self._plot_lines:
            for i, (d, r) in enumerate(zip(dates, rates)):
                if math.isnan(r):
                    continue
                # Convert date to matplotlib number for comparison
                try:
                    d_num = mdates.date2num(d)
                    dist = abs(event.xdata - d_num) + abs(event.ydata - r) * 10
                    if dist < closest_dist:
                        closest_dist = dist
                        closest_info = (d, r, label, source)
                except:
                    pass

        if closest_info and closest_dist < 5:
            d, r, label, source = closest_info
            date_str = d.strftime('%Y-%m-%d') if hasattr(d, 'strftime') else str(d)
            self._hover_label.config(text=f"📍 {date_str}  |  {label}: {r:.4f}%")
        else:
            self._hover_label.config(text="")

    def _load_data(self):
        """Load rates data from history."""
        from history import get_rates_table_data, get_fixing_table_data

        contrib = get_rates_table_data(limit=500)
        fixing = get_fixing_table_data(limit=500)

        # Process data
        self._contrib_data = self._process_data(contrib)
        self._fixing_data = self._process_data(fixing)

        # Update our embedded chart
        self._redraw_chart()

        # Update status
        contrib_count = len(self._contrib_data)
        fixing_count = len(self._fixing_data)
        self._status_label.config(text=f"📊 Swedbank: {contrib_count} entries  |  Fixing: {fixing_count} entries")

    def _process_data(self, raw_data):
        """Normalize and process data."""
        processed = []
        if not raw_data:
            return processed

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

                date_val = new_row.get('date') or new_row.get('timestamp')
                if date_val:
                    d_str = str(date_val).split("T")[0].split(" ")[0]
                    new_row['dt'] = datetime.strptime(d_str, "%Y-%m-%d").date()
                    processed.append(new_row)
            except Exception:
                continue

        return processed


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