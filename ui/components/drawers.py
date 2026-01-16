"""
Drawer components for the Nibor Calculation Terminal.
Right-side panel that slides in to show calculation details.
"""
import tkinter as tk
from typing import Optional, Dict, Any, Callable
from datetime import datetime

try:
    import customtkinter as ctk
    CTK_AVAILABLE = True
except ImportError:
    CTK_AVAILABLE = False
    ctk = None

from ui.theme import COLORS, FONTS, SPACING, RADII, ICONS


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

    # Status colors
    STATUS_COLORS = {
        "MATCHED": {"bg": "#E8F5E9", "fg": COLORS.SUCCESS},
        "WARN": {"bg": COLORS.WARNING_BG, "fg": COLORS.WARNING},
        "FAIL": {"bg": "#FFEBEE", "fg": COLORS.DANGER},
        "PENDING": {"bg": COLORS.CHIP_BG, "fg": COLORS.TEXT_MUTED}
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
                fg_color=COLORS.SURFACE,
                corner_radius=0,
                border_width=1,
                border_color=COLORS.BORDER,
                width=width,
                **kwargs
            )
        else:
            super().__init__(
                master,
                bg=COLORS.SURFACE,
                highlightthickness=1,
                highlightbackground=COLORS.BORDER,
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
            self._header = ctk.CTkFrame(self, fg_color=COLORS.SURFACE, corner_radius=0)
        else:
            self._header = tk.Frame(self, bg=COLORS.SURFACE)
        self._header.pack(fill="x", side="top")

        # Header content container
        header_content = tk.Frame(self._header, bg=COLORS.SURFACE)
        header_content.pack(fill="x", padx=SPACING.LG, pady=SPACING.MD)

        # Top row: Tenor title + Close button
        top_row = tk.Frame(header_content, bg=COLORS.SURFACE)
        top_row.pack(fill="x")

        # Tenor title (large)
        self._tenor_label = tk.Label(
            top_row,
            text="NIBOR 3M",
            font=FONTS.H3,
            fg=COLORS.TEXT,
            bg=COLORS.SURFACE,
            anchor="w"
        )
        self._tenor_label.pack(side="left")

        # Close button (X)
        close_btn = tk.Label(
            top_row,
            text=ICONS.CLOSE,
            font=(FONTS.BODY[0], 16),
            fg=COLORS.TEXT_MUTED,
            bg=COLORS.SURFACE,
            cursor="hand2",
            padx=8,
            pady=4
        )
        close_btn.pack(side="right")
        close_btn.bind("<Button-1>", lambda e: self.close())
        close_btn.bind("<Enter>", lambda e: close_btn.config(fg=COLORS.TEXT))
        close_btn.bind("<Leave>", lambda e: close_btn.config(fg=COLORS.TEXT_MUTED))

        # Status badge row
        status_row = tk.Frame(header_content, bg=COLORS.SURFACE)
        status_row.pack(fill="x", pady=(SPACING.SM, 0))

        # Status badge
        self._status_badge = tk.Label(
            status_row,
            text="MATCHED",
            font=FONTS.BUTTON_SM,
            fg=COLORS.SUCCESS,
            bg="#E8F5E9",
            padx=10,
            pady=3
        )
        self._status_badge.pack(side="left")

        # Run context
        self._run_context = tk.Label(
            status_row,
            text="",
            font=FONTS.BODY_SM,
            fg=COLORS.TEXT_MUTED,
            bg=COLORS.SURFACE,
            anchor="w"
        )
        self._run_context.pack(side="left", padx=(SPACING.SM, 0))

        # Action buttons row
        actions_row = tk.Frame(header_content, bg=COLORS.SURFACE)
        actions_row.pack(fill="x", pady=(SPACING.MD, 0))

        # Copy summary button
        self._copy_btn = self._create_small_button(actions_row, "Copy summary", self._copy_summary)
        self._copy_btn.pack(side="left")

        # Open evidence button
        self._evidence_btn = self._create_small_button(actions_row, "Open evidence", self._open_evidence)
        self._evidence_btn.pack(side="left", padx=(SPACING.SM, 0))

        # Header separator
        tk.Frame(self._header, bg=COLORS.BORDER, height=1).pack(fill="x", side="bottom")

    def _create_small_button(self, parent, text: str, command: Callable) -> tk.Label:
        """Create a small secondary action button."""
        btn = tk.Label(
            parent,
            text=text,
            font=FONTS.BODY_SM,
            fg=COLORS.TEXT_SECONDARY,
            bg=COLORS.CHIP_BG,
            padx=10,
            pady=4,
            cursor="hand2"
        )
        btn.bind("<Button-1>", lambda e: command())
        btn.bind("<Enter>", lambda e: btn.config(bg=COLORS.SURFACE_HOVER))
        btn.bind("<Leave>", lambda e: btn.config(bg=COLORS.CHIP_BG))
        return btn

    def _build_scrollable_content(self):
        """Build the scrollable content area with all sections."""
        # Create canvas for scrolling
        self._canvas = tk.Canvas(
            self,
            bg=COLORS.SURFACE,
            highlightthickness=0,
            borderwidth=0
        )
        self._scrollbar = tk.Scrollbar(
            self,
            orient="vertical",
            command=self._canvas.yview
        )

        # Scrollable frame
        self._scroll_frame = tk.Frame(self._canvas, bg=COLORS.SURFACE)

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
        self._build_inputs_section()
        self._build_steps_section()
        self._build_checks_section()
        self._build_output_section()

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
        card = tk.Frame(section, bg=COLORS.SURFACE, highlightthickness=1, highlightbackground=COLORS.BORDER)
        card.pack(fill="x", pady=(SPACING.SM, 0))

        card_content = tk.Frame(card, bg=COLORS.SURFACE)
        card_content.pack(fill="x", padx=SPACING.MD, pady=SPACING.MD)

        # App result
        self._result_app_row = self._create_result_row(card_content, "App result", "—")

        # Excel facit
        self._result_excel_row = self._create_result_row(card_content, "Excel facit", "—")

        # Separator
        tk.Frame(card_content, bg=COLORS.BORDER, height=1).pack(fill="x", pady=SPACING.SM)

        # Delta + tolerance
        delta_row = tk.Frame(card_content, bg=COLORS.SURFACE)
        delta_row.pack(fill="x", pady=(SPACING.XS, 0))

        tk.Label(
            delta_row,
            text=f"{ICONS.DELTA} (diff)",
            font=FONTS.BODY_SM,
            fg=COLORS.TEXT_MUTED,
            bg=COLORS.SURFACE
        ).pack(side="left")

        self._result_delta = tk.Label(
            delta_row,
            text="0.0000",
            font=FONTS.NUMERIC,
            fg=COLORS.TEXT,
            bg=COLORS.SURFACE
        )
        self._result_delta.pack(side="right")

        # Tolerance
        tol_row = tk.Frame(card_content, bg=COLORS.SURFACE)
        tol_row.pack(fill="x", pady=(SPACING.XS, 0))

        tk.Label(
            tol_row,
            text="Tolerance",
            font=FONTS.BODY_SM,
            fg=COLORS.TEXT_MUTED,
            bg=COLORS.SURFACE
        ).pack(side="left")

        self._result_tolerance = tk.Label(
            tol_row,
            text="0.0001",
            font=FONTS.NUMERIC,
            fg=COLORS.TEXT_MUTED,
            bg=COLORS.SURFACE
        )
        self._result_tolerance.pack(side="right")

    def _create_result_row(self, parent, label: str, value: str) -> Dict[str, tk.Label]:
        """Create a result row with label and value."""
        row = tk.Frame(parent, bg=COLORS.SURFACE)
        row.pack(fill="x", pady=(SPACING.XS, 0))

        lbl = tk.Label(
            row,
            text=label,
            font=FONTS.BODY_SM,
            fg=COLORS.TEXT_MUTED,
            bg=COLORS.SURFACE
        )
        lbl.pack(side="left")

        val = tk.Label(
            row,
            text=value,
            font=FONTS.NUMERIC_LG,
            fg=COLORS.TEXT,
            bg=COLORS.SURFACE
        )
        val.pack(side="right")

        return {"label": lbl, "value": val}

    def _build_inputs_section(self):
        """Build the Inputs table section."""
        section = self._create_section("Inputs")
        self._inputs_section = section

        # Container for inputs table
        self._inputs_container = tk.Frame(section, bg=COLORS.SURFACE)
        self._inputs_container.pack(fill="x", pady=(SPACING.SM, 0))

    def _build_steps_section(self):
        """Build the Calculation steps section."""
        section = self._create_section("Calculation Steps")
        self._steps_section = section

        # Container for steps list
        self._steps_container = tk.Frame(section, bg=COLORS.SURFACE)
        self._steps_container.pack(fill="x", pady=(SPACING.SM, 0))

    def _build_checks_section(self):
        """Build the Per-tenor checks section."""
        section = self._create_section("Validation Checks")
        self._checks_section = section

        # Container for checks list
        self._checks_container = tk.Frame(section, bg=COLORS.SURFACE)
        self._checks_container.pack(fill="x", pady=(SPACING.SM, 0))

    def _build_output_section(self):
        """Build the Output mapping section."""
        section = self._create_section("Output Mapping")
        self._output_section = section

        # Container for output mapping
        self._output_container = tk.Frame(section, bg=COLORS.SURFACE)
        self._output_container.pack(fill="x", pady=(SPACING.SM, 0))

    def _create_section(self, title: str) -> tk.Frame:
        """Create a section container with title."""
        section = tk.Frame(self._scroll_frame, bg=COLORS.SURFACE)
        section.pack(fill="x", padx=SPACING.LG, pady=(SPACING.LG, 0))

        # Section title
        tk.Label(
            section,
            text=title,
            font=FONTS.TABLE_HEADER,
            fg=COLORS.TEXT_MUTED,
            bg=COLORS.SURFACE,
            anchor="w"
        ).pack(fill="x")

        return section

    def _build_footer(self):
        """Build sticky footer with timestamp and re-run button."""
        if CTK_AVAILABLE:
            self._footer = ctk.CTkFrame(self, fg_color=COLORS.SURFACE, corner_radius=0)
        else:
            self._footer = tk.Frame(self, bg=COLORS.SURFACE)
        self._footer.pack(fill="x", side="bottom")

        # Footer separator
        tk.Frame(self._footer, bg=COLORS.BORDER, height=1).pack(fill="x", side="top")

        # Footer content
        footer_content = tk.Frame(self._footer, bg=COLORS.SURFACE)
        footer_content.pack(fill="x", padx=SPACING.LG, pady=SPACING.MD)

        # Last validated timestamp
        self._last_validated = tk.Label(
            footer_content,
            text="Last validated: —",
            font=FONTS.BODY_SM,
            fg=COLORS.TEXT_MUTED,
            bg=COLORS.SURFACE
        )
        self._last_validated.pack(side="left")

        # Re-run button
        if CTK_AVAILABLE:
            self._rerun_btn = ctk.CTkButton(
                footer_content,
                text="Re-run checks",
                font=FONTS.BUTTON_SM,
                fg_color=COLORS.CHIP_BG,
                text_color=COLORS.TEXT_SECONDARY,
                hover_color=COLORS.SURFACE_HOVER,
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
                fg=COLORS.TEXT_SECONDARY,
                bg=COLORS.CHIP_BG,
                activebackground=COLORS.SURFACE_HOVER,
                activeforeground=COLORS.TEXT,
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
        self._update_inputs_section(tenor_key, data)
        self._update_steps_section(data)
        self._update_checks_section(data)
        self._update_output_section(tenor_key, data)

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
            self._evidence_btn.config(fg=COLORS.TEXT_SECONDARY, cursor="hand2")
        else:
            self._evidence_btn.config(fg=COLORS.TEXT_PLACEHOLDER, cursor="arrow")

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
            self._result_delta.config(text="—", fg=COLORS.TEXT_MUTED)

        # Tolerance
        self._result_tolerance.config(text="0.0001")

    def _update_inputs_section(self, tenor_key: str, data: Dict[str, Any]):
        """Update the inputs table with field values and sources."""
        # Clear existing
        for widget in self._inputs_container.winfo_children():
            widget.destroy()

        # Create table
        table = tk.Frame(self._inputs_container, bg=COLORS.SURFACE)
        table.pack(fill="x")

        # Header
        header = tk.Frame(table, bg=COLORS.TABLE_HEADER_BG)
        header.pack(fill="x")

        for col, (text, width) in enumerate([("Field", 100), ("Value", 80), ("Source", 120)]):
            tk.Label(
                header,
                text=text,
                font=FONTS.TABLE_HEADER,
                fg=COLORS.TEXT_MUTED,
                bg=COLORS.TABLE_HEADER_BG,
                width=width // 8,
                anchor="w",
                padx=SPACING.SM,
                pady=SPACING.SM
            ).pack(side="left", fill="x", expand=(col == 2))

        # Data rows
        weights = data.get("weights", {})
        rate_source = data.get("rate_label", "Bloomberg")

        # Build inputs list - include rates used for implied calculation
        inputs = [
            ("EUR Implied", f"{data.get('eur_impl', 0):.4f}%" if data.get('eur_impl') else "—", "Calculated"),
            ("USD Implied", f"{data.get('usd_impl', 0):.4f}%" if data.get('usd_impl') else "—", "Calculated"),
        ]

        # Add separator for rates used in calculation
        inputs.append(("─── Rates ───", "", ""))

        # EUR CM rate (EURIBOR) used in implied calculation
        inputs.append((
            "EUR CM (EURIBOR)",
            f"{data.get('eur_rate', 0):.4f}%" if data.get('eur_rate') else "—",
            "Bloomberg"
        ))

        # USD CM rate (SOFR) used in implied calculation
        inputs.append((
            "USD CM (SOFR)",
            f"{data.get('usd_rate', 0):.4f}%" if data.get('usd_rate') else "—",
            "Bloomberg"
        ))

        # NOK ECP rate
        inputs.append((
            "NOK ECP",
            f"{data.get('nok_cm', 0):.4f}%" if data.get('nok_cm') else "—",
            "Bloomberg"
        ))

        # Add separator for FX data
        inputs.append(("─── FX Data ───", "", ""))

        # EUR FX inputs
        inputs.append(("EUR Spot", f"{data.get('eur_spot', 0):.4f}" if data.get('eur_spot') else "—", "Bloomberg"))
        inputs.append(("EUR Pips", f"{data.get('eur_pips', 0):.2f}" if data.get('eur_pips') else "—", "Bloomberg"))
        inputs.append(("EUR Days", f"{int(data.get('eur_days', 0))}" if data.get('eur_days') else "—", "Days file"))

        # USD FX inputs
        inputs.append(("USD Spot", f"{data.get('usd_spot', 0):.4f}" if data.get('usd_spot') else "—", "Bloomberg"))
        inputs.append(("USD Pips", f"{data.get('usd_pips', 0):.2f}" if data.get('usd_pips') else "—", "Bloomberg"))
        inputs.append(("USD Days", f"{int(data.get('usd_days', 0))}" if data.get('usd_days') else "—", "Days file"))

        # Add separator for weights
        inputs.append(("─── Weights ───", "", ""))

        inputs.append(("EUR Weight", f"{weights.get('EUR', 0) * 100:.2f}%", "Weights file"))
        inputs.append(("USD Weight", f"{weights.get('USD', 0) * 100:.2f}%", "Weights file"))
        inputs.append(("NOK Weight", f"{weights.get('NOK', 0) * 100:.2f}%", "Weights file"))

        # Spread
        inputs.append(("─── Config ───", "", ""))
        inputs.append(("Spread", f"{data.get('spread', 0):.2f}%", "Config"))

        for i, (field, value, source) in enumerate(inputs):
            # Check if this is a separator row
            is_separator = field.startswith("───")

            if is_separator:
                # Separator row - section header style
                row = tk.Frame(table, bg=COLORS.TABLE_HEADER_BG)
                row.pack(fill="x", pady=(SPACING.SM, 0))

                tk.Label(
                    row,
                    text=field,
                    font=FONTS.TABLE_HEADER,
                    fg=COLORS.TEXT_MUTED,
                    bg=COLORS.TABLE_HEADER_BG,
                    anchor="w",
                    padx=SPACING.SM,
                    pady=SPACING.XS
                ).pack(side="left", fill="x", expand=True)
            else:
                # Normal data row
                row_bg = COLORS.SURFACE if i % 2 == 0 else COLORS.ROW_ZEBRA
                row = tk.Frame(table, bg=row_bg)
                row.pack(fill="x")

                tk.Label(
                    row,
                    text=field,
                    font=FONTS.BODY_SM,
                    fg=COLORS.TEXT,
                    bg=row_bg,
                    width=14,
                    anchor="w",
                    padx=SPACING.SM,
                    pady=SPACING.XS
                ).pack(side="left")

                tk.Label(
                    row,
                    text=value,
                    font=FONTS.TABLE_CELL_MONO,
                    fg=COLORS.TEXT,
                    bg=row_bg,
                    width=10,
                    anchor="e",
                    padx=SPACING.SM,
                    pady=SPACING.XS
                ).pack(side="left")

                tk.Label(
                    row,
                    text=source,
                    font=FONTS.BODY_SM,
                    fg=COLORS.TEXT_MUTED,
                    bg=row_bg,
                    anchor="w",
                    padx=SPACING.SM,
                    pady=SPACING.XS
                ).pack(side="left", fill="x", expand=True)

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
            row = tk.Frame(self._steps_container, bg=COLORS.SURFACE)
            row.pack(fill="x", pady=(SPACING.XS, 0))

            tk.Label(
                row,
                text=step_label,
                font=FONTS.BODY_SM,
                fg=COLORS.TEXT_MUTED,
                bg=COLORS.SURFACE,
                anchor="w"
            ).pack(side="left")

            tk.Label(
                row,
                text=step_calc,
                font=FONTS.TABLE_CELL_MONO,
                fg=COLORS.TEXT,
                bg=COLORS.SURFACE,
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
                fg=COLORS.TEXT_MUTED,
                bg=COLORS.SURFACE
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
            bg=COLORS.SURFACE,
            highlightthickness=1,
            highlightbackground=COLORS.BORDER
        )
        item.pack(fill="x", pady=(SPACING.XS, 0))

        # Header row (clickable)
        header = tk.Frame(item, bg=COLORS.SURFACE, cursor="hand2")
        header.pack(fill="x", padx=SPACING.SM, pady=SPACING.SM)

        # Status icon
        icon_text = ICONS.CHECK if matched else ICONS.CROSS
        icon_color = COLORS.SUCCESS if matched else COLORS.DANGER

        tk.Label(
            header,
            text=icon_text,
            font=FONTS.BODY,
            fg=icon_color,
            bg=COLORS.SURFACE
        ).pack(side="left")

        # Check name
        tk.Label(
            header,
            text=name,
            font=FONTS.BODY_SM,
            fg=COLORS.TEXT,
            bg=COLORS.SURFACE
        ).pack(side="left", padx=(SPACING.XS, 0))

        # Status text
        status_text = "PASS" if matched else "FAIL"
        tk.Label(
            header,
            text=status_text,
            font=FONTS.BUTTON_SM,
            fg=icon_color,
            bg=COLORS.SURFACE
        ).pack(side="right")

        # Details container (initially visible for failed checks)
        details = tk.Frame(item, bg=COLORS.ROW_ZEBRA)
        if not matched:
            details.pack(fill="x", padx=SPACING.SM, pady=(0, SPACING.SM))

        # Observed vs Expected
        if gui_value is not None:
            tk.Label(
                details,
                text=f"Observed: {gui_value:.4f}",
                font=FONTS.TABLE_CELL_MONO,
                fg=COLORS.TEXT,
                bg=COLORS.ROW_ZEBRA,
                padx=SPACING.SM,
                pady=SPACING.XS
            ).pack(anchor="w")

        if excel_value is not None:
            tk.Label(
                details,
                text=f"Expected: {excel_value:.4f}",
                font=FONTS.TABLE_CELL_MONO,
                fg=COLORS.TEXT,
                bg=COLORS.ROW_ZEBRA,
                padx=SPACING.SM,
                pady=SPACING.XS
            ).pack(anchor="w")

        if description:
            tk.Label(
                details,
                text=f"({description})",
                font=FONTS.BODY_SM,
                fg=COLORS.TEXT_MUTED,
                bg=COLORS.ROW_ZEBRA,
                padx=SPACING.SM,
                pady=SPACING.XS
            ).pack(anchor="w")

        # Toggle details on click
        def toggle_details(e):
            if details.winfo_manager():
                details.pack_forget()
            else:
                details.pack(fill="x", padx=SPACING.SM, pady=(0, SPACING.SM))

        header.bind("<Button-1>", toggle_details)
        for child in header.winfo_children():
            child.bind("<Button-1>", toggle_details)

    def _update_output_section(self, tenor_key: str, data: Dict[str, Any]):
        """Update the output mapping section."""
        # Clear existing
        for widget in self._output_container.winfo_children():
            widget.destroy()

        final_rate = data.get("final_rate")
        match_data = data.get("match_data", {})
        criteria = match_data.get("criteria", [])

        # Output file info
        info_frame = tk.Frame(self._output_container, bg=COLORS.SURFACE)
        info_frame.pack(fill="x")

        # Get Excel cell info from criteria
        excel_cell = None
        excel_value = None
        for criterion in criteria:
            if criterion.get("excel_cell"):
                excel_cell = criterion.get("excel_cell")
                excel_value = criterion.get("excel_value")
                break

        output_info = [
            ("Tenor key", tenor_key.upper()),
            ("Output cell", excel_cell or "—"),
            ("Written value", f"{final_rate:.4f}%" if final_rate else "—"),
            ("Expected facit", f"{excel_value:.4f}%" if excel_value else "—"),
        ]

        for label, value in output_info:
            row = tk.Frame(info_frame, bg=COLORS.SURFACE)
            row.pack(fill="x", pady=(SPACING.XS, 0))

            tk.Label(
                row,
                text=label,
                font=FONTS.BODY_SM,
                fg=COLORS.TEXT_MUTED,
                bg=COLORS.SURFACE
            ).pack(side="left")

            tk.Label(
                row,
                text=value,
                font=FONTS.TABLE_CELL_MONO,
                fg=COLORS.TEXT,
                bg=COLORS.SURFACE
            ).pack(side="right")

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
