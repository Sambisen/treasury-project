"""
Theme Preview Page - Nordic Light Design System
================================================
Demo page showing all components in the design system.
"""

import tkinter as tk
from tkinter import ttk

from .theme import (
    COLORS, FONTS, SPACING, ICONS, COMPONENTS,
    apply_matplotlib_theme, apply_ttk_theme
)
from .components import (
    # Buttons
    PrimaryButton, SecondaryButton, GhostButton, DangerButton, IconButton,
    # Cards
    Card, CardHeader, MetricCard, InfoCard,
    # Badges
    Badge, StatusBadge, CountBadge, MatchedBadge, EnvironmentBadge,
    # Tables
    ThemedTable, SimpleTable,
    # Navigation
    SidebarNav, NavItem, NavSection,
    # Modals
    show_info, show_warning, show_error, show_success, ask_confirm, ask_input,
    # Status
    StatusStrip, StatusChip, ConnectionIndicator, ModeIndicator,
    # Inputs
    ThemedEntry, ThemedCombobox, ThemedCheckbox, ThemedRadioGroup,
    # App Shell
    PageContainer, PageHeader, TabContainer, ScrollableFrame,
)


class ThemePreviewPage(tk.Frame):
    """
    Preview page demonstrating all Nordic Light design system components.
    """

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=COLORS.BG, **kwargs)

        # Apply theme
        apply_ttk_theme(self)

        # Main scrollable container
        scroll_frame = ScrollableFrame(self)
        scroll_frame.pack(fill="both", expand=True)

        content = scroll_frame.content

        # Page header
        header = PageHeader(
            content,
            title="Nordic Light Design System",
            description="Component preview and documentation"
        )
        header.pack(fill="x", pady=(0, SPACING.XL))

        # Color palette section
        self._build_color_section(content)

        # Typography section
        self._build_typography_section(content)

        # Button section
        self._build_button_section(content)

        # Badge section
        self._build_badge_section(content)

        # Card section
        self._build_card_section(content)

        # Input section
        self._build_input_section(content)

        # Table section
        self._build_table_section(content)

        # Status section
        self._build_status_section(content)

        # Modal section
        self._build_modal_section(content)

    def _build_section_header(self, parent, title: str):
        """Build a section header."""
        frame = tk.Frame(parent, bg=COLORS.BG)
        frame.pack(fill="x", pady=(SPACING.XL, SPACING.MD))

        tk.Label(
            frame,
            text=title,
            fg=COLORS.TEXT,
            bg=COLORS.BG,
            font=FONTS.H2
        ).pack(anchor="w")

        tk.Frame(frame, bg=COLORS.BORDER, height=1).pack(fill="x", pady=(SPACING.SM, 0))

        return frame

    def _build_color_section(self, parent):
        """Build color palette preview."""
        self._build_section_header(parent, "Color Palette")

        colors_frame = tk.Frame(parent, bg=COLORS.BG)
        colors_frame.pack(fill="x")

        # Color swatches
        color_groups = [
            ("Backgrounds", [
                ("BG", COLORS.BG),
                ("Surface", COLORS.SURFACE),
                ("Surface Hover", COLORS.SURFACE_HOVER),
                ("Nav BG", COLORS.NAV_BG),
            ]),
            ("Brand", [
                ("Accent", COLORS.ACCENT),
                ("Accent Hover", COLORS.ACCENT_HOVER),
                ("Accent Light", COLORS.ACCENT_LIGHT),
            ]),
            ("Text", [
                ("Primary", COLORS.TEXT),
                ("Secondary", COLORS.TEXT_SECONDARY),
                ("Muted", COLORS.TEXT_MUTED),
                ("Placeholder", COLORS.TEXT_PLACEHOLDER),
            ]),
            ("Status", [
                ("Success", COLORS.SUCCESS),
                ("Warning", COLORS.WARNING),
                ("Danger", COLORS.DANGER),
                ("Info", COLORS.INFO),
            ]),
        ]

        for group_name, colors in color_groups:
            group_frame = tk.Frame(colors_frame, bg=COLORS.BG)
            group_frame.pack(side="left", padx=(0, SPACING.XL), anchor="n")

            tk.Label(
                group_frame,
                text=group_name,
                fg=COLORS.TEXT_MUTED,
                bg=COLORS.BG,
                font=FONTS.LABEL_CAPS
            ).pack(anchor="w", pady=(0, SPACING.SM))

            for name, color in colors:
                swatch_row = tk.Frame(group_frame, bg=COLORS.BG)
                swatch_row.pack(fill="x", pady=2)

                # Color swatch
                swatch = tk.Frame(
                    swatch_row,
                    bg=color,
                    width=24,
                    height=24,
                    highlightbackground=COLORS.BORDER,
                    highlightthickness=1
                )
                swatch.pack(side="left")
                swatch.pack_propagate(False)

                # Color name and hex
                tk.Label(
                    swatch_row,
                    text=f"{name}",
                    fg=COLORS.TEXT,
                    bg=COLORS.BG,
                    font=FONTS.BODY_SM,
                    width=12,
                    anchor="w"
                ).pack(side="left", padx=(SPACING.SM, 0))

                tk.Label(
                    swatch_row,
                    text=color,
                    fg=COLORS.TEXT_MUTED,
                    bg=COLORS.BG,
                    font=FONTS.MONO_SM
                ).pack(side="left")

    def _build_typography_section(self, parent):
        """Build typography preview."""
        self._build_section_header(parent, "Typography")

        type_frame = tk.Frame(parent, bg=COLORS.BG)
        type_frame.pack(fill="x")

        type_samples = [
            ("H1", FONTS.H1, "Page Title"),
            ("H2", FONTS.H2, "Section Header"),
            ("H3", FONTS.H3, "Card Title"),
            ("H4", FONTS.H4, "Subsection"),
            ("Body", FONTS.BODY, "Body text for paragraphs and descriptions"),
            ("Body Small", FONTS.BODY_SM, "Smaller body text for captions"),
            ("Mono", FONTS.MONO, "1,234.56789"),
            ("Label", FONTS.LABEL, "Field Label"),
            ("Label Caps", FONTS.LABEL_CAPS, "SECTION LABEL"),
        ]

        for name, font, sample in type_samples:
            row = tk.Frame(type_frame, bg=COLORS.BG)
            row.pack(fill="x", pady=4)

            tk.Label(
                row,
                text=name,
                fg=COLORS.TEXT_MUTED,
                bg=COLORS.BG,
                font=FONTS.BODY_SM,
                width=12,
                anchor="w"
            ).pack(side="left")

            tk.Label(
                row,
                text=sample,
                fg=COLORS.TEXT,
                bg=COLORS.BG,
                font=font
            ).pack(side="left")

    def _build_button_section(self, parent):
        """Build button preview."""
        self._build_section_header(parent, "Buttons")

        btn_frame = tk.Frame(parent, bg=COLORS.BG)
        btn_frame.pack(fill="x")

        # Row 1: Primary variants
        row1 = tk.Frame(btn_frame, bg=COLORS.BG)
        row1.pack(fill="x", pady=SPACING.SM)

        PrimaryButton(row1, text="Primary", command=lambda: None).pack(side="left", padx=(0, SPACING.SM))
        SecondaryButton(row1, text="Secondary", command=lambda: None).pack(side="left", padx=(0, SPACING.SM))
        GhostButton(row1, text="Ghost", command=lambda: None).pack(side="left", padx=(0, SPACING.SM))
        DangerButton(row1, text="Danger", command=lambda: None).pack(side="left", padx=(0, SPACING.SM))

        # Row 2: Sizes
        row2 = tk.Frame(btn_frame, bg=COLORS.BG)
        row2.pack(fill="x", pady=SPACING.SM)

        PrimaryButton(row2, text="Small", size="sm", command=lambda: None).pack(side="left", padx=(0, SPACING.SM))
        PrimaryButton(row2, text="Medium", size="md", command=lambda: None).pack(side="left", padx=(0, SPACING.SM))
        PrimaryButton(row2, text="Large", size="lg", command=lambda: None).pack(side="left", padx=(0, SPACING.SM))

        # Row 3: With icons
        row3 = tk.Frame(btn_frame, bg=COLORS.BG)
        row3.pack(fill="x", pady=SPACING.SM)

        PrimaryButton(row3, text="Refresh", icon=ICONS.REFRESH, command=lambda: None).pack(side="left", padx=(0, SPACING.SM))
        SecondaryButton(row3, text="Settings", icon=ICONS.SETTINGS, command=lambda: None).pack(side="left", padx=(0, SPACING.SM))
        GhostButton(row3, text="Export", icon=ICONS.EXPORT, command=lambda: None).pack(side="left", padx=(0, SPACING.SM))

        # Row 4: Icon buttons
        row4 = tk.Frame(btn_frame, bg=COLORS.BG)
        row4.pack(fill="x", pady=SPACING.SM)

        tk.Label(row4, text="Icon buttons:", fg=COLORS.TEXT_MUTED, bg=COLORS.BG, font=FONTS.BODY_SM).pack(side="left", padx=(0, SPACING.SM))
        IconButton(row4, icon=ICONS.REFRESH, command=lambda: None).pack(side="left", padx=4)
        IconButton(row4, icon=ICONS.SETTINGS, command=lambda: None).pack(side="left", padx=4)
        IconButton(row4, icon=ICONS.CLOSE, command=lambda: None).pack(side="left", padx=4)
        IconButton(row4, icon=ICONS.CHART_LINE, command=lambda: None).pack(side="left", padx=4)

        # Row 5: Disabled
        row5 = tk.Frame(btn_frame, bg=COLORS.BG)
        row5.pack(fill="x", pady=SPACING.SM)

        PrimaryButton(row5, text="Disabled", disabled=True, command=lambda: None).pack(side="left", padx=(0, SPACING.SM))
        SecondaryButton(row5, text="Disabled", disabled=True, command=lambda: None).pack(side="left", padx=(0, SPACING.SM))

    def _build_badge_section(self, parent):
        """Build badge preview."""
        self._build_section_header(parent, "Badges & Status")

        badge_frame = tk.Frame(parent, bg=COLORS.BG)
        badge_frame.pack(fill="x")

        # Row 1: Badge variants
        row1 = tk.Frame(badge_frame, bg=COLORS.BG)
        row1.pack(fill="x", pady=SPACING.SM)

        tk.Label(row1, text="Badges:", fg=COLORS.TEXT_MUTED, bg=COLORS.BG, font=FONTS.BODY_SM, width=10, anchor="w").pack(side="left")
        Badge(row1, text="Default").pack(side="left", padx=4)
        Badge(row1, text="Primary", variant="primary").pack(side="left", padx=4)
        Badge(row1, text="Success", variant="success").pack(side="left", padx=4)
        Badge(row1, text="Warning", variant="warning").pack(side="left", padx=4)
        Badge(row1, text="Danger", variant="danger").pack(side="left", padx=4)

        # Row 2: Status badges
        row2 = tk.Frame(badge_frame, bg=COLORS.BG)
        row2.pack(fill="x", pady=SPACING.SM)

        tk.Label(row2, text="Status:", fg=COLORS.TEXT_MUTED, bg=COLORS.BG, font=FONTS.BODY_SM, width=10, anchor="w").pack(side="left")
        StatusBadge(row2, text="Online", status="online").pack(side="left", padx=4)
        StatusBadge(row2, text="Offline", status="offline").pack(side="left", padx=4)
        StatusBadge(row2, text="Pending", status="pending").pack(side="left", padx=4)
        StatusBadge(row2, text="Error", status="error").pack(side="left", padx=4)

        # Row 3: Count badges
        row3 = tk.Frame(badge_frame, bg=COLORS.BG)
        row3.pack(fill="x", pady=SPACING.SM)

        tk.Label(row3, text="Counts:", fg=COLORS.TEXT_MUTED, bg=COLORS.BG, font=FONTS.BODY_SM, width=10, anchor="w").pack(side="left")
        CountBadge(row3, count=5).pack(side="left", padx=4)
        CountBadge(row3, count=42, variant="accent").pack(side="left", padx=4)
        CountBadge(row3, count=99, variant="danger").pack(side="left", padx=4)
        CountBadge(row3, count=150).pack(side="left", padx=4)

        # Row 4: Special badges
        row4 = tk.Frame(badge_frame, bg=COLORS.BG)
        row4.pack(fill="x", pady=SPACING.SM)

        tk.Label(row4, text="Special:", fg=COLORS.TEXT_MUTED, bg=COLORS.BG, font=FONTS.BODY_SM, width=10, anchor="w").pack(side="left")
        MatchedBadge(row4, matched=True).pack(side="left", padx=4)
        MatchedBadge(row4, matched=False).pack(side="left", padx=4)
        EnvironmentBadge(row4, environment="TEST").pack(side="left", padx=4)
        EnvironmentBadge(row4, environment="PROD").pack(side="left", padx=4)

    def _build_card_section(self, parent):
        """Build card preview."""
        self._build_section_header(parent, "Cards")

        cards_frame = tk.Frame(parent, bg=COLORS.BG)
        cards_frame.pack(fill="x")

        # Row of metric cards
        metrics_row = tk.Frame(cards_frame, bg=COLORS.BG)
        metrics_row.pack(fill="x", pady=SPACING.SM)

        MetricCard(metrics_row, label="NIBOR 1M", value="4.2500%", variant="default").pack(side="left", padx=(0, SPACING.SM))
        MetricCard(metrics_row, label="Change", value="+0.125%", variant="success").pack(side="left", padx=(0, SPACING.SM))
        MetricCard(metrics_row, label="Spread", value="-0.050%", variant="danger").pack(side="left", padx=(0, SPACING.SM))
        MetricCard(metrics_row, label="Volume", value="1.2M", sublabel="NOK", variant="accent").pack(side="left", padx=(0, SPACING.SM))

        # Info cards
        info_row = tk.Frame(cards_frame, bg=COLORS.BG)
        info_row.pack(fill="x", pady=SPACING.SM)

        InfoCard(info_row, message="This is an info message", title="Information", variant="info").pack(fill="x", pady=4)
        InfoCard(info_row, message="Operation completed successfully", title="Success", variant="success").pack(fill="x", pady=4)
        InfoCard(info_row, message="Please review before continuing", title="Warning", variant="warning").pack(fill="x", pady=4)
        InfoCard(info_row, message="An error occurred during processing", title="Error", variant="danger").pack(fill="x", pady=4)

    def _build_input_section(self, parent):
        """Build input preview."""
        self._build_section_header(parent, "Form Inputs")

        inputs_frame = tk.Frame(parent, bg=COLORS.BG)
        inputs_frame.pack(fill="x")

        # Row 1: Text entry
        row1 = tk.Frame(inputs_frame, bg=COLORS.BG)
        row1.pack(fill="x", pady=SPACING.SM)

        entry1 = ThemedEntry(row1, label="Text Input", placeholder="Enter value...")
        entry1.pack(side="left", padx=(0, SPACING.MD), fill="x", expand=True)

        entry2 = ThemedEntry(row1, label="With Value")
        entry2.set("Sample text")
        entry2.pack(side="left", padx=(0, SPACING.MD), fill="x", expand=True)

        # Row 2: Combobox
        row2 = tk.Frame(inputs_frame, bg=COLORS.BG)
        row2.pack(fill="x", pady=SPACING.SM)

        combo = ThemedCombobox(row2, label="Select Tenor", values=["1W", "1M", "2M", "3M", "6M"], default="1M")
        combo.pack(side="left", padx=(0, SPACING.MD))

        # Row 3: Checkboxes
        row3 = tk.Frame(inputs_frame, bg=COLORS.BG)
        row3.pack(fill="x", pady=SPACING.SM)

        ThemedCheckbox(row3, text="Option 1", checked=True).pack(side="left", padx=(0, SPACING.MD))
        ThemedCheckbox(row3, text="Option 2", checked=False).pack(side="left", padx=(0, SPACING.MD))
        ThemedCheckbox(row3, text="Option 3", checked=True).pack(side="left", padx=(0, SPACING.MD))

        # Row 4: Radio group
        row4 = tk.Frame(inputs_frame, bg=COLORS.BG)
        row4.pack(fill="x", pady=SPACING.SM)

        ThemedRadioGroup(
            row4,
            label="Select Mode",
            options=["Production", "Test", "Development"],
            default="Test",
            orientation="horizontal"
        ).pack(side="left")

    def _build_table_section(self, parent):
        """Build table preview."""
        self._build_section_header(parent, "Tables")

        table_frame = tk.Frame(parent, bg=COLORS.BG)
        table_frame.pack(fill="x")

        # Themed table
        columns = [
            {"id": "tenor", "heading": "Tenor", "width": 80},
            {"id": "rate", "heading": "Rate", "width": 100, "anchor": "e"},
            {"id": "change", "heading": "Change", "width": 100, "anchor": "e"},
            {"id": "status", "heading": "Status", "width": 100},
        ]

        table = ThemedTable(table_frame, columns=columns)
        table.pack(fill="x", pady=SPACING.SM)

        # Sample data
        data = [
            ("1W", "4.2500", "+0.125", "OK"),
            ("1M", "4.3750", "+0.250", "OK"),
            ("2M", "4.5000", "-0.125", "CHECK"),
            ("3M", "4.6250", "+0.000", "OK"),
            ("6M", "4.8750", "+0.375", "OK"),
        ]

        for row in data:
            tag = "good" if row[3] == "OK" else "warning"
            table.insert_row(row, tag=tag)

    def _build_status_section(self, parent):
        """Build status indicator preview."""
        self._build_section_header(parent, "Status Indicators")

        status_frame = tk.Frame(parent, bg=COLORS.BG)
        status_frame.pack(fill="x")

        # Connection indicators
        row1 = tk.Frame(status_frame, bg=COLORS.BG)
        row1.pack(fill="x", pady=SPACING.SM)

        tk.Label(row1, text="Connections:", fg=COLORS.TEXT_MUTED, bg=COLORS.BG, font=FONTS.BODY_SM, width=12, anchor="w").pack(side="left")
        ConnectionIndicator(row1, label="Bloomberg", connected=True).pack(side="left", padx=(0, SPACING.MD))
        ConnectionIndicator(row1, label="Excel", connected=True).pack(side="left", padx=(0, SPACING.MD))
        ConnectionIndicator(row1, label="Database", connected=False).pack(side="left", padx=(0, SPACING.MD))

        # Status chips
        row2 = tk.Frame(status_frame, bg=COLORS.BG)
        row2.pack(fill="x", pady=SPACING.SM)

        tk.Label(row2, text="Chips:", fg=COLORS.TEXT_MUTED, bg=COLORS.BG, font=FONTS.BODY_SM, width=12, anchor="w").pack(side="left")
        StatusChip(row2, text="Active", status="success").pack(side="left", padx=4)
        StatusChip(row2, text="Pending", status="warning").pack(side="left", padx=4)
        StatusChip(row2, text="Failed", status="danger").pack(side="left", padx=4)
        StatusChip(row2, text="Info", status="info").pack(side="left", padx=4)

        # Mode indicators
        row3 = tk.Frame(status_frame, bg=COLORS.BG)
        row3.pack(fill="x", pady=SPACING.SM)

        tk.Label(row3, text="Mode:", fg=COLORS.TEXT_MUTED, bg=COLORS.BG, font=FONTS.BODY_SM, width=12, anchor="w").pack(side="left")
        ModeIndicator(row3, mode="TEST").pack(side="left", padx=4)
        ModeIndicator(row3, mode="PROD").pack(side="left", padx=4)

    def _build_modal_section(self, parent):
        """Build modal preview with trigger buttons."""
        self._build_section_header(parent, "Modals & Dialogs")

        modal_frame = tk.Frame(parent, bg=COLORS.BG)
        modal_frame.pack(fill="x")

        row = tk.Frame(modal_frame, bg=COLORS.BG)
        row.pack(fill="x", pady=SPACING.SM)

        PrimaryButton(
            row,
            text="Info Modal",
            command=lambda: show_info(self, "Information", "This is an informational message.")
        ).pack(side="left", padx=(0, SPACING.SM))

        SecondaryButton(
            row,
            text="Warning Modal",
            command=lambda: show_warning(self, "Warning", "This action may have consequences.")
        ).pack(side="left", padx=(0, SPACING.SM))

        DangerButton(
            row,
            text="Error Modal",
            command=lambda: show_error(self, "Error", "Something went wrong during the operation.")
        ).pack(side="left", padx=(0, SPACING.SM))

        GhostButton(
            row,
            text="Success Modal",
            command=lambda: show_success(self, "Success", "The operation completed successfully!")
        ).pack(side="left", padx=(0, SPACING.SM))

        row2 = tk.Frame(modal_frame, bg=COLORS.BG)
        row2.pack(fill="x", pady=SPACING.SM)

        SecondaryButton(
            row2,
            text="Confirm Dialog",
            command=lambda: self._show_confirm_result(ask_confirm(self, "Confirm Action", "Are you sure you want to proceed?"))
        ).pack(side="left", padx=(0, SPACING.SM))

        SecondaryButton(
            row2,
            text="Input Dialog",
            command=lambda: self._show_input_result(ask_input(self, "Enter Value", "Please enter a name:", "Default"))
        ).pack(side="left", padx=(0, SPACING.SM))

    def _show_confirm_result(self, result):
        """Show confirm dialog result."""
        if result:
            show_success(self, "Confirmed", "You clicked confirm!")
        else:
            show_info(self, "Cancelled", "You clicked cancel.")

    def _show_input_result(self, result):
        """Show input dialog result."""
        if result:
            show_success(self, "Input Received", f"You entered: {result}")
        else:
            show_info(self, "Cancelled", "Input was cancelled.")


def launch_preview():
    """Launch the theme preview as a standalone window."""
    root = tk.Tk()
    root.title("Nordic Light Design System - Preview")
    root.geometry("1200x900")
    root.configure(bg=COLORS.BG)

    preview = ThemePreviewPage(root)
    preview.pack(fill="both", expand=True, padx=SPACING.PAGE_PADDING, pady=SPACING.PAGE_PADDING)

    root.mainloop()


if __name__ == "__main__":
    launch_preview()
