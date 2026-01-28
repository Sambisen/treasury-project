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
    """Semantic color tokens for the Premium Nordic theme."""

    # Backgrounds - More sophisticated gray tones
    BG: str = "#F8F9FC"                 # Main app background (soft blue-gray)
    SURFACE: str = "#FFFFFF"            # Card/panel surface (white)
    SURFACE_ELEVATED: str = "#FFFFFF"   # Elevated surfaces
    SURFACE_HOVER: str = "#F1F5F9"      # Hover state background
    SURFACE_OVERLAY: str = "#FBFCFD"    # Subtle overlay

    # Header
    HEADER_BG: str = "#FFFFFF"          # App header background

    # Borders & Dividers - More refined
    BORDER: str = "#E2E8F0"             # Default border (lighter)
    BORDER_STRONG: str = "#CBD5E1"      # Stronger border for emphasis
    BORDER_SUBTLE: str = "#F1F5F9"      # Very subtle border
    DIVIDER: str = "#E8ECF2"            # Divider lines

    # Text - Better hierarchy
    TEXT: str = "#0F172A"               # Primary text (slate-900)
    TEXT_SECONDARY: str = "#475569"     # Secondary text (slate-600)
    TEXT_MUTED: str = "#64748B"         # Muted text (slate-500)
    TEXT_PLACEHOLDER: str = "#94A3B8"   # Placeholder text (slate-400)
    TEXT_INVERSE: str = "#FFFFFF"       # Text on dark backgrounds
    TEXT_LIGHT: str = "#CBD5E1"         # Very light text

    # Accent (Swedbank Orange) - Refined
    ACCENT: str = "#FF6B35"             # Primary accent (vibrant orange)
    ACCENT_HOVER: str = "#FF5722"       # Darker on hover
    ACCENT_LIGHT: str = "#FFF4F0"       # Light accent background (softer)
    ACCENT_MUTED: str = "#FFB59A"       # Muted accent
    ACCENT_GLOW: str = "rgba(255, 107, 53, 0.15)"  # Glow effect

    # Semantic Colors - More vibrant
    SUCCESS: str = "#10B981"            # Success green (emerald)
    SUCCESS_BG: str = "#ECFDF5"         # Success background
    SUCCESS_LIGHT: str = "#D1FAE5"      # Light success

    WARNING: str = "#F59E0B"            # Warning amber
    WARNING_BG: str = "#FFFBEB"         # Warning background
    WARNING_LIGHT: str = "#FDE68A"      # Light warning

    DANGER: str = "#EF4444"             # Error/danger red
    DANGER_BG: str = "#FEF2F2"          # Danger background
    DANGER_LIGHT: str = "#FECACA"       # Light danger

    INFO: str = "#3B82F6"               # Info blue
    INFO_BG: str = "#EFF6FF"            # Info background
    INFO_LIGHT: str = "#DBEAFE"         # Light info

    # UI Elements - Enhanced
    CHIP_BG: str = "#F1F5F9"            # Chip/badge background
    ROW_HOVER: str = "#F8FAFC"          # Table row hover
    ROW_ZEBRA: str = "#FAFBFC"          # Alternating row color
    TABLE_HEADER_BG: str = "#F8FAFC"    # Table header background

    # Navigation - Premium slate sidebar
    NAV_BG: str = "#1E293B"             # Sidebar background (slate-800)
    NAV_BG_DARK: str = "#0F172A"        # Darker sidebar variant
    NAV_ACTIVE_BG: str = "#334155"      # Active nav item background (slate-700)
    NAV_HOVER_BG: str = "#293548"       # Nav item hover
    NAV_INDICATOR: str = "#FF6B35"      # Active indicator (orange)
    NAV_TEXT: str = "#F1F5F9"           # Sidebar text (light)
    NAV_TEXT_MUTED: str = "#94A3B8"     # Sidebar muted text
    NAV_DIVIDER: str = "#334155"        # Sidebar divider

    # Shadows
    SHADOW_COLOR: str = "rgba(15, 23, 42, 0.08)"
    SHADOW_STRONG: str = "rgba(15, 23, 42, 0.12)"

    # Chart specific
    CHART_BG: str = "#FFFFFF"           # Chart background
    CHART_GRID: str = "#E8ECF2"         # Grid lines
    CHART_LINE_PRIMARY: str = "#FF6B35" # Primary line (orange)
    CHART_LINE_SECONDARY: str = "#3B82F6"  # Secondary line (blue)

    # Status indicators
    STATUS_ONLINE: str = "#10B981"      # Online/connected
    STATUS_OFFLINE: str = "#94A3B8"     # Offline/disconnected
    STATUS_ERROR: str = "#EF4444"       # Error state
    STATUS_PENDING: str = "#F59E0B"     # Pending/loading


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
    Nordic Light theme - light background, colored glow.
    """

    # Badge container
    # Note: The app is dark-themed; keep border subtle/dark so it feels premium.
    BADGE_BG: str = "#0B1220"
    BADGE_BORDER: str = "#22314B"

    # PROD colors (premium "sigill" green/teal tint)
    # Tuned to feel less "alert" and more "status label".
    PROD_DOT: str = "#22C55E"       # Emerald 500 (slightly brighter dot)
    PROD_GLOW: str = "#22C55E"
    PROD_TEXT: str = "#86EFAC"      # Emerald 200 for softer text
    PROD_BG_TINT: str = "#0B1F16"   # Dark green-tinted background

    # DEV colors (warm amber tint, still premium)
    DEV_DOT: str = "#F59E0B"       # Amber 500
    DEV_GLOW: str = "#F59E0B"
    DEV_TEXT: str = "#FCD34D"      # Amber 300
    DEV_BG_TINT: str = "#2A1B14"   # Dark accent-tinted background (matches THEME['accent_light'])

    # Animation
    PULSE_INTERVAL_MS: int = 1500
    GLOW_OPACITY_MIN: float = 0.2
    GLOW_OPACITY_MAX: float = 0.6


ENV_BADGE_COLORS = EnvBadgeColors()


@dataclass(frozen=True)
class SegmentedControlColors:
    """
    Segmented control colors for Nordic Light theme.
    """

    # Container (dark app integration)
    # NOTE: This UI project uses a dark fintech theme in config.py (THEME['bg_main']).
    # The segmented control is used inside the dark global header, so we keep it dark
    # to avoid the “white patches” you see around 10:00/10:30.
    BG: str = "#0E172A"       # matches THEME['bg_panel'] in config.py
    BORDER: str = "#22314B"   # matches THEME['border'] in config.py

    # Segments
    SEGMENT_BG: str = "#0B1220"         # matches THEME['bg_main']
    SEGMENT_ACTIVE_BG: str = "#FF6B35"  # matches THEME['accent']
    SEGMENT_HOVER_BG: str = "#1C2A44"   # matches THEME['bg_hover']

    # Text
    TEXT: str = "#A8B3C7"         # matches THEME['text_muted']
    TEXT_ACTIVE: str = "#FFFFFF"
    TEXT_HOVER: str = "#E7ECF3"   # matches THEME['text']


SEGMENT_COLORS = SegmentedControlColors()


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
    """Spacing scale based on 4px baseline grid - More generous for premium feel."""

    NONE: int = 0
    XXS: int = 2    # 2px
    XS: int = 4     # 4px
    SM: int = 8     # 8px
    MD: int = 14    # 14px (increased from 12)
    LG: int = 20    # 20px (increased from 16)
    XL: int = 24    # 24px (increased from 20)
    XXL: int = 28   # 28px (increased from 24)
    XXXL: int = 36  # 36px (increased from 32)

    # Component-specific - More breathing room
    CARD_PADDING: int = 24      # Increased from 20
    CARD_GAP: int = 20          # Increased from 16
    SECTION_GAP: int = 28       # Increased from 24
    PAGE_PADDING: int = 28      # Increased from 24

    # Table - More comfortable
    TABLE_CELL_X: int = 16      # Increased from 12
    TABLE_CELL_Y: int = 12      # Increased from 10
    TABLE_ROW_HEIGHT: int = 44  # Increased from 40

    # Button - More substantial
    BUTTON_X: int = 20          # Increased from 16
    BUTTON_Y: int = 12          # Increased from 10
    BUTTON_GAP: int = 10        # Increased from 8

    # Input
    INPUT_X: int = 14           # Increased from 12
    INPUT_Y: int = 12           # Increased from 10


SPACING = Spacing()


# =============================================================================
# RADIUS TOKENS
# =============================================================================

@dataclass(frozen=True)
class Radii:
    """Border radius values for consistent rounding - More modern, rounded."""

    NONE: int = 0
    SM: int = 6     # Increased from 4
    MD: int = 8     # Increased from 6
    LG: int = 10    # Increased from 8
    XL: int = 14    # Increased from 10
    XXL: int = 16   # Increased from 12
    FULL: int = 999  # Pill shape

    # Component-specific - More rounded for modern look
    CARD: int = 16      # Increased from 12
    BUTTON: int = 10    # Kept at 10
    CHIP: int = 999     # Full rounded
    INPUT: int = 10     # Increased from 8
    MODAL: int = 16     # Increased from 12
    TOOLTIP: int = 8    # Increased from 6


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
    CHART_LINE: str = "\u2197"     # ↗ Alias used by some components
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
    "bg_panel": COLORS.SURFACE_OVERLAY,
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
