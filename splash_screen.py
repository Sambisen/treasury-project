"""
Professional splash screen for Nibor Calculation Terminal.
Light theme with Swedbank branding.
"""
import tkinter as tk
import os
import time

# Try to import PIL for logo support
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


# Swedbank brand colors
SWEDBANK_ORANGE = "#FF5F00"
SWEDBANK_ORANGE_LIGHT = "#FF8533"
LIGHT_BG = "#FFFFFF"
LIGHT_BG_SECONDARY = "#F5F5F5"
TEXT_PRIMARY = "#333333"
TEXT_SECONDARY = "#666666"
TEXT_MUTED = "#999999"
BORDER_COLOR = "#E0E0E0"


class SplashScreen(tk.Toplevel):
    """Professional splash screen with loading progress - Light theme."""

    def __init__(self, parent=None):
        super().__init__(parent)

        # Window setup - borderless, centered
        self.overrideredirect(True)
        self.configure(bg=LIGHT_BG)

        # Size
        self._width = 520
        self._height = 340

        # Center on screen
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x = (screen_w - self._width) // 2
        y = (screen_h - self._height) // 2
        self.geometry(f"{self._width}x{self._height}+{x}+{y}")

        # Make it stay on top
        self.attributes("-topmost", True)

        # Store logo reference to prevent garbage collection
        self._logo_image = None

        # Build UI
        self._build_ui()

        # Progress tracking
        self._progress = 0
        self._status_text = "Initializing..."

    def _load_logo(self):
        """Load the Swedbank logo from assets folder."""
        if not PIL_AVAILABLE:
            return None

        # Try to find the logo
        logo_paths = [
            os.path.join(os.path.dirname(__file__), "assets", "swedbank_logo.png"),
            os.path.join(os.path.dirname(__file__), "assets", "logo.png"),
        ]

        for logo_path in logo_paths:
            if os.path.exists(logo_path):
                try:
                    img = Image.open(logo_path)
                    # Resize to fit nicely (max height 80px, maintain aspect ratio)
                    max_height = 80
                    aspect = img.width / img.height
                    new_height = min(img.height, max_height)
                    new_width = int(new_height * aspect)
                    img = img.resize((new_width, new_height), Image.LANCZOS)
                    return ImageTk.PhotoImage(img)
                except Exception:
                    pass
        return None

    def _build_ui(self):
        """Build the splash screen UI with light theme."""
        # Main container with subtle shadow effect
        main_frame = tk.Frame(self, bg=BORDER_COLOR)
        main_frame.pack(fill="both", expand=True, padx=1, pady=1)

        inner_frame = tk.Frame(main_frame, bg=LIGHT_BG)
        inner_frame.pack(fill="both", expand=True)

        # Top accent line (Swedbank orange)
        accent_line = tk.Frame(inner_frame, bg=SWEDBANK_ORANGE, height=4)
        accent_line.pack(fill="x")

        # Content area
        content = tk.Frame(inner_frame, bg=LIGHT_BG)
        content.pack(fill="both", expand=True, padx=50, pady=30)

        # Logo area
        logo_frame = tk.Frame(content, bg=LIGHT_BG)
        logo_frame.pack(pady=(15, 10))

        # Try to load and display the logo
        self._logo_image = self._load_logo()
        if self._logo_image:
            logo_label = tk.Label(
                logo_frame,
                image=self._logo_image,
                bg=LIGHT_BG
            )
            logo_label.pack()
        else:
            # Fallback: stylized text logo
            icon_label = tk.Label(
                logo_frame,
                text="S",
                font=("Segoe UI", 48, "bold"),
                fg=SWEDBANK_ORANGE,
                bg=LIGHT_BG
            )
            icon_label.pack()

        # App name
        title_label = tk.Label(
            content,
            text="NIBOR TERMINAL",
            font=("Segoe UI", 22, "bold"),
            fg=TEXT_PRIMARY,
            bg=LIGHT_BG
        )
        title_label.pack(pady=(15, 5))

        # Subtitle
        subtitle_label = tk.Label(
            content,
            text="Treasury Reference Rate System",
            font=("Segoe UI", 11),
            fg=TEXT_SECONDARY,
            bg=LIGHT_BG
        )
        subtitle_label.pack(pady=(0, 35))

        # Progress bar frame
        progress_frame = tk.Frame(content, bg=LIGHT_BG)
        progress_frame.pack(fill="x", pady=(10, 5))

        # Custom progress bar with rounded look
        self.progress_bg = tk.Frame(progress_frame, bg=LIGHT_BG_SECONDARY, height=8)
        self.progress_bg.pack(fill="x")

        self.progress_bar = tk.Frame(self.progress_bg, bg=SWEDBANK_ORANGE, height=8, width=0)
        self.progress_bar.place(x=0, y=0, height=8)

        # Status text
        self.status_label = tk.Label(
            content,
            text="Initializing...",
            font=("Segoe UI", 10),
            fg=TEXT_MUTED,
            bg=LIGHT_BG
        )
        self.status_label.pack(pady=(12, 0))

        # Version info at bottom
        version_frame = tk.Frame(inner_frame, bg=LIGHT_BG)
        version_frame.pack(side="bottom", fill="x", pady=15)

        version_label = tk.Label(
            version_frame,
            text="v1.0.0  |  Swedbank Treasury",
            font=("Segoe UI", 9),
            fg=TEXT_MUTED,
            bg=LIGHT_BG
        )
        version_label.pack()

        # Store reference to progress bar width
        self._progress_max_width = self._width - 102  # Account for padding

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
        self.progress_bar.place(x=0, y=0, height=8, width=bar_width)

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


def show_splash_then_run(app, total_duration=6.0):
    """
    Show a splash screen over an existing app, then reveal the app.

    Args:
        app: The main application window (already created but can be hidden)
        total_duration: Total time to show splash screen in seconds (default 6)
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

    # Hide the main app temporarily
    app.withdraw()

    # Create splash as Toplevel of the app
    splash = SplashScreen(app)
    splash.update()

    # Calculate delay between steps (in milliseconds)
    step_delay_ms = int((total_duration * 1000) / len(LOADING_STEPS))

    # Current step index
    current_step = [0]

    def show_next_step():
        if current_step[0] < len(LOADING_STEPS):
            progress, status = LOADING_STEPS[current_step[0]]
            splash.set_progress(progress, status)
            current_step[0] += 1
            app.after(step_delay_ms, show_next_step)
        else:
            # All steps done - close splash and show app
            app.after(300, finish_splash)

    def finish_splash():
        splash.destroy()
        app.deiconify()
        app.lift()
        app.focus_force()

    # Start the animation
    app.after(100, show_next_step)


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
