"""
UI Components Package
====================
Reusable, themed components for the Nordic Light design system.
"""

from .buttons import (
    BaseButton,
    PrimaryButton,
    SecondaryButton,
    GhostButton,
    DangerButton,
    IconButton,
)

from .cards import (
    Card,
    CardHeader,
    CardBody,
    CardFooter,
    MetricCard,
    InfoCard,
)

from .badges import (
    Badge,
    StatusBadge,
    CountBadge,
    MatchedBadge,
    EnvironmentBadge,
)

from .tables import (
    ThemedTable,
    SimpleTable,
)

from .navigation import (
    SidebarNav,
    NavItem,
    NavSection,
    QuickAccessItem,
)

from .modals import (
    ModalOverlay,
    ConfirmModal,
    AlertModal,
    InputModal,
    SelectModal,
    ProgressModal,
    # Convenience functions
    show_info,
    show_warning,
    show_error,
    show_success,
    ask_confirm,
    ask_input,
    ask_select,
)

from .status import (
    StatusStrip,
    StatusChip,
    ConnectionIndicator,
    ActivityIndicator,
    LastUpdatedLabel,
    ModeIndicator,
    EnvironmentBanner,
)

from .inputs import (
    ThemedEntry,
    ThemedCombobox,
    ThemedCheckbox,
    ThemedRadioGroup,
    ThemedSpinbox,
    SearchEntry,
)

from .app_shell import (
    AppShell,
    AppHeader,
    PageContainer,
    PageHeader,
    SplitPanel,
    TabContainer,
    ScrollableFrame,
)

__all__ = [
    # Buttons
    "BaseButton",
    "PrimaryButton",
    "SecondaryButton",
    "GhostButton",
    "DangerButton",
    "IconButton",
    # Cards
    "Card",
    "CardHeader",
    "CardBody",
    "CardFooter",
    "MetricCard",
    "InfoCard",
    # Badges
    "Badge",
    "StatusBadge",
    "CountBadge",
    "MatchedBadge",
    "EnvironmentBadge",
    # Tables
    "ThemedTable",
    "SimpleTable",
    # Navigation
    "SidebarNav",
    "NavItem",
    "NavSection",
    "QuickAccessItem",
    # Modals
    "ModalOverlay",
    "ConfirmModal",
    "AlertModal",
    "InputModal",
    "SelectModal",
    "ProgressModal",
    "show_info",
    "show_warning",
    "show_error",
    "show_success",
    "ask_confirm",
    "ask_input",
    "ask_select",
    # Status
    "StatusStrip",
    "StatusChip",
    "ConnectionIndicator",
    "ActivityIndicator",
    "LastUpdatedLabel",
    "ModeIndicator",
    "EnvironmentBanner",
    # Inputs
    "ThemedEntry",
    "ThemedCombobox",
    "ThemedCheckbox",
    "ThemedRadioGroup",
    "ThemedSpinbox",
    "SearchEntry",
    # App Shell
    "AppShell",
    "AppHeader",
    "PageContainer",
    "PageHeader",
    "SplitPanel",
    "TabContainer",
    "ScrollableFrame",
]
