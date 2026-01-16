"""
Professional splash screen for Nibor Calculation Terminal.
"""
import tkinter as tk
from tkinter import ttk
import threading
import time


class SplashScreen(tk.Toplevel):
    """Professional splash screen with loading progress."""

    def __init__(self, parent=None):
        super().__init__(parent)

        # Window setup - borderless, centered
        self.overrideredirect(True)
        self.configure(bg="#1a1a2e")

        # Size
        width = 500
        height = 320

        # Center on screen
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x = (screen_w - width) // 2
        y = (screen_h - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")

        # Make it stay on top
        self.attributes("-topmost", True)

        # Build UI
        self._build_ui()

        # Progress tracking
        self._progress = 0
        self._status_text = "Initializing..."

    def _build_ui(self):
        """Build the splash screen UI."""
        # Main container with gradient-like effect
        main_frame = tk.Frame(self, bg="#1a1a2e")
        main_frame.pack(fill="both", expand=True, padx=3, pady=3)

        # Border effect
        border_frame = tk.Frame(main_frame, bg="#16213e")
        border_frame.pack(fill="both", expand=True)

        inner_frame = tk.Frame(border_frame, bg="#1a1a2e")
        inner_frame.pack(fill="both", expand=True, padx=2, pady=2)

        # Top accent line
        accent_line = tk.Frame(inner_frame, bg="#e94560", height=3)
        accent_line.pack(fill="x")

        # Content area
        content = tk.Frame(inner_frame, bg="#1a1a2e")
        content.pack(fill="both", expand=True, padx=40, pady=30)

        # Logo area (stylized text)
        logo_frame = tk.Frame(content, bg="#1a1a2e")
        logo_frame.pack(pady=(20, 10))

        # App icon (stylized N)
        icon_label = tk.Label(
            logo_frame,
            text="N",
            font=("Segoe UI", 48, "bold"),
            fg="#e94560",
            bg="#1a1a2e"
        )
        icon_label.pack()

        # App name
        title_label = tk.Label(
            content,
            text="NIBOR CALCULATION TERMINAL",
            font=("Segoe UI", 18, "bold"),
            fg="#ffffff",
            bg="#1a1a2e"
        )
        title_label.pack(pady=(5, 5))

        # Subtitle
        subtitle_label = tk.Label(
            content,
            text="Treasury Reference Rate System",
            font=("Segoe UI", 10),
            fg="#888888",
            bg="#1a1a2e"
        )
        subtitle_label.pack(pady=(0, 30))

        # Progress bar frame
        progress_frame = tk.Frame(content, bg="#1a1a2e")
        progress_frame.pack(fill="x", pady=(10, 5))

        # Custom progress bar
        self.progress_bg = tk.Frame(progress_frame, bg="#2d2d44", height=6)
        self.progress_bg.pack(fill="x")

        self.progress_bar = tk.Frame(self.progress_bg, bg="#e94560", height=6, width=0)
        self.progress_bar.place(x=0, y=0, height=6)

        # Status text
        self.status_label = tk.Label(
            content,
            text="Initializing...",
            font=("Segoe UI", 9),
            fg="#666666",
            bg="#1a1a2e"
        )
        self.status_label.pack(pady=(10, 0))

        # Version info at bottom
        version_frame = tk.Frame(inner_frame, bg="#1a1a2e")
        version_frame.pack(side="bottom", fill="x", pady=10)

        version_label = tk.Label(
            version_frame,
            text="v1.0.0  |  Swedbank Treasury",
            font=("Segoe UI", 8),
            fg="#444444",
            bg="#1a1a2e"
        )
        version_label.pack()

        # Store reference to progress bar width
        self._progress_max_width = width - 86  # Account for padding

    def set_progress(self, value: int, status: str = None):
        """
        Set progress bar value (0-100) and optional status text.

        Args:
            value: Progress percentage (0-100)
            status: Status message to display
        """
        self._progress = max(0, min(100, value))

        # Calculate bar width
        bar_width = int((self._progress / 100) * self._progress_max_width)
        self.progress_bar.configure(width=bar_width)
        self.progress_bar.place(x=0, y=0, height=6, width=bar_width)

        if status:
            self._status_text = status
            self.status_label.configure(text=status)

        self.update_idletasks()

    def finish(self):
        """Complete the splash and prepare for close."""
        self.set_progress(100, "Ready!")
        self.after(500, self.destroy)


class SplashScreenManager:
    """
    Manager for showing splash screen during app initialization.

    Usage:
        splash = SplashScreenManager()
        splash.show()
        splash.update(20, "Loading configuration...")
        splash.update(40, "Connecting to Bloomberg...")
        # ... more updates ...
        splash.finish()
    """

    def __init__(self):
        self._splash = None
        self._root = None

    def show(self):
        """Show the splash screen."""
        # Create temporary root if needed
        self._root = tk.Tk()
        self._root.withdraw()

        self._splash = SplashScreen(self._root)
        self._splash.update()

    def update(self, progress: int, status: str):
        """Update progress and status."""
        if self._splash:
            self._splash.set_progress(progress, status)

    def finish(self):
        """Finish and close splash screen."""
        if self._splash:
            self._splash.set_progress(100, "Launching...")
            self._splash.update()
            time.sleep(0.3)
            self._splash.destroy()
            self._splash = None

        if self._root:
            self._root.destroy()
            self._root = None

    def get_root(self):
        """Get the hidden root window (for passing to main app)."""
        return self._root


def run_with_splash(app_factory, total_duration=6.0):
    """
    Run an application with a splash screen.

    Args:
        app_factory: A callable that creates and returns the main app window
        total_duration: Total time to show splash screen in seconds (default 6)

    Returns:
        The created app instance
    """
    # Loading steps with progress percentages
    LOADING_STEPS = [
        (0, "Initializing..."),
        (15, "Loading Configuration..."),
        (30, "Loading Bloomberg..."),
        (50, "Loading Excel..."),
        (70, "Loading History..."),
        (85, "Building Interface..."),
        (95, "Finalizing..."),
        (100, "Ready!"),
    ]

    # Calculate delay between steps
    step_delay = total_duration / len(LOADING_STEPS)

    # Create hidden root for splash
    root = tk.Tk()
    root.withdraw()

    splash = SplashScreen(root)
    splash.update()

    # Show loading steps with timing
    for progress, status in LOADING_STEPS:
        splash.set_progress(progress, status)
        splash.update()
        time.sleep(step_delay)

    # Brief pause on "Ready!"
    time.sleep(0.3)

    # Destroy splash
    splash.destroy()
    root.destroy()

    # Now create and return the main app
    return app_factory()


def demo_splash():
    """Demo the splash screen standalone."""
    root = tk.Tk()
    root.withdraw()

    splash = SplashScreen(root)

    def update_progress():
        steps = [
            (0, "Initializing..."),
            (15, "Loading Configuration..."),
            (30, "Loading Bloomberg..."),
            (50, "Loading Excel..."),
            (70, "Loading History..."),
            (85, "Building Interface..."),
            (95, "Finalizing..."),
            (100, "Ready!"),
        ]

        # 6 seconds total / 8 steps = 0.75 seconds per step
        for progress, status in steps:
            splash.set_progress(progress, status)
            splash.update()
            time.sleep(0.75)

        splash.after(300, splash.destroy)
        splash.after(400, root.destroy)

    splash.after(100, update_progress)
    root.mainloop()


if __name__ == "__main__":
    demo_splash()
