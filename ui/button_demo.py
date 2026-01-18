"""
Premium Button Demo
===================
Showcase of the dark theme CTkButton system.
Run: python -m ui.button_demo
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from ctk_compat import ctk
from ui.theme import BUTTON_COLORS, BUTTON_CONFIG
from ui.components.buttons import (
    make_ctk_button,
    set_button_disabled,
    CTkPrimaryButton,
    CTkSecondaryButton,
    CTkDangerButton,
    CTkGhostButton,
)

# Configure appearance
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")


class ButtonDemo(ctk.CTk):
    """Demo window showcasing premium button styles."""

    def __init__(self):
        super().__init__()
        self.title("Premium Buttons Demo")
        self.geometry("900x500")
        self.configure(fg_color=BUTTON_COLORS.BG)

        # Main card container
        card = ctk.CTkFrame(
            self,
            fg_color=BUTTON_COLORS.CARD,
            corner_radius=18,
            border_width=1,
            border_color=BUTTON_COLORS.CARD_BORDER
        )
        card.pack(padx=24, pady=24, fill="both", expand=True)

        # Title
        title = ctk.CTkLabel(
            card,
            text="Premium Buttons",
            font=(BUTTON_CONFIG.FONT_FAMILY, 20, "bold"),
            text_color=BUTTON_COLORS.TEXT
        )
        title.pack(anchor="w", padx=20, pady=(20, 6))

        # Subtitle
        subtitle = ctk.CTkLabel(
            card,
            text="Consistent sizing, subtle hover/pressed states, and clear hierarchy.",
            font=(BUTTON_CONFIG.FONT_FAMILY, 13),
            text_color=BUTTON_COLORS.TEXT_MUTED
        )
        subtitle.pack(anchor="w", padx=20, pady=(0, 16))

        # --- Row 1: Using factory function ---
        section1 = ctk.CTkLabel(
            card,
            text="Using make_ctk_button():",
            font=(BUTTON_CONFIG.FONT_FAMILY, 12),
            text_color=BUTTON_COLORS.TEXT_MUTED
        )
        section1.pack(anchor="w", padx=20, pady=(8, 4))

        row1 = ctk.CTkFrame(card, fg_color="transparent")
        row1.pack(anchor="w", padx=20, pady=8)

        btn_primary = make_ctk_button(
            row1, "Confirm rates",
            command=lambda: print("Confirm clicked"),
            variant="primary",
            width=200,
            icon="✓"
        )
        btn_secondary = make_ctk_button(
            row1, "Re-run checks",
            command=lambda: print("Re-run clicked"),
            variant="secondary",
            width=200,
            icon="↻"
        )
        btn_danger = make_ctk_button(
            row1, "Reject",
            command=lambda: print("Reject clicked"),
            variant="danger",
            width=160,
            icon="✖"
        )
        btn_ghost = make_ctk_button(
            row1, "Details",
            command=lambda: print("Details clicked"),
            variant="ghost",
            width=140
        )

        btn_primary.grid(row=0, column=0, padx=(0, 12), pady=8)
        btn_secondary.grid(row=0, column=1, padx=(0, 12), pady=8)
        btn_danger.grid(row=0, column=2, padx=(0, 12), pady=8)
        btn_ghost.grid(row=0, column=3, padx=(0, 12), pady=8)

        # --- Row 2: Using class constructors ---
        section2 = ctk.CTkLabel(
            card,
            text="Using CTk*Button classes:",
            font=(BUTTON_CONFIG.FONT_FAMILY, 12),
            text_color=BUTTON_COLORS.TEXT_MUTED
        )
        section2.pack(anchor="w", padx=20, pady=(16, 4))

        row2 = ctk.CTkFrame(card, fg_color="transparent")
        row2.pack(anchor="w", padx=20, pady=8)

        primary2 = CTkPrimaryButton(row2, "Submit", icon="✓", width=160)
        secondary2 = CTkSecondaryButton(row2, "Cancel", width=140)
        danger2 = CTkDangerButton(row2, "Delete", icon="✖", width=140)
        ghost2 = CTkGhostButton(row2, "More info", width=120)

        primary2.grid(row=0, column=0, padx=(0, 12), pady=8)
        secondary2.grid(row=0, column=1, padx=(0, 12), pady=8)
        danger2.grid(row=0, column=2, padx=(0, 12), pady=8)
        ghost2.grid(row=0, column=3, padx=(0, 12), pady=8)

        # --- Row 3: Size variants ---
        section3 = ctk.CTkLabel(
            card,
            text="Size variants (sm, md, lg):",
            font=(BUTTON_CONFIG.FONT_FAMILY, 12),
            text_color=BUTTON_COLORS.TEXT_MUTED
        )
        section3.pack(anchor="w", padx=20, pady=(16, 4))

        row3 = ctk.CTkFrame(card, fg_color="transparent")
        row3.pack(anchor="w", padx=20, pady=8)

        btn_sm = make_ctk_button(row3, "Small", variant="primary", size="sm", width=120)
        btn_md = make_ctk_button(row3, "Medium", variant="primary", size="md", width=140)
        btn_lg = make_ctk_button(row3, "Large", variant="primary", size="lg", width=160)

        btn_sm.grid(row=0, column=0, padx=(0, 12), pady=8)
        btn_md.grid(row=0, column=1, padx=(0, 12), pady=8)
        btn_lg.grid(row=0, column=2, padx=(0, 12), pady=8)

        # --- Row 4: Disabled states ---
        section4 = ctk.CTkLabel(
            card,
            text="Disabled states:",
            font=(BUTTON_CONFIG.FONT_FAMILY, 12),
            text_color=BUTTON_COLORS.TEXT_MUTED
        )
        section4.pack(anchor="w", padx=20, pady=(16, 4))

        row4 = ctk.CTkFrame(card, fg_color="transparent")
        row4.pack(anchor="w", padx=20, pady=8)

        disabled_btn = make_ctk_button(
            row4, "Locked until 10:30 CET",
            variant="secondary",
            width=280,
            icon="⏳",
            disabled=True
        )
        disabled_primary = make_ctk_button(
            row4, "Unavailable",
            variant="primary",
            width=180,
            disabled=True
        )

        disabled_btn.grid(row=0, column=0, padx=(0, 12), pady=8)
        disabled_primary.grid(row=0, column=1, padx=(0, 12), pady=8)

        # Toggle button to demonstrate enable/disable
        self._toggle_state = True
        toggle_target = make_ctk_button(
            row4, "Click to toggle",
            variant="secondary",
            width=180
        )

        def toggle_disabled():
            self._toggle_state = not self._toggle_state
            set_button_disabled(toggle_target, self._toggle_state)
            toggle_btn.configure(
                text="Enable" if self._toggle_state else "Disable"
            )

        toggle_btn = make_ctk_button(
            row4, "Enable",
            command=toggle_disabled,
            variant="ghost",
            width=100
        )
        set_button_disabled(toggle_target, True)

        toggle_target.grid(row=0, column=2, padx=(0, 12), pady=8)
        toggle_btn.grid(row=0, column=3, padx=(0, 12), pady=8)


if __name__ == "__main__":
    app = ButtonDemo()
    app.mainloop()
