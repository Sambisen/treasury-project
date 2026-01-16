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
            activebg = "#EF4444"
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
        self.tree.tag_configure("bad", background="#FEE2E2", foreground=THEME["bad"])
        self.tree.tag_configure("good", background="#DCFCE7", foreground=THEME["good"])
        self.tree.tag_configure("warn", background="#FEF3C7", foreground=THEME["warning"])
        self.tree.tag_configure("yellow", background="#FEF3C7", foreground=THEME["warning"])
        self.tree.tag_configure("normal_even", background=THEME["row_even"], foreground=THEME["text"])
        self.tree.tag_configure("normal_odd", background=THEME["row_odd"], foreground=THEME["text"])
        self.tree.tag_configure("active", background="#FFF7ED", foreground=THEME["accent"])

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
            self.CONNECTED: {"dot": THEME["good"], "text": "OK", "bg": "#DCFCE7"},
            self.ERROR: {"dot": THEME["bad"], "text": "ERR", "bg": "#FEE2E2"},
            self.STALE: {"dot": THEME["warning"], "text": "OLD", "bg": "#FEF3C7"},
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


# =============================================================================
# PREMIUM ACTION BAR COMPONENTS
# =============================================================================

# Color helpers for premium buttons
def _hex_to_rgb(h: str) -> tuple:
    h = h.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _rgb_to_hex(rgb: tuple) -> str:
    return "#{:02X}{:02X}{:02X}".format(*rgb)


def _lerp(a: int, b: int, t: float) -> int:
    return int(a + (b - a) * t)


def _blend(c1: str, c2: str, t: float) -> str:
    r1, g1, b1 = _hex_to_rgb(c1)
    r2, g2, b2 = _hex_to_rgb(c2)
    return _rgb_to_hex((_lerp(r1, r2, t), _lerp(g1, g2, t), _lerp(b1, b2, t)))


def _lighten(c: str, amount: float) -> str:
    return _blend(c, "#FFFFFF", amount)


def _darken(c: str, amount: float) -> str:
    return _blend(c, "#000000", amount)


if CTK_AVAILABLE:
    class PremiumCTAButton(ctk.CTkFrame):
        """
        A premium-looking CTA button with gradient, shadow, and states.
        Supports: hover/pressed/disabled/loading/confirmed.
        """

        def __init__(
            self,
            master,
            text: str = "Confirm rates",
            command=None,
            width: int = 190,
            height: int = 46,
            radius: int = 14,
            fg_top: str = None,
            fg_bottom: str = None,
            border_color: str = None,
            text_color: str = "#FFFFFF",
            font: tuple = ("Segoe UI", 13, "bold"),
            shadow: bool = True,
            **kwargs,
        ):
            super().__init__(master, fg_color="transparent", **kwargs)

            self._btn_width = width
            self._btn_height = height
            self._btn_radius = radius
            self._text = text
            self._command = command

            self._enabled = True
            self._hover = False
            self._pressed = False
            self._loading = False
            self._confirmed = False
            self._focus = False

            accent = THEME.get("accent", "#FF6A00")
            accent_hover = THEME.get("accent_hover", "#FF7A1A")

            self._fg_top = fg_top or _lighten(accent, 0.06)
            self._fg_bottom = fg_bottom or _darken(accent, 0.04)
            self._border_color = border_color or _darken(accent, 0.12)
            self._text_color = text_color
            self._font = font
            self._shadow_on = shadow

            # Get accent color for canvas background
            accent = THEME.get("accent", "#FF6A00")

            # Shadow layer
            self._shadow_canvas = ctk.CTkCanvas(self, width=self._btn_width, height=self._btn_height, highlightthickness=0, bd=0, bg=accent)
            self._shadow_canvas.grid(row=0, column=0, sticky="nsew")

            # Main canvas layer
            self._canvas = ctk.CTkCanvas(self, width=self._btn_width, height=self._btn_height, highlightthickness=0, bd=0, bg=accent)
            self._canvas.grid(row=0, column=0, sticky="nsew")

            # Content label
            self._label = ctk.CTkLabel(
                self,
                text=self._text,
                text_color=self._text_color,
                font=self._font,
                fg_color="transparent",
            )
            self._label.place(relx=0.5, rely=0.5, anchor="center")

            # Progress bar for loading state
            self._progress = ctk.CTkProgressBar(
                self,
                mode="indeterminate",
                width=int(self._btn_width * 0.55),
                height=8,
                fg_color=_lighten("#000000", 0.92),
                progress_color=_lighten("#FFFFFF", 0.1),
                corner_radius=999,
            )
            self._progress.place_forget()

            # Bindings
            for widget in (self, self._canvas, self._label):
                widget.bind("<Enter>", self._on_enter)
                widget.bind("<Leave>", self._on_leave)
                widget.bind("<ButtonPress-1>", self._on_press)
                widget.bind("<ButtonRelease-1>", self._on_release)

            self.configure(width=self._btn_width, height=self._btn_height)
            self.grid_propagate(False)
            self._redraw()

        def set_enabled(self, enabled: bool) -> None:
            self._enabled = bool(enabled)
            if not self._enabled:
                self._hover = False
                self._pressed = False
            self._redraw()

        def set_loading(self, loading: bool, loading_text: str = "Confirming...") -> None:
            self._loading = bool(loading)
            if self._loading:
                self._label.configure(text=loading_text)
                self._progress.place(relx=0.5, rely=0.78, anchor="center")
                self._progress.start()
            else:
                self._progress.stop()
                self._progress.place_forget()
                self._label.configure(text=self._text)
            self._redraw()

        def flash_confirmed(self, confirmed_text: str = "Confirmed") -> None:
            self._confirmed = True
            self._label.configure(text=confirmed_text)
            self._redraw()

            def _restore():
                self._confirmed = False
                self._label.configure(text=self._text)
                self._redraw()

            self.after(1200, _restore)

        def _on_enter(self, _evt=None) -> None:
            if not self._enabled or self._loading:
                return
            self._hover = True
            self._redraw()

        def _on_leave(self, _evt=None) -> None:
            self._hover = False
            self._pressed = False
            self._redraw()

        def _on_press(self, _evt=None) -> None:
            if not self._enabled or self._loading:
                return
            self._pressed = True
            self._redraw()

        def _on_release(self, _evt=None) -> None:
            if not self._enabled or self._loading:
                return
            was_pressed = self._pressed
            self._pressed = False
            self._redraw()
            if was_pressed and self._hover and callable(self._command):
                self._command()

        def _redraw(self) -> None:
            self._shadow_canvas.delete("all")
            self._canvas.delete("all")

            accent = THEME.get("accent", "#FF6A00")
            accent_hover = THEME.get("accent_hover", "#FF7A1A")
            accent_pressed = _darken(accent, 0.1)
            success = THEME.get("good", "#1E8E3E")
            text_primary = THEME.get("text", "#1F2937")
            bg_canvas = THEME.get("bg_panel", "#F7F7F6")
            shadow_color = "#000000"

            if not self._enabled:
                top = _lighten("#9CA3AF", 0.20)
                bottom = _darken("#9CA3AF", 0.08)
                border = _darken("#9CA3AF", 0.15)
                text_color = _lighten(text_primary, 0.45)
                shadow_alpha = 0.00
            elif self._confirmed:
                top = _lighten(success, 0.08)
                bottom = _darken(success, 0.05)
                border = _darken(success, 0.18)
                text_color = "#FFFFFF"
                shadow_alpha = 0.14
            elif self._pressed:
                top = _lighten(accent_pressed, 0.04)
                bottom = _darken(accent_pressed, 0.06)
                border = _darken(accent_pressed, 0.20)
                text_color = "#FFFFFF"
                shadow_alpha = 0.10
            elif self._hover:
                top = _lighten(accent_hover, 0.06)
                bottom = _darken(accent_hover, 0.05)
                border = _darken(accent_hover, 0.18)
                text_color = "#FFFFFF"
                shadow_alpha = 0.16
            else:
                top = self._fg_top
                bottom = self._fg_bottom
                border = self._border_color
                text_color = self._text_color
                shadow_alpha = 0.14

            if self._loading and self._enabled:
                top = _blend(top, "#FFFFFF", 0.06)
                bottom = _blend(bottom, "#FFFFFF", 0.06)

            self._label.configure(text_color=text_color)

            # Shadow
            if self._shadow_on and shadow_alpha > 0:
                self._draw_rounded_rect(
                    self._shadow_canvas,
                    x=2,
                    y=3 if not self._pressed else 4,
                    w=self._btn_width - 2,
                    h=self._btn_height - 2,
                    r=self._btn_radius,
                    fill=_blend(shadow_color, bg_canvas, 0.93),
                    outline="",
                )

            # Main button with gradient
            y_offset = 0 if not self._pressed else 1
            self._draw_vertical_gradient(
                self._canvas, 0, y_offset, self._btn_width, self._btn_height - y_offset, self._btn_radius, top, bottom
            )

            # Border
            self._draw_rounded_rect(
                self._canvas, 0, y_offset, self._btn_width - 1, self._btn_height - 1 - y_offset, self._btn_radius, fill="", outline=border
            )

            # Top highlight
            self._draw_rounded_rect(
                self._canvas, 1, 1 + y_offset, self._btn_width - 3, int((self._btn_height - y_offset) * 0.42),
                max(8, self._btn_radius - 3), fill="", outline=_blend("#FFFFFF", top, 0.35)
            )

        def _draw_vertical_gradient(self, canvas, x, y, w, h, r, top, bottom, steps=16):
            for i in range(steps):
                t = i / max(1, steps - 1)
                color = _blend(top, bottom, t)
                y0 = y + int((h * i) / steps)
                y1 = y + int((h * (i + 1)) / steps)
                self._draw_rounded_rect(canvas, x, y0, w, (y1 - y0) + 1, r, fill=color, outline=color)

        def _draw_rounded_rect(self, canvas, x, y, w, h, r, fill, outline, width=1):
            r = max(0, min(r, int(min(w, h) / 2)))
            x2, y2 = x + w, y + h
            points = [
                (x + r, y), (x2 - r, y), (x2, y), (x2, y + r),
                (x2, y2 - r), (x2, y2), (x2 - r, y2), (x + r, y2),
                (x, y2), (x, y2 - r), (x, y + r), (x, y),
            ]
            flat = [p for xy in points for p in xy]
            canvas.create_polygon(flat, smooth=True, splinesteps=36, fill=fill, outline=outline, width=width)


    class SecondaryActionButton(ctk.CTkFrame):
        """
        Secondary button with outlined/soft style for action bars.
        White/light gray background, 1px border, dark text.
        """

        def __init__(
            self,
            master,
            text: str = "Re-run checks",
            command=None,
            width: int = 140,
            height: int = 44,
            radius: int = 12,
            icon_text: str = None,
            **kwargs,
        ):
            super().__init__(master, fg_color="transparent", **kwargs)

            self._btn_width = width
            self._btn_height = height
            self._btn_radius = radius
            self._text = text
            self._command = command
            self._icon_text = icon_text

            self._enabled = True
            self._hover = False
            self._pressed = False

            # Colors
            self._bg_normal = THEME.get("bg_card", "#FFFFFF")
            self._bg_hover = _darken(self._bg_normal, 0.04)
            self._bg_pressed = _darken(self._bg_normal, 0.08)
            self._border_color = THEME.get("border", "#E6E6E6")
            self._text_color = THEME.get("text", "#1F2937")
            self._text_disabled = THEME.get("muted", "#9CA3AF")

            # Main frame with border
            self._inner = ctk.CTkFrame(
                self,
                width=self._btn_width,
                height=self._btn_height,
                corner_radius=self._btn_radius,
                fg_color=self._bg_normal,
                border_color=self._border_color,
                border_width=1,
            )
            self._inner.pack(fill="both", expand=True)
            self._inner.pack_propagate(False)

            # Content frame
            content = ctk.CTkFrame(self._inner, fg_color="transparent")
            content.place(relx=0.5, rely=0.5, anchor="center")

            # Icon (if provided)
            if self._icon_text:
                self._icon_lbl = ctk.CTkLabel(
                    content,
                    text=self._icon_text,
                    font=("Segoe UI", 14),
                    text_color=self._text_color,
                    fg_color="transparent",
                )
                self._icon_lbl.pack(side="left", padx=(0, 6))
            else:
                self._icon_lbl = None

            # Text label
            self._label = ctk.CTkLabel(
                content,
                text=self._text,
                font=("Segoe UI Semibold", 12),
                text_color=self._text_color,
                fg_color="transparent",
            )
            self._label.pack(side="left")

            # Bindings
            for widget in (self, self._inner, self._label, content):
                widget.bind("<Enter>", self._on_enter)
                widget.bind("<Leave>", self._on_leave)
                widget.bind("<ButtonPress-1>", self._on_press)
                widget.bind("<ButtonRelease-1>", self._on_release)

            if self._icon_lbl:
                self._icon_lbl.bind("<Enter>", self._on_enter)
                self._icon_lbl.bind("<Leave>", self._on_leave)
                self._icon_lbl.bind("<ButtonPress-1>", self._on_press)
                self._icon_lbl.bind("<ButtonRelease-1>", self._on_release)

            self.configure(width=self._btn_width, height=self._btn_height)

        def set_enabled(self, enabled: bool) -> None:
            self._enabled = bool(enabled)
            color = self._text_color if self._enabled else self._text_disabled
            self._label.configure(text_color=color)
            if self._icon_lbl:
                self._icon_lbl.configure(text_color=color)
            self._update_bg()

        def _on_enter(self, _evt=None) -> None:
            if not self._enabled:
                return
            self._hover = True
            self._update_bg()

        def _on_leave(self, _evt=None) -> None:
            self._hover = False
            self._pressed = False
            self._update_bg()

        def _on_press(self, _evt=None) -> None:
            if not self._enabled:
                return
            self._pressed = True
            self._update_bg()

        def _on_release(self, _evt=None) -> None:
            if not self._enabled:
                return
            was_pressed = self._pressed
            self._pressed = False
            self._update_bg()
            if was_pressed and self._hover and callable(self._command):
                self._command()

        def _update_bg(self) -> None:
            if not self._enabled:
                bg = _lighten(self._bg_normal, 0.02)
            elif self._pressed:
                bg = self._bg_pressed
            elif self._hover:
                bg = self._bg_hover
            else:
                bg = self._bg_normal
            self._inner.configure(fg_color=bg)


    class RatesActionBar(ctk.CTkFrame):
        """
        Action bar for rates confirmation with metadata and buttons.
        Left: metadata (last updated, data source)
        Right: Re-run checks + Confirm rates buttons
        """

        def __init__(
            self,
            master,
            on_rerun_checks=None,
            on_confirm_rates=None,
            **kwargs,
        ):
            # Off-white background with border
            bg_color = _blend(THEME.get("bg_card", "#FFFFFF"), "#000000", 0.02)

            super().__init__(
                master,
                fg_color=bg_color,
                corner_radius=14,
                border_color=THEME.get("border", "#E6E6E6"),
                border_width=1,
                **kwargs,
            )

            self._on_rerun = on_rerun_checks
            self._on_confirm = on_confirm_rates
            self._last_update_time = None
            self._data_source = "Bloomberg / Excel"
            self._is_ready = False

            # Left side: metadata
            left = ctk.CTkFrame(self, fg_color="transparent")
            left.pack(side="left", padx=16, pady=14)

            self._update_lbl = ctk.CTkLabel(
                left,
                text="Last updated: --:--:--",
                font=("Segoe UI Semibold", 12),
                text_color=THEME.get("text", "#1F2937"),
            )
            self._update_lbl.pack(anchor="w")

            self._source_lbl = ctk.CTkLabel(
                left,
                text=f"Data source: {self._data_source}",
                font=("Segoe UI", 11),
                text_color=THEME.get("muted", "#6B7280"),
            )
            self._source_lbl.pack(anchor="w", pady=(2, 0))

            # Right side: buttons
            right = ctk.CTkFrame(self, fg_color="transparent")
            right.pack(side="right", padx=16, pady=14)

            # Re-run checks button (secondary)
            self.rerun_btn = SecondaryActionButton(
                right,
                text="Re-run checks",
                command=self._handle_rerun,
                width=140,
                height=44,
                radius=12,
                icon_text="\u21BB",  # ↻ refresh symbol
            )
            self.rerun_btn.pack(side="left", padx=(0, 10))

            # Confirm rates button (premium)
            self.confirm_btn = PremiumCTAButton(
                right,
                text="Confirm rates",
                command=self._handle_confirm,
                width=180,
                height=44,
                radius=12,
            )
            self.confirm_btn.pack(side="left")

            # Start disabled until ready
            self.confirm_btn.set_enabled(False)

            # Start freshness timer
            self._update_freshness()

        def set_last_updated(self, timestamp: datetime = None):
            """Set the last updated timestamp."""
            self._last_update_time = timestamp or datetime.now()
            self._update_freshness()

        def set_data_source(self, source: str):
            """Set the data source text."""
            self._data_source = source
            self._source_lbl.configure(text=f"Data source: {self._data_source}")

        def set_ready(self, ready: bool):
            """Enable/disable confirm button based on validation state."""
            self._is_ready = ready
            self.confirm_btn.set_enabled(ready)

        def set_loading(self, loading: bool):
            """Set loading state on confirm button."""
            self.confirm_btn.set_loading(loading)

        def flash_confirmed(self):
            """Flash confirmed state on confirm button."""
            self.confirm_btn.flash_confirmed()

        def _handle_rerun(self):
            """Handle re-run checks button click."""
            if callable(self._on_rerun):
                self._on_rerun()

        def _handle_confirm(self):
            """Handle confirm rates button click."""
            if callable(self._on_confirm):
                self._on_confirm()

        def _update_freshness(self):
            """Update the last updated display with relative time."""
            if self._last_update_time:
                time_str = self._last_update_time.strftime("%H:%M:%S")
                ago = (datetime.now() - self._last_update_time).seconds

                if ago < 60:
                    ago_text = f"({ago}s ago)"
                elif ago < 3600:
                    ago_text = f"({ago // 60}m ago)"
                else:
                    ago_text = f"({ago // 3600}h ago)"

                self._update_lbl.configure(text=f"Last updated: {time_str} {ago_text}")
            else:
                self._update_lbl.configure(text="Last updated: --:--:--")

            # Schedule next update
            self.after(5000, self._update_freshness)
