"""
MetaDataPage for Nibor Calculation Terminal.
"""
import tkinter as tk

from config import THEME, get_logger

log = get_logger("ui_pages")


class MetaDataPage(tk.Frame):
    """Meta Data page - placeholder for future implementation."""

    def __init__(self, master, app):
        super().__init__(master, bg=THEME["bg_panel"])
        self.app = app
        self._build_ui()

    def _build_ui(self):
        # Header
        header = tk.Frame(self, bg=THEME["bg_panel"])
        header.pack(fill="x", padx=24, pady=(24, 16))

        tk.Label(
            header,
            text="Meta Data",
            font=("Segoe UI Semibold", 24),
            fg=THEME["text"],
            bg=THEME["bg_panel"]
        ).pack(side="left")

        # Placeholder content
        content = tk.Frame(self, bg=THEME["bg_panel"])
        content.pack(fill="both", expand=True, padx=24, pady=16)

        tk.Label(
            content,
            text="Coming soon...",
            font=("Segoe UI", 14),
            fg=THEME["text_muted"],
            bg=THEME["bg_panel"]
        ).pack(pady=40)

    def update(self):
        """Refresh the page."""
        pass


