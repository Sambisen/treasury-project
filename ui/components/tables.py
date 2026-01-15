"""
Table Components - Nordic Light Design System
=============================================
Themed data tables with consistent styling.
"""

import tkinter as tk
from tkinter import ttk
from typing import List, Dict, Optional, Callable
from ..theme import COLORS, FONTS, SPACING, COMPONENTS, apply_ttk_theme


class ThemedTable(tk.Frame):
    """
    Themed Treeview table with Nordic Light styling.
    Supports sorting, row tags, and custom formatting.
    """

    def __init__(
        self,
        parent,
        columns: List[Dict],
        show_header: bool = True,
        row_height: int = None,
        zebra_stripes: bool = True,
        on_select: Optional[Callable] = None,
        on_double_click: Optional[Callable] = None,
        **kwargs
    ):
        super().__init__(parent, bg=COLORS.SURFACE, **kwargs)

        self.columns = columns
        self.zebra_stripes = zebra_stripes
        self.on_select_callback = on_select
        self.on_double_click_callback = on_double_click
        self._row_count = 0

        # Apply ttk styling
        self._style = ttk.Style()
        self._style.theme_use("clam")
        self._configure_style(row_height)

        # Create treeview
        col_ids = [col.get("id", f"col_{i}") for i, col in enumerate(columns)]

        self.tree = ttk.Treeview(
            self,
            columns=col_ids,
            show="headings" if show_header else "tree",
            selectmode="browse",
            style="Nordic.Treeview"
        )

        # Configure columns
        for i, col in enumerate(columns):
            col_id = col.get("id", f"col_{i}")
            heading = col.get("heading", col_id)
            width = col.get("width", 100)
            anchor = col.get("anchor", "w")
            stretch = col.get("stretch", True)

            self.tree.heading(col_id, text=heading, anchor=anchor)
            self.tree.column(col_id, width=width, anchor=anchor, stretch=stretch)

        # Scrollbar
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        # Pack
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Configure tags
        self._configure_tags()

        # Bindings
        if on_select:
            self.tree.bind("<<TreeviewSelect>>", self._on_select)
        if on_double_click:
            self.tree.bind("<Double-1>", self._on_double_click)

        # Hover effect
        self.tree.bind("<Motion>", self._on_motion)
        self._hovered_item = None

    def _configure_style(self, row_height: int = None):
        """Configure ttk style for Nordic Light theme."""
        height = row_height or COMPONENTS.TABLE_ROW_HEIGHT

        self._style.configure(
            "Nordic.Treeview",
            background=COLORS.SURFACE,
            foreground=COLORS.TEXT,
            fieldbackground=COLORS.SURFACE,
            borderwidth=0,
            rowheight=height,
            font=FONTS.TABLE_CELL
        )

        self._style.configure(
            "Nordic.Treeview.Heading",
            background=COLORS.TABLE_HEADER_BG,
            foreground=COLORS.TEXT_MUTED,
            font=FONTS.TABLE_HEADER,
            borderwidth=0,
            relief="flat",
            padding=(SPACING.TABLE_CELL_X, SPACING.SM)
        )

        self._style.map(
            "Nordic.Treeview",
            background=[("selected", COLORS.ACCENT_LIGHT)],
            foreground=[("selected", COLORS.TEXT)]
        )

        self._style.map(
            "Nordic.Treeview.Heading",
            background=[("active", COLORS.SURFACE_HOVER)]
        )

    def _configure_tags(self):
        """Configure row tags for different states."""
        self.tree.tag_configure("normal_even", background=COLORS.SURFACE)
        self.tree.tag_configure("normal_odd", background=COLORS.ROW_ZEBRA)
        self.tree.tag_configure("hover", background=COLORS.ROW_HOVER)
        self.tree.tag_configure("good", background=COLORS.SUCCESS_BG, foreground=COLORS.SUCCESS)
        self.tree.tag_configure("bad", background=COLORS.DANGER_BG, foreground=COLORS.DANGER)
        self.tree.tag_configure("warning", background=COLORS.WARNING_BG, foreground=COLORS.WARNING)
        self.tree.tag_configure("section", background=COLORS.TABLE_HEADER_BG, foreground=COLORS.TEXT_MUTED)
        self.tree.tag_configure("muted", foreground=COLORS.TEXT_MUTED)

        # Numeric colors
        self.tree.tag_configure("positive", foreground=COLORS.SUCCESS)
        self.tree.tag_configure("negative", foreground=COLORS.DANGER)
        self.tree.tag_configure("zero", foreground=COLORS.TEXT_MUTED)

    def insert_row(self, values: List, tag: str = None, **kwargs) -> str:
        """Insert a row and return the item ID."""
        # Determine zebra tag
        if tag is None and self.zebra_stripes:
            tag = "normal_even" if self._row_count % 2 == 0 else "normal_odd"

        tags = (tag,) if tag else ()

        item_id = self.tree.insert("", "end", values=values, tags=tags, **kwargs)
        self._row_count += 1
        return item_id

    def clear(self):
        """Remove all rows."""
        for item in self.tree.get_children():
            self.tree.delete(item)
        self._row_count = 0

    def get_selected(self) -> Optional[str]:
        """Get the currently selected item ID."""
        selection = self.tree.selection()
        return selection[0] if selection else None

    def get_values(self, item_id: str) -> tuple:
        """Get values for a row."""
        return self.tree.item(item_id, "values")

    def set_values(self, item_id: str, values: List):
        """Update values for a row."""
        self.tree.item(item_id, values=values)

    def set_tag(self, item_id: str, tag: str):
        """Set tag for a row."""
        self.tree.item(item_id, tags=(tag,))

    def _on_select(self, event):
        """Handle selection event."""
        if self.on_select_callback:
            item_id = self.get_selected()
            if item_id:
                values = self.get_values(item_id)
                self.on_select_callback(item_id, values)

    def _on_double_click(self, event):
        """Handle double-click event."""
        if self.on_double_click_callback:
            item_id = self.get_selected()
            if item_id:
                values = self.get_values(item_id)
                self.on_double_click_callback(item_id, values)

    def _on_motion(self, event):
        """Handle hover effect."""
        item = self.tree.identify_row(event.y)
        if item != self._hovered_item:
            # Reset previous hover
            if self._hovered_item:
                idx = list(self.tree.get_children()).index(self._hovered_item) if self._hovered_item in self.tree.get_children() else 0
                tag = "normal_even" if idx % 2 == 0 else "normal_odd"
                # Only reset if not a special tag
                current_tags = self.tree.item(self._hovered_item, "tags")
                if current_tags and current_tags[0] in ("normal_even", "normal_odd", "hover"):
                    self.tree.item(self._hovered_item, tags=(tag,))

            self._hovered_item = item


class SimpleTable(tk.Frame):
    """
    Simple table using tk.Frame for more control over styling.
    Good for small, static tables.
    """

    def __init__(
        self,
        parent,
        columns: List[str],
        widths: List[int] = None,
        **kwargs
    ):
        super().__init__(parent, bg=COLORS.SURFACE, **kwargs)

        self.columns = columns
        self.widths = widths or [100] * len(columns)
        self._rows = []

        # Header row
        header_frame = tk.Frame(self, bg=COLORS.TABLE_HEADER_BG)
        header_frame.pack(fill="x")

        for i, col in enumerate(columns):
            tk.Label(
                header_frame,
                text=col,
                fg=COLORS.TEXT_MUTED,
                bg=COLORS.TABLE_HEADER_BG,
                font=FONTS.TABLE_HEADER,
                width=self.widths[i] // 8,
                anchor="w",
                padx=SPACING.TABLE_CELL_X,
                pady=SPACING.SM
            ).pack(side="left")

        # Body container
        self.body = tk.Frame(self, bg=COLORS.SURFACE)
        self.body.pack(fill="both", expand=True)

    def add_row(self, values: List[str], tag: str = None):
        """Add a row to the table."""
        row_idx = len(self._rows)
        bg = COLORS.SURFACE if row_idx % 2 == 0 else COLORS.ROW_ZEBRA

        if tag == "good":
            bg = COLORS.SUCCESS_BG
        elif tag == "bad":
            bg = COLORS.DANGER_BG
        elif tag == "warning":
            bg = COLORS.WARNING_BG

        row_frame = tk.Frame(self.body, bg=bg)
        row_frame.pack(fill="x")

        for i, val in enumerate(values):
            fg = COLORS.TEXT
            if tag == "good":
                fg = COLORS.SUCCESS
            elif tag == "bad":
                fg = COLORS.DANGER
            elif tag == "warning":
                fg = COLORS.WARNING

            tk.Label(
                row_frame,
                text=str(val),
                fg=fg,
                bg=bg,
                font=FONTS.TABLE_CELL,
                width=self.widths[i] // 8 if i < len(self.widths) else 12,
                anchor="w",
                padx=SPACING.TABLE_CELL_X,
                pady=SPACING.TABLE_CELL_Y
            ).pack(side="left")

        self._rows.append(row_frame)

    def clear(self):
        """Clear all rows."""
        for row in self._rows:
            row.destroy()
        self._rows = []
