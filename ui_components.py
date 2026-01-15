"""
UI components for Onyx Terminal.
Contains reusable GUI widgets.
"""
import tkinter as tk
from tkinter import ttk
from datetime import datetime

import matplotlib
matplotlib.use('TkAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from config import THEME, CURRENT_MODE
from utils import fmt_ts, LogoPipelineTK


def style_ttk(root: tk.Tk):
    """Apply Onyx theme to ttk widgets."""
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except Exception:
        pass

    style.configure(
        "Treeview",
        background=THEME["bg_card"],
        fieldbackground=THEME["bg_card"],
        foreground=THEME["text"],
        rowheight=28,
        bordercolor=THEME["border"],
        borderwidth=1,
        font=("Segoe UI", CURRENT_MODE["small"]),
    )
    style.configure(
        "Treeview.Heading",
        background=THEME["bg_card_2"],
        foreground=THEME["muted"],
        relief="flat",
        font=("Segoe UI", CURRENT_MODE["small"], "bold"),
    )
    style.map(
        "Treeview",
        background=[("selected", THEME["tree_sel_bg"])],
        foreground=[("selected", THEME["text"])],
    )


class OnyxButtonTK(tk.Button):
    """Styled button for Onyx Terminal."""

    def __init__(self, master, text, command=None, variant="default", **kwargs):
        if variant == "accent":
            bg = THEME["accent"]
            fg = "#101216"
            activebg = THEME["accent2"]
            activefg = "#101216"
        elif variant == "danger":
            bg = THEME["bad"]
            fg = "#101216"
            activebg = "#F87171"
            activefg = "#101216"
        else:
            bg = THEME["chip2"]
            fg = THEME["text"]
            activebg = "#2B2B2B"
            activefg = THEME["text"]

        super().__init__(
            master,
            text=text,
            command=command,
            bg=bg,
            fg=fg,
            activebackground=activebg,
            activeforeground=activefg,
            relief="flat",
            bd=0,
            padx=14,
            pady=10,
            font=("Segoe UI", CURRENT_MODE["body"], "bold"),
            **kwargs
        )


class NavButtonTK(tk.Button):
    """Navigation button for sidebar."""

    def __init__(self, master, text, command, selected=False):
        self._selected = selected
        super().__init__(
            master,
            text=text,
            command=command,
            bg=(THEME["bg_nav_sel"] if selected else THEME["bg_nav"]),
            fg=(THEME["accent"] if selected else THEME["text"]),
            activebackground=THEME["bg_nav_sel"],
            activeforeground=THEME["accent"],
            relief="flat",
            bd=0,
            anchor="w",
            padx=14,
            pady=10,
            font=("Segoe UI", CURRENT_MODE["body"], "bold"),
        )

    def set_selected(self, selected: bool):
        self._selected = bool(selected)
        self.configure(
            bg=(THEME["bg_nav_sel"] if self._selected else THEME["bg_nav"]),
            fg=(THEME["accent"] if self._selected else THEME["text"]),
        )


class SourceCardTK(tk.Frame):
    """Card widget for displaying data source status."""

    def __init__(self, master, title: str, pipeline: LogoPipelineTK, candidates, kind: str):
        super().__init__(master, bg=THEME["bg_card"], highlightthickness=1, highlightbackground=THEME["border"])
        self.pipeline = pipeline
        self.candidates = candidates
        self.kind = kind
        self.title = title
        self.logo_img = None
        self.src_path = None

        logo_max_h = 36 if CURRENT_MODE["type"] == "OFFICE" else 30
        if kind == "excel":
            logo_max_w = logo_max_h
        else:
            logo_max_w = 160 if CURRENT_MODE["type"] == "OFFICE" else 130

        self.logo_img, self.src_path = self.pipeline.build_tk_image(candidates, max_w=logo_max_w, max_h=logo_max_h, kind=kind)

        left = tk.Frame(self, bg=THEME["bg_card"])
        left.pack(side="left", padx=(12, 10), pady=12)

        if self.logo_img:
            self.logo_label = tk.Label(left, image=self.logo_img, bg=THEME["bg_card"])
            self.logo_label.pack(anchor="w")
        else:
            self.logo_label = tk.Label(left, text=title[:1].upper(), fg=THEME["text"], bg=THEME["bg_card"],
                                       font=("Segoe UI", 18, "bold"))
            self.logo_label.pack(anchor="w")

        right = tk.Frame(self, bg=THEME["bg_card"])
        right.pack(side="left", fill="both", expand=True, padx=(0, 12), pady=12)

        self.lbl_title = tk.Label(right, text=title.upper(), fg=THEME["muted"], bg=THEME["bg_card"],
                                  font=("Segoe UI", CURRENT_MODE["small"], "bold"))
        self.lbl_title.pack(anchor="w")

        self.lbl_status = tk.Label(right, text="OFFLINE", fg=THEME["bad"], bg=THEME["bg_card"],
                                   font=("Segoe UI", CURRENT_MODE["body"], "bold"))
        self.lbl_status.pack(anchor="w")

        self.lbl_updated = tk.Label(right, text="Last updated: -", fg=THEME["muted2"], bg=THEME["bg_card"],
                                    font=("Segoe UI", CURRENT_MODE["small"]))
        self.lbl_updated.pack(anchor="w")

    def set_status(self, ok: bool, last_updated: datetime | None, detail_text: str | None = None):
        if ok:
            self.lbl_status.configure(text="CONNECTED", fg=THEME["good"])
        else:
            self.lbl_status.configure(text="OFFLINE", fg=THEME["bad"])
        if detail_text:
            self.lbl_updated.configure(text=detail_text)
        else:
            self.lbl_updated.configure(text=f"Last updated: {fmt_ts(last_updated)}")


class MetricChipTK(tk.Frame):
    """Small metric display chip."""

    def __init__(self, master, title: str, value: str = "-"):
        super().__init__(master, bg=THEME["chip"], highlightthickness=1, highlightbackground=THEME["border"])
        self.lbl_title = tk.Label(self, text=title, fg=THEME["muted"], bg=THEME["chip"],
                                  font=("Segoe UI", CURRENT_MODE["small"], "bold"))
        self.lbl_value = tk.Label(self, text=value, fg=THEME["text"], bg=THEME["chip"],
                                  font=("Consolas", CURRENT_MODE["h2"], "bold"))
        self.lbl_title.pack(anchor="w", padx=12, pady=(8, 0))
        self.lbl_value.pack(anchor="w", padx=12, pady=(0, 10))

    def set_value(self, v: str):
        self.lbl_value.configure(text=str(v))


class DataTableTree(tk.Frame):
    """
    Fast table using ttk.Treeview.
    Supports row tags: section / bad / good / normal.
    """

    def __init__(self, master, columns, col_widths=None, height=18):
        super().__init__(master, bg=THEME["bg_card"], highlightthickness=1, highlightbackground=THEME["border"])
        self.columns = columns
        self.col_widths = col_widths or [160] * len(columns)

        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=height)
        self.vsb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.vsb.set)

        for i, col in enumerate(columns):
            self.tree.heading(col, text=col.upper())
            self.tree.column(col, width=int(self.col_widths[i]), anchor="center", stretch=False)

        self.tree.tag_configure("section", background=THEME["bg_card_2"], foreground=THEME["accent"])
        self.tree.tag_configure("bad", background="#1A0C10", foreground=THEME["bad"])
        self.tree.tag_configure("good", background="#07160F", foreground=THEME["good"])
        self.tree.tag_configure("warn", background="#2A1D04", foreground=THEME["warn"])
        self.tree.tag_configure("yellow", background="#2A2406", foreground=THEME["yellow"])
        self.tree.tag_configure("normal_even", background=THEME["row_even"], foreground=THEME["text"])
        self.tree.tag_configure("normal_odd", background=THEME["row_odd"], foreground=THEME["text"])

        self.tree.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        self.vsb.pack(side="right", fill="y", padx=(0, 10), pady=10)

        self._row_idx = 0

    def clear(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self._row_idx = 0

    def add_row(self, values, style="normal"):
        if style == "section":
            tag = "section"
        elif style == "bad":
            tag = "bad"
        elif style == "good":
            tag = "good"
        elif style == "warn":
            tag = "warn"
        elif style == "yellow":
            tag = "yellow"
        else:
            tag = "normal_even" if (self._row_idx % 2 == 0) else "normal_odd"

        self.tree.insert("", "end", values=[("" if v is None else str(v)) for v in values], tags=(tag,))
        self._row_idx += 1


class TimeSeriesChartTK(tk.Frame):
    """
    Matplotlib chart component for displaying historical Nibor rates.
    Embedded in Tkinter using FigureCanvasTkAgg.
    """

    def __init__(self, master, title: str = "NIBOR HISTORICAL RATES"):
        super().__init__(master, bg=THEME["bg_card"],
                        highlightthickness=1, highlightbackground=THEME["border"])

        self.title = title

        # Create figure with dark theme
        self.fig = Figure(figsize=(10, 4), dpi=100, facecolor=THEME["bg_card"])
        self.ax = self.fig.add_subplot(111)

        # Style axis with THEME colors
        self.ax.set_facecolor(THEME["bg_card"])
        self.ax.tick_params(colors=THEME["text"], labelsize=9)
        self.ax.spines['bottom'].set_color(THEME["border"])
        self.ax.spines['top'].set_color(THEME["border"])
        self.ax.spines['left'].set_color(THEME["border"])
        self.ax.spines['right'].set_color(THEME["border"])

        # Embed in Tkinter
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(fill="both", expand=True, padx=10, pady=10)

        # Initialize with empty message
        self.clear_chart()

    def plot_nibor_history(self, dates: list, rates_by_tenor: dict):
        """
        Plot historical Nibor rates.

        Args:
            dates: List of datetime objects
            rates_by_tenor: Dict like {"1M": [4.6, 4.55, ...], "3M": [...]}
        """
        self.ax.clear()

        # Color mapping for tenors
        colors = {
            "1M": THEME["accent"],
            "2M": "#FFA500",  # Orange
            "3M": THEME["good"],
            "6M": THEME["warn"]
        }

        # Plot each tenor
        for tenor, rates in rates_by_tenor.items():
            if len(rates) == len(dates):
                # Filter out None values for gap handling
                valid_indices = [i for i, r in enumerate(rates) if r is not None]
                valid_dates = [dates[i] for i in valid_indices]
                valid_rates = [rates[i] for i in valid_indices]

                if valid_dates:
                    self.ax.plot(valid_dates, valid_rates,
                               label=f"{tenor} NIBOR",
                               color=colors.get(tenor, THEME["text"]),
                               linewidth=2,
                               marker='o',
                               markersize=4)

        # Styling
        self.ax.set_title(self.title, color=THEME["accent"], fontsize=12, fontweight='bold', pad=10)
        self.ax.set_xlabel("Date", color=THEME["muted"], fontsize=10)
        self.ax.set_ylabel("Rate (%)", color=THEME["muted"], fontsize=10)

        # Legend
        if any(rates_by_tenor.values()):
            self.ax.legend(loc='upper right', facecolor=THEME["bg_card_2"],
                          edgecolor=THEME["border"], labelcolor=THEME["text"],
                          fontsize=9, framealpha=0.9)

        # Grid
        self.ax.grid(True, alpha=0.2, color=THEME["border"], linestyle='--', linewidth=0.5)

        # Rotate date labels
        self.fig.autofmt_xdate()

        # Tight layout
        self.fig.tight_layout()

        # Refresh canvas
        self.canvas.draw()

    def clear_chart(self):
        """Clear the chart and show 'No data available' message."""
        self.ax.clear()
        self.ax.text(0.5, 0.5, "No historical data available",
                    ha='center', va='center',
                    color=THEME["muted"],
                    fontsize=11,
                    transform=self.ax.transAxes)
        self.ax.set_facecolor(THEME["bg_card"])
        self.ax.axis('off')
        self.canvas.draw()


class MatchCriteriaPopup(tk.Toplevel):
    """Popup showing matching criteria used in validation."""

    def __init__(self, master, criteria_stats: dict = None):
        super().__init__(master)
        self.title("Matchningskriterier")
        self.geometry("700x550")
        self.configure(bg=THEME["bg_panel"])
        self.transient(master)
        self.grab_set()

        # Center the window
        self.update_idletasks()
        x = (self.winfo_screenwidth() - 700) // 2
        y = (self.winfo_screenheight() - 550) // 2
        self.geometry(f"700x550+{x}+{y}")

        # Title
        tk.Label(self, text="MATCHNINGSKRITERIER",
                fg=THEME["accent"], bg=THEME["bg_panel"],
                font=("Segoe UI", 18, "bold")).pack(pady=(20, 5))

        tk.Label(self, text="Dessa kriterier används för att validera data",
                fg=THEME["muted"], bg=THEME["bg_panel"],
                font=("Segoe UI", 11)).pack(pady=(0, 20))

        # Main content frame
        content = tk.Frame(self, bg=THEME["bg_panel"])
        content.pack(fill="both", expand=True, padx=30)

        # Criteria definitions
        criteria = [
            {
                "name": "1. Exakt Match",
                "icon": "=",
                "color": THEME["good"],
                "desc": "Jämför två cellvärden för exakt likhet.\nNumeriskt: differens < 0.000001\nText: exakt strängmatchning",
                "example": "Exempel: A6 = A29"
            },
            {
                "name": "2. Avrundat 2 dec",
                "icon": "≈",
                "color": THEME["accent"],
                "desc": "Avrundar båda värden till 2 decimaler\noch jämför sedan för likhet.",
                "example": "Exempel: round(Z7, 2) = round(Z30, 2)"
            },
            {
                "name": "3. Intervallkontroll",
                "icon": "[]",
                "color": THEME["warn"],
                "desc": "Kontrollerar att värdet ligger inom\nett specificerat intervall.",
                "example": "Exempel: 0.10 ≤ Y6 ≤ 0.20"
            },
            {
                "name": "4. Exakt Värde",
                "icon": "≡",
                "color": "#9F7AEA",
                "desc": "Kontrollerar att värdet är exakt lika\nmed ett fast specificerat värde.",
                "example": "Exempel: Y29 == 0.15 (fast spread)"
            }
        ]

        for i, c in enumerate(criteria):
            frame = tk.Frame(content, bg=THEME["bg_card"],
                           highlightthickness=1, highlightbackground=THEME["border"])
            frame.pack(fill="x", pady=8)

            # Icon
            tk.Label(frame, text=c["icon"], fg=c["color"], bg=THEME["bg_card"],
                    font=("Consolas", 24, "bold"), width=3).pack(side="left", padx=15, pady=15)

            # Text content
            text_frame = tk.Frame(frame, bg=THEME["bg_card"])
            text_frame.pack(side="left", fill="both", expand=True, pady=10)

            tk.Label(text_frame, text=c["name"], fg=c["color"], bg=THEME["bg_card"],
                    font=("Segoe UI", 12, "bold"), anchor="w").pack(anchor="w")

            tk.Label(text_frame, text=c["desc"], fg=THEME["text"], bg=THEME["bg_card"],
                    font=("Segoe UI", 10), anchor="w", justify="left").pack(anchor="w", pady=(5, 0))

            tk.Label(text_frame, text=c["example"], fg=THEME["muted"], bg=THEME["bg_card"],
                    font=("Consolas", 9), anchor="w").pack(anchor="w", pady=(5, 0))

            # Stats if available
            if criteria_stats:
                stat_key = ["exact", "rounded", "range", "fixed"][i]
                stats = criteria_stats.get(stat_key, {})
                passed = stats.get("passed", 0)
                failed = stats.get("failed", 0)
                total = passed + failed

                stat_frame = tk.Frame(frame, bg=THEME["bg_card"])
                stat_frame.pack(side="right", padx=15)

                status_color = THEME["good"] if failed == 0 else THEME["bad"]
                tk.Label(stat_frame, text=f"{passed}/{total}",
                        fg=status_color, bg=THEME["bg_card"],
                        font=("Consolas", 14, "bold")).pack()
                tk.Label(stat_frame, text="OK",
                        fg=THEME["muted"], bg=THEME["bg_card"],
                        font=("Segoe UI", 9)).pack()

        # Close button
        OnyxButtonTK(self, "Stäng", command=self.destroy,
                    variant="default").pack(pady=20)


class MatchDetailPopup(tk.Toplevel):
    """Popup showing details of a specific match."""

    def __init__(self, master, match_data: dict):
        super().__init__(master)
        self.title("Matchningsdetaljer")
        self.geometry("600x450")
        self.configure(bg=THEME["bg_panel"])
        self.transient(master)
        self.grab_set()

        # Center the window
        self.update_idletasks()
        x = (self.winfo_screenwidth() - 600) // 2
        y = (self.winfo_screenheight() - 450) // 2
        self.geometry(f"600x450+{x}+{y}")

        cell = match_data.get("cell", "-")
        desc = match_data.get("desc", "-")
        model_val = match_data.get("model", "-")
        market_val = match_data.get("market", "-")
        logic = match_data.get("logic", "Exakt Match")
        status = match_data.get("status", False)
        diff = match_data.get("diff", "-")

        # Header with status
        header = tk.Frame(self, bg=THEME["bg_panel"])
        header.pack(fill="x", padx=30, pady=(25, 15))

        status_icon = "✔" if status else "✘"
        status_color = THEME["good"] if status else THEME["bad"]
        status_text = "MATCHED" if status else "MISMATCH"

        tk.Label(header, text=status_icon, fg=status_color, bg=THEME["bg_panel"],
                font=("Segoe UI", 36, "bold")).pack(side="left")

        title_frame = tk.Frame(header, bg=THEME["bg_panel"])
        title_frame.pack(side="left", padx=15)

        tk.Label(title_frame, text=f"Cell {cell}", fg=THEME["text"], bg=THEME["bg_panel"],
                font=("Segoe UI", 18, "bold")).pack(anchor="w")
        tk.Label(title_frame, text=status_text, fg=status_color, bg=THEME["bg_panel"],
                font=("Segoe UI", 12, "bold")).pack(anchor="w")

        # Details card
        card = tk.Frame(self, bg=THEME["bg_card"],
                       highlightthickness=1, highlightbackground=THEME["border"])
        card.pack(fill="both", expand=True, padx=30, pady=10)

        def add_detail_row(parent, label, value, value_color=THEME["text"], row=0):
            tk.Label(parent, text=label, fg=THEME["muted"], bg=THEME["bg_card"],
                    font=("Segoe UI", 11), anchor="e", width=18).grid(row=row, column=0, sticky="e", padx=(20, 10), pady=8)
            tk.Label(parent, text=str(value), fg=value_color, bg=THEME["bg_card"],
                    font=("Consolas", 12, "bold"), anchor="w").grid(row=row, column=1, sticky="w", padx=(0, 20), pady=8)

        add_detail_row(card, "Beskrivning:", desc, row=0)
        add_detail_row(card, "Matchningslogik:", logic, THEME["accent"], row=1)
        add_detail_row(card, "Modellvärde:", model_val, THEME["text"], row=2)
        add_detail_row(card, "Referensvärde:", market_val, THEME["text"], row=3)
        add_detail_row(card, "Differens:", diff, THEME["warn"] if diff != "-" and diff != "0" else THEME["text"], row=4)

        # Logic explanation
        logic_frame = tk.Frame(card, bg=THEME["bg_card_2"])
        logic_frame.grid(row=5, column=0, columnspan=2, sticky="ew", padx=15, pady=(15, 15))

        logic_text = self._get_logic_explanation(logic, model_val, market_val)
        tk.Label(logic_frame, text="Så här fungerar matchningen:",
                fg=THEME["accent"], bg=THEME["bg_card_2"],
                font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=15, pady=(10, 5))
        tk.Label(logic_frame, text=logic_text,
                fg=THEME["text"], bg=THEME["bg_card_2"],
                font=("Segoe UI", 10), justify="left").pack(anchor="w", padx=15, pady=(0, 10))

        card.grid_columnconfigure(1, weight=1)

        # Close button
        OnyxButtonTK(self, "Stäng", command=self.destroy,
                    variant="default").pack(pady=20)

    def _get_logic_explanation(self, logic: str, model_val: str, market_val: str) -> str:
        if logic == "Exakt Match":
            return f"Kontrollerar om {model_val} är exakt lika med {market_val}.\nTolerans: 0.000001 för numeriska värden."
        elif logic == "Avrundat 2 dec":
            return f"Avrundar {model_val} och {market_val} till 2 decimaler\noch jämför sedan för likhet."
        elif "-" in logic and logic[0].isdigit():
            parts = logic.split("-")
            return f"Kontrollerar om {model_val} ligger inom intervallet [{parts[0]}, {parts[1]}]."
        elif "Exakt" in logic:
            target = logic.split()[1] if len(logic.split()) > 1 else "-"
            return f"Kontrollerar om {model_val} är exakt lika med det fasta värdet {target}."
        return "Okänd matchningslogik."


class ClickableDataTableTree(DataTableTree):
    """DataTableTree with clickable rows that can show match details."""

    def __init__(self, master, columns, col_widths=None, height=18, on_row_click=None):
        super().__init__(master, columns, col_widths, height)
        self.on_row_click = on_row_click
        self._row_data = []

        # Bind click event
        self.tree.bind("<Double-1>", self._on_double_click)
        self.tree.bind("<Return>", self._on_double_click)

        # Change cursor on hover for rows with data
        self.tree.bind("<Motion>", self._on_motion)

    def clear(self):
        super().clear()
        self._row_data = []

    def add_row(self, values, style="normal", row_data=None):
        super().add_row(values, style)
        self._row_data.append(row_data)

    def _on_double_click(self, event):
        if self.on_row_click is None:
            return

        item = self.tree.selection()
        if not item:
            return

        # Get row index
        idx = self.tree.index(item[0])
        if 0 <= idx < len(self._row_data):
            row_data = self._row_data[idx]
            if row_data:
                self.on_row_click(row_data)

    def _on_motion(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            idx = self.tree.index(item)
            if 0 <= idx < len(self._row_data) and self._row_data[idx]:
                self.tree.configure(cursor="hand2")
            else:
                self.tree.configure(cursor="")
        else:
            self.tree.configure(cursor="")
