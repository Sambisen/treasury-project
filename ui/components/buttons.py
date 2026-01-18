"""
Button Components - Nordic Light Design System
==============================================
Themed button components with consistent styling.

Includes:
- Pure Tkinter buttons (BaseButton, PrimaryButton, etc.) for Nordic Light theme
- CTkButton-based buttons (CTkPrimaryButton, etc.) for dark premium theme
- make_ctk_button() factory function for easy button creation
"""

import tkinter as tk
from typing import Callable, Optional
from ..theme import COLORS, FONTS, SPACING, RADII, BUTTON_COLORS, BUTTON_CONFIG

# Import ctk_compat for CustomTkinter support
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from ctk_compat import ctk, CTK_AVAILABLE


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


# =============================================================================
# CTK BUTTON SYSTEM - Dark Premium Theme
# =============================================================================

def make_ctk_button(
    parent,
    text: str,
    command: Optional[Callable] = None,
    variant: str = "primary",   # primary | secondary | danger | ghost
    width: int = 180,
    height: int = None,
    size: str = "md",           # sm | md | lg
    icon: str = None,
    disabled: bool = False,
) -> ctk.CTkButton:
    """
    Creates a consistent, premium-looking CTkButton with dark theme styling.

    Args:
        parent: Parent widget
        text: Button text
        command: Click callback
        variant: "primary" (orange), "secondary" (outlined), "danger" (red), "ghost" (transparent)
        width: Button width in pixels
        height: Override height (otherwise uses size)
        size: "sm", "md", or "lg" for predefined heights
        icon: Optional icon text (e.g., "✓", "↻", "✖")
        disabled: Start in disabled state

    Returns:
        Configured CTkButton with press feedback
    """
    # Determine height from size
    if height is None:
        height = {
            "sm": BUTTON_CONFIG.HEIGHT_SM,
            "md": BUTTON_CONFIG.HEIGHT_MD,
            "lg": BUTTON_CONFIG.HEIGHT_LG,
        }.get(size, BUTTON_CONFIG.HEIGHT_MD)

    # Build label with optional icon
    label = f"{icon}  {text}" if icon else text

    # Font weight: bold for primary, normal for others
    font_weight = "bold" if variant == "primary" else "normal"
    font = (BUTTON_CONFIG.FONT_FAMILY, BUTTON_CONFIG.FONT_SIZE, font_weight)
    if size == "sm":
        font = (BUTTON_CONFIG.FONT_FAMILY, BUTTON_CONFIG.FONT_SIZE_SM, font_weight)

    # Base configuration (secondary style as default)
    config = dict(
        master=parent,
        text=label,
        command=command,
        height=height,
        width=width,
        corner_radius=BUTTON_CONFIG.CORNER_RADIUS,
        font=font,
        text_color=BUTTON_COLORS.TEXT,
        fg_color=BUTTON_COLORS.SECONDARY_BG,
        hover_color=BUTTON_COLORS.SECONDARY_HOVER,
        border_width=1,
        border_color=BUTTON_COLORS.SECONDARY_BORDER,
    )

    # Apply variant-specific styling
    if variant == "primary":
        config.update(
            fg_color=BUTTON_COLORS.PRIMARY,
            hover_color=BUTTON_COLORS.PRIMARY_HOVER,
            border_width=0,
            text_color=BUTTON_COLORS.TEXT_ON_ACCENT,
        )
    elif variant == "danger":
        config.update(
            fg_color=BUTTON_COLORS.DANGER,
            hover_color=BUTTON_COLORS.DANGER_HOVER,
            border_width=0,
            text_color=BUTTON_COLORS.TEXT_ON_ACCENT,
        )
    elif variant == "ghost":
        config.update(
            fg_color="transparent",
            hover_color=BUTTON_COLORS.GHOST_HOVER,
            border_width=0,
            text_color=BUTTON_COLORS.TEXT,
        )

    btn = ctk.CTkButton(**config)

    # Store variant for state restoration
    btn._button_variant = variant

    # Add press feedback for tactile feel
    def on_press(event):
        if btn.cget("state") != "disabled":
            pressed_colors = {
                "primary": BUTTON_COLORS.PRIMARY_PRESSED,
                "secondary": BUTTON_COLORS.SECONDARY_PRESSED,
                "danger": BUTTON_COLORS.DANGER_PRESSED,
                "ghost": BUTTON_COLORS.GHOST_PRESSED,
            }
            btn.configure(fg_color=pressed_colors.get(variant, BUTTON_COLORS.SECONDARY_PRESSED))

    def on_release(event):
        if btn.cget("state") != "disabled":
            release_colors = {
                "primary": BUTTON_COLORS.PRIMARY,
                "secondary": BUTTON_COLORS.SECONDARY_BG,
                "danger": BUTTON_COLORS.DANGER,
                "ghost": "transparent",
            }
            btn.configure(fg_color=release_colors.get(variant, BUTTON_COLORS.SECONDARY_BG))

    btn.bind("<ButtonPress-1>", on_press)
    btn.bind("<ButtonRelease-1>", on_release)

    # Apply disabled state if requested
    if disabled:
        set_button_disabled(btn, True)

    return btn


def set_button_disabled(btn: ctk.CTkButton, disabled: bool = True):
    """
    Set disabled state with premium styling that doesn't look 'washed out'.

    Args:
        btn: CTkButton to modify
        disabled: True to disable, False to enable
    """
    if disabled:
        btn.configure(
            state="disabled",
            fg_color=BUTTON_COLORS.DISABLED_BG,
            hover_color=BUTTON_COLORS.DISABLED_BG,
            text_color=BUTTON_COLORS.DISABLED_TEXT,
        )
        # Only set border if button has one
        try:
            if btn.cget("border_width") and btn.cget("border_width") > 0:
                btn.configure(border_color=BUTTON_COLORS.DISABLED_BORDER)
        except:
            pass
    else:
        btn.configure(state="normal")
        # Restore original variant colors
        variant = getattr(btn, "_button_variant", "secondary")
        if variant == "primary":
            btn.configure(
                fg_color=BUTTON_COLORS.PRIMARY,
                hover_color=BUTTON_COLORS.PRIMARY_HOVER,
                text_color=BUTTON_COLORS.TEXT_ON_ACCENT,
            )
        elif variant == "danger":
            btn.configure(
                fg_color=BUTTON_COLORS.DANGER,
                hover_color=BUTTON_COLORS.DANGER_HOVER,
                text_color=BUTTON_COLORS.TEXT_ON_ACCENT,
            )
        elif variant == "ghost":
            btn.configure(
                fg_color="transparent",
                hover_color=BUTTON_COLORS.GHOST_HOVER,
                text_color=BUTTON_COLORS.TEXT,
            )
        else:  # secondary
            btn.configure(
                fg_color=BUTTON_COLORS.SECONDARY_BG,
                hover_color=BUTTON_COLORS.SECONDARY_HOVER,
                text_color=BUTTON_COLORS.TEXT,
                border_color=BUTTON_COLORS.SECONDARY_BORDER,
            )


# =============================================================================
# CTK BUTTON CLASSES - Object-Oriented Alternative
# =============================================================================

class CTkBaseButton:
    """
    Mixin for CTkButton with press feedback and variant support.
    Use with make_ctk_button() for simpler API, or subclass for custom behavior.
    """

    @staticmethod
    def create(
        parent,
        text: str,
        command: Optional[Callable] = None,
        variant: str = "primary",
        **kwargs
    ) -> ctk.CTkButton:
        """Factory method - alias for make_ctk_button()."""
        return make_ctk_button(parent, text, command, variant, **kwargs)


class CTkPrimaryButton:
    """Primary action button (orange fill, dark text)."""

    def __new__(
        cls,
        parent,
        text: str,
        command: Optional[Callable] = None,
        width: int = 180,
        icon: str = None,
        **kwargs
    ):
        return make_ctk_button(
            parent, text, command,
            variant="primary",
            width=width,
            icon=icon,
            **kwargs
        )


class CTkSecondaryButton:
    """Secondary button (outlined, subtle)."""

    def __new__(
        cls,
        parent,
        text: str,
        command: Optional[Callable] = None,
        width: int = 180,
        icon: str = None,
        **kwargs
    ):
        return make_ctk_button(
            parent, text, command,
            variant="secondary",
            width=width,
            icon=icon,
            **kwargs
        )


class CTkDangerButton:
    """Danger/destructive action button (red fill)."""

    def __new__(
        cls,
        parent,
        text: str,
        command: Optional[Callable] = None,
        width: int = 160,
        icon: str = None,
        **kwargs
    ):
        return make_ctk_button(
            parent, text, command,
            variant="danger",
            width=width,
            icon=icon,
            **kwargs
        )


class CTkGhostButton:
    """Ghost/text button (transparent, text only)."""

    def __new__(
        cls,
        parent,
        text: str,
        command: Optional[Callable] = None,
        width: int = 140,
        icon: str = None,
        **kwargs
    ):
        return make_ctk_button(
            parent, text, command,
            variant="ghost",
            width=width,
            icon=icon,
            **kwargs
        )
