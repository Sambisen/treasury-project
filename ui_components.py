"""
UI components for Nibor Terminal.
Contains reusable GUI widgets.
CustomTkinter Edition - Modern UI components with rounded corners.

NOTE: This file uses the dark theme from config.py.
For the new Nordic Light design system, use ui.components instead.
Migration path:
    from ui.components import PrimaryButton, Card, Badge, ...
"""
import tkinter as tk
from tkinter import ttk
from datetime import datetime

try:
    import customtkinter as ctk
    CTK_AVAILABLE = True
except ImportError:
    CTK_AVAILABLE = False
    ctk = None

from config import THEME, CURRENT_MODE, CTK_CORNER_RADIUS
from utils import fmt_ts, LogoPipelineTK

# New Nordic Light theme (optional - use for new components)
try:
    from ui.theme import COLORS as NORDIC_COLORS, FONTS as NORDIC_FONTS, SPACING
    NORDIC_THEME_AVAILABLE = True
except ImportError:
    NORDIC_THEME_AVAILABLE = False
    NORDIC_COLORS = None
    NORDIC_FONTS = None
    SPACING = None


def style_ttk(root: tk.Tk):
    """Apply Nibor theme to ttk widgets."""
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


class NiborButtonTK(tk.Button):
    """Styled button for Nibor Terminal (legacy tk version)."""

    def __init__(self, master, text, command=None, variant="default", **kwargs):
        if variant == "accent" or variant == "primary":
            bg = THEME["accent"]
            fg = THEME["bg_panel"]
            activebg = THEME["accent_hover"]
            activefg = THEME["bg_panel"]
        elif variant == "danger":
            bg = THEME["bad"]
            fg = THEME["bg_panel"]
            activebg = "#FF5252"
            activefg = THEME["bg_panel"]
        else:
            bg = THEME["bg_card_2"]
            fg = THEME["text"]
            activebg = THEME["bg_hover"]
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


# Modern CustomTkinter button
if CTK_AVAILABLE:
    class NiborButtonCTK(ctk.CTkButton):
        """Modern styled button for Nibor Terminal using CustomTkinter."""

        def __init__(self, master, text, command=None, variant="default", **kwargs):
            if variant == "accent" or variant == "primary":
                fg_color = THEME["accent"]
                hover_color = THEME["accent_hover"]
                text_color = THEME["bg_panel"]
            elif variant == "danger":
                fg_color = THEME["bad"]
                hover_color = "#FF5252"
                text_color = THEME["bg_panel"]
            else:
                fg_color = THEME["bg_card_2"]
                hover_color = THEME["bg_hover"]
                text_color = THEME["text"]

            super().__init__(
                master,
                text=text,
                command=command,
                fg_color=fg_color,
                hover_color=hover_color,
                text_color=text_color,
                corner_radius=CTK_CORNER_RADIUS["button"],
                font=("Segoe UI Semibold", CURRENT_MODE["body"]),
                **kwargs
            )

    # Use CTk version as default
    OnyxButtonTK = NiborButtonCTK
else:
    # Fallback to tk version
    OnyxButtonTK = NiborButtonTK


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

        # IMPORTANT: keep a strong reference to the image object on self
        self.logo_img = None
        self.src_path = None

        logo_max_h = 36 if CURRENT_MODE["type"] == "OFFICE" else 30
        if kind == "excel":
            logo_max_w = logo_max_h
        else:
            logo_max_w = 160 if CURRENT_MODE["type"] == "OFFICE" else 130

        self.logo_img, self.src_path = self.pipeline.build_tk_image(
            candidates, max_w=logo_max_w, max_h=logo_max_h, kind=kind
        )

        left = tk.Frame(self, bg=THEME["bg_card"])
        left.pack(side="left", padx=(12, 10), pady=12)

        if self.logo_img:
            self.logo_label = tk.Label(left, image=self.logo_img, bg=THEME["bg_card"])
            self.logo_label.pack(anchor="w")
        else:
            self.logo_label = tk.Label(
                left,
                text=title[:1].upper(),
                fg=THEME["text"],
                bg=THEME["bg_card"],
                font=("Segoe UI", 18, "bold"),
            )
            self.logo_label.pack(anchor="w")

        right = tk.Frame(self, bg=THEME["bg_card"])
        right.pack(side="left", fill="both", expand=True, padx=(0, 12), pady=12)

        self.lbl_title = tk.Label(
            right,
            text=title.upper(),
            fg=THEME["muted"],
            bg=THEME["bg_card"],
            font=("Segoe UI", CURRENT_MODE["small"], "bold"),
        )
        self.lbl_title.pack(anchor="w")

        self.lbl_status = tk.Label(
            right,
            text="OFFLINE",
            fg=THEME["bad"],
            bg=THEME["bg_card"],
            font=("Segoe UI", CURRENT_MODE["body"], "bold"),
        )
        self.lbl_status.pack(anchor="w")

        self.lbl_updated = tk.Label(
            right,
            text="Last updated: -",
            fg=THEME["muted2"],
            bg=THEME["bg_card"],
            font=("Segoe UI", CURRENT_MODE["small"]),
        )
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
        self.tree.tag_configure("bad", background="#3D1F1F", foreground=THEME["bad"])
        self.tree.tag_configure("good", background="#1F3D2D", foreground=THEME["good"])
        self.tree.tag_configure("warn", background="#3D3520", foreground=THEME["warning"])
        self.tree.tag_configure("yellow", background="#3D3520", foreground=THEME["warning"])
        self.tree.tag_configure("normal_even", background=THEME["row_even"], foreground=THEME["text"])
        self.tree.tag_configure("normal_odd", background=THEME["row_odd"], foreground=THEME["text"])
        self.tree.tag_configure("active", background="#3D2D1F", foreground=THEME["accent"])

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


class ConnectionStatusIndicator(tk.Frame):
    """
    Professional connection status indicator with pill design.
    Shows status for Bloomberg, Excel, etc. with click-for-details.

    FIX:
    - bg must not be passed twice to tk.Frame.
    - Therefore: pop bg out of kwargs BEFORE calling super().__init__.
    """

    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"
    STALE = "stale"

    def __init__(self, master, label: str, icon: str = "●", **kwargs):
        # --- Critical: remove bg from kwargs so it can't be passed twice ---
        bg = kwargs.pop("bg", None)
        if bg is None:
            bg = THEME["bg_card"]

        super().__init__(master, bg=bg, **kwargs)

        self.label_text = label
        self._status = self.DISCONNECTED
        self._last_update = None
        self._details = {}
        self._pulse_job = None
        self._pulse_state = True

        # Container frame (pill shape)
        self._pill = tk.Frame(self, bg=THEME["bg_card"], highlightthickness=1,
                             highlightbackground=THEME["border"])
        self._pill.pack(padx=2, pady=2)

        # Status dot
        self._dot = tk.Label(self._pill, text=icon, fg=THEME["muted"],
                            bg=THEME["bg_card"], font=("Segoe UI", 11))
        self._dot.pack(side="left", padx=(10, 5), pady=5)

        # Label
        self._label = tk.Label(self._pill, text=label, fg=THEME["text"],
                              bg=THEME["bg_card"], font=("Segoe UI", 9, "bold"))
        self._label.pack(side="left", padx=(0, 5), pady=5)

        # Status text (short)
        self._status_lbl = tk.Label(self._pill, text="--", fg=THEME["muted"],
                                   bg=THEME["bg_card"], font=("Segoe UI", 9))
        self._status_lbl.pack(side="left", padx=(0, 10), pady=5)

        # Make clickable
        self._pill.config(cursor="hand2")
        for widget in [self._pill, self._dot, self._label, self._status_lbl]:
            widget.bind("<Button-1>", self._on_click)
            widget.bind("<Enter>", self._on_enter)
            widget.bind("<Leave>", self._on_leave)

    def set_status(self, status: str, details: dict = None):
        self._status = status
        self._details = details or {}

        # Stop any existing pulse animation
        if self._pulse_job:
            self.after_cancel(self._pulse_job)
            self._pulse_job = None

        # Update colors based on status
        colors = {
            self.DISCONNECTED: {"dot": THEME["muted"], "text": "--", "bg": THEME["bg_card"]},
            self.CONNECTING: {"dot": THEME["warning"], "text": "...", "bg": THEME["bg_card_2"]},
            self.CONNECTED: {"dot": THEME["good"], "text": "OK", "bg": "#1F3D2D"},
            self.ERROR: {"dot": THEME["bad"], "text": "ERR", "bg": "#3D1F1F"},
            self.STALE: {"dot": THEME["warning"], "text": "OLD", "bg": "#3D3520"},
        }
        style = colors.get(status, colors[self.DISCONNECTED])

        self._dot.config(fg=style["dot"])
        self._status_lbl.config(text=style["text"], fg=style["dot"])
        self._pill.config(bg=style["bg"])
        self._dot.config(bg=style["bg"])
        self._label.config(bg=style["bg"])
        self._status_lbl.config(bg=style["bg"])

        if status == self.CONNECTING:
            self._start_pulse()

        if status == self.CONNECTED:
            self._last_update = datetime.now()

    def _start_pulse(self):
        if self._status != self.CONNECTING:
            return

        self._pulse_state = not self._pulse_state
        color = THEME["warning"] if self._pulse_state else THEME["text_light"]
        self._dot.config(fg=color)

        self._pulse_job = self.after(500, self._start_pulse)

    def _on_enter(self, event):
        self._pill.config(highlightbackground=THEME["accent"])

    def _on_leave(self, event):
        self._pill.config(highlightbackground=THEME["border"])

    def _on_click(self, event):
        self._show_details_popup()

    def _show_details_popup(self):
        popup = tk.Toplevel(self)
        popup.title(f"{self.label_text} Status")
        popup.geometry("350x250")
        popup.configure(bg=THEME["bg_main"])
        popup.transient(self.winfo_toplevel())
        popup.grab_set()

        popup.update_idletasks()
        x = self.winfo_toplevel().winfo_x() + 100
        y = self.winfo_toplevel().winfo_y() + 100
        popup.geometry(f"+{x}+{y}")

        header = tk.Frame(popup, bg=THEME["bg_main"])
        header.pack(fill="x", padx=20, pady=(15, 10))

        status_colors = {
            self.CONNECTED: THEME["good"],
            self.CONNECTING: THEME["warning"],
            self.ERROR: THEME["bad"],
            self.STALE: THEME["warning"],
            self.DISCONNECTED: THEME["muted"],
        }

        tk.Label(header, text=f"● {self.label_text}",
                 fg=status_colors.get(self._status, THEME["muted"]),
                 bg=THEME["bg_main"],
                 font=("Segoe UI", 14, "bold")).pack(side="left")

        content = tk.Frame(popup, bg=THEME["bg_card"], highlightthickness=1,
                           highlightbackground=THEME["border"])
        content.pack(fill="both", expand=True, padx=20, pady=10)

        details_frame = tk.Frame(content, bg=THEME["bg_card"])
        details_frame.pack(fill="both", expand=True, padx=15, pady=15)

        self._add_detail_row(details_frame, "Status:", self._status.upper(), 0)

        if self._last_update:
            time_str = self._last_update.strftime("%H:%M:%S")
            ago = (datetime.now() - self._last_update).seconds
            self._add_detail_row(details_frame, "Last Update:", f"{time_str} ({ago}s ago)", 1)
        else:
            self._add_detail_row(details_frame, "Last Update:", "--", 1)

        row = 2
        for key, value in self._details.items():
            self._add_detail_row(details_frame, f"{key}:", str(value), row)
            row += 1

        btn_frame = tk.Frame(popup, bg=THEME["bg_main"])
        btn_frame.pack(fill="x", padx=20, pady=(0, 15))

        refresh_btn = tk.Button(btn_frame, text="🔄 Refresh", bg=THEME["accent"],
                                fg=THEME["bg_panel"], font=("Segoe UI", 10), relief="flat",
                                padx=15, pady=5, cursor="hand2",
                                activebackground=THEME["accent_hover"], activeforeground=THEME["bg_panel"],
                                command=lambda: self._trigger_refresh(popup))
        refresh_btn.pack(side="left")

        tk.Button(btn_frame, text="Close", bg=THEME["bg_card_2"], fg=THEME["text"],
                  font=("Segoe UI", 10), relief="flat", padx=15, pady=5,
                  cursor="hand2", activebackground=THEME["bg_hover"], activeforeground=THEME["text"],
                  command=popup.destroy).pack(side="right")

        popup.bind("<Escape>", lambda e: popup.destroy())

    def _add_detail_row(self, parent, label: str, value: str, row: int):
        tk.Label(parent, text=label, fg=THEME["muted"], bg=THEME["bg_card"],
                 font=("Segoe UI", 10), anchor="w").grid(row=row, column=0, sticky="w", pady=3)
        tk.Label(parent, text=value, fg=THEME["text"], bg=THEME["bg_card"],
                 font=("Consolas", 10), anchor="w").grid(row=row, column=1, sticky="w",
                                                        padx=(10, 0), pady=3)

    def _trigger_refresh(self, popup):
        popup.destroy()
        try:
            app = self.winfo_toplevel()
            if hasattr(app, 'refresh_data'):
                app.refresh_data()
        except Exception:
            pass

    def get_status(self) -> str:
        return self._status

    def get_last_update(self) -> datetime:
        return self._last_update


class ConnectionStatusPanel(tk.Frame):
    """
    Panel containing multiple connection status indicators.
    Typically placed in the status bar.
    """

    def __init__(self, master, **kwargs):
        bg = kwargs.pop("bg", THEME["bg_nav"])
        super().__init__(master, bg=bg, **kwargs)

        self._indicators = {}

        # Bloomberg indicator
        self.bbg = ConnectionStatusIndicator(self, "Bloomberg", "●", bg=bg)
        self.bbg.pack(side="left", padx=(0, 8))
        self._indicators["bloomberg"] = self.bbg

        # Excel indicator
        self.excel = ConnectionStatusIndicator(self, "Excel", "●", bg=bg)
        self.excel.pack(side="left", padx=(0, 8))
        self._indicators["excel"] = self.excel

        # Separator
        tk.Frame(self, bg=THEME["border"], width=1, height=20).pack(side="left", padx=10)

        # Data freshness indicator
        self._freshness_frame = tk.Frame(self, bg=bg)
        self._freshness_frame.pack(side="left", padx=5)

        tk.Label(self._freshness_frame, text="Data:", fg=THEME["muted"], bg=bg,
                font=("Segoe UI", 9)).pack(side="left")

        self._freshness_lbl = tk.Label(self._freshness_frame, text="--:--:--",
                                       fg=THEME["text"], bg=bg, font=("Consolas", 10, "bold"))
        self._freshness_lbl.pack(side="left", padx=(5, 0))

        self._freshness_ago = tk.Label(self._freshness_frame, text="",
                                       fg=THEME["muted"], bg=bg, font=("Segoe UI", 9))
        self._freshness_ago.pack(side="left", padx=(5, 0))

        # Start freshness update timer
        self._update_freshness_display()

    def set_bloomberg_status(self, status: str, details: dict = None):
        self.bbg.set_status(status, details)

    def set_excel_status(self, status: str, details: dict = None):
        self.excel.set_status(status, details)

    def set_data_time(self, timestamp: datetime = None):
        if timestamp:
            self._data_time = timestamp
            self._freshness_lbl.config(text=timestamp.strftime("%H:%M:%S"))
        else:
            self._data_time = datetime.now()
            self._freshness_lbl.config(text=datetime.now().strftime("%H:%M:%S"))

    def _update_freshness_display(self):
        if hasattr(self, '_data_time') and self._data_time:
            ago = (datetime.now() - self._data_time).seconds
            if ago < 60:
                ago_text = f"({ago}s ago)"
                color = THEME["good"] if ago < 30 else THEME["muted"]
            elif ago < 300:
                ago_text = f"({ago // 60}m ago)"
                color = THEME["warning"]
            else:
                ago_text = f"({ago // 60}m ago)"
                color = THEME["bad"]

            self._freshness_ago.config(text=ago_text, fg=color)

        self.after(5000, self._update_freshness_display)
