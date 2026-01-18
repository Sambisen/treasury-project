"""
Nordic Light Design System - Design Tokens
==========================================
Single source of truth for all styling in the Nibor Calculation Terminal.
Clean, enterprise Nordic Light theme with Swedbank orange accents.
"""

from dataclasses import dataclass
from typing import Tuple
import platform

# =============================================================================
# COLOR TOKENS
# =============================================================================

@dataclass(frozen=True)
class Colors:
    """Semantic color tokens for the Nordic Light theme."""

    # Backgrounds
    BG: str = "#F6F7F9"                 # Main app background (warm light gray)
    SURFACE: str = "#FFFFFF"            # Card/panel surface (white)
    SURFACE_ELEVATED: str = "#FFFFFF"   # Elevated surfaces
    SURFACE_HOVER: str = "#F1F5F9"      # Hover state background

    # Borders & Dividers
    BORDER: str = "#E6E8EE"             # Default border
    BORDER_STRONG: str = "#CBD5E1"      # Stronger border for emphasis
    BORDER_SUBTLE: str = "#F1F5F9"      # Very subtle border

    # Text
    TEXT: str = "#0F172A"               # Primary text (slate-900)
    TEXT_SECONDARY: str = "#334155"     # Secondary text (slate-700)
    TEXT_MUTED: str = "#475569"         # Muted text (slate-600)
    TEXT_PLACEHOLDER: str = "#94A3B8"   # Placeholder text (slate-400)
    TEXT_INVERSE: str = "#FFFFFF"       # Text on dark backgrounds

    # Accent (Swedbank Orange)
    ACCENT: str = "#F57C00"             # Primary accent (Swedbank orange)
    ACCENT_HOVER: str = "#E65100"       # Darker on hover
    ACCENT_LIGHT: str = "#FFF3E0"       # Light accent background
    ACCENT_MUTED: str = "#FFCC80"       # Muted accent

    # Semantic Colors
    SUCCESS: str = "#1E8E3E"            # Success green
    SUCCESS_BG: str = "#E8F5E9"         # Success background
    SUCCESS_LIGHT: str = "#C8E6C9"      # Light success

    WARNING: str = "#B45309"            # Warning amber
    WARNING_BG: str = "#FFF8E1"         # Warning background
    WARNING_LIGHT: str = "#FFE082"      # Light warning

    DANGER: str = "#D93025"             # Error/danger red
    DANGER_BG: str = "#FFEBEE"          # Danger background
    DANGER_LIGHT: str = "#FFCDD2"       # Light danger

    INFO: str = "#2563EB"               # Info blue
    INFO_BG: str = "#E3F2FD"            # Info background
    INFO_LIGHT: str = "#BBDEFB"         # Light info

    # UI Elements
    CHIP_BG: str = "#EEF2F7"            # Chip/badge background
    ROW_HOVER: str = "#F1F5F9"          # Table row hover
    ROW_ZEBRA: str = "#FAFBFC"          # Alternating row color
    TABLE_HEADER_BG: str = "#F8FAFC"    # Table header background

    # Navigation
    NAV_BG: str = "#FFFFFF"             # Sidebar background
    NAV_ACTIVE_BG: str = "#FFF3E0"      # Active nav item background
    NAV_HOVER_BG: str = "#F8FAFC"       # Nav item hover
    NAV_INDICATOR: str = "#F57C00"      # Active indicator (orange line)

    # Shadows (for reference - actual shadow values below)
    SHADOW_COLOR: str = "rgba(0, 0, 0, 0.08)"

    # Chart specific
    CHART_BG: str = "#FFFFFF"           # Chart background
    CHART_GRID: str = "#E6E8EE"         # Grid lines
    CHART_LINE_PRIMARY: str = "#F57C00" # Primary line (orange)
    CHART_LINE_SECONDARY: str = "#2563EB"  # Secondary line (blue)

    # Status indicators
    STATUS_ONLINE: str = "#1E8E3E"      # Online/connected
    STATUS_OFFLINE: str = "#94A3B8"     # Offline/disconnected
    STATUS_ERROR: str = "#D93025"       # Error state
    STATUS_PENDING: str = "#F57C00"     # Pending/loading


# Singleton instance
COLORS = Colors()


# =============================================================================
# DARK BUTTON THEME TOKENS
# =============================================================================

@dataclass(frozen=True)
class ButtonColors:
    """
    Dark theme button colors for premium CTkButton styling.
    Based on a dark card UI with orange accent.
    """

    # Background colors
    BG: str = "#0E1116"           # App background (darkest)
    CARD: str = "#121824"         # Card/panel background
    CARD_BORDER: str = "#222B3A"  # Card border

    # Text colors
    TEXT: str = "#E7ECF3"         # Primary text (light)
    TEXT_MUTED: str = "#A9B4C2"   # Muted/secondary text
    TEXT_ON_ACCENT: str = "#0B0D10"  # Dark text on accent buttons

    # Primary (Orange accent)
    PRIMARY: str = "#F37A1F"
    PRIMARY_HOVER: str = "#FF8A33"
    PRIMARY_PRESSED: str = "#D96512"

    # Danger (Red)
    DANGER: str = "#D93025"
    DANGER_HOVER: str = "#E24B41"
    DANGER_PRESSED: str = "#B8261D"

    # Secondary (Outlined/subtle)
    SECONDARY_BG: str = "#121824"
    SECONDARY_HOVER: str = "#182033"
    SECONDARY_PRESSED: str = "#0F1524"
    SECONDARY_BORDER: str = "#2A364A"

    # Ghost (Transparent)
    GHOST_HOVER: str = "#182033"
    GHOST_PRESSED: str = "#0F1524"

    # Disabled state
    DISABLED_BG: str = "#1A2232"
    DISABLED_TEXT: str = "#7C8796"
    DISABLED_BORDER: str = "#2A364A"


BUTTON_COLORS = ButtonColors()


@dataclass(frozen=True)
class ButtonConfig:
    """Button sizing and style configuration."""

    HEIGHT_SM: int = 32
    HEIGHT_MD: int = 40
    HEIGHT_LG: int = 48

    CORNER_RADIUS: int = 12

    FONT_FAMILY: str = "Segoe UI"
    FONT_SIZE: int = 13
    FONT_SIZE_SM: int = 12


BUTTON_CONFIG = ButtonConfig()


# =============================================================================
# ENVIRONMENT BADGE COLORS
# =============================================================================

@dataclass(frozen=True)
class EnvBadgeColors:
    """
    Premium environment badge colors with glow effects.
    """

    # Badge container (dark pill)
    BADGE_BG: str = "#121824"
    BADGE_BORDER: str = "#222B3A"

    # PROD colors (green)
    PROD_DOT: str = "#22C55E"
    PROD_GLOW: str = "#22C55E"
    PROD_TEXT: str = "#E7ECF3"

    # DEV colors (amber/orange)
    DEV_DOT: str = "#F59E0B"
    DEV_GLOW: str = "#F59E0B"
    DEV_TEXT: str = "#E7ECF3"

    # Animation
    PULSE_INTERVAL_MS: int = 1500
    GLOW_OPACITY_MIN: float = 0.3
    GLOW_OPACITY_MAX: float = 0.8


ENV_BADGE_COLORS = EnvBadgeColors()


# =============================================================================
# TYPOGRAPHY TOKENS
# =============================================================================

def get_system_font() -> str:
    """Get the appropriate system font for the current platform."""
    system = platform.system()
    if system == "Windows":
        return "Segoe UI"
    elif system == "Darwin":  # macOS
        return "SF Pro Display"
    else:
        return "Ubuntu"  # Linux fallback


def get_mono_font() -> str:
    """Get monospace font for numeric values."""
    system = platform.system()
    if system == "Windows":
        return "Consolas"
    elif system == "Darwin":
        return "SF Mono"
    else:
        return "Ubuntu Mono"


@dataclass(frozen=True)
class Typography:
    """Typography scale and font specifications."""

    # Font families
    FAMILY: str = get_system_font()
    FAMILY_MONO: str = get_mono_font()

    # Font sizes (in points)
    SIZE_XS: int = 10
    SIZE_SM: int = 11
    SIZE_BASE: int = 12
    SIZE_MD: int = 13
    SIZE_LG: int = 14
    SIZE_XL: int = 16
    SIZE_2XL: int = 18
    SIZE_3XL: int = 20
    SIZE_4XL: int = 24

    # Font weights (for Segoe UI: normal, semibold, bold)
    WEIGHT_NORMAL: str = ""
    WEIGHT_MEDIUM: str = ""
    WEIGHT_SEMIBOLD: str = "Semibold"
    WEIGHT_BOLD: str = "Bold"


TYPOGRAPHY = Typography()


# Font tuples for tkinter (family, size, weight)
class Fonts:
    """Pre-configured font tuples for tkinter widgets."""

    # Headings
    H1: Tuple[str, int, str] = (f"{TYPOGRAPHY.FAMILY} {TYPOGRAPHY.WEIGHT_SEMIBOLD}".strip(), TYPOGRAPHY.SIZE_3XL)
    H2: Tuple[str, int, str] = (f"{TYPOGRAPHY.FAMILY} {TYPOGRAPHY.WEIGHT_SEMIBOLD}".strip(), TYPOGRAPHY.SIZE_2XL)
    H3: Tuple[str, int, str] = (f"{TYPOGRAPHY.FAMILY} {TYPOGRAPHY.WEIGHT_SEMIBOLD}".strip(), TYPOGRAPHY.SIZE_XL)
    H4: Tuple[str, int, str] = (f"{TYPOGRAPHY.FAMILY} {TYPOGRAPHY.WEIGHT_SEMIBOLD}".strip(), TYPOGRAPHY.SIZE_LG)

    # Body text
    BODY: Tuple[str, int] = (TYPOGRAPHY.FAMILY, TYPOGRAPHY.SIZE_BASE)
    BODY_SM: Tuple[str, int] = (TYPOGRAPHY.FAMILY, TYPOGRAPHY.SIZE_SM)
    BODY_LG: Tuple[str, int] = (TYPOGRAPHY.FAMILY, TYPOGRAPHY.SIZE_MD)

    # Labels
    LABEL: Tuple[str, int] = (TYPOGRAPHY.FAMILY, TYPOGRAPHY.SIZE_SM)
    LABEL_CAPS: Tuple[str, int] = (TYPOGRAPHY.FAMILY, TYPOGRAPHY.SIZE_XS)

    # Buttons
    BUTTON: Tuple[str, int, str] = (f"{TYPOGRAPHY.FAMILY} {TYPOGRAPHY.WEIGHT_SEMIBOLD}".strip(), TYPOGRAPHY.SIZE_BASE)
    BUTTON_SM: Tuple[str, int, str] = (f"{TYPOGRAPHY.FAMILY} {TYPOGRAPHY.WEIGHT_SEMIBOLD}".strip(), TYPOGRAPHY.SIZE_SM)

    # Numeric/Data
    NUMERIC: Tuple[str, int] = (TYPOGRAPHY.FAMILY_MONO, TYPOGRAPHY.SIZE_BASE)
    NUMERIC_LG: Tuple[str, int] = (TYPOGRAPHY.FAMILY_MONO, TYPOGRAPHY.SIZE_LG)
    NUMERIC_XL: Tuple[str, int, str] = (f"{TYPOGRAPHY.FAMILY_MONO}", TYPOGRAPHY.SIZE_XL)

    # KPI/Metrics
    KPI: Tuple[str, int, str] = (f"{TYPOGRAPHY.FAMILY} {TYPOGRAPHY.WEIGHT_SEMIBOLD}".strip(), TYPOGRAPHY.SIZE_2XL)
    KPI_LABEL: Tuple[str, int] = (TYPOGRAPHY.FAMILY, TYPOGRAPHY.SIZE_SM)

    # Navigation
    NAV: Tuple[str, int] = (TYPOGRAPHY.FAMILY, TYPOGRAPHY.SIZE_BASE)
    NAV_SECTION: Tuple[str, int] = (TYPOGRAPHY.FAMILY, TYPOGRAPHY.SIZE_XS)

    # Table
    TABLE_HEADER: Tuple[str, int, str] = (f"{TYPOGRAPHY.FAMILY} {TYPOGRAPHY.WEIGHT_SEMIBOLD}".strip(), TYPOGRAPHY.SIZE_SM)
    TABLE_CELL: Tuple[str, int] = (TYPOGRAPHY.FAMILY, TYPOGRAPHY.SIZE_SM)
    TABLE_CELL_MONO: Tuple[str, int] = (TYPOGRAPHY.FAMILY_MONO, TYPOGRAPHY.SIZE_SM)


FONTS = Fonts()


# =============================================================================
# SPACING TOKENS
# =============================================================================

@dataclass(frozen=True)
class Spacing:
    """Spacing scale based on 4px baseline grid."""

    NONE: int = 0
    XXS: int = 2    # 2px
    XS: int = 4     # 4px
    SM: int = 8     # 8px
    MD: int = 12    # 12px
    LG: int = 16    # 16px
    XL: int = 20    # 20px
    XXL: int = 24   # 24px
    XXXL: int = 32  # 32px

    # Component-specific
    CARD_PADDING: int = 20
    CARD_GAP: int = 16
    SECTION_GAP: int = 24
    PAGE_PADDING: int = 24

    # Table
    TABLE_CELL_X: int = 12
    TABLE_CELL_Y: int = 10
    TABLE_ROW_HEIGHT: int = 40

    # Button
    BUTTON_X: int = 16
    BUTTON_Y: int = 10
    BUTTON_GAP: int = 8

    # Input
    INPUT_X: int = 12
    INPUT_Y: int = 10


SPACING = Spacing()


# =============================================================================
# RADIUS TOKENS
# =============================================================================

@dataclass(frozen=True)
class Radii:
    """Border radius values for consistent rounding."""

    NONE: int = 0
    SM: int = 4
    MD: int = 6
    LG: int = 8
    XL: int = 10
    XXL: int = 12
    FULL: int = 999  # Pill shape

    # Component-specific
    CARD: int = 12
    BUTTON: int = 10
    CHIP: int = 999     # Full rounded
    INPUT: int = 8
    MODAL: int = 12
    TOOLTIP: int = 6


RADII = Radii()


# =============================================================================
# SHADOW TOKENS
# =============================================================================

@dataclass(frozen=True)
class Shadows:
    """Shadow definitions (for reference, applied via CSS-like syntax or effects)."""

    # Note: tkinter doesn't support box-shadow directly
    # These are for reference and can be simulated with borders/frames
    NONE: str = "none"
    SM: str = "0 1px 2px rgba(0, 0, 0, 0.05)"
    MD: str = "0 2px 4px rgba(0, 0, 0, 0.08)"
    LG: str = "0 4px 8px rgba(0, 0, 0, 0.1)"
    XL: str = "0 8px 16px rgba(0, 0, 0, 0.12)"

    # For tkinter, we simulate with border colors
    BORDER_SHADOW: str = "#E6E8EE"  # Subtle border that gives shadow effect


SHADOWS = Shadows()


# =============================================================================
# ICON SET (Unicode/Text-based for cross-platform compatibility)
# =============================================================================

@dataclass(frozen=True)
class Icons:
    """Consistent icon set using Unicode symbols."""

    # Navigation
    DASHBOARD: str = "\u25A6"      # ▦ Grid
    CHART: str = "\u2197"          # ↗ Trend up
    TABLE: str = "\u2630"          # ☰ Menu/list
    SETTINGS: str = "\u2699"       # ⚙ Gear
    REFRESH: str = "\u21BB"        # ↻ Refresh

    # Status
    CHECK: str = "\u2713"          # ✓ Checkmark
    CROSS: str = "\u2717"          # ✗ Cross
    WARNING_ICON: str = "\u26A0"   # ⚠ Warning
    INFO_ICON: str = "\u2139"      # ℹ Info
    ERROR_ICON: str = "\u2716"     # ✖ Error

    # Actions
    EDIT: str = "\u270E"           # ✎ Edit
    DELETE: str = "\u2212"         # − Minus
    ADD: str = "\u002B"            # + Plus
    SAVE: str = "\u2713"           # ✓ Save (same as check)
    EXPORT: str = "\u2913"         # ⤓ Download

    # Navigation arrows
    ARROW_RIGHT: str = "\u203A"    # › Right
    ARROW_LEFT: str = "\u2039"     # ‹ Left
    ARROW_UP: str = "\u2191"       # ↑ Up
    ARROW_DOWN: str = "\u2193"     # ↓ Down
    CHEVRON_RIGHT: str = "\u276F" # ❯ Chevron right
    CHEVRON_DOWN: str = "\u276E"  # ❮ Chevron down

    # Data
    CALENDAR: str = "\u2637"       # ☷ Calendar-like
    CLOCK: str = "\u25F4"          # ◴ Clock
    FOLDER: str = "\u2750"         # ❐ Folder
    FILE: str = "\u2630"           # ☰ File

    # Status dots
    DOT: str = "\u2022"            # • Bullet
    DOT_FILLED: str = "\u25CF"     # ● Filled circle
    DOT_EMPTY: str = "\u25CB"      # ○ Empty circle

    # Finance
    MONEY: str = "\u00A4"          # ¤ Currency
    PERCENT: str = "\u0025"        # % Percent
    DELTA: str = "\u0394"          # Δ Delta

    # Misc
    MENU: str = "\u2630"           # ☰ Hamburger menu
    CLOSE: str = "\u2715"          # ✕ Close
    MINIMIZE: str = "\u2212"       # − Minimize
    MAXIMIZE: str = "\u25A1"       # □ Maximize
    SEARCH: str = "\u26B2"         # ⚲ Search


ICONS = Icons()


# =============================================================================
# COMPONENT TOKENS
# =============================================================================

@dataclass(frozen=True)
class Components:
    """Component-specific configuration."""

    # Sidebar
    SIDEBAR_WIDTH: int = 220
    SIDEBAR_COLLAPSED_WIDTH: int = 60

    # Header
    HEADER_HEIGHT: int = 56

    # Card
    CARD_MIN_WIDTH: int = 300

    # Table
    TABLE_ROW_HEIGHT: int = 40
    TABLE_HEADER_HEIGHT: int = 44

    # Button sizes
    BUTTON_HEIGHT_SM: int = 32
    BUTTON_HEIGHT_MD: int = 38
    BUTTON_HEIGHT_LG: int = 44

    # Input sizes
    INPUT_HEIGHT: int = 38

    # Modal
    MODAL_SM_WIDTH: int = 400
    MODAL_MD_WIDTH: int = 560
    MODAL_LG_WIDTH: int = 720


COMPONENTS = Components()


# =============================================================================
# ANIMATION TOKENS
# =============================================================================

@dataclass(frozen=True)
class Animation:
    """Animation timing values (in milliseconds)."""

    INSTANT: int = 0
    FAST: int = 100
    NORMAL: int = 200
    SLOW: int = 300
    VERY_SLOW: int = 500


ANIMATION = Animation()


# =============================================================================
# THEME EXPORT (Compatibility with existing config.py patterns)
# =============================================================================

# For backwards compatibility, export a THEME dict matching old structure
THEME = {
    # Backgrounds
    "bg_main": COLORS.BG,
    "bg_panel": COLORS.NAV_BG,
    "bg_card": COLORS.SURFACE,
    "bg_card_2": COLORS.SURFACE_HOVER,
    "bg_hover": COLORS.ROW_HOVER,

    # Text
    "text": COLORS.TEXT,
    "text_secondary": COLORS.TEXT_SECONDARY,
    "muted": COLORS.TEXT_MUTED,
    "placeholder": COLORS.TEXT_PLACEHOLDER,

    # Accent
    "accent": COLORS.ACCENT,
    "accent_hover": COLORS.ACCENT_HOVER,
    "accent_light": COLORS.ACCENT_LIGHT,

    # Semantic
    "good": COLORS.SUCCESS,
    "bad": COLORS.DANGER,
    "warning": COLORS.WARNING,
    "info": COLORS.INFO,

    # Borders
    "border": COLORS.BORDER,
    "border_strong": COLORS.BORDER_STRONG,

    # Navigation
    "nav_bg": COLORS.NAV_BG,
    "nav_active": COLORS.NAV_ACTIVE_BG,
    "nav_hover": COLORS.NAV_HOVER_BG,
    "nav_indicator": COLORS.NAV_INDICATOR,

    # Table
    "table_header": COLORS.TABLE_HEADER_BG,
    "row_hover": COLORS.ROW_HOVER,
    "row_zebra": COLORS.ROW_ZEBRA,

    # Charts
    "chart_bg": COLORS.CHART_BG,
    "chart_grid": COLORS.CHART_GRID,
}

# Font tuples for backwards compatibility
FONT_TUPLES = {
    "h1": FONTS.H1,
    "h2": FONTS.H2,
    "h3": FONTS.H3,
    "h4": FONTS.H4,
    "body": FONTS.BODY,
    "body_sm": FONTS.BODY_SM,
    "label": FONTS.LABEL,
    "button": FONTS.BUTTON,
    "numeric": FONTS.NUMERIC,
    "nav": FONTS.NAV,
    "table_header": FONTS.TABLE_HEADER,
    "table_cell": FONTS.TABLE_CELL,
}


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_change_color(value: float) -> str:
    """Get color for change values (positive=green, negative=red, zero=muted)."""
    if value > 0:
        return COLORS.SUCCESS
    elif value < 0:
        return COLORS.DANGER
    else:
        return COLORS.TEXT_MUTED


def get_status_color(status: str) -> str:
    """Get color for status strings."""
    status_lower = status.lower()
    if status_lower in ("ok", "connected", "online", "success", "matched", "valid"):
        return COLORS.SUCCESS
    elif status_lower in ("error", "failed", "offline", "disconnected", "invalid"):
        return COLORS.DANGER
    elif status_lower in ("warning", "pending", "loading", "stale"):
        return COLORS.WARNING
    else:
        return COLORS.TEXT_MUTED


def get_badge_colors(variant: str) -> tuple:
    """Get (bg_color, text_color) for badge variants."""
    variants = {
        "default": (COLORS.CHIP_BG, COLORS.TEXT_MUTED),
        "primary": (COLORS.ACCENT_LIGHT, COLORS.ACCENT),
        "success": (COLORS.SUCCESS_BG, COLORS.SUCCESS),
        "warning": (COLORS.WARNING_BG, COLORS.WARNING),
        "danger": (COLORS.DANGER_BG, COLORS.DANGER),
        "info": (COLORS.INFO_BG, COLORS.INFO),
    }
    return variants.get(variant, variants["default"])


# =============================================================================
# MATPLOTLIB THEME CONFIGURATION
# =============================================================================

def apply_matplotlib_theme():
    """Apply Nordic Light theme to matplotlib globally."""
    try:
        import matplotlib.pyplot as plt
        import matplotlib as mpl

        # Set the style
        plt.style.use('seaborn-v0_8-whitegrid')

        # Override with our tokens
        mpl.rcParams.update({
            # Figure
            'figure.facecolor': COLORS.BG,
            'figure.edgecolor': COLORS.BORDER,
            'figure.dpi': 100,

            # Axes
            'axes.facecolor': COLORS.CHART_BG,
            'axes.edgecolor': COLORS.BORDER,
            'axes.labelcolor': COLORS.TEXT,
            'axes.titlecolor': COLORS.TEXT,
            'axes.titlesize': TYPOGRAPHY.SIZE_LG,
            'axes.labelsize': TYPOGRAPHY.SIZE_SM,
            'axes.grid': True,
            'axes.spines.top': False,
            'axes.spines.right': False,

            # Grid
            'grid.color': COLORS.CHART_GRID,
            'grid.alpha': 0.5,
            'grid.linewidth': 0.5,

            # Ticks
            'xtick.color': COLORS.TEXT_MUTED,
            'ytick.color': COLORS.TEXT_MUTED,
            'xtick.labelsize': TYPOGRAPHY.SIZE_SM,
            'ytick.labelsize': TYPOGRAPHY.SIZE_SM,

            # Legend
            'legend.facecolor': COLORS.SURFACE,
            'legend.edgecolor': COLORS.BORDER,
            'legend.fontsize': TYPOGRAPHY.SIZE_SM,
            'legend.framealpha': 0.95,

            # Font
            'font.family': 'sans-serif',
            'font.sans-serif': [TYPOGRAPHY.FAMILY, 'DejaVu Sans', 'Arial'],
            'font.size': TYPOGRAPHY.SIZE_BASE,

            # Lines
            'lines.linewidth': 2,
            'lines.markersize': 6,

            # Patches (bars, etc.)
            'patch.edgecolor': COLORS.BORDER,
        })

        return True
    except ImportError:
        return False


# =============================================================================
# TTK STYLE CONFIGURATION
# =============================================================================

def apply_ttk_theme(style):
    """Apply Nordic Light theme to ttk widgets."""
    from tkinter import ttk

    # Treeview (tables)
    style.configure("Treeview",
        background=COLORS.SURFACE,
        foreground=COLORS.TEXT,
        fieldbackground=COLORS.SURFACE,
        bordercolor=COLORS.BORDER,
        lightcolor=COLORS.BORDER,
        darkcolor=COLORS.BORDER,
        rowheight=COMPONENTS.TABLE_ROW_HEIGHT,
        font=FONTS.TABLE_CELL
    )

    style.configure("Treeview.Heading",
        background=COLORS.TABLE_HEADER_BG,
        foreground=COLORS.TEXT_MUTED,
        font=FONTS.TABLE_HEADER,
        borderwidth=0,
        relief="flat"
    )

    style.map("Treeview",
        background=[("selected", COLORS.ACCENT_LIGHT)],
        foreground=[("selected", COLORS.TEXT)]
    )

    # Scrollbars
    style.configure("Vertical.TScrollbar",
        background=COLORS.CHIP_BG,
        troughcolor=COLORS.SURFACE,
        bordercolor=COLORS.BORDER,
        arrowcolor=COLORS.TEXT_MUTED
    )

    # Combobox
    style.configure("TCombobox",
        background=COLORS.SURFACE,
        foreground=COLORS.TEXT,
        fieldbackground=COLORS.SURFACE,
        selectbackground=COLORS.ACCENT_LIGHT,
        selectforeground=COLORS.TEXT
    )

    # Entry
    style.configure("TEntry",
        background=COLORS.SURFACE,
        foreground=COLORS.TEXT,
        fieldbackground=COLORS.SURFACE,
        insertcolor=COLORS.TEXT
    )

    # Define tag colors for treeview rows
    return {
        "good": {"background": COLORS.SUCCESS_BG, "foreground": COLORS.SUCCESS},
        "bad": {"background": COLORS.DANGER_BG, "foreground": COLORS.DANGER},
        "warning": {"background": COLORS.WARNING_BG, "foreground": COLORS.WARNING},
        "normal_even": {"background": COLORS.SURFACE},
        "normal_odd": {"background": COLORS.ROW_ZEBRA},
        "header": {"background": COLORS.TABLE_HEADER_BG, "foreground": COLORS.TEXT_MUTED},
    }
