"""
Drawer components for the Nibor Calculation Terminal.
Right-side panel that slides in to show calculation details.
"""
import tkinter as tk
from typing import Optional, Dict, Any, Callable
from datetime import datetime

from ctk_compat import ctk, CTK_AVAILABLE

from ui.theme import COLORS, FONTS, SPACING, RADII, ICONS
from config import THEME  # Dark theme colors


class CompactCalculationDrawer(tk.Toplevel):
    """
    Compact drawer showing NIBOR calculation breakdown with collapsible sections.

    Shows:
    - NIBOR result with Funding Rate + Spread
    - Collapsible sections for EUR Implied, USD Implied, NOK ECP
    - Weights always visible
    """

    def __init__(self, master, tenor_key: str, data: Dict[str, Any], on_close: Callable = None, show_spread: bool = True):
        super().__init__(master)

        self._tenor_key = tenor_key
        self._data = data
        self._on_close = on_close
        self._show_spread = show_spread  # True for NIBOR, False for Funding Rate
        self._expanded_sections = {}  # Track which sections are expanded

        # Window setup - compact, no decorations
        self.overrideredirect(True)
        self.configure(bg=THEME["bg_card"])

        # Build content
        self._build_ui()

        # Position near the click
        self._position_drawer()

        # Bind escape to close
        self.bind("<Escape>", lambda e: self.close())

        # Click outside to close
        self.bind("<FocusOut>", self._on_focus_out)

    def _build_ui(self):
        """Build the compact drawer UI."""
        # Main container with border
        container = tk.Frame(
            self,
            bg=THEME["bg_card"],
            highlightthickness=1,
            highlightbackground=THEME["border"]
        )
        container.pack(fill="both", expand=True)

        # Header: NIBOR + value
        self._build_header(container)

        # Separator
        tk.Frame(container, bg=THEME["border"], height=1).pack(fill="x")

        # Funding Rate + Spread section
        self._build_funding_section(container)

        # Separator
        tk.Frame(container, bg=THEME["border"], height=1).pack(fill="x")

        # Collapsible components
        self._build_components_section(container)

        # Close button at bottom
        self._build_footer(container)

    def _build_header(self, parent):
        """Build header with title and value."""
        header = tk.Frame(parent, bg=THEME["bg_card"])
        header.pack(fill="x", padx=16, pady=12)

        # Title - different for Funding Rate vs NIBOR
        if self._show_spread:
            title = f"NIBOR {self._tenor_key.upper()}"
            display_value = self._data.get("final_rate", 0)
        else:
            title = f"Funding Rate {self._tenor_key.upper()}"
            display_value = self._data.get("funding_rate", 0)

        tk.Label(
            header,
            text=title,
            font=("Segoe UI Semibold", 14),
            fg=THEME["text"],
            bg=THEME["bg_card"]
        ).pack(side="left")

        # Close button
        close_btn = tk.Label(
            header,
            text="✕",
            font=("Segoe UI", 12),
            fg=THEME["text_muted"],
            bg=THEME["bg_card"],
            cursor="hand2"
        )
        close_btn.pack(side="right")
        close_btn.bind("<Button-1>", lambda e: self.close())
        close_btn.bind("<Enter>", lambda e: close_btn.config(fg=THEME["text"]))
        close_btn.bind("<Leave>", lambda e: close_btn.config(fg=THEME["text_muted"]))

        # Value (large, accent color)
        tk.Label(
            header,
            text=f"{display_value:.4f}%" if display_value else "—",
            font=("Consolas", 18, "bold"),
            fg=THEME["accent"],
            bg=THEME["bg_card"]
        ).pack(side="right", padx=(0, 16))

    def _build_funding_section(self, parent):
        """Build Funding Rate + Spread section (spread only shown for NIBOR)."""
        section = tk.Frame(parent, bg=THEME["bg_card"])
        section.pack(fill="x", padx=16, pady=10)

        funding_rate = self._data.get("funding_rate", 0)

        # Funding Rate row
        row1 = tk.Frame(section, bg=THEME["bg_card"])
        row1.pack(fill="x", pady=2)
        tk.Label(row1, text="Funding Rate", font=("Segoe UI", 11),
                fg=THEME["text"], bg=THEME["bg_card"]).pack(side="left")
        tk.Label(row1, text=f"{funding_rate:.4f}%" if funding_rate else "—", font=("Consolas", 11),
                fg=THEME["text"], bg=THEME["bg_card"]).pack(side="right")

        # Spread row - only show for NIBOR (when show_spread=True)
        if self._show_spread:
            spread = self._data.get("spread", 0)
            row2 = tk.Frame(section, bg=THEME["bg_card"])
            row2.pack(fill="x", pady=2)
            tk.Label(row2, text="+ Spread", font=("Segoe UI", 11),
                    fg=THEME["text_muted"], bg=THEME["bg_card"]).pack(side="left")
            tk.Label(row2, text=f"{spread:.4f}%", font=("Consolas", 11),
                    fg=THEME["text_muted"], bg=THEME["bg_card"]).pack(side="right")

    def _build_components_section(self, parent):
        """Build collapsible components (EUR, USD, NOK)."""
        section = tk.Frame(parent, bg=THEME["bg_card"])
        section.pack(fill="x", padx=16, pady=10)

        weights = self._data.get("weights", {})

        components = [
            ("EUR Implied", "eur_impl", weights.get("EUR", 0), self._get_eur_details),
            ("USD Implied", "usd_impl", weights.get("USD", 0), self._get_usd_details),
            ("NOK ECP", "nok_cm", weights.get("NOK", 0), self._get_nok_details),
        ]

        for name, data_key, weight, detail_func in components:
            self._build_collapsible_row(section, name, data_key, weight, detail_func)

    def _build_collapsible_row(self, parent, name: str, data_key: str, weight: float, detail_func: Callable):
        """Build a single collapsible component row."""
        value = self._data.get(data_key, 0)

        # Container for row + details
        container = tk.Frame(parent, bg=THEME["bg_card"])
        container.pack(fill="x", pady=2)

        # Main row (clickable)
        row = tk.Frame(container, bg=THEME["bg_card"], cursor="hand2")
        row.pack(fill="x")

        # Expand/collapse indicator
        indicator = tk.Label(
            row,
            text="▶",
            font=("Segoe UI", 8),
            fg=THEME["text_muted"],
            bg=THEME["bg_card"]
        )
        indicator.pack(side="left", padx=(0, 6))

        # Name - fixed width for alignment
        tk.Label(
            row,
            text=name,
            font=("Segoe UI", 11),
            fg=THEME["text"],
            bg=THEME["bg_card"],
            width=12,
            anchor="w"
        ).pack(side="left")

        # Weight (always visible) - fixed width for alignment
        tk.Label(
            row,
            text=f"{weight*100:.0f}%",
            font=("Segoe UI", 10),
            fg=THEME["text_muted"],
            bg=THEME["bg_card"],
            width=4,
            anchor="e"
        ).pack(side="left", padx=(4, 0))

        # Value - right aligned
        tk.Label(
            row,
            text=f"{value:.4f}%" if value else "—",
            font=("Consolas", 11),
            fg=THEME["text"],
            bg=THEME["bg_card"]
        ).pack(side="right")

        # Details frame (hidden by default)
        details_frame = tk.Frame(container, bg=THEME["bg_panel"])

        # Populate details
        details = detail_func()
        for label, val in details:
            detail_row = tk.Frame(details_frame, bg=THEME["bg_panel"])
            detail_row.pack(fill="x", padx=(20, 8), pady=1)
            tk.Label(detail_row, text=label, font=("Segoe UI", 10),
                    fg=THEME["text_muted"], bg=THEME["bg_panel"]).pack(side="left")
            tk.Label(detail_row, text=val, font=("Consolas", 10),
                    fg=THEME["text"], bg=THEME["bg_panel"]).pack(side="right")

        # Add formula at bottom
        formula = self._get_formula(data_key)
        if formula:
            formula_row = tk.Frame(details_frame, bg=THEME["bg_panel"])
            formula_row.pack(fill="x", padx=(20, 8), pady=(4, 6))
            tk.Label(formula_row, text=formula, font=("Consolas", 9),
                    fg=THEME["text_muted"], bg=THEME["bg_panel"]).pack(side="left")

        # Toggle function
        def toggle(e=None):
            if details_frame.winfo_manager():
                details_frame.pack_forget()
                indicator.config(text="▶")
            else:
                details_frame.pack(fill="x", pady=(4, 0))
                indicator.config(text="▼")

        # Bind click to toggle
        for widget in [row, indicator] + list(row.winfo_children()):
            widget.bind("<Button-1>", toggle)

    def _get_eur_details(self) -> list:
        """Get EUR Implied calculation details."""
        return [
            ("Spot", f"{self._data.get('eur_spot', 0):.4f}"),
            ("Pips", f"{self._data.get('eur_pips', 0):.2f}"),
            ("Days", f"{int(self._data.get('eur_days', 0))}"),
            ("Rate", f"{self._data.get('eur_rate', 0):.2f}%"),
        ]

    def _get_usd_details(self) -> list:
        """Get USD Implied calculation details."""
        return [
            ("Spot", f"{self._data.get('usd_spot', 0):.4f}"),
            ("Pips", f"{self._data.get('usd_pips', 0):.2f}"),
            ("Days", f"{int(self._data.get('usd_days', 0))}"),
            ("Rate", f"{self._data.get('usd_rate', 0):.2f}%"),
        ]

    def _get_nok_details(self) -> list:
        """Get NOK ECP details."""
        return [
            ("ECP Rate", f"{self._data.get('nok_cm', 0):.4f}%"),
            ("Source", "Bloomberg"),
        ]

    def _get_formula(self, data_key: str) -> str:
        """Get formula explanation for a component."""
        if data_key == "eur_impl":
            return "= (Spot + Pips/10000) × Days/360"
        elif data_key == "usd_impl":
            return "= (Spot + Pips/10000) × Days/360"
        return ""

    def _build_footer(self, parent):
        """Build footer with close hint."""
        footer = tk.Frame(parent, bg=THEME["bg_main"])
        footer.pack(fill="x", side="bottom")

        tk.Label(
            footer,
            text="ESC or click outside to close",
            font=("Segoe UI", 9),
            fg=THEME["text_muted"],
            bg=THEME["bg_main"],
            pady=6
        ).pack()

    def _position_drawer(self):
        """Position drawer near the parent window."""
        self.update_idletasks()

        # Get drawer size
        width = self.winfo_reqwidth()
        height = self.winfo_reqheight()

        # Get parent position
        parent = self.master.winfo_toplevel()
        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()

        # Position to the right of center, vertically centered
        x = parent_x + parent_width // 2 - width // 2
        y = parent_y + parent_height // 3

        self.geometry(f"+{x}+{y}")

        # Ensure focus for keyboard events
        self.focus_force()

    def _on_focus_out(self, event):
        """Handle focus out - close if clicked outside."""
        # Small delay to check if focus went to a child widget
        self.after(100, self._check_focus)

    def _check_focus(self):
        """Check if focus is still within drawer."""
        try:
            focused = self.focus_get()
            if focused is None or not str(focused).startswith(str(self)):
                self.close()
        except:
            pass

    def close(self):
        """Close the drawer."""
        if self._on_close:
            self._on_close()
        self.destroy()


class CalculationDrawer(ctk.CTkFrame if CTK_AVAILABLE else tk.Frame):
    """
    Right-side drawer panel for displaying calculation details.

    Features:
    - Sticky header with tenor name, status badge, and close button
    - Result card showing app result vs Excel facit
    - Inputs table with field/value/source
    - Calculation steps breakdown
    - Per-tenor validation checks
    - Output mapping section
    - Sticky footer with timestamp and re-run button

    Usage:
        drawer = CalculationDrawer(parent, on_close=callback)
        drawer.show_for_tenor("3m", data_dict)
        drawer.close()
    """

    # Status colors (using dark theme from config)
    STATUS_COLORS = {
        "MATCHED": {"bg": "#0d2818", "fg": "#22C55E"},  # Dark green, emerald text
        "WARN": {"bg": "#2a1b14", "fg": "#F59E0B"},     # Dark amber
        "FAIL": {"bg": "#2a1215", "fg": "#EF4444"},     # Dark red
        "PENDING": {"bg": "#18243A", "fg": "#A8B3C7"}   # Dark card, muted text
    }

    def __init__(
        self,
        master,
        width: int = 400,
        on_close: Optional[Callable] = None,
        on_rerun: Optional[Callable[[str], None]] = None,
        **kwargs
    ):
        """
        Initialize the CalculationDrawer.

        Args:
            master: Parent widget
            width: Drawer width in pixels (default 400)
            on_close: Callback when drawer is closed
            on_rerun: Callback when re-run button is clicked, receives tenor_key
        """
        self._drawer_width = width
        self._on_close = on_close
        self._on_rerun = on_rerun
        self._current_tenor: Optional[str] = None
        self._is_visible = False
        self._current_data: Dict[str, Any] = {}

        if CTK_AVAILABLE:
            super().__init__(
                master,
                fg_color=THEME["bg_card"],
                corner_radius=0,
                border_width=1,
                border_color=THEME["border"],
                width=width,
                **kwargs
            )
        else:
            super().__init__(
                master,
                bg=THEME["bg_card"],
                highlightthickness=1,
                highlightbackground=THEME["border"],
                width=width,
                **kwargs
            )

        # Configure fixed width - drawer should not shrink horizontally
        self.configure(width=width)
        if CTK_AVAILABLE:
            # For CTk, we need to prevent width from auto-sizing
            self._desired_width = width

        # Build internal structure
        self._build_layout()

        # Initially hidden
        self._hide()

    def _build_layout(self):
        """Build the internal drawer layout with all sections."""
        # Main container with scrolling
        self._build_header()
        self._build_scrollable_content()
        self._build_footer()

    def _build_header(self):
        """Build sticky header with tenor, status, and close button."""
        if CTK_AVAILABLE:
            self._header = ctk.CTkFrame(self, fg_color=THEME["bg_card"], corner_radius=0)
        else:
            self._header = tk.Frame(self, bg=THEME["bg_card"])
        self._header.pack(fill="x", side="top")

        # Header content container
        header_content = tk.Frame(self._header, bg=THEME["bg_card"])
        header_content.pack(fill="x", padx=SPACING.LG, pady=SPACING.MD)

        # Top row: Tenor title + Close button
        top_row = tk.Frame(header_content, bg=THEME["bg_card"])
        top_row.pack(fill="x")

        # Tenor title (large)
        self._tenor_label = tk.Label(
            top_row,
            text="NIBOR 3M",
            font=FONTS.H3,
            fg=THEME["text"],
            bg=THEME["bg_card"],
            anchor="w"
        )
        self._tenor_label.pack(side="left")

        # Close button (X)
        close_btn = tk.Label(
            top_row,
            text=ICONS.CLOSE,
            font=(FONTS.BODY[0], 16),
            fg=THEME["text_muted"],
            bg=THEME["bg_card"],
            cursor="hand2",
            padx=8,
            pady=4
        )
        close_btn.pack(side="right")
        close_btn.bind("<Button-1>", lambda e: self.close())
        close_btn.bind("<Enter>", lambda e: close_btn.config(fg=THEME["text"]))
        close_btn.bind("<Leave>", lambda e: close_btn.config(fg=THEME["text_muted"]))

        # Status badge row
        status_row = tk.Frame(header_content, bg=THEME["bg_card"])
        status_row.pack(fill="x", pady=(SPACING.SM, 0))

        # Status badge
        self._status_badge = tk.Label(
            status_row,
            text="MATCHED",
            font=FONTS.BUTTON_SM,
            fg=COLORS.SUCCESS,
            bg=THEME["bg_main"],
            padx=10,
            pady=3
        )
        self._status_badge.pack(side="left")

        # Run context
        self._run_context = tk.Label(
            status_row,
            text="",
            font=FONTS.BODY_SM,
            fg=THEME["text_muted"],
            bg=THEME["bg_card"],
            anchor="w"
        )
        self._run_context.pack(side="left", padx=(SPACING.SM, 0))

        # Action buttons row
        actions_row = tk.Frame(header_content, bg=THEME["bg_card"])
        actions_row.pack(fill="x", pady=(SPACING.MD, 0))

        # Copy summary button
        self._copy_btn = self._create_small_button(actions_row, "Copy summary", self._copy_summary)
        self._copy_btn.pack(side="left")

        # Open evidence button
        self._evidence_btn = self._create_small_button(actions_row, "Open evidence", self._open_evidence)
        self._evidence_btn.pack(side="left", padx=(SPACING.SM, 0))

        # Header separator
        tk.Frame(self._header, bg=THEME["border"], height=1).pack(fill="x", side="bottom")

    def _create_small_button(self, parent, text: str, command: Callable) -> tk.Label:
        """Create a small secondary action button."""
        btn = tk.Label(
            parent,
            text=text,
            font=FONTS.BODY_SM,
            fg=THEME["text_secondary"],
            bg=THEME["bg_card_2"],
            padx=10,
            pady=4,
            cursor="hand2"
        )
        btn.bind("<Button-1>", lambda e: command())
        btn.bind("<Enter>", lambda e: btn.config(bg=THEME["bg_hover"]))
        btn.bind("<Leave>", lambda e: btn.config(bg=THEME["bg_card_2"]))
        return btn

    def _build_scrollable_content(self):
        """Build the scrollable content area with all sections."""
        # Create canvas for scrolling
        self._canvas = tk.Canvas(
            self,
            bg=THEME["bg_card"],
            highlightthickness=0,
            borderwidth=0
        )
        self._scrollbar = tk.Scrollbar(
            self,
            orient="vertical",
            command=self._canvas.yview
        )

        # Scrollable frame
        self._scroll_frame = tk.Frame(self._canvas, bg=THEME["bg_card"])

        # Configure canvas
        self._canvas_window = self._canvas.create_window(
            (0, 0),
            window=self._scroll_frame,
            anchor="nw"
        )

        self._canvas.configure(yscrollcommand=self._scrollbar.set)

        # Pack scrollbar and canvas
        self._scrollbar.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)

        # Bind events for scrolling
        self._scroll_frame.bind("<Configure>", self._on_frame_configure)
        self._canvas.bind("<Configure>", self._on_canvas_configure)

        # Enable mousewheel scrolling
        self._canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self._canvas.bind_all("<Button-4>", self._on_mousewheel)
        self._canvas.bind_all("<Button-5>", self._on_mousewheel)

        # Build sections
        self._build_result_section()
        self._build_recon_section()
        self._build_inputs_section()
        self._build_steps_section()
        self._build_checks_section()

    def _on_frame_configure(self, event=None):
        """Update scroll region when frame size changes."""
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    def _on_canvas_configure(self, event=None):
        """Update frame width when canvas size changes."""
        canvas_width = event.width if event else self._canvas.winfo_width()
        self._canvas.itemconfig(self._canvas_window, width=canvas_width)

    def _on_mousewheel(self, event):
        """Handle mousewheel scrolling."""
        if not self._is_visible:
            return
        # Windows and macOS
        if event.num == 4 or event.delta > 0:
            self._canvas.yview_scroll(-1, "units")
        elif event.num == 5 or event.delta < 0:
            self._canvas.yview_scroll(1, "units")

    def _build_result_section(self):
        """Build the Result card section."""
        section = self._create_section("Result")
        self._result_section = section

        # Result card container
        card = tk.Frame(section, bg=THEME["bg_card"], highlightthickness=1, highlightbackground=THEME["border"])
        card.pack(fill="x", pady=(SPACING.SM, 0))

        card_content = tk.Frame(card, bg=THEME["bg_card"])
        card_content.pack(fill="x", padx=SPACING.MD, pady=SPACING.MD)

        # App result
        self._result_app_row = self._create_result_row(card_content, "App result", "—")

        # Excel facit
        self._result_excel_row = self._create_result_row(card_content, "Excel facit", "—")

        # Separator
        tk.Frame(card_content, bg=THEME["border"], height=1).pack(fill="x", pady=SPACING.SM)

        # Delta + tolerance
        delta_row = tk.Frame(card_content, bg=THEME["bg_card"])
        delta_row.pack(fill="x", pady=(SPACING.XS, 0))

        tk.Label(
            delta_row,
            text=f"{ICONS.DELTA} (diff)",
            font=FONTS.BODY_SM,
            fg=THEME["text_muted"],
            bg=THEME["bg_card"]
        ).pack(side="left")

        self._result_delta = tk.Label(
            delta_row,
            text="0.0000",
            font=FONTS.NUMERIC,
            fg=THEME["text"],
            bg=THEME["bg_card"]
        )
        self._result_delta.pack(side="right")

    def _create_result_row(self, parent, label: str, value: str) -> Dict[str, tk.Label]:
        """Create a result row with label and value."""
        row = tk.Frame(parent, bg=THEME["bg_card"])
        row.pack(fill="x", pady=(SPACING.XS, 0))

        lbl = tk.Label(
            row,
            text=label,
            font=FONTS.BODY_SM,
            fg=THEME["text_muted"],
            bg=THEME["bg_card"]
        )
        lbl.pack(side="left")

        val = tk.Label(
            row,
            text=value,
            font=FONTS.NUMERIC_LG,
            fg=THEME["text"],
            bg=THEME["bg_card"]
        )
        val.pack(side="right")

        return {"label": lbl, "value": val}

    def _build_recon_section(self):
        """Build the Reconciliation section for Excel comparison."""
        section = self._create_section("Reconciliation")
        self._recon_section = section

        # Container for recon table
        self._recon_container = tk.Frame(section, bg=THEME["bg_card"])
        self._recon_container.pack(fill="x", pady=(SPACING.SM, 0))

    def _build_inputs_section(self):
        """Build the Inputs table section."""
        section = self._create_section("Inputs")
        self._inputs_section = section

        # Container for inputs table
        self._inputs_container = tk.Frame(section, bg=THEME["bg_card"])
        self._inputs_container.pack(fill="x", pady=(SPACING.SM, 0))

    def _build_steps_section(self):
        """Build the Calculation steps section."""
        section = self._create_section("Calculation Steps")
        self._steps_section = section

        # Container for steps list
        self._steps_container = tk.Frame(section, bg=THEME["bg_card"])
        self._steps_container.pack(fill="x", pady=(SPACING.SM, 0))

    def _build_checks_section(self):
        """Build the Per-tenor checks section."""
        section = self._create_section("Validation Checks")
        self._checks_section = section

        # Container for checks list
        self._checks_container = tk.Frame(section, bg=THEME["bg_card"])
        self._checks_container.pack(fill="x", pady=(SPACING.SM, 0))


    def _create_section(self, title: str) -> tk.Frame:
        """Create a section container with title."""
        section = tk.Frame(self._scroll_frame, bg=THEME["bg_card"])
        section.pack(fill="x", padx=SPACING.LG, pady=(SPACING.LG, 0))

        # Section title
        tk.Label(
            section,
            text=title,
            font=FONTS.TABLE_HEADER,
            fg=THEME["text_muted"],
            bg=THEME["bg_card"],
            anchor="w"
        ).pack(fill="x")

        return section

    def _build_footer(self):
        """Build sticky footer with timestamp and re-run button."""
        if CTK_AVAILABLE:
            self._footer = ctk.CTkFrame(self, fg_color=THEME["bg_card"], corner_radius=0)
        else:
            self._footer = tk.Frame(self, bg=THEME["bg_card"])
        self._footer.pack(fill="x", side="bottom")

        # Footer separator
        tk.Frame(self._footer, bg=THEME["border"], height=1).pack(fill="x", side="top")

        # Footer content
        footer_content = tk.Frame(self._footer, bg=THEME["bg_card"])
        footer_content.pack(fill="x", padx=SPACING.LG, pady=SPACING.MD)

        # Last validated timestamp
        self._last_validated = tk.Label(
            footer_content,
            text="Last validated: —",
            font=FONTS.BODY_SM,
            fg=THEME["text_muted"],
            bg=THEME["bg_card"]
        )
        self._last_validated.pack(side="left")

        # Re-run button
        if CTK_AVAILABLE:
            self._rerun_btn = ctk.CTkButton(
                footer_content,
                text="Re-run checks",
                font=FONTS.BUTTON_SM,
                fg_color=THEME["bg_card_2"],
                text_color=THEME["text_secondary"],
                hover_color=THEME["bg_hover"],
                corner_radius=RADII.SM,
                height=28,
                width=100,
                command=self._on_rerun_click
            )
        else:
            self._rerun_btn = tk.Button(
                footer_content,
                text="Re-run checks",
                font=FONTS.BODY_SM,
                fg=THEME["text_secondary"],
                bg=THEME["bg_card_2"],
                activebackground=THEME["bg_hover"],
                activeforeground=THEME["text"],
                relief="flat",
                cursor="hand2",
                padx=10,
                pady=4,
                command=self._on_rerun_click
            )
        self._rerun_btn.pack(side="right")

    def _hide(self):
        """Hide the drawer."""
        self._is_visible = False
        # Don't pack_forget - just set flag. Window visibility is handled by parent.

    def _show(self):
        """Show the drawer."""
        self._is_visible = True
        # Ensure drawer is packed (in case it was removed)
        if not self.winfo_ismapped():
            self.pack(fill="both", expand=True)

    def show_for_tenor(self, tenor_key: str, data: Dict[str, Any]):
        """
        Show the drawer with data for a specific tenor.

        Args:
            tenor_key: Tenor identifier (e.g., "1m", "2m", "3m", "6m")
            data: Dictionary containing calculation data for the tenor.
                  Expected keys:
                  - funding_rate: float
                  - spread: float
                  - final_rate: float
                  - eur_impl, usd_impl, nok_cm: float (implied rates)
                  - eur_spot, eur_pips, eur_rate, eur_days: EUR data
                  - usd_spot, usd_pips, usd_rate, usd_days: USD data
                  - weights: dict with EUR, USD, NOK weights
                  - match_data: dict with criteria and status
        """
        self._current_tenor = tenor_key
        self._current_data = data or {}

        # Update header
        self._update_header(tenor_key, data)

        # Update sections
        self._update_result_section(data)
        self._update_recon_section(data)
        self._update_inputs_section(tenor_key, data)
        self._update_steps_section(data)
        self._update_checks_section(data)

        # Update footer
        self._last_validated.config(text=f"Last validated: {datetime.now().strftime('%H:%M:%S')}")

        # Scroll to top
        self._canvas.yview_moveto(0)

        # Show drawer
        self._show()

    def _update_header(self, tenor_key: str, data: Dict[str, Any]):
        """Update header with tenor and status."""
        # Tenor title
        self._tenor_label.config(text=f"NIBOR {tenor_key.upper()}")

        # Status badge
        match_data = data.get("match_data", {})
        all_matched = match_data.get("all_matched", False)
        errors = match_data.get("errors", [])

        if all_matched:
            status = "MATCHED"
        elif errors:
            status = "FAIL"
        else:
            status = "PENDING"

        colors = self.STATUS_COLORS.get(status, self.STATUS_COLORS["PENDING"])
        self._status_badge.config(text=status, fg=colors["fg"], bg=colors["bg"])

        # Run context
        fixing_status = data.get("fixing_status", "Pre-fixing")
        run_id = data.get("run_id", "Current")
        current_time = datetime.now().strftime("%H:%M")
        self._run_context.config(text=f"{run_id} | {current_time} | {fixing_status}")

        # Evidence button state
        has_evidence = bool(data.get("evidence_path"))
        if has_evidence:
            self._evidence_btn.config(fg=THEME["text_secondary"], cursor="hand2")
        else:
            self._evidence_btn.config(fg=THEME["text_muted"], cursor="arrow")

    def _update_result_section(self, data: Dict[str, Any]):
        """Update the result card with calculation results."""
        final_rate = data.get("final_rate")

        # App result
        if final_rate is not None:
            self._result_app_row["value"].config(text=f"{final_rate:.4f}%")
        else:
            self._result_app_row["value"].config(text="N/A")

        # Excel facit (from match data)
        match_data = data.get("match_data", {})
        criteria = match_data.get("criteria", [])
        excel_value = None
        for criterion in criteria:
            if criterion.get("excel_value") is not None:
                excel_value = criterion.get("excel_value")
                break

        if excel_value is not None:
            self._result_excel_row["value"].config(text=f"{excel_value:.4f}%")
        else:
            self._result_excel_row["value"].config(text="N/A")

        # Delta
        if final_rate is not None and excel_value is not None:
            delta = abs(final_rate - excel_value)
            delta_color = COLORS.SUCCESS if delta < 0.0001 else COLORS.DANGER
            self._result_delta.config(text=f"{delta:.4f}", fg=delta_color)
        else:
            self._result_delta.config(text="—", fg=THEME["text_muted"])

    def _update_recon_section(self, data: Dict[str, Any]):
        """Update the reconciliation section - ONLY show diffs, not matches."""
        # Clear existing
        for widget in self._recon_container.winfo_children():
            widget.destroy()

        recon_data = data.get("recon_data", [])
        all_inputs_match = data.get("all_inputs_match", False)

        if not recon_data:
            tk.Label(
                self._recon_container,
                text="No reconciliation data available",
                font=FONTS.BODY_SM,
                fg=THEME["text_muted"],
                bg=THEME["bg_card"]
            ).pack(anchor="w", pady=SPACING.SM)
            return

        # Separate diffs from matches
        input_diffs = [item for item in recon_data if item.get("is_input") and not item.get("matched")]
        output_diffs = [item for item in recon_data if not item.get("is_input") and not item.get("matched") and not item.get("skipped")]

        # Count for summary
        total_inputs = len([item for item in recon_data if item.get("is_input")])
        total_outputs = len([item for item in recon_data if not item.get("is_input")])

        # If everything matches, show success message
        if not input_diffs and not output_diffs:
            success_frame = tk.Frame(self._recon_container, bg=THEME["bg_panel"])
            success_frame.pack(fill="x", pady=SPACING.SM)

            tk.Label(
                success_frame,
                text=f"{ICONS.CHECK} All {total_inputs} inputs match Excel",
                font=FONTS.BODY_SM,
                fg=COLORS.SUCCESS,
                bg=THEME["bg_panel"],
                padx=SPACING.MD,
                pady=SPACING.SM
            ).pack(anchor="w")

            if all_inputs_match:
                tk.Label(
                    success_frame,
                    text=f"{ICONS.CHECK} Formula outputs verified ({total_outputs} checks)",
                    font=FONTS.BODY_SM,
                    fg=COLORS.SUCCESS,
                    bg=THEME["bg_panel"],
                    padx=SPACING.MD
                ).pack(anchor="w", pady=(0, SPACING.SM))
            return

        # Collect unique component names that differ
        all_diffs = input_diffs + output_diffs
        unique_labels = []
        seen = set()
        for item in all_diffs:
            label = item.get("label", "Unknown")
            if label not in seen:
                seen.add(label)
                unique_labels.append(label)

        # Header showing what differs
        header_frame = tk.Frame(self._recon_container, bg=THEME["bg_panel"])
        header_frame.pack(fill="x", pady=SPACING.SM)

        tk.Label(
            header_frame,
            text=f"{ICONS.CROSS} Diff: {', '.join(unique_labels)}",
            font=FONTS.TABLE_HEADER,
            fg=COLORS.DANGER,
            bg=THEME["bg_panel"],
            padx=SPACING.MD,
            pady=SPACING.SM
        ).pack(anchor="w")

    def _add_recon_diff_row(self, parent, item: Dict[str, Any], index: int):
        """Add a single diff row to the recon table."""
        label = item.get("label", "")
        cell = item.get("cell", "")
        gui_value = item.get("gui_value")
        excel_value = item.get("excel_value")
        decimals = item.get("decimals", 4)

        row_bg = THEME["bg_panel"]  # Dark background for diff rows
        row = tk.Frame(parent, bg=row_bg)
        row.pack(fill="x")

        # Field name
        tk.Label(
            row,
            text=label,
            font=FONTS.BODY_SM,
            fg=COLORS.DANGER,
            bg=row_bg,
            width=9,
            anchor="w",
            padx=SPACING.XS,
            pady=SPACING.XS
        ).pack(side="left")

        # Cell reference
        tk.Label(
            row,
            text=cell,
            font=FONTS.TABLE_CELL_MONO,
            fg=THEME["text_muted"],
            bg=row_bg,
            width=4,
            anchor="w",
            padx=SPACING.XS,
            pady=SPACING.XS
        ).pack(side="left")

        # GUI value
        gui_str = f"{gui_value:.{decimals}f}" if gui_value is not None else "N/A"
        tk.Label(
            row,
            text=gui_str,
            font=FONTS.TABLE_CELL_MONO,
            fg=THEME["text"],
            bg=row_bg,
            width=8,
            anchor="e",
            padx=SPACING.XS,
            pady=SPACING.XS
        ).pack(side="left")

        # Excel value
        excel_str = f"{excel_value:.{decimals}f}" if excel_value is not None else "N/A"
        tk.Label(
            row,
            text=excel_str,
            font=FONTS.TABLE_CELL_MONO,
            fg=THEME["text"],
            bg=row_bg,
            width=8,
            anchor="e",
            padx=SPACING.XS,
            pady=SPACING.XS
        ).pack(side="left")

        # Diff value
        if gui_value is not None and excel_value is not None:
            try:
                diff = float(gui_value) - float(excel_value)
                diff_str = f"{diff:+.{decimals}f}"
            except (ValueError, TypeError):
                diff_str = "—"
        else:
            diff_str = "—"

        tk.Label(
            row,
            text=diff_str,
            font=FONTS.TABLE_CELL_MONO,
            fg=COLORS.DANGER,
            bg=row_bg,
            width=7,
            anchor="e",
            padx=SPACING.XS,
            pady=SPACING.XS
        ).pack(side="left")

    def _add_recon_section_header(self, parent, text: str):
        """Add a section header in the recon table."""
        header = tk.Frame(parent, bg=THEME["bg_main"])
        header.pack(fill="x", pady=(SPACING.SM, 0))

        tk.Label(
            header,
            text=text,
            font=FONTS.TABLE_HEADER,
            fg=THEME["text_muted"],
            bg=THEME["bg_main"],
            anchor="w",
            padx=SPACING.SM,
            pady=SPACING.XS
        ).pack(side="left", fill="x", expand=True)

    def _update_inputs_section(self, tenor_key: str, data: Dict[str, Any]):
        """Update the inputs section with 3-column layout (EUR, USD, NOK)."""
        # Clear existing
        for widget in self._inputs_container.winfo_children():
            widget.destroy()

        weights = data.get("weights", {})

        # === 3-COLUMN HEADER: EUR | USD | NOK ===
        columns_frame = tk.Frame(self._inputs_container, bg=THEME["bg_card"])
        columns_frame.pack(fill="x", pady=(0, SPACING.SM))

        # Configure 3 equal columns
        columns_frame.columnconfigure(0, weight=1, uniform="col")
        columns_frame.columnconfigure(1, weight=1, uniform="col")
        columns_frame.columnconfigure(2, weight=1, uniform="col")

        # EUR Column
        eur_col = self._create_currency_column(
            columns_frame,
            title="EUR Implied",
            source="Bloomberg",
            value=data.get('eur_impl'),
            weight=weights.get('EUR', 0),
            details=[
                ("Spot", f"{data.get('eur_spot', 0):.4f}" if data.get('eur_spot') else "—", "Bloomberg"),
                ("Pips", f"{data.get('eur_pips', 0):.2f}" if data.get('eur_pips') else "—", "Bloomberg"),
                ("Rate", f"{data.get('eur_rate', 0):.2f}%" if data.get('eur_rate') else "—", "Internal"),
                ("Days", f"{int(data.get('eur_days', 0))}" if data.get('eur_days') else "—", "Days file"),
            ]
        )
        eur_col.grid(row=0, column=0, sticky="nsew", padx=(0, 2))

        # USD Column
        usd_col = self._create_currency_column(
            columns_frame,
            title="USD Implied",
            source="Bloomberg",
            value=data.get('usd_impl'),
            weight=weights.get('USD', 0),
            details=[
                ("Spot", f"{data.get('usd_spot', 0):.4f}" if data.get('usd_spot') else "—", "Bloomberg"),
                ("Pips", f"{data.get('usd_pips', 0):.2f}" if data.get('usd_pips') else "—", "Bloomberg"),
                ("Rate", f"{data.get('usd_rate', 0):.2f}%" if data.get('usd_rate') else "—", "Internal"),
                ("Days", f"{int(data.get('usd_days', 0))}" if data.get('usd_days') else "—", "Days file"),
            ]
        )
        usd_col.grid(row=0, column=1, sticky="nsew", padx=2)

        # NOK Column
        nok_col = self._create_currency_column(
            columns_frame,
            title="NOK ECP",
            source="Bloomberg",
            value=data.get('nok_cm'),
            weight=weights.get('NOK', 0),
            details=[]  # NOK has no sub-details
        )
        nok_col.grid(row=0, column=2, sticky="nsew", padx=(2, 0))

        # === FUNDING CALCULATION SUMMARY ===
        calc_frame = tk.Frame(self._inputs_container, bg=THEME["bg_panel"])
        calc_frame.pack(fill="x", pady=(SPACING.SM, 0))

        # Funding Rate row
        self._add_summary_row(calc_frame, "Funding Rate",
            f"{data.get('funding_rate', 0):.4f}%" if data.get('funding_rate') else "—")

        # Spread row
        self._add_summary_row(calc_frame, "+ Spread",
            f"{data.get('spread', 0):.2f}%", muted=True)

        # Separator
        tk.Frame(calc_frame, bg=THEME["border"], height=1).pack(fill="x", padx=SPACING.SM)

        # Final NIBOR row
        self._add_summary_row(calc_frame, f"NIBOR {tenor_key.upper()}",
            f"{data.get('final_rate', 0):.4f}%" if data.get('final_rate') else "—",
            bold=True, accent=True)

    def _create_currency_column(self, parent, title: str, source: str, value, weight: float, details: list) -> tk.Frame:
        """Create a currency column with header, source badge, value, weight, and details."""
        col = tk.Frame(parent, bg=THEME["bg_card"], highlightthickness=1, highlightbackground=THEME["border"])

        # Header with title
        header = tk.Frame(col, bg=THEME["bg_main"])
        header.pack(fill="x")

        tk.Label(
            header,
            text=title,
            font=FONTS.TABLE_HEADER,
            fg=THEME["text"],
            bg=THEME["bg_main"],
            pady=SPACING.XS
        ).pack()

        # Source badge
        source_badge = tk.Label(
            header,
            text=f"░ {source}",
            font=("Segoe UI", 8),
            fg=THEME["text_muted"],
            bg=THEME["bg_main"],
            pady=2
        )
        source_badge.pack()

        # Main value (large)
        value_str = f"{value:.4f}%" if value else "—"
        tk.Label(
            col,
            text=value_str,
            font=("Consolas", 13, "bold"),
            fg=THEME["accent"],
            bg=THEME["bg_card"],
            pady=SPACING.SM
        ).pack()

        # Weight (always visible)
        weight_str = f"{weight * 100:.0f}%"
        weight_frame = tk.Frame(col, bg=THEME["bg_card_2"])
        weight_frame.pack(pady=(0, SPACING.SM))
        tk.Label(
            weight_frame,
            text=f"Weight: {weight_str}",
            font=("Segoe UI", 9),
            fg=THEME["text_muted"],
            bg=THEME["bg_card_2"],
            padx=SPACING.SM,
            pady=2
        ).pack()

        # Details (spot, pips, rate, days)
        if details:
            details_frame = tk.Frame(col, bg=THEME["bg_card"])
            details_frame.pack(fill="x", padx=SPACING.XS, pady=(0, SPACING.XS))

            for label, val, src in details:
                row = tk.Frame(details_frame, bg=THEME["bg_card"])
                row.pack(fill="x", pady=1)

                tk.Label(
                    row,
                    text=label,
                    font=("Segoe UI", 9),
                    fg=THEME["text_muted"],
                    bg=THEME["bg_card"],
                    anchor="w",
                    width=5
                ).pack(side="left")

                tk.Label(
                    row,
                    text=val,
                    font=("Consolas", 9),
                    fg=THEME["text"],
                    bg=THEME["bg_card"],
                    anchor="e"
                ).pack(side="right")

        return col

    def _add_summary_row(self, parent, label: str, value: str, muted: bool = False, bold: bool = False, accent: bool = False):
        """Add a summary row to the calculation frame."""
        row = tk.Frame(parent, bg=THEME["bg_panel"])
        row.pack(fill="x", padx=SPACING.SM, pady=SPACING.XS)

        label_font = FONTS.TABLE_HEADER if bold else FONTS.BODY_SM
        value_font = ("Consolas", 12, "bold") if bold else FONTS.TABLE_CELL_MONO

        tk.Label(
            row,
            text=label,
            font=label_font,
            fg=THEME["text_muted"] if muted else THEME["text"],
            bg=THEME["bg_panel"]
        ).pack(side="left")

        tk.Label(
            row,
            text=value,
            font=value_font,
            fg=THEME["accent"] if accent else (THEME["text_muted"] if muted else THEME["text"]),
            bg=THEME["bg_panel"]
        ).pack(side="right")

    def _update_steps_section(self, data: Dict[str, Any]):
        """Update the calculation steps."""
        # Clear existing
        for widget in self._steps_container.winfo_children():
            widget.destroy()

        weights = data.get("weights", {})
        eur_impl = data.get("eur_impl", 0)
        usd_impl = data.get("usd_impl", 0)
        nok_cm = data.get("nok_cm", 0)
        funding_rate = data.get("funding_rate")
        spread = data.get("spread", 0)
        final_rate = data.get("final_rate")

        # Calculate contributions
        eur_w = weights.get('EUR', 0)
        usd_w = weights.get('USD', 0)
        nok_w = weights.get('NOK', 0)

        eur_contrib = eur_impl * eur_w if eur_impl else 0
        usd_contrib = usd_impl * usd_w if usd_impl else 0
        nok_contrib = nok_cm * nok_w if nok_cm else 0

        steps = [
            ("1. EUR contribution", f"{eur_impl:.4f} x {eur_w:.4f} = {eur_contrib:.4f}"),
            ("2. USD contribution", f"{usd_impl:.4f} x {usd_w:.4f} = {usd_contrib:.4f}"),
            ("3. NOK contribution", f"{nok_cm:.4f} x {nok_w:.4f} = {nok_contrib:.4f}"),
            ("4. Funding rate", f"= {funding_rate:.4f}%" if funding_rate else "= —"),
            ("5. Add spread", f"+ {spread:.2f}%"),
            ("6. Final NIBOR", f"= {final_rate:.4f}%" if final_rate else "= —"),
        ]

        for step_label, step_calc in steps:
            row = tk.Frame(self._steps_container, bg=THEME["bg_card"])
            row.pack(fill="x", pady=(SPACING.XS, 0))

            tk.Label(
                row,
                text=step_label,
                font=FONTS.BODY_SM,
                fg=THEME["text_muted"],
                bg=THEME["bg_card"],
                anchor="w"
            ).pack(side="left")

            tk.Label(
                row,
                text=step_calc,
                font=FONTS.TABLE_CELL_MONO,
                fg=THEME["text"],
                bg=THEME["bg_card"],
                anchor="e"
            ).pack(side="right")

    def _update_checks_section(self, data: Dict[str, Any]):
        """Update the validation checks list."""
        # Clear existing
        for widget in self._checks_container.winfo_children():
            widget.destroy()

        match_data = data.get("match_data", {})
        criteria = match_data.get("criteria", [])

        if not criteria:
            tk.Label(
                self._checks_container,
                text="No validation data available",
                font=FONTS.BODY_SM,
                fg=THEME["text_muted"],
                bg=THEME["bg_card"]
            ).pack(anchor="w", pady=SPACING.SM)
            return

        for criterion in criteria:
            self._create_check_item(criterion)

    def _create_check_item(self, criterion: Dict[str, Any]):
        """Create a single check item that can expand to show details."""
        matched = criterion.get("matched", False)
        name = criterion.get("name", "Unknown")
        description = criterion.get("description", "")
        gui_value = criterion.get("gui_value")
        excel_value = criterion.get("excel_value")

        # Container
        item = tk.Frame(
            self._checks_container,
            bg=THEME["bg_card"],
            highlightthickness=1,
            highlightbackground=THEME["border"]
        )
        item.pack(fill="x", pady=(SPACING.XS, 0))

        # Header row (clickable)
        header = tk.Frame(item, bg=THEME["bg_card"], cursor="hand2")
        header.pack(fill="x", padx=SPACING.SM, pady=SPACING.SM)

        # Expand/collapse indicator
        expand_indicator = tk.Label(
            header,
            text="▶",
            font=("Segoe UI", 8),
            fg=THEME["text_muted"],
            bg=THEME["bg_card"]
        )
        expand_indicator.pack(side="left", padx=(0, 4))

        # Status icon
        icon_text = ICONS.CHECK if matched else ICONS.CROSS
        icon_color = COLORS.SUCCESS if matched else COLORS.DANGER

        tk.Label(
            header,
            text=icon_text,
            font=FONTS.BODY,
            fg=icon_color,
            bg=THEME["bg_card"]
        ).pack(side="left")

        # Check name
        tk.Label(
            header,
            text=name,
            font=FONTS.BODY_SM,
            fg=THEME["text"],
            bg=THEME["bg_card"]
        ).pack(side="left", padx=(SPACING.XS, 0))

        # Status text
        status_text = "PASS" if matched else "FAIL"
        tk.Label(
            header,
            text=status_text,
            font=FONTS.BUTTON_SM,
            fg=icon_color,
            bg=THEME["bg_card"]
        ).pack(side="right")

        # Details container (collapsed by default - click to expand)
        details = tk.Frame(item, bg=THEME["bg_panel"])

        # Observed vs Expected
        if gui_value is not None:
            tk.Label(
                details,
                text=f"Observed: {gui_value:.4f}",
                font=FONTS.TABLE_CELL_MONO,
                fg=THEME["text"],
                bg=THEME["bg_panel"],
                padx=SPACING.SM,
                pady=SPACING.XS
            ).pack(anchor="w")

        if excel_value is not None:
            tk.Label(
                details,
                text=f"Expected: {excel_value:.4f}",
                font=FONTS.TABLE_CELL_MONO,
                fg=THEME["text"],
                bg=THEME["bg_panel"],
                padx=SPACING.SM,
                pady=SPACING.XS
            ).pack(anchor="w")

        if description:
            tk.Label(
                details,
                text=f"({description})",
                font=FONTS.BODY_SM,
                fg=THEME["text_muted"],
                bg=THEME["bg_panel"],
                padx=SPACING.SM,
                pady=SPACING.XS
            ).pack(anchor="w")

        # Toggle details on click
        def toggle_details(e):
            if details.winfo_manager():
                details.pack_forget()
                expand_indicator.config(text="▶")
            else:
                details.pack(fill="x", padx=SPACING.SM, pady=(0, SPACING.SM))
                expand_indicator.config(text="▼")

        header.bind("<Button-1>", toggle_details)
        for child in header.winfo_children():
            child.bind("<Button-1>", toggle_details)

    def _copy_summary(self):
        """Copy calculation summary to clipboard."""
        if not self._current_data:
            return

        tenor = self._current_tenor or "Unknown"
        data = self._current_data
        final_rate = data.get("final_rate")
        funding_rate = data.get("funding_rate")
        spread = data.get("spread", 0)

        summary = f"""NIBOR {tenor.upper()} Calculation Summary
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Funding Rate: {funding_rate:.4f}% if funding_rate else "N/A"
Spread: {spread:.2f}%
Final NIBOR: {final_rate:.4f}% if final_rate else "N/A"
Timestamp: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""

        try:
            self.clipboard_clear()
            self.clipboard_append(summary)
        except Exception:
            pass

    def _open_evidence(self):
        """Open evidence file if available."""
        evidence_path = self._current_data.get("evidence_path")
        if not evidence_path:
            return

        import os
        import subprocess
        import platform

        try:
            if platform.system() == "Windows":
                os.startfile(evidence_path)
            elif platform.system() == "Darwin":
                subprocess.run(["open", evidence_path])
            else:
                subprocess.run(["xdg-open", evidence_path])
        except Exception:
            pass

    def _on_rerun_click(self):
        """Handle re-run button click."""
        if self._on_rerun and self._current_tenor:
            self._on_rerun(self._current_tenor)

    def close(self):
        """Close the drawer."""
        self._current_tenor = None
        self._current_data = {}
        self._hide()

        if self._on_close:
            self._on_close()

    def is_visible(self) -> bool:
        """Check if drawer is currently visible."""
        return self._is_visible

    def get_current_tenor(self) -> Optional[str]:
        """Get the currently displayed tenor."""
        return self._current_tenor
