"""
Premium Environment Badge Demo
==============================
Showcase of the glowing environment badge with pulse animation.
Nordic Light theme version.
Run: python -m ui.env_badge_demo
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import tkinter as tk
from ui.theme import ENV_BADGE_COLORS, BUTTON_CONFIG, COLORS
from ui.components.status import PremiumEnvBadge


class EnvBadgeDemo(tk.Tk):
    """Demo window showcasing premium environment badges."""

    def __init__(self):
        super().__init__()
        self.title("Premium Environment Badge Demo")
        self.geometry("500x350")
        self.configure(bg=COLORS.BG)  # Nordic Light background

        # Title
        title = tk.Label(
            self,
            text="Premium Environment Badges",
            fg=COLORS.TEXT,
            bg=COLORS.BG,
            font=(BUTTON_CONFIG.FONT_FAMILY, 18, "bold")
        )
        title.pack(pady=(30, 10))

        subtitle = tk.Label(
            self,
            text="Nordic Light theme - PROD pulses, DEV is static",
            fg=COLORS.TEXT_MUTED,
            bg=COLORS.BG,
            font=(BUTTON_CONFIG.FONT_FAMILY, 12)
        )
        subtitle.pack(pady=(0, 30))

        # Container for badges
        badge_container = tk.Frame(self, bg=COLORS.BG)
        badge_container.pack(pady=20)

        # PROD badge (with pulse)
        prod_label = tk.Label(
            badge_container,
            text="PROD (pulsing glow):",
            fg=COLORS.TEXT_SECONDARY,
            bg=COLORS.BG,
            font=(BUTTON_CONFIG.FONT_FAMILY, 11)
        )
        prod_label.grid(row=0, column=0, padx=(0, 20), pady=10, sticky="e")

        prod_badge = PremiumEnvBadge(badge_container, environment="PROD")
        prod_badge.grid(row=0, column=1, pady=10, sticky="w")

        # DEV badge (static)
        dev_label = tk.Label(
            badge_container,
            text="DEV (static glow):",
            fg=COLORS.TEXT_SECONDARY,
            bg=COLORS.BG,
            font=(BUTTON_CONFIG.FONT_FAMILY, 11)
        )
        dev_label.grid(row=1, column=0, padx=(0, 20), pady=10, sticky="e")

        dev_badge = PremiumEnvBadge(badge_container, environment="DEV")
        dev_badge.grid(row=1, column=1, pady=10, sticky="w")

        # Interactive toggle demo
        toggle_label = tk.Label(
            self,
            text="Click badge or button to toggle:",
            fg=COLORS.TEXT_SECONDARY,
            bg=COLORS.BG,
            font=(BUTTON_CONFIG.FONT_FAMILY, 11)
        )
        toggle_label.pack(pady=(30, 10))

        toggle_frame = tk.Frame(self, bg=COLORS.BG)
        toggle_frame.pack()

        self._current_env = "PROD"
        self._toggle_badge = PremiumEnvBadge(toggle_frame, environment="PROD")
        self._toggle_badge.pack(side="left", padx=(0, 15))

        # Make badge clickable
        self._toggle_badge.bind("<Button-1>", lambda e: self._toggle_env())
        self._toggle_badge.configure(cursor="hand2")
        for widget in self._toggle_badge.winfo_children():
            widget.bind("<Button-1>", lambda e: self._toggle_env())
            try:
                widget.configure(cursor="hand2")
            except:
                pass

        toggle_btn = tk.Button(
            toggle_frame,
            text="Toggle",
            command=self._toggle_env,
            font=(BUTTON_CONFIG.FONT_FAMILY, 11),
            bg=COLORS.ACCENT,
            fg="white",
            relief="flat",
            padx=15,
            pady=8,
            cursor="hand2"
        )
        toggle_btn.pack(side="left")

    def _toggle_env(self):
        """Toggle between PROD and DEV."""
        self._current_env = "DEV" if self._current_env == "PROD" else "PROD"
        self._toggle_badge.set_environment(self._current_env)


if __name__ == "__main__":
    app = EnvBadgeDemo()
    app.mainloop()
