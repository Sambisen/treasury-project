"""
Badge Components - Nordic Light Design System
=============================================
Chips, badges, and status indicators.
"""

import tkinter as tk
from typing import Optional
from ..theme import COLORS, FONTS, SPACING, RADII, get_badge_colors


class Badge(tk.Frame):
    """
    Small badge/chip component for labels and status.
    Supports variants: default, primary, success, warning, danger, info
    """

    def __init__(
        self,
        parent,
        text: str,
        variant: str = "default",
        icon: str = "",
        size: str = "md",  # sm, md
        **kwargs
    ):
        bg_color, fg_color = get_badge_colors(variant)

        super().__init__(parent, bg=bg_color, **kwargs)

        # Size config
        sizes = {
            "sm": {"padx": 6, "pady": 2, "font": FONTS.LABEL_CAPS},
            "md": {"padx": 10, "pady": 4, "font": FONTS.LABEL},
        }
        config = sizes.get(size, sizes["md"])

        content = tk.Frame(self, bg=bg_color)
        content.pack(padx=config["padx"], pady=config["pady"])

        # Icon
        if icon:
            tk.Label(
                content,
                text=icon,
                fg=fg_color,
                bg=bg_color,
                font=config["font"]
            ).pack(side="left", padx=(0, 4))

        # Text
        tk.Label(
            content,
            text=text,
            fg=fg_color,
            bg=bg_color,
            font=config["font"]
        ).pack(side="left")


class StatusBadge(tk.Frame):
    """
    Status badge with dot indicator.
    Common statuses: online, offline, pending, error
    """

    def __init__(
        self,
        parent,
        text: str,
        status: str = "default",  # online, offline, pending, error
        show_dot: bool = True,
        **kwargs
    ):
        # Status colors
        status_colors = {
            "online": (COLORS.SUCCESS_BG, COLORS.SUCCESS),
            "connected": (COLORS.SUCCESS_BG, COLORS.SUCCESS),
            "ok": (COLORS.SUCCESS_BG, COLORS.SUCCESS),
            "offline": (COLORS.CHIP_BG, COLORS.TEXT_MUTED),
            "disconnected": (COLORS.CHIP_BG, COLORS.TEXT_MUTED),
            "pending": (COLORS.WARNING_BG, COLORS.WARNING),
            "loading": (COLORS.WARNING_BG, COLORS.WARNING),
            "error": (COLORS.DANGER_BG, COLORS.DANGER),
            "failed": (COLORS.DANGER_BG, COLORS.DANGER),
            "default": (COLORS.CHIP_BG, COLORS.TEXT_MUTED),
        }
        bg_color, fg_color = status_colors.get(status.lower(), status_colors["default"])

        super().__init__(parent, bg=bg_color, **kwargs)

        content = tk.Frame(self, bg=bg_color)
        content.pack(padx=10, pady=4)

        # Status dot
        if show_dot:
            tk.Label(
                content,
                text="\u25CF",  # Filled circle
                fg=fg_color,
                bg=bg_color,
                font=(FONTS.BODY[0], 8)
            ).pack(side="left", padx=(0, 6))

        # Text
        tk.Label(
            content,
            text=text,
            fg=fg_color,
            bg=bg_color,
            font=FONTS.LABEL
        ).pack(side="left")


class CountBadge(tk.Label):
    """
    Simple numeric count badge (e.g., notification count).
    """

    def __init__(
        self,
        parent,
        count: int = 0,
        variant: str = "default",  # default, accent, danger
        **kwargs
    ):
        colors = {
            "default": (COLORS.CHIP_BG, COLORS.TEXT_MUTED),
            "accent": (COLORS.ACCENT, COLORS.TEXT_INVERSE),
            "danger": (COLORS.DANGER, COLORS.TEXT_INVERSE),
        }
        bg_color, fg_color = colors.get(variant, colors["default"])

        super().__init__(
            parent,
            text=str(count) if count < 100 else "99+",
            fg=fg_color,
            bg=bg_color,
            font=FONTS.LABEL_CAPS,
            padx=6,
            pady=2,
            **kwargs
        )

    def set_count(self, count: int):
        """Update the count value."""
        self.configure(text=str(count) if count < 100 else "99+")


class MatchedBadge(tk.Frame):
    """
    Special badge for showing matched status with checkmark.
    """

    def __init__(
        self,
        parent,
        matched: bool = True,
        text: str = None,
        **kwargs
    ):
        if matched:
            bg_color = COLORS.SUCCESS_BG
            fg_color = COLORS.SUCCESS
            icon = "\u2713"
            label = text or "Matched"
        else:
            bg_color = COLORS.CHIP_BG
            fg_color = COLORS.TEXT_MUTED
            icon = "\u2014"  # Em dash
            label = text or "Pending"

        super().__init__(parent, bg=bg_color, **kwargs)

        content = tk.Frame(self, bg=bg_color)
        content.pack(padx=10, pady=4)

        tk.Label(
            content,
            text=icon,
            fg=fg_color,
            bg=bg_color,
            font=FONTS.LABEL
        ).pack(side="left", padx=(0, 4))

        tk.Label(
            content,
            text=label,
            fg=fg_color,
            bg=bg_color,
            font=FONTS.LABEL
        ).pack(side="left")

    def update_status(self, matched: bool, text: str = None):
        """Update the matched status."""
        # Recreate the badge (simpler than updating colors)
        for widget in self.winfo_children():
            widget.destroy()

        if matched:
            bg_color = COLORS.SUCCESS_BG
            fg_color = COLORS.SUCCESS
            icon = "\u2713"
            label = text or "Matched"
        else:
            bg_color = COLORS.CHIP_BG
            fg_color = COLORS.TEXT_MUTED
            icon = "\u2014"
            label = text or "Pending"

        self.configure(bg=bg_color)

        content = tk.Frame(self, bg=bg_color)
        content.pack(padx=10, pady=4)

        tk.Label(
            content,
            text=icon,
            fg=fg_color,
            bg=bg_color,
            font=FONTS.LABEL
        ).pack(side="left", padx=(0, 4))

        tk.Label(
            content,
            text=label,
            fg=fg_color,
            bg=bg_color,
            font=FONTS.LABEL
        ).pack(side="left")


class EnvironmentBadge(tk.Frame):
    """
    Badge showing environment (Dev/Prod).
    """

    def __init__(
        self,
        parent,
        environment: str = "Dev",
        **kwargs
    ):
        is_dev = environment.lower() in ("dev", "test", "development")

        if is_dev:
            bg_color = COLORS.WARNING_BG
            fg_color = COLORS.WARNING
        else:
            bg_color = COLORS.SUCCESS_BG
            fg_color = COLORS.SUCCESS

        super().__init__(parent, bg=bg_color, **kwargs)

        tk.Label(
            self,
            text=environment,
            fg=fg_color,
            bg=bg_color,
            font=FONTS.LABEL_CAPS,
            padx=8,
            pady=2
        ).pack()

    def set_environment(self, environment: str):
        """Update the environment."""
        is_dev = environment.lower() in ("dev", "test", "development")

        if is_dev:
            bg_color = COLORS.WARNING_BG
            fg_color = COLORS.WARNING
        else:
            bg_color = COLORS.SUCCESS_BG
            fg_color = COLORS.SUCCESS

        self.configure(bg=bg_color)
        for child in self.winfo_children():
            child.configure(text=environment, fg=fg_color, bg=bg_color)
