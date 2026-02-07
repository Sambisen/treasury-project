"""
ReconPage for Nibor Calculation Terminal.
"""
import tkinter as tk
from tkinter import ttk

from config import THEME, CURRENT_MODE, get_logger

log = get_logger("ui_pages")
from ui_components import DataTableTree


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


