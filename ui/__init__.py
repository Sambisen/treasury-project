"""
UI Package - Nordic Light Design System
=======================================
Reusable components and design tokens for the Nibor Calculation Terminal.
"""

from .theme import (
    COLORS,
    TYPOGRAPHY,
    FONTS,
    SPACING,
    RADII,
    SHADOWS,
    ICONS,
    COMPONENTS,
    ANIMATION,
    THEME,
    FONT_TUPLES,
    get_change_color,
    get_status_color,
    get_badge_colors,
    apply_matplotlib_theme,
    apply_ttk_theme,
)

# Theme preview - only import if needed to avoid circular dependencies
def launch_theme_preview():
    """Launch the theme preview window for development."""
    from .theme_preview import launch_preview
    launch_preview()

__all__ = [
    "COLORS",
    "TYPOGRAPHY",
    "FONTS",
    "SPACING",
    "RADII",
    "SHADOWS",
    "ICONS",
    "COMPONENTS",
    "ANIMATION",
    "THEME",
    "FONT_TUPLES",
    "get_change_color",
    "get_status_color",
    "get_badge_colors",
    "apply_matplotlib_theme",
    "apply_ttk_theme",
]
