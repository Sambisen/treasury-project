"""
UI components for Onyx Terminal.
Contains reusable GUI widgets.
"""
import tkinter as tk
from tkinter import ttk
from datetime import datetime

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


class SummaryCard(tk.Frame):
    """Summary card showing tenor and calculated rate."""

    def __init__(self, master, tenor: str, value: str = "-"):
        super().__init__(master, bg=THEME["bg_card"], highlightthickness=1,
                        highlightbackground=THEME["border"])

        self.lbl_tenor = tk.Label(self, text=tenor, fg=THEME["muted"], bg=THEME["bg_card"],
                                  font=("Segoe UI", CURRENT_MODE["small"], "bold"))
        self.lbl_tenor.pack(anchor="center", pady=(12, 2))

        self.lbl_value = tk.Label(self, text=value, fg=THEME["accent_secondary"], bg=THEME["bg_card"],
                                  font=("Consolas", 18, "bold"))
        self.lbl_value.pack(anchor="center", pady=(0, 4))

        self.lbl_label = tk.Label(self, text="Funding Rate", fg=THEME["muted2"], bg=THEME["bg_card"],
                                  font=("Segoe UI", 8))
        self.lbl_label.pack(anchor="center", pady=(0, 10))

    def set_value(self, v: str):
        self.lbl_value.configure(text=str(v))


class CollapsibleSection(tk.Frame):
    """Expandable/collapsible section with header and content."""

    def __init__(self, master, title: str, expanded: bool = False, accent_color=None):
        super().__init__(master, bg=THEME["bg_panel"])

        self._expanded = expanded
        self._accent = accent_color or THEME["muted"]

        # Header frame (clickable)
        self.header = tk.Frame(self, bg=THEME["bg_card"], cursor="hand2",
                              highlightthickness=1, highlightbackground=THEME["border"])
        self.header.pack(fill="x", pady=(5, 0))

        # Toggle icon
        self.toggle_icon = tk.Label(self.header, text="▶" if not expanded else "▼",
                                    fg=self._accent, bg=THEME["bg_card"],
                                    font=("Segoe UI", 10))
        self.toggle_icon.pack(side="left", padx=(12, 8), pady=10)

        # Title
        self.title_label = tk.Label(self.header, text=title, fg=self._accent,
                                    bg=THEME["bg_card"],
                                    font=("Segoe UI", CURRENT_MODE["body"], "bold"))
        self.title_label.pack(side="left", pady=10)

        # Content frame
        self.content = tk.Frame(self, bg=THEME["bg_panel"])

        # Bind click events
        for widget in [self.header, self.toggle_icon, self.title_label]:
            widget.bind("<Button-1>", self._toggle)

        # Show/hide based on initial state
        if expanded:
            self.content.pack(fill="x", padx=10, pady=(0, 5))

    def _toggle(self, event=None):
        self._expanded = not self._expanded
        if self._expanded:
            self.toggle_icon.configure(text="▼")
            self.content.pack(fill="x", padx=10, pady=(0, 5))
        else:
            self.toggle_icon.configure(text="▶")
            self.content.pack_forget()

    def expand(self):
        if not self._expanded:
            self._toggle()

    def collapse(self):
        if self._expanded:
            self._toggle()


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
        self.tree.tag_configure("bad", background="#FEE2E2", foreground=THEME["bad"])
        self.tree.tag_configure("good", background="#D1FAE5", foreground="#047857")
        self.tree.tag_configure("warn", background="#FEF3C7", foreground="#B45309")
        self.tree.tag_configure("yellow", background="#FEF9C3", foreground="#A16207")
        self.tree.tag_configure("normal_even", background=THEME["row_even"], foreground=THEME["text"])
        self.tree.tag_configure("normal_odd", background=THEME["row_odd"], foreground=THEME["text"])
        self.tree.tag_configure("active", background="#FFF3E0", foreground=THEME["accent"])

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
        elif style == "active":
            tag = "active"
        else:
            tag = "normal_even" if (self._row_idx % 2 == 0) else "normal_odd"

        self.tree.insert("", "end", values=[("" if v is None else str(v)) for v in values], tags=(tag,))
        self._row_idx += 1
