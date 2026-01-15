"""
Status Components - Nordic Light Design System
===============================================
Status indicators, strips, and connection status displays.
"""

import tkinter as tk
from typing import Optional, Dict
from ..theme import COLORS, FONTS, SPACING, ICONS


class StatusStrip(tk.Frame):
    """
    Bottom status strip for application-wide status display.
    Shows connection status, last update time, environment, etc.
    """

    def __init__(
        self,
        parent,
        **kwargs
    ):
        super().__init__(
            parent,
            bg=COLORS.STATUS_BAR_BG,
            height=28,
            **kwargs
        )
        self.pack_propagate(False)

        # Left section
        self._left = tk.Frame(self, bg=COLORS.STATUS_BAR_BG)
        self._left.pack(side="left", fill="y", padx=SPACING.MD)

        # Right section
        self._right = tk.Frame(self, bg=COLORS.STATUS_BAR_BG)
        self._right.pack(side="right", fill="y", padx=SPACING.MD)

        # Center section
        self._center = tk.Frame(self, bg=COLORS.STATUS_BAR_BG)
        self._center.pack(side="left", fill="both", expand=True)

        # Status items storage
        self._items: Dict[str, tk.Widget] = {}

    def add_item(
        self,
        key: str,
        text: str = "",
        icon: str = "",
        position: str = "left",  # left, center, right
        fg: str = None
    ) -> tk.Label:
        """Add a status item."""
        parent = {
            "left": self._left,
            "center": self._center,
            "right": self._right
        }.get(position, self._left)

        frame = tk.Frame(parent, bg=COLORS.STATUS_BAR_BG)
        frame.pack(side="left" if position != "right" else "right", padx=SPACING.SM)

        if icon:
            tk.Label(
                frame,
                text=icon,
                fg=fg or COLORS.TEXT_MUTED,
                bg=COLORS.STATUS_BAR_BG,
                font=(FONTS.BODY[0], 10)
            ).pack(side="left", padx=(0, 4))

        label = tk.Label(
            frame,
            text=text,
            fg=fg or COLORS.TEXT_SECONDARY,
            bg=COLORS.STATUS_BAR_BG,
            font=FONTS.STATUS
        )
        label.pack(side="left")

        self._items[key] = {"frame": frame, "label": label}
        return label

    def update_item(self, key: str, text: str = None, fg: str = None):
        """Update a status item."""
        if key in self._items:
            label = self._items[key]["label"]
            if text is not None:
                label.configure(text=text)
            if fg is not None:
                label.configure(fg=fg)

    def remove_item(self, key: str):
        """Remove a status item."""
        if key in self._items:
            self._items[key]["frame"].destroy()
            del self._items[key]


class ConnectionIndicator(tk.Frame):
    """
    Connection status indicator with dot and label.
    """

    def __init__(
        self,
        parent,
        label: str = "Bloomberg",
        connected: bool = False,
        **kwargs
    ):
        super().__init__(parent, bg=COLORS.SURFACE, **kwargs)

        self._connected = connected

        # Status dot
        self._dot = tk.Label(
            self,
            text=ICONS.CIRCLE_FILLED,
            fg=COLORS.SUCCESS if connected else COLORS.TEXT_PLACEHOLDER,
            bg=COLORS.SURFACE,
            font=(FONTS.BODY[0], 8)
        )
        self._dot.pack(side="left", padx=(0, 6))

        # Label
        self._label = tk.Label(
            self,
            text=label,
            fg=COLORS.TEXT_SECONDARY,
            bg=COLORS.SURFACE,
            font=FONTS.BODY_SM
        )
        self._label.pack(side="left")

    def set_connected(self, connected: bool):
        """Update connection status."""
        self._connected = connected
        self._dot.configure(
            fg=COLORS.SUCCESS if connected else COLORS.TEXT_PLACEHOLDER
        )

    def is_connected(self) -> bool:
        """Get current connection status."""
        return self._connected


class StatusChip(tk.Frame):
    """
    Compact status chip with icon and text.
    """

    def __init__(
        self,
        parent,
        text: str,
        status: str = "default",  # default, success, warning, danger, info
        icon: str = None,
        **kwargs
    ):
        # Status configuration
        configs = {
            "default": (COLORS.CHIP_BG, COLORS.TEXT_MUTED, None),
            "success": (COLORS.SUCCESS_BG, COLORS.SUCCESS, ICONS.SUCCESS),
            "warning": (COLORS.WARNING_BG, COLORS.WARNING, ICONS.WARNING),
            "danger": (COLORS.DANGER_BG, COLORS.DANGER, ICONS.DANGER),
            "info": (COLORS.INFO_BG, COLORS.INFO, ICONS.INFO),
        }
        bg_color, fg_color, default_icon = configs.get(status, configs["default"])

        super().__init__(parent, bg=bg_color, **kwargs)

        content = tk.Frame(self, bg=bg_color)
        content.pack(padx=8, pady=3)

        # Icon
        icon_text = icon or default_icon
        if icon_text:
            tk.Label(
                content,
                text=icon_text,
                fg=fg_color,
                bg=bg_color,
                font=(FONTS.BODY[0], 9)
            ).pack(side="left", padx=(0, 4))

        # Text
        tk.Label(
            content,
            text=text,
            fg=fg_color,
            bg=bg_color,
            font=FONTS.LABEL
        ).pack(side="left")


class ActivityIndicator(tk.Frame):
    """
    Activity/loading indicator with animated dots.
    """

    def __init__(
        self,
        parent,
        text: str = "Loading",
        **kwargs
    ):
        super().__init__(parent, bg=COLORS.SURFACE, **kwargs)

        self._text = text
        self._dots = 0
        self._running = False

        self._label = tk.Label(
            self,
            text=text,
            fg=COLORS.TEXT_MUTED,
            bg=COLORS.SURFACE,
            font=FONTS.BODY_SM
        )
        self._label.pack()

    def start(self):
        """Start the animation."""
        self._running = True
        self._animate()

    def stop(self):
        """Stop the animation."""
        self._running = False
        self._label.configure(text=self._text)

    def _animate(self):
        """Animate the dots."""
        if not self._running:
            return

        self._dots = (self._dots + 1) % 4
        dots_str = "." * self._dots
        self._label.configure(text=f"{self._text}{dots_str}")
        self.after(400, self._animate)


class LastUpdatedLabel(tk.Frame):
    """
    Shows last updated timestamp with auto-refresh.
    """

    def __init__(
        self,
        parent,
        prefix: str = "Last updated:",
        **kwargs
    ):
        super().__init__(parent, bg=COLORS.SURFACE, **kwargs)

        self._prefix = prefix

        tk.Label(
            self,
            text=prefix,
            fg=COLORS.TEXT_MUTED,
            bg=COLORS.SURFACE,
            font=FONTS.BODY_SM
        ).pack(side="left", padx=(0, 4))

        self._time_label = tk.Label(
            self,
            text="--:--",
            fg=COLORS.TEXT_SECONDARY,
            bg=COLORS.SURFACE,
            font=FONTS.BODY_SM
        )
        self._time_label.pack(side="left")

    def update_time(self, time_str: str = None):
        """Update the displayed time."""
        if time_str is None:
            from datetime import datetime
            time_str = datetime.now().strftime("%H:%M:%S")
        self._time_label.configure(text=time_str)


class ModeIndicator(tk.Frame):
    """
    TEST/PROD mode indicator with prominent styling.
    """

    def __init__(
        self,
        parent,
        mode: str = "TEST",
        **kwargs
    ):
        self._mode = mode.upper()
        is_test = self._mode in ("TEST", "DEV", "DEVELOPMENT")

        bg_color = COLORS.WARNING_BG if is_test else COLORS.SUCCESS_BG
        fg_color = COLORS.WARNING if is_test else COLORS.SUCCESS

        super().__init__(parent, bg=bg_color, **kwargs)

        self._label = tk.Label(
            self,
            text=self._mode,
            fg=fg_color,
            bg=bg_color,
            font=FONTS.LABEL_CAPS,
            padx=10,
            pady=4
        )
        self._label.pack()

    def set_mode(self, mode: str):
        """Update the mode display."""
        self._mode = mode.upper()
        is_test = self._mode in ("TEST", "DEV", "DEVELOPMENT")

        bg_color = COLORS.WARNING_BG if is_test else COLORS.SUCCESS_BG
        fg_color = COLORS.WARNING if is_test else COLORS.SUCCESS

        self.configure(bg=bg_color)
        self._label.configure(text=self._mode, fg=fg_color, bg=bg_color)

    def get_mode(self) -> str:
        """Get current mode."""
        return self._mode


class EnvironmentBanner(tk.Frame):
    """
    Full-width environment banner for TEST mode warning.
    """

    def __init__(
        self,
        parent,
        environment: str = "TEST",
        message: str = None,
        **kwargs
    ):
        is_test = environment.upper() in ("TEST", "DEV", "DEVELOPMENT")

        if is_test:
            bg_color = COLORS.WARNING_BG
            fg_color = COLORS.WARNING
            default_msg = "TEST ENVIRONMENT - Data may not reflect production"
        else:
            bg_color = COLORS.SUCCESS_BG
            fg_color = COLORS.SUCCESS
            default_msg = "PRODUCTION"

        super().__init__(parent, bg=bg_color, **kwargs)

        content = tk.Frame(self, bg=bg_color)
        content.pack(pady=6)

        tk.Label(
            content,
            text=ICONS.WARNING if is_test else ICONS.SUCCESS,
            fg=fg_color,
            bg=bg_color,
            font=(FONTS.BODY[0], 12)
        ).pack(side="left", padx=(0, 8))

        tk.Label(
            content,
            text=message or default_msg,
            fg=fg_color,
            bg=bg_color,
            font=FONTS.BUTTON
        ).pack(side="left")
