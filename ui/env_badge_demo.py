"""
Premium Environment Badge Demo
==============================
Showcase of the glowing environment badge with pulse animation.
Run: python -m ui.env_badge_demo
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import tkinter as tk
from ui.theme import ENV_BADGE_COLORS, BUTTON_CONFIG
from ui.components.status import PremiumEnvBadge


class EnvBadgeDemo(tk.Tk):
    """Demo window showcasing premium environment badges."""

    def __init__(self):
        super().__init__()
        self.title("Premium Environment Badge Demo")
        self.geometry("500x300")
        self.configure(bg=ENV_BADGE_COLORS.BADGE_BG)

        # Title
        title = tk.Label(
            self,
            text="Premium Environment Badges",
            fg=ENV_BADGE_COLORS.PROD_TEXT,
            bg=ENV_BADGE_COLORS.BADGE_BG,
            font=(BUTTON_CONFIG.FONT_FAMILY, 18, "bold")
        )
        title.pack(pady=(30, 10))

        subtitle = tk.Label(
            self,
            text="PROD has pulse animation, DEV is static",
            fg="#A9B4C2",
            bg=ENV_BADGE_COLORS.BADGE_BG,
            font=(BUTTON_CONFIG.FONT_FAMILY, 12)
        )
        subtitle.pack(pady=(0, 30))

        # Container for badges
        badge_container = tk.Frame(self, bg=ENV_BADGE_COLORS.BADGE_BG)
        badge_container.pack(pady=20)

        # PROD badge (with pulse)
        prod_label = tk.Label(
            badge_container,
            text="PROD (pulsing glow):",
            fg="#A9B4C2",
            bg=ENV_BADGE_COLORS.BADGE_BG,
            font=(BUTTON_CONFIG.FONT_FAMILY, 11)
        )
        prod_label.grid(row=0, column=0, padx=(0, 20), pady=10, sticky="e")

        prod_badge = PremiumEnvBadge(badge_container, environment="PROD")
        prod_badge.grid(row=0, column=1, pady=10, sticky="w")

        # DEV badge (static)
        dev_label = tk.Label(
            badge_container,
            text="DEV (static glow):",
            fg="#A9B4C2",
            bg=ENV_BADGE_COLORS.BADGE_BG,
            font=(BUTTON_CONFIG.FONT_FAMILY, 11)
        )
        dev_label.grid(row=1, column=0, padx=(0, 20), pady=10, sticky="e")

        dev_badge = PremiumEnvBadge(badge_container, environment="DEV")
        dev_badge.grid(row=1, column=1, pady=10, sticky="w")

        # Toggle button
        self._current_env = "PROD"
        self._toggle_badge = PremiumEnvBadge(self, environment="PROD")
        self._toggle_badge.pack(pady=30)

        toggle_btn = tk.Button(
            self,
            text="Toggle Environment",
            command=self._toggle_env,
            font=(BUTTON_CONFIG.FONT_FAMILY, 11),
            bg="#2A364A",
            fg="white",
            relief="flat",
            padx=15,
            pady=8
        )
        toggle_btn.pack()

    def _toggle_env(self):
        """Toggle between PROD and DEV."""
        self._current_env = "DEV" if self._current_env == "PROD" else "PROD"
        self._toggle_badge.set_environment(self._current_env)


if __name__ == "__main__":
    app = EnvBadgeDemo()
    app.mainloop()
