"""
App Shell Components - Nordic Light Design System
==================================================
Application shell, header, and layout components.
"""

import tkinter as tk
from typing import Optional, Callable, List, Dict
from ..theme import COLORS, FONTS, SPACING, ICONS, COMPONENTS
from .navigation import SidebarNav
from .status import StatusStrip, ModeIndicator, ConnectionIndicator


class AppHeader(tk.Frame):
    """
    Application header with logo, title, and actions area.
    """

    def __init__(
        self,
        parent,
        title: str = "Application",
        subtitle: str = "",
        show_logo: bool = True,
        **kwargs
    ):
        super().__init__(
            parent,
            bg=COLORS.HEADER_BG,
            height=COMPONENTS.HEADER_HEIGHT,
            **kwargs
        )
        self.pack_propagate(False)

        # Left section: logo and title
        left = tk.Frame(self, bg=COLORS.HEADER_BG)
        left.pack(side="left", fill="y", padx=SPACING.LG)

        # Logo/icon
        if show_logo:
            tk.Label(
                left,
                text=ICONS.CHART_LINE,
                fg=COLORS.ACCENT,
                bg=COLORS.HEADER_BG,
                font=(FONTS.BODY[0], 20)
            ).pack(side="left", padx=(0, SPACING.MD))

        # Title section
        title_frame = tk.Frame(left, bg=COLORS.HEADER_BG)
        title_frame.pack(side="left", fill="y")

        tk.Label(
            title_frame,
            text=title,
            fg=COLORS.TEXT,
            bg=COLORS.HEADER_BG,
            font=FONTS.H2
        ).pack(side="top", anchor="w")

        if subtitle:
            tk.Label(
                title_frame,
                text=subtitle,
                fg=COLORS.TEXT_MUTED,
                bg=COLORS.HEADER_BG,
                font=FONTS.BODY_SM
            ).pack(side="top", anchor="w")

        # Center section
        self.center = tk.Frame(self, bg=COLORS.HEADER_BG)
        self.center.pack(side="left", fill="both", expand=True)

        # Right section: actions
        self.actions = tk.Frame(self, bg=COLORS.HEADER_BG)
        self.actions.pack(side="right", fill="y", padx=SPACING.LG)


class AppShell(tk.Frame):
    """
    Complete application shell with header, sidebar, content area, and status bar.

    Usage:
        shell = AppShell(root, title="My App")
        shell.pack(fill="both", expand=True)

        # Add content to shell.content
        my_page = MyPage(shell.content)
        my_page.pack(fill="both", expand=True)
    """

    def __init__(
        self,
        parent,
        title: str = "Application",
        subtitle: str = "",
        nav_items: List[Dict] = None,
        show_sidebar: bool = True,
        show_status_bar: bool = True,
        on_nav_select: Optional[Callable] = None,
        **kwargs
    ):
        super().__init__(parent, bg=COLORS.BG, **kwargs)

        self._pages = {}
        self._current_page = None

        # Header
        self.header = AppHeader(self, title=title, subtitle=subtitle)
        self.header.pack(fill="x")

        # Main area (sidebar + content)
        main_area = tk.Frame(self, bg=COLORS.BG)
        main_area.pack(fill="both", expand=True)

        # Sidebar
        if show_sidebar and nav_items:
            self.sidebar = SidebarNav(
                main_area,
                items=nav_items,
                on_select=on_nav_select or self._on_nav_select
            )
            self.sidebar.pack(side="left", fill="y")
        else:
            self.sidebar = None

        # Content area
        self.content = tk.Frame(main_area, bg=COLORS.BG)
        self.content.pack(side="left", fill="both", expand=True)

        # Status bar
        if show_status_bar:
            self.status_bar = StatusStrip(self)
            self.status_bar.pack(fill="x", side="bottom")
        else:
            self.status_bar = None

    def _on_nav_select(self, item_id: str):
        """Default navigation handler - show page by ID."""
        self.show_page(item_id)

    def register_page(self, page_id: str, page_class, **page_kwargs):
        """
        Register a page class for lazy loading.
        Page will be instantiated when first shown.
        """
        self._pages[page_id] = {
            "class": page_class,
            "kwargs": page_kwargs,
            "instance": None
        }

    def show_page(self, page_id: str):
        """Show a registered page."""
        if page_id not in self._pages:
            return

        page_info = self._pages[page_id]

        # Lazy instantiation
        if page_info["instance"] is None:
            page_info["instance"] = page_info["class"](
                self.content,
                **page_info["kwargs"]
            )
            page_info["instance"].place(x=0, y=0, relwidth=1, relheight=1)

        # Hide current page
        if self._current_page and self._current_page in self._pages:
            current_instance = self._pages[self._current_page]["instance"]
            if current_instance:
                current_instance.lower()

        # Show new page
        page_info["instance"].tkraise()
        self._current_page = page_id

        # Update sidebar
        if self.sidebar:
            self.sidebar.set_active(page_id)

    def add_header_action(self, widget):
        """Add a widget to the header actions area."""
        widget.pack(side="right", padx=(SPACING.SM, 0))

    def add_status_item(self, key: str, text: str, **kwargs):
        """Add an item to the status bar."""
        if self.status_bar:
            return self.status_bar.add_item(key, text, **kwargs)

    def update_status(self, key: str, text: str, **kwargs):
        """Update a status bar item."""
        if self.status_bar:
            self.status_bar.update_item(key, text, **kwargs)


class PageContainer(tk.Frame):
    """
    Base container for application pages.
    Provides consistent padding and background.
    """

    def __init__(
        self,
        parent,
        padding: int = None,
        **kwargs
    ):
        super().__init__(parent, bg=COLORS.BG, **kwargs)

        padding = padding if padding is not None else SPACING.PAGE_PADDING

        # Inner content area with padding
        self.content = tk.Frame(self, bg=COLORS.BG)
        self.content.pack(fill="both", expand=True, padx=padding, pady=padding)

    def get_content(self) -> tk.Frame:
        """Return the content frame for adding widgets."""
        return self.content


class PageHeader(tk.Frame):
    """
    Page-level header with title, description, and actions.
    """

    def __init__(
        self,
        parent,
        title: str = "",
        description: str = "",
        **kwargs
    ):
        super().__init__(parent, bg=COLORS.BG, **kwargs)

        # Left: title and description
        left = tk.Frame(self, bg=COLORS.BG)
        left.pack(side="left", fill="x", expand=True)

        if title:
            tk.Label(
                left,
                text=title,
                fg=COLORS.TEXT,
                bg=COLORS.BG,
                font=FONTS.H1
            ).pack(anchor="w")

        if description:
            tk.Label(
                left,
                text=description,
                fg=COLORS.TEXT_MUTED,
                bg=COLORS.BG,
                font=FONTS.BODY
            ).pack(anchor="w", pady=(4, 0))

        # Right: actions
        self.actions = tk.Frame(self, bg=COLORS.BG)
        self.actions.pack(side="right")


class SplitPanel(tk.Frame):
    """
    Two-panel layout (horizontal or vertical split).
    """

    def __init__(
        self,
        parent,
        orientation: str = "horizontal",  # horizontal, vertical
        ratio: float = 0.5,  # 0-1, size of first panel
        **kwargs
    ):
        super().__init__(parent, bg=COLORS.BG, **kwargs)

        self._orientation = orientation

        if orientation == "horizontal":
            # Left panel
            self.panel1 = tk.Frame(self, bg=COLORS.BG)
            self.panel1.place(x=0, y=0, relwidth=ratio, relheight=1)

            # Divider
            divider = tk.Frame(self, bg=COLORS.BORDER, width=1)
            divider.place(relx=ratio, y=0, relheight=1)

            # Right panel
            self.panel2 = tk.Frame(self, bg=COLORS.BG)
            self.panel2.place(relx=ratio, y=0, relwidth=1-ratio, relheight=1)
        else:
            # Top panel
            self.panel1 = tk.Frame(self, bg=COLORS.BG)
            self.panel1.place(x=0, y=0, relwidth=1, relheight=ratio)

            # Divider
            divider = tk.Frame(self, bg=COLORS.BORDER, height=1)
            divider.place(x=0, rely=ratio, relwidth=1)

            # Bottom panel
            self.panel2 = tk.Frame(self, bg=COLORS.BG)
            self.panel2.place(x=0, rely=ratio, relwidth=1, relheight=1-ratio)


class TabContainer(tk.Frame):
    """
    Tab container with themed tab buttons.
    """

    def __init__(
        self,
        parent,
        tabs: List[str] = None,
        on_tab_change: Optional[Callable] = None,
        **kwargs
    ):
        super().__init__(parent, bg=COLORS.SURFACE, **kwargs)

        tabs = tabs or []
        self._tabs = {}
        self._active_tab = None
        self.on_tab_change = on_tab_change

        # Tab bar
        self._tab_bar = tk.Frame(self, bg=COLORS.SURFACE)
        self._tab_bar.pack(fill="x")

        # Create tabs
        for tab_name in tabs:
            self._create_tab_button(tab_name)

        # Bottom border
        tk.Frame(self, bg=COLORS.BORDER, height=1).pack(fill="x")

        # Content area
        self.content = tk.Frame(self, bg=COLORS.SURFACE)
        self.content.pack(fill="both", expand=True)

        # Activate first tab
        if tabs:
            self.select_tab(tabs[0])

    def _create_tab_button(self, name: str):
        """Create a tab button."""
        tab_frame = tk.Frame(self._tab_bar, bg=COLORS.SURFACE, cursor="hand2")
        tab_frame.pack(side="left")

        label = tk.Label(
            tab_frame,
            text=name,
            fg=COLORS.TEXT_MUTED,
            bg=COLORS.SURFACE,
            font=FONTS.BUTTON,
            padx=SPACING.LG,
            pady=SPACING.SM
        )
        label.pack()

        # Active indicator
        indicator = tk.Frame(tab_frame, bg=COLORS.SURFACE, height=3)
        indicator.pack(fill="x")

        self._tabs[name] = {
            "frame": tab_frame,
            "label": label,
            "indicator": indicator
        }

        # Bindings
        def on_click(e, tab=name):
            self.select_tab(tab)

        tab_frame.bind("<Button-1>", on_click)
        label.bind("<Button-1>", on_click)

    def select_tab(self, name: str):
        """Select a tab."""
        if name not in self._tabs:
            return

        # Deactivate previous
        if self._active_tab and self._active_tab in self._tabs:
            prev = self._tabs[self._active_tab]
            prev["label"].configure(fg=COLORS.TEXT_MUTED)
            prev["indicator"].configure(bg=COLORS.SURFACE)

        # Activate new
        tab = self._tabs[name]
        tab["label"].configure(fg=COLORS.ACCENT)
        tab["indicator"].configure(bg=COLORS.ACCENT)
        self._active_tab = name

        if self.on_tab_change:
            self.on_tab_change(name)

    def get_active_tab(self) -> Optional[str]:
        """Get the currently active tab."""
        return self._active_tab


class ScrollableFrame(tk.Frame):
    """
    Scrollable frame container.
    """

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=COLORS.BG, **kwargs)

        # Canvas for scrolling
        self._canvas = tk.Canvas(self, bg=COLORS.BG, highlightthickness=0)
        self._canvas.pack(side="left", fill="both", expand=True)

        # Scrollbar
        scrollbar = tk.Scrollbar(
            self,
            orient="vertical",
            command=self._canvas.yview
        )
        scrollbar.pack(side="right", fill="y")

        self._canvas.configure(yscrollcommand=scrollbar.set)

        # Inner frame
        self.content = tk.Frame(self._canvas, bg=COLORS.BG)
        self._canvas_window = self._canvas.create_window(
            (0, 0),
            window=self.content,
            anchor="nw"
        )

        # Bindings
        self.content.bind("<Configure>", self._on_frame_configure)
        self._canvas.bind("<Configure>", self._on_canvas_configure)

        # Mouse wheel scrolling
        self._canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _on_frame_configure(self, event=None):
        """Update scroll region."""
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    def _on_canvas_configure(self, event=None):
        """Update inner frame width."""
        self._canvas.itemconfig(self._canvas_window, width=event.width)

    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling."""
        self._canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def scroll_to_top(self):
        """Scroll to top."""
        self._canvas.yview_moveto(0)

    def scroll_to_bottom(self):
        """Scroll to bottom."""
        self._canvas.yview_moveto(1)
