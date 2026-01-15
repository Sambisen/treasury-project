"""
Card Components - Nordic Light Design System
============================================
Card containers with consistent styling and shadow effects.
"""

import tkinter as tk
from typing import Optional
from ..theme import COLORS, FONTS, SPACING, RADII


class Card(tk.Frame):
    """
    Card container with white background, subtle border, and optional shadow effect.
    Use for content grouping throughout the app.
    """

    def __init__(
        self,
        parent,
        padding: int = None,
        shadow: bool = True,
        border: bool = True,
        **kwargs
    ):
        # Use BG color for shadow simulation
        super().__init__(
            parent,
            bg=COLORS.BORDER if shadow else COLORS.BG,
            **kwargs
        )

        padding = padding if padding is not None else SPACING.CARD_PADDING

        # Inner frame creates the card surface with border/shadow effect
        self._inner = tk.Frame(
            self,
            bg=COLORS.SURFACE,
            highlightbackground=COLORS.BORDER if border else COLORS.SURFACE,
            highlightthickness=1 if border else 0,
        )

        # Pack with small offset for shadow effect
        if shadow:
            self._inner.pack(fill="both", expand=True, padx=(0, 2), pady=(0, 2))
        else:
            self._inner.pack(fill="both", expand=True)

        # Content frame with padding
        self.content = tk.Frame(self._inner, bg=COLORS.SURFACE)
        self.content.pack(fill="both", expand=True, padx=padding, pady=padding)

    def get_content_frame(self) -> tk.Frame:
        """Return the content frame for adding widgets."""
        return self.content


class CardHeader(tk.Frame):
    """
    Card header section with title and optional actions.
    """

    def __init__(
        self,
        parent,
        title: str = "",
        subtitle: str = "",
        badge_text: str = "",
        badge_variant: str = "default",
        **kwargs
    ):
        super().__init__(parent, bg=COLORS.SURFACE, **kwargs)

        # Left side: title and subtitle
        title_frame = tk.Frame(self, bg=COLORS.SURFACE)
        title_frame.pack(side="left", fill="x", expand=True)

        # Title row
        title_row = tk.Frame(title_frame, bg=COLORS.SURFACE)
        title_row.pack(anchor="w")

        if title:
            tk.Label(
                title_row,
                text=title,
                fg=COLORS.TEXT,
                bg=COLORS.SURFACE,
                font=FONTS.H4
            ).pack(side="left")

        # Badge (if provided)
        if badge_text:
            from .badges import Badge
            Badge(title_row, text=badge_text, variant=badge_variant).pack(side="left", padx=(12, 0))

        if subtitle:
            tk.Label(
                title_frame,
                text=subtitle,
                fg=COLORS.TEXT_MUTED,
                bg=COLORS.SURFACE,
                font=FONTS.BODY_SM
            ).pack(anchor="w", pady=(4, 0))

        # Right side: actions container
        self.actions = tk.Frame(self, bg=COLORS.SURFACE)
        self.actions.pack(side="right")


class CardBody(tk.Frame):
    """Card body section with standard spacing."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=COLORS.SURFACE, **kwargs)


class CardFooter(tk.Frame):
    """Card footer section with top border."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=COLORS.SURFACE, **kwargs)

        # Top border line
        tk.Frame(self, bg=COLORS.BORDER, height=1).pack(fill="x", pady=(0, SPACING.MD))


class MetricCard(tk.Frame):
    """
    Compact metric display card for KPIs.
    Shows a label and large value.
    """

    def __init__(
        self,
        parent,
        label: str,
        value: str,
        sublabel: str = "",
        variant: str = "default",  # default, success, warning, danger, accent
        **kwargs
    ):
        super().__init__(
            parent,
            bg=COLORS.SURFACE,
            highlightbackground=COLORS.BORDER,
            highlightthickness=1,
            **kwargs
        )

        # Color mapping
        colors = {
            "default": COLORS.TEXT,
            "success": COLORS.SUCCESS,
            "warning": COLORS.WARNING,
            "danger": COLORS.DANGER,
            "accent": COLORS.ACCENT,
        }
        value_color = colors.get(variant, COLORS.TEXT)

        # Content with padding
        content = tk.Frame(self, bg=COLORS.SURFACE)
        content.pack(fill="both", expand=True, padx=SPACING.LG, pady=SPACING.MD)

        # Label (top)
        tk.Label(
            content,
            text=label.upper(),
            fg=COLORS.TEXT_MUTED,
            bg=COLORS.SURFACE,
            font=FONTS.LABEL_CAPS
        ).pack(anchor="w")

        # Value (large)
        tk.Label(
            content,
            text=value,
            fg=value_color,
            bg=COLORS.SURFACE,
            font=FONTS.KPI
        ).pack(anchor="w", pady=(4, 0))

        # Sublabel (optional)
        if sublabel:
            tk.Label(
                content,
                text=sublabel,
                fg=COLORS.TEXT_MUTED,
                bg=COLORS.SURFACE,
                font=FONTS.BODY_SM
            ).pack(anchor="w", pady=(2, 0))


class InfoCard(tk.Frame):
    """
    Information card with icon and message.
    Used for alerts, tips, and notifications.
    """

    def __init__(
        self,
        parent,
        message: str,
        title: str = "",
        variant: str = "info",  # info, success, warning, danger
        icon: str = None,
        dismissable: bool = False,
        on_dismiss: callable = None,
        **kwargs
    ):
        # Variant colors
        variants = {
            "info": (COLORS.INFO_BG, COLORS.INFO, "\u2139"),
            "success": (COLORS.SUCCESS_BG, COLORS.SUCCESS, "\u2713"),
            "warning": (COLORS.WARNING_BG, COLORS.WARNING, "\u26A0"),
            "danger": (COLORS.DANGER_BG, COLORS.DANGER, "\u2716"),
        }
        bg_color, fg_color, default_icon = variants.get(variant, variants["info"])

        super().__init__(
            parent,
            bg=bg_color,
            highlightbackground=fg_color,
            highlightthickness=1,
            **kwargs
        )

        content = tk.Frame(self, bg=bg_color)
        content.pack(fill="both", expand=True, padx=SPACING.MD, pady=SPACING.SM)

        # Icon
        icon_text = icon or default_icon
        tk.Label(
            content,
            text=icon_text,
            fg=fg_color,
            bg=bg_color,
            font=(FONTS.BODY[0], 14)
        ).pack(side="left", padx=(0, SPACING.SM))

        # Text container
        text_frame = tk.Frame(content, bg=bg_color)
        text_frame.pack(side="left", fill="both", expand=True)

        if title:
            tk.Label(
                text_frame,
                text=title,
                fg=fg_color,
                bg=bg_color,
                font=FONTS.BUTTON
            ).pack(anchor="w")

        tk.Label(
            text_frame,
            text=message,
            fg=COLORS.TEXT,
            bg=bg_color,
            font=FONTS.BODY_SM,
            wraplength=400,
            justify="left"
        ).pack(anchor="w")

        # Dismiss button
        if dismissable and on_dismiss:
            tk.Label(
                content,
                text="\u2715",
                fg=COLORS.TEXT_MUTED,
                bg=bg_color,
                font=FONTS.BODY,
                cursor="hand2"
            ).pack(side="right")
