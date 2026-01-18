"""
Status Components - Nordic Light Design System
===============================================
Status indicators, strips, and connection status displays.
"""

import tkinter as tk
from tkinter import Canvas
from typing import Optional, Dict
import math
from ..theme import COLORS, FONTS, SPACING, ICONS, ENV_BADGE_COLORS, BUTTON_CONFIG


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


# =============================================================================
# PREMIUM ENVIRONMENT BADGE
# =============================================================================

class PremiumEnvBadge(tk.Frame):
    """
    Premium environment badge with glowing dot and pulse animation.

    Features:
    - Dark pill-shaped container with subtle border
    - Colored dot with soft glow effect
    - Pulse animation for PROD (indicates "live")
    - Static dot for DEV

    Usage:
        badge = PremiumEnvBadge(parent, environment="PROD")
        badge.pack()
    """

    def __init__(
        self,
        parent,
        environment: str = "DEV",
        **kwargs
    ):
        # Determine colors based on environment
        self._is_prod = environment.upper() == "PROD"
        self._env_text = "PRODUCTION" if self._is_prod else "DEVELOPMENT"

        if self._is_prod:
            self._dot_color = ENV_BADGE_COLORS.PROD_DOT
            self._glow_color = ENV_BADGE_COLORS.PROD_GLOW
            self._text_color = ENV_BADGE_COLORS.PROD_TEXT
        else:
            self._dot_color = ENV_BADGE_COLORS.DEV_DOT
            self._glow_color = ENV_BADGE_COLORS.DEV_GLOW
            self._text_color = ENV_BADGE_COLORS.DEV_TEXT

        # Initialize frame with dark background
        super().__init__(
            parent,
            bg=ENV_BADGE_COLORS.BADGE_BG,
            highlightbackground=ENV_BADGE_COLORS.BADGE_BORDER,
            highlightthickness=1,
            **kwargs
        )

        # Inner padding frame
        inner = tk.Frame(self, bg=ENV_BADGE_COLORS.BADGE_BG)
        inner.pack(padx=12, pady=8)

        # Canvas for the glowing dot
        self._dot_size = 12
        self._glow_size = 24
        canvas_size = self._glow_size + 4

        self._canvas = Canvas(
            inner,
            width=canvas_size,
            height=canvas_size,
            bg=ENV_BADGE_COLORS.BADGE_BG,
            highlightthickness=0
        )
        self._canvas.pack(side="left", padx=(0, 10))

        # Draw glow layers (multiple circles with decreasing opacity)
        self._glow_items = []
        center = canvas_size // 2

        # Create glow layers (will be animated)
        for i in range(3):
            radius = self._glow_size // 2 - (i * 2)
            # Glow gets more transparent towards the edge
            glow_id = self._canvas.create_oval(
                center - radius, center - radius,
                center + radius, center + radius,
                fill="",
                outline="",
                width=0
            )
            self._glow_items.append(glow_id)

        # Draw the main dot
        dot_radius = self._dot_size // 2
        self._dot_item = self._canvas.create_oval(
            center - dot_radius, center - dot_radius,
            center + dot_radius, center + dot_radius,
            fill=self._dot_color,
            outline=""
        )

        # Environment text
        self._label = tk.Label(
            inner,
            text=self._env_text,
            fg=self._text_color,
            bg=ENV_BADGE_COLORS.BADGE_BG,
            font=(BUTTON_CONFIG.FONT_FAMILY, 11, "bold")
        )
        self._label.pack(side="left")

        # Animation state
        self._animation_phase = 0.0
        self._animation_id = None

        # Start pulse animation for PROD
        if self._is_prod:
            self._start_pulse()
        else:
            # Static glow for DEV
            self._draw_static_glow()

    def _hex_to_rgb(self, hex_color: str) -> tuple:
        """Convert hex color to RGB tuple."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def _rgb_to_hex(self, r: int, g: int, b: int) -> str:
        """Convert RGB to hex color."""
        return f"#{r:02x}{g:02x}{b:02x}"

    def _blend_with_bg(self, color: str, opacity: float) -> str:
        """Blend a color with the badge background at given opacity."""
        fg_rgb = self._hex_to_rgb(color)
        bg_rgb = self._hex_to_rgb(ENV_BADGE_COLORS.BADGE_BG)

        blended = tuple(
            int(fg * opacity + bg * (1 - opacity))
            for fg, bg in zip(fg_rgb, bg_rgb)
        )
        return self._rgb_to_hex(*blended)

    def _draw_static_glow(self):
        """Draw a static glow effect (for DEV)."""
        opacities = [0.15, 0.25, 0.4]
        for i, glow_id in enumerate(self._glow_items):
            blended = self._blend_with_bg(self._glow_color, opacities[i])
            self._canvas.itemconfig(glow_id, fill=blended, outline="")

    def _start_pulse(self):
        """Start the pulse animation for PROD."""
        self._animate_pulse()

    def _animate_pulse(self):
        """Animate the glow with a smooth pulse effect."""
        # Smooth sine wave oscillation
        self._animation_phase += 0.1
        if self._animation_phase > 2 * math.pi:
            self._animation_phase = 0

        # Calculate current opacity multiplier (0.5 to 1.0)
        pulse = (math.sin(self._animation_phase) + 1) / 2  # 0 to 1
        min_opacity = ENV_BADGE_COLORS.GLOW_OPACITY_MIN
        max_opacity = ENV_BADGE_COLORS.GLOW_OPACITY_MAX
        opacity_mult = min_opacity + (max_opacity - min_opacity) * pulse

        # Update glow layers
        base_opacities = [0.15, 0.25, 0.4]
        for i, glow_id in enumerate(self._glow_items):
            opacity = base_opacities[i] * opacity_mult
            blended = self._blend_with_bg(self._glow_color, opacity)
            self._canvas.itemconfig(glow_id, fill=blended)

        # Schedule next frame (~60fps would be 16ms, but 50ms is smooth enough)
        self._animation_id = self.after(50, self._animate_pulse)

    def destroy(self):
        """Clean up animation when widget is destroyed."""
        if self._animation_id:
            self.after_cancel(self._animation_id)
        super().destroy()

    def set_environment(self, environment: str):
        """Update the environment display."""
        was_prod = self._is_prod
        self._is_prod = environment.upper() == "PROD"
        self._env_text = "PRODUCTION" if self._is_prod else "DEVELOPMENT"

        if self._is_prod:
            self._dot_color = ENV_BADGE_COLORS.PROD_DOT
            self._glow_color = ENV_BADGE_COLORS.PROD_GLOW
            self._text_color = ENV_BADGE_COLORS.PROD_TEXT
        else:
            self._dot_color = ENV_BADGE_COLORS.DEV_DOT
            self._glow_color = ENV_BADGE_COLORS.DEV_GLOW
            self._text_color = ENV_BADGE_COLORS.DEV_TEXT

        # Update dot color
        self._canvas.itemconfig(self._dot_item, fill=self._dot_color)

        # Update label
        self._label.config(text=self._env_text, fg=self._text_color)

        # Handle animation change
        if self._is_prod and not was_prod:
            self._start_pulse()
        elif not self._is_prod and was_prod:
            if self._animation_id:
                self.after_cancel(self._animation_id)
                self._animation_id = None
            self._draw_static_glow()
