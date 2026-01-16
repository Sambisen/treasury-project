"""
Premium CTA Button for customtkinter (Nordic Light / bank-grade).

Features:
- Subtle vertical gradient, top highlight, soft shadow
- Hover / Pressed / Disabled states
- Loading state with indeterminate progress bar
- Confirmed flash state
- Keyboard focus ring (basic)

Requires: customtkinter
pip install customtkinter
"""

from __future__ import annotations

import customtkinter as ctk
from dataclasses import dataclass
from typing import Callable, Optional


# -----------------------------
# Color tokens (Nordic Light)
# -----------------------------
@dataclass(frozen=True)
class NordicTokens:
    bg_canvas: str = "#F7F7F6"
    surface: str = "#FFFFFF"
    border: str = "#E6E6E6"
    text_primary: str = "#1F2937"
    text_secondary: str = "#6B7280"

    # Swedbank-ish orange accent (tweak to your exact brand)
    accent: str = "#FF6A00"
    accent_hover: str = "#FF7A1A"
    accent_pressed: str = "#E85E00"

    success: str = "#1E8E3E"
    error: str = "#D93025"
    warn: str = "#B45309"

    shadow: str = "#000000"


TOKENS = NordicTokens()


# -----------------------------
# Helpers
# -----------------------------
def _hex_to_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    return "#{:02X}{:02X}{:02X}".format(*rgb)


def _lerp(a: int, b: int, t: float) -> int:
    return int(a + (b - a) * t)


def _blend(c1: str, c2: str, t: float) -> str:
    r1, g1, b1 = _hex_to_rgb(c1)
    r2, g2, b2 = _hex_to_rgb(c2)
    return _rgb_to_hex((_lerp(r1, r2, t), _lerp(g1, g2, t), _lerp(b1, b2, t)))


def _lighten(c: str, amount: float) -> str:
    # amount: 0..1 toward white
    return _blend(c, "#FFFFFF", amount)


def _darken(c: str, amount: float) -> str:
    # amount: 0..1 toward black
    return _blend(c, "#000000", amount)


# -----------------------------
# Premium CTA Button
# -----------------------------
class PremiumCTAButton(ctk.CTkFrame):
    """
    A premium-looking CTA button implemented as a frame + canvas drawing.
    Supports: hover/pressed/disabled/loading/confirmed.
    """

    def __init__(
        self,
        master,
        text: str = "Confirm rates",
        command: Optional[Callable[[], None]] = None,
        width: int = 190,
        height: int = 46,
        radius: int = 14,
        fg_top: str = None,
        fg_bottom: str = None,
        border_color: str = None,
        text_color: str = "#FFFFFF",
        font: tuple = ("Segoe UI", 13, "bold"),
        shadow: bool = True,
        **kwargs,
    ):
        super().__init__(master, fg_color="transparent", **kwargs)

        self._w = width
        self._h = height
        self._r = radius
        self._text = text
        self._command = command

        self._enabled = True
        self._hover = False
        self._pressed = False
        self._loading = False
        self._confirmed = False
        self._focus = False

        self._fg_top = fg_top or _lighten(TOKENS.accent, 0.06)
        self._fg_bottom = fg_bottom or _darken(TOKENS.accent, 0.04)
        self._border_color = border_color or _darken(TOKENS.accent, 0.12)
        self._text_color = text_color
        self._font = font
        self._shadow_on = shadow

        # Shadow layer (a separate canvas behind main)
        self._shadow_canvas = ctk.CTkCanvas(self, width=self._w, height=self._h, highlightthickness=0, bd=0)
        self._shadow_canvas.grid(row=0, column=0, sticky="nsew")

        # Main canvas layer
        self._canvas = ctk.CTkCanvas(self, width=self._w, height=self._h, highlightthickness=0, bd=0)
        self._canvas.grid(row=0, column=0, sticky="nsew")

        # Content: label + optional progress bar
        self._label = ctk.CTkLabel(
            self,
            text=self._text,
            text_color=self._text_color,
            font=self._font,
            fg_color="transparent",
        )
        self._label.place(relx=0.5, rely=0.5, anchor="center")

        self._progress = ctk.CTkProgressBar(
            self,
            mode="indeterminate",
            width=int(self._w * 0.55),
            height=8,
            fg_color=_lighten("#000000", 0.92),
            progress_color=_lighten("#FFFFFF", 0.1),
            corner_radius=999,
        )
        self._progress.place_forget()

        # Bindings for interaction
        for widget in (self, self._canvas, self._label):
            widget.bind("<Enter>", self._on_enter)
            widget.bind("<Leave>", self._on_leave)
            widget.bind("<ButtonPress-1>", self._on_press)
            widget.bind("<ButtonRelease-1>", self._on_release)

        # Keyboard focus (basic)
        self.bind("<FocusIn>", self._on_focus_in)
        self.bind("<FocusOut>", self._on_focus_out)
        self.bind("<space>", self._on_key_activate)
        self.bind("<Return>", self._on_key_activate)

        self.configure(width=self._w, height=self._h)
        self.grid_propagate(False)

        self._redraw()

    # -------- Public API --------
    def set_enabled(self, enabled: bool) -> None:
        self._enabled = bool(enabled)
        if not self._enabled:
            self._hover = False
            self._pressed = False
        self._redraw()

    def set_loading(self, loading: bool, loading_text: str = "Confirming…") -> None:
        self._loading = bool(loading)
        if self._loading:
            self._label.configure(text=loading_text)
            self._progress.place(relx=0.5, rely=0.78, anchor="center")
            self._progress.start()
        else:
            self._progress.stop()
            self._progress.place_forget()
            self._label.configure(text=self._text)
        self._redraw()

    def flash_confirmed(self, confirmed_text: str = "Confirmed") -> None:
        # brief success flash
        self._confirmed = True
        old_text = self._label.cget("text")
        self._label.configure(text=confirmed_text)
        self._redraw()

        def _restore():
            self._confirmed = False
            self._label.configure(text=self._text if not self._loading else old_text)
            self._redraw()

        self.after(1200, _restore)

    # -------- Event handlers --------
    def _on_enter(self, _evt=None) -> None:
        if not self._enabled or self._loading:
            return
        self._hover = True
        self._redraw()

    def _on_leave(self, _evt=None) -> None:
        self._hover = False
        self._pressed = False
        self._redraw()

    def _on_press(self, _evt=None) -> None:
        if not self._enabled or self._loading:
            return
        self._pressed = True
        self._redraw()

    def _on_release(self, _evt=None) -> None:
        if not self._enabled or self._loading:
            return
        was_pressed = self._pressed
        self._pressed = False
        self._redraw()
        if was_pressed and self._hover:
            self._activate()

    def _on_focus_in(self, _evt=None) -> None:
        self._focus = True
        self._redraw()

    def _on_focus_out(self, _evt=None) -> None:
        self._focus = False
        self._redraw()

    def _on_key_activate(self, _evt=None) -> None:
        if not self._enabled or self._loading:
            return
        self._activate()

    def _activate(self) -> None:
        if callable(self._command):
            self._command()

    # -------- Drawing --------
    def _redraw(self) -> None:
        self._shadow_canvas.delete("all")
        self._canvas.delete("all")

        # Determine state colors
        if not self._enabled:
            top = _lighten("#9CA3AF", 0.20)
            bottom = _darken("#9CA3AF", 0.08)
            border = _darken("#9CA3AF", 0.15)
            text_color = _lighten(TOKENS.text_primary, 0.45)
            shadow_alpha = 0.00
        elif self._confirmed:
            top = _lighten(TOKENS.success, 0.08)
            bottom = _darken(TOKENS.success, 0.05)
            border = _darken(TOKENS.success, 0.18)
            text_color = "#FFFFFF"
            shadow_alpha = 0.14
        elif self._pressed:
            top = _lighten(TOKENS.accent_pressed, 0.04)
            bottom = _darken(TOKENS.accent_pressed, 0.06)
            border = _darken(TOKENS.accent_pressed, 0.20)
            text_color = "#FFFFFF"
            shadow_alpha = 0.10
        elif self._hover:
            top = _lighten(TOKENS.accent_hover, 0.06)
            bottom = _darken(TOKENS.accent_hover, 0.05)
            border = _darken(TOKENS.accent_hover, 0.18)
            text_color = "#FFFFFF"
            shadow_alpha = 0.16
        else:
            top = self._fg_top
            bottom = self._fg_bottom
            border = self._border_color
            text_color = self._text_color
            shadow_alpha = 0.14

        # Loading dims interaction slightly (but keeps premium)
        if self._loading and self._enabled:
            top = _blend(top, "#FFFFFF", 0.06)
            bottom = _blend(bottom, "#FFFFFF", 0.06)

        self._label.configure(text_color=text_color)

        # Shadow (soft). Canvas doesn't support alpha per item reliably; simulate with lighter shadow.
        if self._shadow_on and shadow_alpha > 0:
            self._draw_rounded_rect(
                self._shadow_canvas,
                x=2,
                y=3 if not self._pressed else 4,
                w=self._w - 2,
                h=self._h - 2,
                r=self._r,
                fill=_blend(TOKENS.shadow, TOKENS.bg_canvas, 0.93),
                outline="",
                width=0,
            )

        # Main button (gradient)
        y_offset = 0 if not self._pressed else 1  # pressed feel
        self._draw_vertical_gradient_roundrect(
            self._canvas,
            x=0,
            y=y_offset,
            w=self._w,
            h=self._h - y_offset,
            r=self._r,
            top=top,
            bottom=bottom,
            steps=18,
        )

        # Border
        self._draw_rounded_rect(
            self._canvas,
            x=0,
            y=y_offset,
            w=self._w - 1,
            h=self._h - 1 - y_offset,
            r=self._r,
            fill="",
            outline=border,
            width=1,
        )

        # Top highlight line (gives “expensive” depth)
        self._draw_rounded_rect(
            self._canvas,
            x=1,
            y=1 + y_offset,
            w=self._w - 3,
            h=int((self._h - y_offset) * 0.42),
            r=max(8, self._r - 3),
            fill="",
            outline=_blend("#FFFFFF", top, 0.35),
            width=1,
        )

        # Focus ring (subtle)
        if self._focus and self._enabled and not self._loading:
            self._draw_rounded_rect(
                self._canvas,
                x=-1,
                y=-1 + y_offset,
                w=self._w + 1,
                h=self._h + 1 - y_offset,
                r=self._r + 2,
                fill="",
                outline=_blend(TOKENS.accent, "#FFFFFF", 0.45),
                width=2,
            )

    def _draw_vertical_gradient_roundrect(
        self,
        canvas: ctk.CTkCanvas,
        x: int,
        y: int,
        w: int,
        h: int,
        r: int,
        top: str,
        bottom: str,
        steps: int = 16,
    ) -> None:
        # draw as stacked horizontal strips clipped by rounded shape impression
        # (good enough for premium feel in Tk).
        for i in range(steps):
            t = i / max(1, steps - 1)
            color = _blend(top, bottom, t)
            y0 = y + int((h * i) / steps)
            y1 = y + int((h * (i + 1)) / steps)
            # expand a bit to avoid gaps
            self._draw_rounded_rect(canvas, x, y0, w, (y1 - y0) + 1, r, fill=color, outline=color, width=0)

        # Re-draw borderless rounded rect to unify edges
        self._draw_rounded_rect(canvas, x, y, w, h, r, fill="", outline="", width=0)

    def _draw_rounded_rect(
        self,
        canvas: ctk.CTkCanvas,
        x: int,
        y: int,
        w: int,
        h: int,
        r: int,
        fill: str,
        outline: str,
        width: int = 1,
    ) -> None:
        # rounded rectangle via polygons + arcs
        # Tk canvas doesn't have native rounded rect, so use smooth polygon.
        r = max(0, min(r, int(min(w, h) / 2)))
        x1, y1 = x, y
        x2, y2 = x + w, y + h

        points = [
            (x1 + r, y1),
            (x2 - r, y1),
            (x2, y1),
            (x2, y1 + r),
            (x2, y2 - r),
            (x2, y2),
            (x2 - r, y2),
            (x1 + r, y2),
            (x1, y2),
            (x1, y2 - r),
            (x1, y1 + r),
            (x1, y1),
        ]

        flat = [p for xy in points for p in xy]
        canvas.create_polygon(
            flat,
            smooth=True,
            splinesteps=36,
            fill=fill,
            outline=outline,
            width=width,
        )


# -----------------------------
# Demo usage: action bar + button
# -----------------------------
class DemoApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Nibor Calculation Terminal — Premium CTA Demo")
        self.geometry("980x560")
        self.configure(fg_color=TOKENS.bg_canvas)

        # Top title area (mock)
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=24, pady=(18, 10))

        title = ctk.CTkLabel(top, text="NIBOR RATES", font=("Segoe UI", 20, "bold"), text_color=TOKENS.text_primary)
        title.pack(side="left")

        # Main surface
        surface = ctk.CTkFrame(self, fg_color=TOKENS.surface, corner_radius=16, border_color=TOKENS.border, border_width=1)
        surface.pack(fill="both", expand=True, padx=24, pady=(0, 18))

        # Placeholder content
        placeholder = ctk.CTkLabel(
            surface,
            text="(Rates table here)\n\nClick Confirm rates to see loading + confirmed states.",
            font=("Segoe UI", 14),
            text_color=TOKENS.text_secondary,
            justify="center",
        )
        placeholder.pack(expand=True)

        # Sticky action bar
        action_bar = ctk.CTkFrame(
            surface,
            fg_color=_blend(TOKENS.surface, "#000000", 0.02),
            corner_radius=14,
            border_color=TOKENS.border,
            border_width=1,
        )
        action_bar.pack(fill="x", padx=16, pady=16)

        left = ctk.CTkFrame(action_bar, fg_color="transparent")
        left.pack(side="left", padx=14, pady=12)

        self.status_lbl = ctk.CTkLabel(
            left, text="Status: NOT READY", font=("Segoe UI", 13, "bold"), text_color=TOKENS.text_primary
        )
        self.status_lbl.pack(anchor="w")

        self.meta_lbl = ctk.CTkLabel(
            left, text="Last updated: —    RunID: —", font=("Segoe UI", 12), text_color=TOKENS.text_secondary
        )
        self.meta_lbl.pack(anchor="w")

        right = ctk.CTkFrame(action_bar, fg_color="transparent")
        right.pack(side="right", padx=14, pady=12)

        secondary = ctk.CTkButton(
            right,
            text="Re-run checks",
            height=40,
            corner_radius=12,
            fg_color=_blend("#000000", "#FFFFFF", 0.93),
            hover_color=_blend("#000000", "#FFFFFF", 0.90),
            text_color=TOKENS.text_primary,
        )
        secondary.pack(side="left", padx=(0, 10))

        self.confirm_btn = PremiumCTAButton(
            right,
            text="Confirm rates",
            width=200,
            height=46,
            radius=14,
            command=self.on_confirm,
        )
        self.confirm_btn.pack(side="left")

        # For demo: enable focus by clicking
        self.confirm_btn.configure(takefocus=1)

    def on_confirm(self):
        # Simulate a real confirm flow: loading -> pass -> confirmed
        self.confirm_btn.set_loading(True, "Confirming…")
        self.status_lbl.configure(text="Status: RUNNING CHECKS")

        def done_ok():
            self.confirm_btn.set_loading(False)
            self.confirm_btn.flash_confirmed("Confirmed")
            self.status_lbl.configure(text="Status: READY TO UPLOAD")
            self.meta_lbl.configure(text="Last updated: 17:02:11    RunID: 2026-01-15-170211")

        self.after(1400, done_ok)


if __name__ == "__main__":
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")  # not critical; we override colors anyway
    app = DemoApp()
    app.mainloop()
