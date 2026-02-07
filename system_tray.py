"""
System tray functionality for Nibor Calculation Terminal.
Allows the app to minimize to system tray and show notifications.
"""
import threading
from typing import Callable, Optional

try:
    from PIL import Image, ImageDraw
    import pystray
    from pystray import MenuItem as item
    TRAY_AVAILABLE = True
except ImportError:
    TRAY_AVAILABLE = False


def create_tray_icon_image(size=64):
    """Create a simple 'N' icon for the system tray."""
    # Create image with transparent background
    image = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    # Draw circle background
    margin = 2
    draw.ellipse([margin, margin, size-margin, size-margin],
                 fill='#e94560', outline='#16213e', width=2)

    # Draw 'N' letter
    # Simple N shape using lines
    n_margin = size // 4
    n_width = size - 2 * n_margin
    n_height = size - 2 * n_margin

    # Left vertical
    draw.line([(n_margin, size - n_margin), (n_margin, n_margin)],
              fill='white', width=max(3, size // 16))

    # Diagonal
    draw.line([(n_margin, n_margin), (size - n_margin, size - n_margin)],
              fill='white', width=max(3, size // 16))

    # Right vertical
    draw.line([(size - n_margin, size - n_margin), (size - n_margin, n_margin)],
              fill='white', width=max(3, size // 16))

    return image


class SystemTray:
    """System tray manager for the application."""

    def __init__(self, app):
        """
        Initialize system tray.

        Args:
            app: The main application instance (NiborTerminalTK)
        """
        self.app = app
        self.icon = None
        self._tray_thread = None
        self._running = False

    def is_available(self) -> bool:
        """Check if system tray is available."""
        return TRAY_AVAILABLE

    def start(self):
        """Start the system tray icon."""
        if not TRAY_AVAILABLE:
            return

        if self._running:
            return

        self._running = True

        # Create menu
        menu = pystray.Menu(
            item('Show', self._on_show, default=True),
            item('Dashboard', lambda: self._show_page('dashboard')),
            item('History', lambda: self._show_page('history')),
            pystray.Menu.SEPARATOR,
            item('Refresh Data', self._on_refresh),
            pystray.Menu.SEPARATOR,
            item('Exit', self._on_exit)
        )

        # Create icon
        image = create_tray_icon_image()
        self.icon = pystray.Icon(
            'nibor_terminal',
            image,
            'Nibor Calculation Terminal',
            menu
        )

        # Run in separate thread
        self._tray_thread = threading.Thread(target=self.icon.run, daemon=True)
        self._tray_thread.start()

    def stop(self):
        """Stop the system tray icon."""
        self._running = False
        if self.icon:
            try:
                self.icon.stop()
            except Exception:
                pass
            self.icon = None

    def show_notification(self, title: str, message: str):
        """Show a system tray notification."""
        if self.icon and TRAY_AVAILABLE:
            try:
                self.icon.notify(message, title)
            except Exception:
                pass

    def _on_show(self, icon=None, item=None):
        """Show the main window."""
        self.app.after(0, self._restore_window)

    def _restore_window(self):
        """Restore the main window (called from main thread)."""
        self.app.deiconify()
        self.app.lift()
        self.app.focus_force()

    def _show_page(self, page_key: str):
        """Show a specific page."""
        self.app.after(0, lambda: self._do_show_page(page_key))

    def _do_show_page(self, page_key: str):
        """Actually show the page (called from main thread)."""
        self._restore_window()
        if hasattr(self.app, 'show_page'):
            self.app.show_page(page_key)

    def _on_refresh(self, icon=None, item=None):
        """Refresh data."""
        self.app.after(0, self._do_refresh)

    def _do_refresh(self):
        """Actually refresh (called from main thread)."""
        if hasattr(self.app, 'refresh_data'):
            self.app.refresh_data()

    def _on_exit(self, icon=None, item=None):
        """Exit the application."""
        self.stop()
        self.app.after(0, self.app.destroy)


class TrayMinimizer:
    """
    Mixin class to add minimize-to-tray functionality to a tkinter window.

    Usage:
        class MyApp(tk.Tk, TrayMinimizer):
            def __init__(self):
                super().__init__()
                self.setup_tray_minimizer()
    """

    def setup_tray_minimizer(self, enable_tray: bool = True):
        """Set up the tray minimizer."""
        self._tray_enabled = enable_tray and TRAY_AVAILABLE
        self._tray = None

        if self._tray_enabled:
            self._tray = SystemTray(self)
            self._tray.start()

            # Override window close button
            self.protocol("WM_DELETE_WINDOW", self._on_close)

            # Add keyboard shortcut for minimize to tray
            self.bind("<Control-m>", lambda e: self._minimize_to_tray())

    def _on_close(self):
        """Handle window close - minimize to tray instead of closing."""
        if self._tray_enabled and hasattr(self, '_settings_minimize_to_tray'):
            # Check user preference
            if getattr(self, '_settings_minimize_to_tray', True):
                self._minimize_to_tray()
                return

        # Actually close
        self._quit_app()

    def _minimize_to_tray(self):
        """Minimize to system tray."""
        if self._tray_enabled and self._tray:
            self.withdraw()
            self._tray.show_notification(
                "Nibor Calculation Terminal",
                "Application minimized to tray. Double-click icon to restore."
            )

    def _quit_app(self):
        """Quit the application."""
        if self._tray:
            self._tray.stop()
        self.destroy()

    def tray_notify(self, title: str, message: str):
        """Show a tray notification."""
        if self._tray:
            self._tray.show_notification(title, message)


# For testing
if __name__ == "__main__":
    import tkinter as tk

    class TestApp(tk.Tk, TrayMinimizer):
        def __init__(self):
            super().__init__()
            self.title("Tray Test")
            self.geometry("400x300")
            self.setup_tray_minimizer()

            tk.Label(self, text="Click X to minimize to tray").pack(pady=20)
            tk.Button(self, text="Quit", command=self._quit_app).pack()
            tk.Button(self, text="Notify",
                     command=lambda: self.tray_notify("Test", "Hello!")).pack()

    if TRAY_AVAILABLE:
        app = TestApp()
        app.mainloop()
    else:
        print("System tray not available. Install pystray: pip install pystray")
