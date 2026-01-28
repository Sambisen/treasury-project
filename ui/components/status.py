"""
Status Components - Nordic Light Design System
===============================================
Status indicators, strips, and connection status displays.
"""

import tkinter as tk
from tkinter import Canvas
from typing import Optional, Dict
import math
from PIL import Image, ImageDraw, ImageTk
from ..theme import COLORS, FONTS, SPACING, ICONS, ENV_BADGE_COLORS, BUTTON_CONFIG, SEGMENT_COLORS
from typing import Callable, List, Tuple


# =============================================================================
# ANALOG CLOCK (HEADER)
# =============================================================================

class AnalogClock(tk.Label):
    """Anti-aliased analog clock.

    Previous implementation used Tkinter Canvas which can look pixelated,
    especially at larger sizes. This version renders the clock using PIL at a
    higher internal resolution and downsamples with LANCZOS for smoother edges.
    """

    def __init__(
        self,
        parent,
        diameter: int = 44,
        bg: str = None,
        ring_color: str = "#22314B",
        tick_color: str = "#A8B3C7",
        hand_color: str = "#E7ECF3",
        second_hand_color: str = "#FF6B35",
        **kwargs,
    ):
        d = int(diameter)
        self._d = d if d > 10 else 10
        self._bg = bg if bg is not None else (parent.cget("bg") if "bg" in parent.keys() else "#0B1220")

        # Not a Tkinter option — pop before calling super().__init__.
        render_scale = int(kwargs.pop("render_scale", 3))

        super().__init__(
            parent,
            bg=self._bg,
            **kwargs,
        )

        self._ring_color = ring_color
        self._tick_color = tick_color
        self._hand_color = hand_color
        self._second_hand_color = second_hand_color

        # Render scale: render larger and downsample for anti-alias.
        # 3x is a good balance between quality and CPU.
        self._scale = render_scale
        if self._scale < 2:
            self._scale = 2

        self._last_hms: tuple[int, int, int] | None = None
        self._photo = None

        # Initial paint
        self.set_time(0, 0, 0)

    def _render_image(self, hour: int, minute: int, second: int) -> Image.Image:
        d = self._d
        s = self._scale
        D = d * s

        # Convert provided bg to RGB (PIL doesn't know theme; we just fill solid)
        img = Image.new("RGBA", (D, D), self._bg)
        draw = ImageDraw.Draw(img)

        cx = cy = D / 2.0
        r = (D / 2.0) - (2 * s)

        # Stroke widths scaled
        ring_w = max(1, int(1.2 * s))
        tick_w = max(1, int(1.0 * s))
        hour_w = max(2, int(2.6 * s))
        min_w = max(2, int(2.2 * s))
        sec_w = max(1, int(1.2 * s))
        hub_r = max(2, int(2.4 * s))

        # Outer ring
        bbox = (cx - r, cy - r, cx + r, cy + r)
        draw.ellipse(bbox, outline=self._ring_color, width=ring_w, fill=self._bg)

        # Ticks (12)
        for i in range(12):
            ang = (math.pi / 6) * i
            r1 = r - (6 * s)
            r2 = r - ((14 * s) if i % 3 == 0 else (12 * s))
            x1 = cx + r1 * math.sin(ang)
            y1 = cy - r1 * math.cos(ang)
            x2 = cx + r2 * math.sin(ang)
            y2 = cy - r2 * math.cos(ang)
            draw.line((x1, y1, x2, y2), fill=self._tick_color, width=tick_w)

        # Hands
        h = int(hour) % 12
        m = int(minute) % 60
        s2 = int(second) % 60

        hour_ang = (2 * math.pi) * ((h + (m / 60.0)) / 12.0)
        min_ang = (2 * math.pi) * ((m + (s2 / 60.0)) / 60.0)
        sec_ang = (2 * math.pi) * (s2 / 60.0)

        def end_point(angle: float, length: float) -> tuple[float, float]:
            x = cx + length * math.sin(angle)
            y = cy - length * math.cos(angle)
            return x, y

        hx, hy = end_point(hour_ang, r * 0.45)
        mx, my = end_point(min_ang, r * 0.65)
        sx, sy = end_point(sec_ang, r * 0.75)

        # Hour/min hands (rounded caps simulated by drawing circles at endpoints)
        draw.line((cx, cy, hx, hy), fill=self._hand_color, width=hour_w)
        draw.line((cx, cy, mx, my), fill=self._hand_color, width=min_w)
        draw.line((cx, cy, sx, sy), fill=self._second_hand_color, width=sec_w)

        # Hub
        draw.ellipse((cx - hub_r, cy - hub_r, cx + hub_r, cy + hub_r), fill=self._hand_color, outline=None)

        # Downsample to target size for anti-aliasing
        out = img.resize((d, d), resample=Image.Resampling.LANCZOS)
        return out

    def set_time(self, hour: int, minute: int, second: int) -> None:
        """Render the clock for the provided time."""
        h = int(hour)
        m = int(minute)
        s = int(second)

        # Avoid unnecessary re-render if called multiple times with same time
        if self._last_hms == (h, m, s):
            return
        self._last_hms = (h, m, s)

        img = self._render_image(h, m, s)
        # IMPORTANT: bind the PhotoImage to *this* widget's Tcl interpreter.
        # In our app we show a splash using a separate Tk root during startup.
        # If PhotoImage is created without an explicit master it can attach to the
        # wrong default root, leading to: _tkinter.TclError: image "pyimageX" doesn't exist
        self._photo = ImageTk.PhotoImage(img, master=self)
        self.configure(image=self._photo)

        # Ensure widget is sized to the image (important for geometry managers)
        self.configure(width=self._d, height=self._d)


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
    Nordic Light theme - light background with colored accents.

    Features:
    - Pill-shaped container with subtle tinted background
    - Colored dot with soft glow effect
    - Premium/static styling (no pulse) to feel more "enterprise" than "alert"

    Usage:
        badge = PremiumEnvBadge(parent, environment="PROD")
        badge.pack()
    """

    def __init__(
        self,
        parent,
        environment: str = "DEV",
        compact: bool = False,
        **kwargs
    ):
        # Determine colors based on environment
        self._is_prod = environment.upper() == "PROD"
        self._compact = compact

        # Text strategy:
        # - Keep PROD as a premium "sigill" (PRODUCTION) even in compact header.
        # - Keep DEV short in compact mode to avoid stealing header space.
        if compact:
            self._env_text = "PRODUCTION" if self._is_prod else "DEV"
        else:
            self._env_text = "PRODUCTION" if self._is_prod else "DEVELOPMENT"

        if self._is_prod:
            self._dot_color = ENV_BADGE_COLORS.PROD_DOT
            self._glow_color = ENV_BADGE_COLORS.PROD_GLOW
            self._text_color = ENV_BADGE_COLORS.PROD_TEXT
            self._bg_tint = ENV_BADGE_COLORS.PROD_BG_TINT
        else:
            self._dot_color = ENV_BADGE_COLORS.DEV_DOT
            self._glow_color = ENV_BADGE_COLORS.DEV_GLOW
            self._text_color = ENV_BADGE_COLORS.DEV_TEXT
            self._bg_tint = ENV_BADGE_COLORS.DEV_BG_TINT

        # Initialize frame with tinted background
        super().__init__(
            parent,
            bg=self._bg_tint,
            highlightbackground=ENV_BADGE_COLORS.BADGE_BORDER,
            highlightthickness=1,
            **kwargs
        )

        # Sizing based on compact mode
        if compact:
            inner_padx, inner_pady = 8, 4
            dot_size, glow_size = 7, 16
            dot_padx = 6
        else:
            inner_padx, inner_pady = 14, 8
            dot_size, glow_size = 10, 22
            dot_padx = 10

        # Inner padding frame
        self._inner = tk.Frame(self, bg=self._bg_tint)
        self._inner.pack(padx=inner_padx, pady=inner_pady)

        # Canvas for the glowing dot
        self._dot_size = dot_size
        self._glow_size = glow_size
        canvas_size = self._glow_size + 4

        self._canvas = Canvas(
            self._inner,
            width=canvas_size,
            height=canvas_size,
            bg=self._bg_tint,
            highlightthickness=0
        )
        self._canvas.pack(side="left", padx=(0, dot_padx))

        # Draw glow layers (multiple circles with decreasing opacity)
        self._glow_items = []
        center = canvas_size // 2

        # Create glow layers (will be animated)
        for i in range(3):
            radius = self._glow_size // 2 - (i * 2)
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
        font_size = 9 if compact else 11
        self._label = tk.Label(
            self._inner,
            text=self._env_text,
            fg=self._text_color,
            bg=self._bg_tint,
            font=(BUTTON_CONFIG.FONT_FAMILY, font_size, "bold")
        )
        self._label.pack(side="left")

        # Animation state
        self._animation_phase = 0.0
        self._animation_id = None

        # Premium feel: keep the badge static in both PROD/DEV.
        # (Pulse often reads like "alert/live", which is not the desired premium feel.)
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
        bg_rgb = self._hex_to_rgb(self._bg_tint)

        blended = tuple(
            int(fg * opacity + bg * (1 - opacity))
            for fg, bg in zip(fg_rgb, bg_rgb)
        )
        return self._rgb_to_hex(*blended)

    def _draw_static_glow(self):
        """Draw a static glow effect (for DEV)."""
        # Subtle glow layers.
        # Keep it intentionally understated so it feels like a high-end status label.
        opacities = [0.10, 0.18, 0.26]
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

        # Calculate current opacity multiplier
        pulse = (math.sin(self._animation_phase) + 1) / 2  # 0 to 1
        min_opacity = ENV_BADGE_COLORS.GLOW_OPACITY_MIN
        max_opacity = ENV_BADGE_COLORS.GLOW_OPACITY_MAX
        opacity_mult = min_opacity + (max_opacity - min_opacity) * pulse

        # Update glow layers
        base_opacities = [0.2, 0.35, 0.5]
        for i, glow_id in enumerate(self._glow_items):
            opacity = base_opacities[i] * opacity_mult
            blended = self._blend_with_bg(self._glow_color, opacity)
            self._canvas.itemconfig(glow_id, fill=blended)

        # Schedule next frame
        self._animation_id = self.after(50, self._animate_pulse)

    def destroy(self):
        """Clean up animation when widget is destroyed."""
        if self._animation_id:
            self.after_cancel(self._animation_id)
        super().destroy()

    def _update_colors(self):
        """Update all widget colors based on current environment."""
        if self._is_prod:
            self._dot_color = ENV_BADGE_COLORS.PROD_DOT
            self._glow_color = ENV_BADGE_COLORS.PROD_GLOW
            self._text_color = ENV_BADGE_COLORS.PROD_TEXT
            self._bg_tint = ENV_BADGE_COLORS.PROD_BG_TINT
        else:
            self._dot_color = ENV_BADGE_COLORS.DEV_DOT
            self._glow_color = ENV_BADGE_COLORS.DEV_GLOW
            self._text_color = ENV_BADGE_COLORS.DEV_TEXT
            self._bg_tint = ENV_BADGE_COLORS.DEV_BG_TINT

        # Update backgrounds
        self.configure(bg=self._bg_tint)
        self._inner.configure(bg=self._bg_tint)
        self._canvas.configure(bg=self._bg_tint)
        self._label.configure(bg=self._bg_tint)

        # Update dot and text
        self._canvas.itemconfig(self._dot_item, fill=self._dot_color)
        self._label.config(text=self._env_text, fg=self._text_color)

    def set_environment(self, environment: str):
        """Update the environment display."""
        self._is_prod = environment.upper() == "PROD"
        if self._compact:
            self._env_text = "PRODUCTION" if self._is_prod else "DEV"
        else:
            self._env_text = "PRODUCTION" if self._is_prod else "DEVELOPMENT"

        # Update all colors
        self._update_colors()

        # Always static glow (premium)
        if self._animation_id:
            try:
                self.after_cancel(self._animation_id)
            except Exception:
                pass
            self._animation_id = None
        self._draw_static_glow()


# =============================================================================
# SEGMENTED CONTROL
# =============================================================================

class SegmentedControl(tk.Frame):
    """
    Premium segmented control with Nordic Light styling.

    A pill-shaped toggle between options, similar to iOS segmented control.

    Usage:
        control = SegmentedControl(
            parent,
            options=[("10:30 CET", "10:30"), ("10:00 CET", "10:00")],
            default="10:30",
            command=on_change
        )
    """

    def __init__(
        self,
        parent,
        options: List[Tuple[str, str]],  # List of (label, value) tuples
        default: str = None,
        command: Optional[Callable[[str], None]] = None,
        compact: bool = False,
        **kwargs
    ):
        super().__init__(
            parent,
            bg=SEGMENT_COLORS.BG,
            highlightbackground=SEGMENT_COLORS.BORDER,
            highlightthickness=1,
            **kwargs
        )

        self._option_items = options
        self._command = command
        self._current_value = default or (options[0][1] if options else None)
        self._segments: Dict[str, tk.Label] = {}
        self._compact = compact

        # Sizing based on compact mode
        if compact:
            inner_pad = 2
            seg_padx, seg_pady = 8, 3
            font_size = 9
        else:
            inner_pad = 3
            seg_padx, seg_pady = 14, 6
            font_size = 11

        self._font_size = font_size

        # Inner container for segments
        inner = tk.Frame(self, bg=SEGMENT_COLORS.BG)
        inner.pack(padx=inner_pad, pady=inner_pad)

        # Create segments
        for i, (label, value) in enumerate(options):
            is_active = value == self._current_value

            segment = tk.Label(
                inner,
                text=label,
                fg=SEGMENT_COLORS.TEXT_ACTIVE if is_active else SEGMENT_COLORS.TEXT,
                bg=SEGMENT_COLORS.SEGMENT_ACTIVE_BG if is_active else SEGMENT_COLORS.SEGMENT_BG,
                font=(BUTTON_CONFIG.FONT_FAMILY, font_size, "bold" if is_active else "normal"),
                padx=seg_padx,
                pady=seg_pady,
                cursor="hand2"
            )
            segment.pack(side="left", padx=(0 if i == 0 else 1, 0))

            # Store reference
            self._segments[value] = segment

            # Bind events
            segment.bind("<Button-1>", lambda e, v=value: self._on_click(v))
            segment.bind("<Enter>", lambda e, v=value: self._on_enter(v))
            segment.bind("<Leave>", lambda e, v=value: self._on_leave(v))

    def _on_click(self, value: str):
        """Handle segment click."""
        if value == self._current_value:
            return

        # Update current value
        old_value = self._current_value
        self._current_value = value

        # Update visual state
        self._update_segment(old_value, active=False)
        self._update_segment(value, active=True)

        # Call command
        if self._command:
            self._command(value)

    def _on_enter(self, value: str):
        """Handle mouse enter."""
        if value != self._current_value:
            segment = self._segments.get(value)
            if segment:
                segment.configure(
                    bg=SEGMENT_COLORS.SEGMENT_HOVER_BG,
                    fg=SEGMENT_COLORS.TEXT_HOVER
                )

    def _on_leave(self, value: str):
        """Handle mouse leave."""
        if value != self._current_value:
            segment = self._segments.get(value)
            if segment:
                segment.configure(
                    bg=SEGMENT_COLORS.SEGMENT_BG,
                    fg=SEGMENT_COLORS.TEXT
                )

    def _update_segment(self, value: str, active: bool):
        """Update segment visual state."""
        segment = self._segments.get(value)
        if not segment:
            return

        if active:
            segment.configure(
                bg=SEGMENT_COLORS.SEGMENT_ACTIVE_BG,
                fg=SEGMENT_COLORS.TEXT_ACTIVE,
                font=(BUTTON_CONFIG.FONT_FAMILY, self._font_size, "bold")
            )
        else:
            segment.configure(
                bg=SEGMENT_COLORS.SEGMENT_BG,
                fg=SEGMENT_COLORS.TEXT,
                font=(BUTTON_CONFIG.FONT_FAMILY, self._font_size, "normal")
            )

    def get(self) -> str:
        """Get current selected value."""
        return self._current_value

    def set(self, value: str):
        """Set selected value programmatically."""
        if value in self._segments and value != self._current_value:
            old_value = self._current_value
            self._current_value = value
            self._update_segment(old_value, active=False)
            self._update_segment(value, active=True)

    def update_options(self, options: List[Tuple[str, str]], default: str = None):
        """Update the available options dynamically.

        Args:
            options: List of (label, value) tuples
            default: Default value to select
        """
        # Destroy existing segments
        for widget in self.winfo_children():
            widget.destroy()
        self._segments.clear()

        # Update stored options
        self._option_items = options
        self._current_value = default or (options[0][1] if options else None)

        # Sizing based on compact mode
        if self._compact:
            inner_pad = 2
            seg_padx, seg_pady = 8, 3
        else:
            inner_pad = 3
            seg_padx, seg_pady = 14, 6

        # Recreate inner container
        inner = tk.Frame(self, bg=SEGMENT_COLORS.BG)
        inner.pack(padx=inner_pad, pady=inner_pad)

        # Recreate segments
        for i, (label, value) in enumerate(options):
            is_active = value == self._current_value

            segment = tk.Label(
                inner,
                text=label,
                fg=SEGMENT_COLORS.TEXT_ACTIVE if is_active else SEGMENT_COLORS.TEXT,
                bg=SEGMENT_COLORS.SEGMENT_ACTIVE_BG if is_active else SEGMENT_COLORS.SEGMENT_BG,
                font=(BUTTON_CONFIG.FONT_FAMILY, self._font_size, "bold" if is_active else "normal"),
                padx=seg_padx,
                pady=seg_pady,
                cursor="hand2"
            )
            segment.pack(side="left", padx=(0 if i == 0 else 1, 0))

            self._segments[value] = segment

            segment.bind("<Button-1>", lambda e, v=value: self._on_click(v))
            segment.bind("<Enter>", lambda e, v=value: self._on_enter(v))
            segment.bind("<Leave>", lambda e, v=value: self._on_leave(v))
