"""
Professional splash screen for Nibor 6 Eyes Terminal.
Uses full background image with progress bar and status text overlay.
"""
import tkinter as tk
import os
import time

# Try to import PIL for image support
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


# Colors matching the splash design
GOLD_COLOR = "#D4A853"
TEAL_COLOR = "#5B9A9A"
DARK_BG = "#0a2030"


class SplashScreen(tk.Toplevel):
    """Splash screen with background image, progress bar and status text."""

    # Minimum time to show each loading step (milliseconds)
    MIN_STEP_TIME_MS = 350

    def __init__(self, parent=None):
        super().__init__(parent)

        # Window setup - borderless, centered
        self.overrideredirect(True)

        # Target size for splash screen (matching image aspect ratio ~1.8:1)
        self._width = 696
        self._height = 384

        # Center on screen
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x = (screen_w - self._width) // 2
        y = (screen_h - self._height) // 2
        self.geometry(f"{self._width}x{self._height}+{x}+{y}")

        # Make it stay on top
        self.attributes("-topmost", True)

        # Store image reference to prevent garbage collection
        self._bg_image = None

        # Track last update time for minimum step duration
        self._last_update_time = 0

        # Build UI
        self._build_ui()

        # Progress tracking
        self._progress = 0

    def _load_background(self):
        """Load the background image from assets folder."""
        if not PIL_AVAILABLE:
            return None

        bg_path = os.path.join(os.path.dirname(__file__), "assets", "splash_bg.png")

        if os.path.exists(bg_path):
            try:
                img = Image.open(bg_path)
                # Resize to fit splash screen dimensions
                img = img.resize((self._width, self._height), Image.LANCZOS)
                return ImageTk.PhotoImage(img)
            except Exception:
                pass
        return None

    def _build_ui(self):
        """Build the splash screen UI with background image."""
        # Load background image
        self._bg_image = self._load_background()

        if self._bg_image:
            # Create canvas for background image
            self.canvas = tk.Canvas(
                self,
                width=self._width,
                height=self._height,
                highlightthickness=0
            )
            self.canvas.pack(fill="both", expand=True)

            # Set background image
            self.canvas.create_image(0, 0, anchor="nw", image=self._bg_image)

            # Progress bar position - near the bottom of the image
            bar_y = int(self._height * 0.88)
            bar_height = 4
            bar_margin = int(self._width * 0.08)  # Small margin from sides

            # Progress bar background (subtle dark)
            self.progress_bg = self.canvas.create_rectangle(
                bar_margin, bar_y,
                self._width - bar_margin, bar_y + bar_height,
                fill="#1a3a4a",
                outline=""
            )

            # Progress bar foreground (gold/amber to match the tree)
            self.progress_bar = self.canvas.create_rectangle(
                bar_margin, bar_y,
                bar_margin, bar_y + bar_height,  # Start with 0 width
                fill=GOLD_COLOR,
                outline=""
            )

            # Status text below progress bar
            status_y = bar_y + bar_height + 16
            self.status_text = self.canvas.create_text(
                self._width // 2, status_y,
                text="",
                font=("Segoe UI", 10),
                fill=TEAL_COLOR,
                anchor="center"
            )

            # Store bar dimensions for progress updates
            self._bar_x_start = bar_margin
            self._bar_x_end = self._width - bar_margin
            self._bar_y = bar_y
            self._bar_height = bar_height

        else:
            # Fallback if no image - simple colored background
            self.configure(bg=DARK_BG)
            self.canvas = None

            fallback_label = tk.Label(
                self,
                text="Nibor 6 Eyes Terminal",
                font=("Segoe UI", 24, "bold"),
                fg=GOLD_COLOR,
                bg=DARK_BG
            )
            fallback_label.pack(expand=True)

            # Simple progress bar frame
            progress_frame = tk.Frame(self, bg=DARK_BG)
            progress_frame.pack(fill="x", padx=50, pady=(0, 10))

            self.progress_bg_frame = tk.Frame(progress_frame, bg="#1a3a4a", height=4)
            self.progress_bg_frame.pack(fill="x")

            self.progress_bar_frame = tk.Frame(self.progress_bg_frame, bg=GOLD_COLOR, height=4, width=0)
            self.progress_bar_frame.place(x=0, y=0, height=4)

            self._bar_max_width = self._width - 100

            # Status label
            self.status_label = tk.Label(
                self,
                text="",
                font=("Segoe UI", 10),
                fg=TEAL_COLOR,
                bg=DARK_BG
            )
            self.status_label.pack(pady=(5, 20))

    def set_progress(self, value: int, status: str = None):
        """
        Set progress bar value (0-100) and optional status text.
        Enforces minimum display time between updates.

        Args:
            value: Progress percentage (0-100)
            status: Status message to display
        """
        # Enforce minimum time between steps
        current_time = time.time() * 1000  # Convert to ms
        elapsed = current_time - self._last_update_time
        if elapsed < self.MIN_STEP_TIME_MS and self._last_update_time > 0:
            time.sleep((self.MIN_STEP_TIME_MS - elapsed) / 1000)

        self._last_update_time = time.time() * 1000
        self._progress = max(0, min(100, value))

        if self.canvas and self._bg_image:
            # Calculate new bar width on canvas
            bar_width = int((self._progress / 100) * (self._bar_x_end - self._bar_x_start))
            new_x_end = self._bar_x_start + bar_width

            # Update progress bar rectangle
            self.canvas.coords(
                self.progress_bar,
                self._bar_x_start, self._bar_y,
                new_x_end, self._bar_y + self._bar_height
            )

            # Update status text
            if status is not None:
                self.canvas.itemconfig(self.status_text, text=status)

        elif hasattr(self, 'progress_bar_frame'):
            # Fallback progress bar
            bar_width = int((self._progress / 100) * self._bar_max_width)
            self.progress_bar_frame.place(x=0, y=0, height=4, width=bar_width)

            # Update status label
            if status is not None and hasattr(self, 'status_label'):
                self.status_label.configure(text=status)

        self.update_idletasks()
        self.update()

    def finish(self):
        """Complete the splash and prepare for close."""
        self.set_progress(100, "Ready!")
        time.sleep(0.3)
        self.destroy()


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

    def update(self, progress: int, status: str = None):
        """Update progress."""
        if self._splash:
            self._splash.set_progress(progress, status)

    def finish(self):
        """Finish and close splash screen."""
        if self._splash:
            self._splash.set_progress(100, "Ready!")
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


def run_with_splash(app_class, loading_steps=None):
    """
    Run an application with a splash screen showing real loading progress.

    Args:
        app_class: The application class to instantiate
        loading_steps: Optional list of (progress, status, callable) tuples.
                      If None, uses default steps.

    Returns:
        The application instance
    """
    import tkinter as tk

    # Create hidden root
    root = tk.Tk()
    root.withdraw()

    # Show splash
    splash = SplashScreen(root)
    splash.update()
    splash.set_progress(0, "Starting...")

    # Default loading steps if none provided
    if loading_steps is None:
        loading_steps = [
            (10, "Initializing...", None),
            (100, "Ready!", None),
        ]

    app = None

    try:
        # Execute loading steps
        for progress, status, callback in loading_steps:
            splash.set_progress(progress, status)
            if callback:
                result = callback()
                if progress == 10 and result is not None:
                    # First step returns the app
                    app = result
    except Exception as e:
        splash.set_progress(100, f"Error: {e}")
        time.sleep(1)
        raise
    finally:
        splash.finish()
        root.destroy()

    return app


def show_splash_then_run(app, total_duration=6.0):
    """
    Show a splash screen over an existing app, then reveal the app.
    This is the legacy function for backwards compatibility.

    Args:
        app: The main application window (already created but can be hidden)
        total_duration: Total time to show splash screen in seconds (default 6)
    """
    # Loading steps with progress percentages
    LOADING_STEPS = [
        (0, "Initializing..."),
        (15, "Loading Configuration..."),
        (30, "Connecting to Bloomberg..."),
        (50, "Loading Excel Data..."),
        (70, "Loading NIBOR Days..."),
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
            (30, "Connecting to Bloomberg..."),
            (50, "Loading Excel Data..."),
            (70, "Loading NIBOR Days..."),
            (85, "Building Interface..."),
            (95, "Finalizing..."),
            (100, "Ready!"),
        ]

        for progress, status in steps:
            splash.set_progress(progress, status)
            time.sleep(0.5)

        splash.after(500, splash.destroy)
        splash.after(600, root.destroy)

    splash.after(100, update_progress)
    root.mainloop()


if __name__ == "__main__":
    demo_splash()
