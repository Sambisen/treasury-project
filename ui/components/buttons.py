"""
Button Components - Nordic Light Design System
==============================================
Themed button components with consistent styling.
"""

import tkinter as tk
from typing import Callable, Optional
from ..theme import COLORS, FONTS, SPACING, RADII


class BaseButton(tk.Frame):
    """Base button with hover effects and consistent styling."""

    def __init__(
        self,
        parent,
        text: str = "",
        command: Optional[Callable] = None,
        icon: str = "",
        width: Optional[int] = None,
        size: str = "md",  # sm, md, lg
        disabled: bool = False,
        **kwargs
    ):
        super().__init__(parent, bg=self._get_bg_color(), cursor="hand2" if not disabled else "")

        self.command = command
        self.disabled = disabled
        self._size = size
        self._pressed = False

        # Size configurations
        sizes = {
            "sm": {"padx": 12, "pady": 6, "font": FONTS.BUTTON_SM},
            "md": {"padx": 16, "pady": 10, "font": FONTS.BUTTON},
            "lg": {"padx": 20, "pady": 12, "font": FONTS.BUTTON},
        }
        config = sizes.get(size, sizes["md"])

        # Create inner container for padding simulation
        self._inner = tk.Frame(self, bg=self._get_bg_color())
        self._inner.pack(fill="both", expand=True, padx=2, pady=2)

        # Build content
        content_frame = tk.Frame(self._inner, bg=self._get_bg_color())
        content_frame.pack(expand=True)

        # Icon (if provided)
        if icon:
            self._icon_label = tk.Label(
                content_frame,
                text=icon,
                fg=self._get_fg_color(),
                bg=self._get_bg_color(),
                font=config["font"]
            )
            self._icon_label.pack(side="left", padx=(0, 6) if text else 0)
            self._icon_label.bind("<Button-1>", self._on_click)
            self._icon_label.bind("<Enter>", self._on_enter)
            self._icon_label.bind("<Leave>", self._on_leave)

        # Text
        if text:
            self._text_label = tk.Label(
                content_frame,
                text=text,
                fg=self._get_fg_color(),
                bg=self._get_bg_color(),
                font=config["font"]
            )
            self._text_label.pack(side="left")
            self._text_label.bind("<Button-1>", self._on_click)
            self._text_label.bind("<Enter>", self._on_enter)
            self._text_label.bind("<Leave>", self._on_leave)

        # Apply padding via frame config
        self.configure(padx=config["padx"], pady=config["pady"])

        # Width handling
        if width:
            self.configure(width=width)

        # Bindings
        self.bind("<Button-1>", self._on_click)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self._inner.bind("<Button-1>", self._on_click)
        self._inner.bind("<Enter>", self._on_enter)
        self._inner.bind("<Leave>", self._on_leave)
        content_frame.bind("<Button-1>", self._on_click)
        content_frame.bind("<Enter>", self._on_enter)
        content_frame.bind("<Leave>", self._on_leave)

        # Apply disabled state
        if disabled:
            self._apply_disabled_state()

    def _get_bg_color(self) -> str:
        """Override in subclasses."""
        return COLORS.SURFACE

    def _get_fg_color(self) -> str:
        """Override in subclasses."""
        return COLORS.TEXT

    def _get_hover_bg(self) -> str:
        """Override in subclasses."""
        return COLORS.SURFACE_HOVER

    def _get_hover_fg(self) -> str:
        """Override in subclasses."""
        return self._get_fg_color()

    def _on_click(self, event=None):
        if not self.disabled and self.command:
            self.command()

    def _on_enter(self, event=None):
        if not self.disabled:
            self._set_colors(self._get_hover_bg(), self._get_hover_fg())

    def _on_leave(self, event=None):
        if not self.disabled:
            self._set_colors(self._get_bg_color(), self._get_fg_color())

    def _set_colors(self, bg: str, fg: str):
        """Update all widget colors."""
        self.configure(bg=bg)
        self._inner.configure(bg=bg)
        for child in self._inner.winfo_children():
            child.configure(bg=bg)
            for subchild in child.winfo_children():
                if isinstance(subchild, tk.Label):
                    subchild.configure(bg=bg, fg=fg)

    def _apply_disabled_state(self):
        """Apply disabled visual state."""
        self.configure(cursor="")
        self._set_colors(COLORS.CHIP_BG, COLORS.TEXT_PLACEHOLDER)

    def set_disabled(self, disabled: bool):
        """Update disabled state."""
        self.disabled = disabled
        if disabled:
            self._apply_disabled_state()
        else:
            self.configure(cursor="hand2")
            self._set_colors(self._get_bg_color(), self._get_fg_color())


class PrimaryButton(BaseButton):
    """Primary action button with accent color fill."""

    def _get_bg_color(self) -> str:
        return COLORS.ACCENT

    def _get_fg_color(self) -> str:
        return COLORS.TEXT_INVERSE

    def _get_hover_bg(self) -> str:
        return COLORS.ACCENT_HOVER

    def _get_hover_fg(self) -> str:
        return COLORS.TEXT_INVERSE


class SecondaryButton(BaseButton):
    """Secondary button with outline/subtle style."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        # Add border effect
        self.configure(highlightbackground=COLORS.BORDER, highlightthickness=1)

    def _get_bg_color(self) -> str:
        return COLORS.SURFACE

    def _get_fg_color(self) -> str:
        return COLORS.TEXT

    def _get_hover_bg(self) -> str:
        return COLORS.SURFACE_HOVER


class GhostButton(BaseButton):
    """Ghost/text button with no background."""

    def _get_bg_color(self) -> str:
        return COLORS.SURFACE  # Transparent effect via same bg as parent

    def _get_fg_color(self) -> str:
        return COLORS.ACCENT

    def _get_hover_bg(self) -> str:
        return COLORS.ACCENT_LIGHT


class DangerButton(BaseButton):
    """Danger/destructive action button."""

    def _get_bg_color(self) -> str:
        return COLORS.DANGER

    def _get_fg_color(self) -> str:
        return COLORS.TEXT_INVERSE

    def _get_hover_bg(self) -> str:
        return "#B91C1C"  # Darker red

    def _get_hover_fg(self) -> str:
        return COLORS.TEXT_INVERSE


class IconButton(tk.Label):
    """Simple icon-only button."""

    def __init__(
        self,
        parent,
        icon: str,
        command: Optional[Callable] = None,
        size: int = 24,
        color: str = None,
        hover_color: str = None,
        bg: str = None,
        **kwargs
    ):
        self.command = command
        self._color = color or COLORS.TEXT_MUTED
        self._hover_color = hover_color or COLORS.ACCENT
        self._bg = bg or COLORS.SURFACE

        super().__init__(
            parent,
            text=icon,
            fg=self._color,
            bg=self._bg,
            font=(FONTS.BODY[0], size),
            cursor="hand2",
            **kwargs
        )

        self.bind("<Button-1>", self._on_click)
        self.bind("<Enter>", lambda e: self.config(fg=self._hover_color))
        self.bind("<Leave>", lambda e: self.config(fg=self._color))

    def _on_click(self, event=None):
        if self.command:
            self.command()
