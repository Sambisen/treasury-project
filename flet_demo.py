"""
Flet Demo - NIBOR Dashboard
===========================
Detta visar hur din nuvarande Tkinter-dashboard skulle se ut i Flet.
Kör med: flet run flet_demo.py

Installation: pip install flet
"""

import flet as ft

# Nordic Light Design Tokens (samma som din theme.py)
class Colors:
    BG = "#F6F7F9"
    SURFACE = "#FFFFFF"
    ACCENT = "#F57C00"
    ACCENT_HOVER = "#E65100"
    ACCENT_LIGHT = "#FFF3E0"
    TEXT = "#0F172A"
    TEXT_MUTED = "#475569"
    TEXT_LIGHT = "#94A3B8"
    BORDER = "#E6E8EE"
    SUCCESS = "#1E8E3E"
    DANGER = "#D93025"
    ROW_HOVER = "#F1F5F9"
    NAV_BG = "#FFFFFF"
    NAV_ACTIVE = "#FFF3E0"


def main(page: ft.Page):
    # Page configuration
    page.title = "NIBOR Calculation Terminal"
    page.bgcolor = Colors.BG
    page.padding = 0
    page.window.width = 1200
    page.window.height = 800

    # Sample data
    rates_data = [
        {"tenor": "1M", "funding": "4.5625", "spread": "+0.08", "nibor": "4.6425", "chg": "+0.02", "contrib": "4.6425"},
        {"tenor": "2M", "funding": "4.5750", "spread": "+0.10", "nibor": "4.6750", "chg": "-0.01", "contrib": "4.6750"},
        {"tenor": "3M", "funding": "4.5875", "spread": "+0.12", "nibor": "4.7075", "chg": "+0.03", "contrib": "4.7075"},
        {"tenor": "6M", "funding": "4.6125", "spread": "+0.15", "nibor": "4.7625", "chg": "0.00", "contrib": "4.7625"},
    ]

    # =========================================================================
    # SIDEBAR NAVIGATION (Command Center)
    # =========================================================================
    def nav_button(icon: str, label: str, active: bool = False):
        return ft.Container(
            content=ft.Row([
                ft.Text(icon, size=16),
                ft.Text(label, size=13, weight=ft.FontWeight.W_500 if active else ft.FontWeight.NORMAL),
            ], spacing=12),
            padding=ft.padding.symmetric(horizontal=16, vertical=12),
            border_radius=8,
            bgcolor=Colors.NAV_ACTIVE if active else None,
            ink=True,
            on_hover=lambda e: setattr(e.control, 'bgcolor', Colors.ROW_HOVER if e.data == "true" and not active else (Colors.NAV_ACTIVE if active else None)) or page.update(),
        )

    sidebar = ft.Container(
        content=ft.Column([
            # Logo/Title
            ft.Container(
                content=ft.Text("NIBOR Terminal", size=16, weight=ft.FontWeight.BOLD, color=Colors.TEXT),
                padding=ft.padding.all(20),
            ),
            ft.Divider(height=1, color=Colors.BORDER),

            # Navigation items
            ft.Container(
                content=ft.Column([
                    nav_button("📊", "NIBOR", active=True),
                    nav_button("📝", "Meta Data"),
                    nav_button("📡", "Bloomberg"),
                    nav_button("✅", "Nibor Recon"),
                    nav_button("⚖️", "Weights"),
                    nav_button("🧮", "Backup Nibor"),
                    nav_button("🔀", "Nibor Roadmap"),
                    nav_button("📋", "Audit Log"),
                ], spacing=4),
                padding=ft.padding.all(12),
            ),

            # Spacer
            ft.Container(expand=True),

            # Quick Access
            ft.Container(
                content=ft.Column([
                    ft.Text("QUICK ACCESS", size=10, color=Colors.TEXT_LIGHT, weight=ft.FontWeight.W_600),
                    ft.TextButton("📁 History folder", style=ft.ButtonStyle(color=Colors.TEXT_MUTED)),
                    ft.TextButton("📁 GRSS folder", style=ft.ButtonStyle(color=Colors.TEXT_MUTED)),
                ], spacing=4),
                padding=ft.padding.all(16),
            ),
        ], spacing=0),
        width=220,
        bgcolor=Colors.NAV_BG,
        border=ft.border.only(right=ft.BorderSide(1, Colors.BORDER)),
    )

    # =========================================================================
    # HEADER
    # =========================================================================
    header = ft.Container(
        content=ft.Row([
            # Environment badge
            ft.Container(
                content=ft.Row([
                    ft.Container(
                        width=8, height=8,
                        border_radius=4,
                        bgcolor=Colors.SUCCESS,
                    ),
                    ft.Text("PROD", size=11, weight=ft.FontWeight.W_600, color=Colors.SUCCESS),
                ], spacing=6),
                padding=ft.padding.symmetric(horizontal=12, vertical=6),
                border_radius=20,
                bgcolor=Colors.SURFACE,
                border=ft.border.all(1, Colors.BORDER),
            ),

            # Spacer
            ft.Container(expand=True),

            # Fixing time toggle (SegmentedButton)
            ft.Container(
                content=ft.Row([
                    ft.Container(
                        content=ft.Text("11:00", size=12, color=Colors.SURFACE),
                        padding=ft.padding.symmetric(horizontal=16, vertical=8),
                        bgcolor=Colors.ACCENT,
                        border_radius=ft.border_radius.only(top_left=6, bottom_left=6),
                    ),
                    ft.Container(
                        content=ft.Text("12:00", size=12, color=Colors.TEXT_MUTED),
                        padding=ft.padding.symmetric(horizontal=16, vertical=8),
                        bgcolor=Colors.SURFACE,
                        border=ft.border.all(1, Colors.BORDER),
                        border_radius=ft.border_radius.only(top_right=6, bottom_right=6),
                    ),
                ], spacing=0),
            ),

            # Clock
            ft.Container(
                content=ft.Text("14:32:45", size=13, font_family="Consolas", color=Colors.TEXT_MUTED),
                padding=ft.padding.only(left=20),
            ),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        padding=ft.padding.symmetric(horizontal=24, vertical=12),
        bgcolor=Colors.SURFACE,
        border=ft.border.only(bottom=ft.BorderSide(1, Colors.BORDER)),
    )

    # =========================================================================
    # NIBOR RATES CARD (Main Dashboard Content)
    # =========================================================================

    def create_table_row(data: dict, is_header: bool = False):
        """Create a table row with hover effect."""

        def get_change_color(val: str) -> str:
            if val.startswith("+"):
                return Colors.SUCCESS
            elif val.startswith("-"):
                return Colors.DANGER
            return Colors.TEXT_MUTED

        if is_header:
            cells = [
                ft.Text("TENOR", size=11, weight=ft.FontWeight.W_600, color=Colors.TEXT, text_align=ft.TextAlign.CENTER),
                ft.Text("FUNDING RATE", size=11, weight=ft.FontWeight.W_600, color=Colors.TEXT, text_align=ft.TextAlign.CENTER),
                ft.Text("SPREAD", size=11, weight=ft.FontWeight.W_600, color=Colors.TEXT, text_align=ft.TextAlign.CENTER),
                ft.Text("NIBOR", size=11, weight=ft.FontWeight.W_600, color=Colors.TEXT, text_align=ft.TextAlign.CENTER),
                ft.Text("CHG", size=11, weight=ft.FontWeight.W_600, color=Colors.TEXT, text_align=ft.TextAlign.CENTER),
                ft.VerticalDivider(width=1, color=Colors.BORDER),
                ft.Text("NIBOR Contribution", size=10, weight=ft.FontWeight.W_600, color=Colors.TEXT_MUTED, text_align=ft.TextAlign.CENTER),
            ]
            bg_color = "#F8FAFC"
        else:
            cells = [
                ft.Text(data["tenor"], size=13, weight=ft.FontWeight.W_600, color=Colors.TEXT, text_align=ft.TextAlign.CENTER),
                ft.Text(data["funding"], size=12, font_family="Consolas", color=Colors.ACCENT, text_align=ft.TextAlign.CENTER),
                ft.Text(data["spread"], size=12, font_family="Consolas", color=Colors.TEXT_MUTED, text_align=ft.TextAlign.CENTER),
                ft.Text(data["nibor"], size=12, font_family="Consolas", weight=ft.FontWeight.W_600, color=Colors.TEXT, text_align=ft.TextAlign.CENTER),
                ft.Text(data["chg"], size=12, font_family="Consolas", color=get_change_color(data["chg"]), text_align=ft.TextAlign.CENTER),
                ft.VerticalDivider(width=1, color=Colors.BORDER),
                ft.Text(data["contrib"], size=11, font_family="Consolas", color=Colors.TEXT_MUTED, text_align=ft.TextAlign.CENTER),
            ]
            bg_color = Colors.SURFACE

        row = ft.Container(
            content=ft.Row(
                cells,
                alignment=ft.MainAxisAlignment.SPACE_AROUND,
            ),
            padding=ft.padding.symmetric(vertical=14, horizontal=18),
            bgcolor=bg_color,
            border=ft.border.only(bottom=ft.BorderSide(1, Colors.BORDER)) if not is_header else None,
        )

        if not is_header:
            row.on_hover = lambda e: (
                setattr(e.control, 'bgcolor', Colors.ROW_HOVER if e.data == "true" else Colors.SURFACE),
                page.update()
            )

        return row

    # Build table
    table_rows = [create_table_row({}, is_header=True)]
    for data in rates_data:
        table_rows.append(create_table_row(data))

    nibor_card = ft.Container(
        content=ft.Column([
            # Card header
            ft.Container(
                content=ft.Row([
                    ft.Text("NIBOR RATES", size=20, weight=ft.FontWeight.W_600, color=Colors.TEXT),
                    ft.Container(expand=True),
                    ft.TextButton(
                        "View History →",
                        style=ft.ButtonStyle(color=Colors.ACCENT),
                    ),
                ]),
                padding=ft.padding.only(bottom=10),
            ),
            ft.Divider(height=1, color=Colors.BORDER),

            # Calculate button
            ft.Container(
                content=ft.ElevatedButton(
                    "Calculate NIBOR",
                    icon=ft.icons.CALCULATE,
                    style=ft.ButtonStyle(
                        bgcolor=Colors.ACCENT,
                        color=Colors.SURFACE,
                        padding=ft.padding.symmetric(horizontal=24, vertical=12),
                    ),
                ),
                padding=ft.padding.symmetric(vertical=16),
            ),

            # 1W Toggle
            ft.Container(
                content=ft.Row([
                    ft.Text("▶", size=9, color=Colors.TEXT_LIGHT),
                    ft.Text("1W", size=10, color=Colors.TEXT_LIGHT),
                    ft.Container(
                        content=ft.Text("Not Available", size=9, color=Colors.TEXT_LIGHT),
                        padding=ft.padding.symmetric(horizontal=8, vertical=2),
                        bgcolor="#EEF2F7",
                        border_radius=4,
                    ),
                ], spacing=8),
                padding=ft.padding.only(left=18, bottom=8),
            ),

            # Rates table
            ft.Container(
                content=ft.Column(table_rows, spacing=0),
                border_radius=8,
                border=ft.border.all(1, Colors.BORDER),
                clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            ),
        ], spacing=0),
        padding=ft.padding.all(24),
        bgcolor=Colors.SURFACE,
        border_radius=0,
        border=ft.border.only(left=ft.BorderSide(4, Colors.ACCENT)),  # Orange accent stripe
        margin=ft.margin.all(12),
    )

    # =========================================================================
    # STATUS BAR
    # =========================================================================
    status_bar = ft.Container(
        content=ft.Row([
            # Bloomberg status
            ft.Row([
                ft.Container(width=8, height=8, border_radius=4, bgcolor=Colors.SUCCESS),
                ft.Text("Bloomberg Connected", size=11, color=Colors.TEXT_MUTED),
            ], spacing=6),

            ft.Container(width=20),

            # Excel status
            ft.Row([
                ft.Container(width=8, height=8, border_radius=4, bgcolor=Colors.SUCCESS),
                ft.Text("Excel Connected", size=11, color=Colors.TEXT_MUTED),
            ], spacing=6),

            ft.Container(expand=True),

            # Last update
            ft.Text("Last update: 14:32:45", size=11, color=Colors.TEXT_LIGHT),
        ]),
        padding=ft.padding.symmetric(horizontal=24, vertical=8),
        bgcolor=Colors.SURFACE,
        border=ft.border.only(top=ft.BorderSide(1, Colors.BORDER)),
    )

    # =========================================================================
    # MAIN LAYOUT
    # =========================================================================
    main_content = ft.Column([
        header,
        ft.Container(
            content=nibor_card,
            expand=True,
            bgcolor=Colors.BG,
        ),
        status_bar,
    ], spacing=0, expand=True)

    page.add(
        ft.Row([
            sidebar,
            ft.Container(content=main_content, expand=True),
        ], spacing=0, expand=True)
    )


# Run the app
if __name__ == "__main__":
    # Use web mode to avoid group policy blocking desktop client
    ft.app(target=main, view=ft.AppView.WEB_BROWSER, port=8550)
