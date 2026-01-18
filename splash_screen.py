"""
Professional splash screen for Nibor 6 Eyes Terminal.
Uses full background image with progress bar overlay.
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


# Swedbank brand colors
SWEDBANK_ORANGE = "#FF5F00"


class SplashScreen(tk.Toplevel):
    """Splash screen with background image and progress bar."""

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
            bar_y = int(self._height * 0.92)
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
                fill="#D4A853",
                outline=""
            )

            # Store bar dimensions for progress updates
            self._bar_x_start = bar_margin
            self._bar_x_end = self._width - bar_margin
            self._bar_y = bar_y
            self._bar_height = bar_height

        else:
            # Fallback if no image - simple colored background
            self.configure(bg="#FFFFFF")
            self.canvas = None

            fallback_label = tk.Label(
                self,
                text="Nibor 6 Eyes Terminal",
                font=("Segoe UI", 24, "bold"),
                fg=SWEDBANK_ORANGE,
                bg="#FFFFFF"
            )
            fallback_label.pack(expand=True)

            # Simple progress bar frame
            progress_frame = tk.Frame(self, bg="#FFFFFF")
            progress_frame.pack(fill="x", padx=50, pady=30)

            self.progress_bg_frame = tk.Frame(progress_frame, bg="#E0E0E0", height=6)
            self.progress_bg_frame.pack(fill="x")

            self.progress_bar_frame = tk.Frame(self.progress_bg_frame, bg=SWEDBANK_ORANGE, height=6, width=0)
            self.progress_bar_frame.place(x=0, y=0, height=6)

            self._bar_max_width = self._width - 100

    def set_progress(self, value: int, status: str = None):
        """
        Set progress bar value (0-100).

        Args:
            value: Progress percentage (0-100)
            status: Status message (ignored for image-based splash)
        """
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
        elif hasattr(self, 'progress_bar_frame'):
            # Fallback progress bar
            bar_width = int((self._progress / 100) * self._bar_max_width)
            self.progress_bar_frame.place(x=0, y=0, height=6, width=bar_width)

        self.update_idletasks()

    def finish(self):
        """Complete the splash and prepare for close."""
        self.set_progress(100)
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

    def update(self, progress: int, status: str = None):
        """Update progress."""
        if self._splash:
            self._splash.set_progress(progress, status)

    def finish(self):
        """Finish and close splash screen."""
        if self._splash:
            self._splash.set_progress(100)
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
            (0, ""),
            (15, ""),
            (30, ""),
            (50, ""),
            (70, ""),
            (85, ""),
            (95, ""),
            (100, ""),
        ]

        # 6 seconds total / 8 steps = 0.75 seconds per step
        for progress, _ in steps:
            splash.set_progress(progress)
            splash.update()
            time.sleep(0.75)

        splash.after(300, splash.destroy)
        splash.after(400, root.destroy)

    splash.after(100, update_progress)
    root.mainloop()


if __name__ == "__main__":
    demo_splash()
