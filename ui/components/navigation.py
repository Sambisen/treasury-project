"""
Navigation Components - Nordic Light Design System
=================================================
Sidebar navigation with consistent styling.
"""

import tkinter as tk
from typing import List, Dict, Optional, Callable
from ..theme import COLORS, FONTS, SPACING, COMPONENTS, ICONS


class NavItem(tk.Frame):
    """
    Single navigation item with icon, label, and active state.
    """

    def __init__(
        self,
        parent,
        text: str,
        icon: str = "",
        active: bool = False,
        command: Optional[Callable] = None,
        **kwargs
    ):
        self.command = command
        self._active = active

        super().__init__(
            parent,
            bg=COLORS.NAV_ACTIVE_BG if active else COLORS.NAV_BG,
            cursor="hand2",
            **kwargs
        )

        # Active indicator (orange line on left)
        self._indicator = tk.Frame(
            self,
            bg=COLORS.NAV_INDICATOR if active else COLORS.NAV_BG,
            width=3
        )
        self._indicator.pack(side="left", fill="y")

        # Content
        content = tk.Frame(self, bg=self.cget("bg"))
        content.pack(fill="both", expand=True, padx=SPACING.MD, pady=SPACING.SM)

        # Icon
        if icon:
            self._icon = tk.Label(
                content,
                text=icon,
                fg=COLORS.ACCENT if active else COLORS.TEXT_MUTED,
                bg=self.cget("bg"),
                font=(FONTS.BODY[0], 14),
                width=2
            )
            self._icon.pack(side="left", padx=(0, SPACING.SM))
            self._icon.bind("<Button-1>", self._on_click)
            self._icon.bind("<Enter>", self._on_enter)
            self._icon.bind("<Leave>", self._on_leave)
        else:
            self._icon = None

        # Label
        self._label = tk.Label(
            content,
            text=text,
            fg=COLORS.TEXT if active else COLORS.TEXT_SECONDARY,
            bg=self.cget("bg"),
            font=FONTS.NAV,
            anchor="w"
        )
        self._label.pack(side="left", fill="x", expand=True)
        self._label.bind("<Button-1>", self._on_click)
        self._label.bind("<Enter>", self._on_enter)
        self._label.bind("<Leave>", self._on_leave)

        # Bindings on frame
        self.bind("<Button-1>", self._on_click)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        content.bind("<Button-1>", self._on_click)
        content.bind("<Enter>", self._on_enter)
        content.bind("<Leave>", self._on_leave)

    def _on_click(self, event=None):
        if self.command:
            self.command()

    def _on_enter(self, event=None):
        if not self._active:
            self._set_hover_state(True)

    def _on_leave(self, event=None):
        if not self._active:
            self._set_hover_state(False)

    def _set_hover_state(self, hover: bool):
        bg = COLORS.NAV_HOVER_BG if hover else COLORS.NAV_BG
        self.configure(bg=bg)
        for child in self.winfo_children():
            if isinstance(child, tk.Frame):
                child.configure(bg=bg)
                for subchild in child.winfo_children():
                    if isinstance(subchild, (tk.Label, tk.Frame)):
                        subchild.configure(bg=bg)

    def set_active(self, active: bool):
        """Update active state."""
        self._active = active

        if active:
            bg = COLORS.NAV_ACTIVE_BG
            fg = COLORS.TEXT
            icon_fg = COLORS.ACCENT
            indicator_bg = COLORS.NAV_INDICATOR
        else:
            bg = COLORS.NAV_BG
            fg = COLORS.TEXT_SECONDARY
            icon_fg = COLORS.TEXT_MUTED
            indicator_bg = COLORS.NAV_BG

        self.configure(bg=bg)
        self._indicator.configure(bg=indicator_bg)
        self._label.configure(fg=fg, bg=bg)
        if self._icon:
            self._icon.configure(fg=icon_fg, bg=bg)

        # Update all nested frames
        for child in self.winfo_children():
            if isinstance(child, tk.Frame) and child != self._indicator:
                child.configure(bg=bg)
                for subchild in child.winfo_children():
                    if hasattr(subchild, 'configure'):
                        try:
                            subchild.configure(bg=bg)
                        except tk.TclError:
                            pass


class NavSection(tk.Frame):
    """
    Section header in navigation (e.g., "COMMAND CENTER").
    """

    def __init__(
        self,
        parent,
        text: str,
        **kwargs
    ):
        super().__init__(parent, bg=COLORS.NAV_BG, **kwargs)

        tk.Label(
            self,
            text=text.upper(),
            fg=COLORS.TEXT_PLACEHOLDER,
            bg=COLORS.NAV_BG,
            font=FONTS.NAV_SECTION,
            anchor="w"
        ).pack(fill="x", padx=SPACING.LG, pady=(SPACING.LG, SPACING.SM))


class SidebarNav(tk.Frame):
    """
    Complete sidebar navigation component.
    """

    def __init__(
        self,
        parent,
        items: List[Dict],
        width: int = None,
        on_select: Optional[Callable] = None,
        **kwargs
    ):
        width = width or COMPONENTS.SIDEBAR_WIDTH

        super().__init__(
            parent,
            bg=COLORS.NAV_BG,
            width=width,
            highlightbackground=COLORS.BORDER,
            highlightthickness=1,
            **kwargs
        )
        self.pack_propagate(False)  # Maintain fixed width

        self.on_select = on_select
        self._items = {}
        self._active_item = None

        # Build navigation
        for item in items:
            item_type = item.get("type", "item")

            if item_type == "section":
                NavSection(self, text=item.get("text", "")).pack(fill="x")

            elif item_type == "item":
                item_id = item.get("id", item.get("text", ""))
                nav_item = NavItem(
                    self,
                    text=item.get("text", ""),
                    icon=item.get("icon", ""),
                    active=item.get("active", False),
                    command=lambda i=item_id: self._on_item_click(i)
                )
                nav_item.pack(fill="x")
                self._items[item_id] = nav_item

                if item.get("active", False):
                    self._active_item = item_id

            elif item_type == "divider":
                tk.Frame(self, bg=COLORS.BORDER, height=1).pack(fill="x", pady=SPACING.SM)

            elif item_type == "spacer":
                tk.Frame(self, bg=COLORS.NAV_BG).pack(fill="both", expand=True)

    def _on_item_click(self, item_id: str):
        """Handle item click."""
        self.set_active(item_id)
        if self.on_select:
            self.on_select(item_id)

    def set_active(self, item_id: str):
        """Set the active navigation item."""
        # Deactivate previous
        if self._active_item and self._active_item in self._items:
            self._items[self._active_item].set_active(False)

        # Activate new
        if item_id in self._items:
            self._items[item_id].set_active(True)
            self._active_item = item_id

    def get_active(self) -> Optional[str]:
        """Get the currently active item ID."""
        return self._active_item


class QuickAccessItem(tk.Frame):
    """
    Quick access link item (folder, file, etc.).
    """

    def __init__(
        self,
        parent,
        text: str,
        icon: str = ICONS.FOLDER,
        command: Optional[Callable] = None,
        **kwargs
    ):
        super().__init__(parent, bg=COLORS.NAV_BG, cursor="hand2", **kwargs)

        self.command = command

        content = tk.Frame(self, bg=COLORS.NAV_BG)
        content.pack(fill="x", padx=SPACING.LG, pady=SPACING.XS)

        # Icon
        tk.Label(
            content,
            text=icon,
            fg=COLORS.TEXT_MUTED,
            bg=COLORS.NAV_BG,
            font=(FONTS.BODY[0], 12)
        ).pack(side="left", padx=(0, SPACING.SM))

        # Text
        self._label = tk.Label(
            content,
            text=text,
            fg=COLORS.TEXT_SECONDARY,
            bg=COLORS.NAV_BG,
            font=FONTS.BODY_SM,
            anchor="w"
        )
        self._label.pack(side="left")

        # Bindings
        for widget in [self, content, self._label]:
            widget.bind("<Button-1>", self._on_click)
            widget.bind("<Enter>", self._on_enter)
            widget.bind("<Leave>", self._on_leave)

    def _on_click(self, event=None):
        if self.command:
            self.command()

    def _on_enter(self, event=None):
        self._label.configure(fg=COLORS.ACCENT)

    def _on_leave(self, event=None):
        self._label.configure(fg=COLORS.TEXT_SECONDARY)
