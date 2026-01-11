"""
Toast notification system for Nibor Calculation Terminal.
"""
import tkinter as tk
from typing import Literal


class Toast:
    """A toast notification that appears and fades out."""

    def __init__(self, parent: tk.Tk, message: str,
                 duration: int = 3000,
                 toast_type: Literal["info", "success", "warning", "error"] = "info"):
        """
        Create a toast notification.

        Args:
            parent: Parent window
            message: Message to display
            duration: Duration in milliseconds (default 3000)
            toast_type: Type of toast (info, success, warning, error)
        """
        self.parent = parent
        self.duration = duration

        # Colors based on type
        colors = {
            "info": {"bg": "#1e3a5f", "fg": "#ffffff", "accent": "#3b82f6"},
            "success": {"bg": "#14532d", "fg": "#ffffff", "accent": "#22c55e"},
            "warning": {"bg": "#713f12", "fg": "#ffffff", "accent": "#eab308"},
            "error": {"bg": "#7f1d1d", "fg": "#ffffff", "accent": "#ef4444"},
        }
        style = colors.get(toast_type, colors["info"])

        # Icons
        icons = {
            "info": "ℹ️",
            "success": "✓",
            "warning": "⚠️",
            "error": "✕",
        }
        icon = icons.get(toast_type, "ℹ️")

        # Create toplevel window
        self.toast = tk.Toplevel(parent)
        self.toast.overrideredirect(True)
        self.toast.configure(bg=style["bg"])
        self.toast.attributes("-topmost", True)

        # Try to make it slightly transparent (Windows)
        try:
            self.toast.attributes("-alpha", 0.95)
        except:
            pass

        # Content frame with accent border
        border = tk.Frame(self.toast, bg=style["accent"])
        border.pack(fill="both", expand=True, padx=0, pady=0)

        content = tk.Frame(border, bg=style["bg"])
        content.pack(fill="both", expand=True, padx=(3, 0), pady=0)

        # Icon
        icon_label = tk.Label(content, text=icon, font=("Segoe UI", 14),
                             fg=style["accent"], bg=style["bg"])
        icon_label.pack(side="left", padx=(12, 8), pady=12)

        # Message
        msg_label = tk.Label(content, text=message, font=("Segoe UI", 10),
                            fg=style["fg"], bg=style["bg"], wraplength=300)
        msg_label.pack(side="left", padx=(0, 15), pady=12)

        # Close button
        close_btn = tk.Label(content, text="×", font=("Segoe UI", 14),
                            fg="#888888", bg=style["bg"], cursor="hand2")
        close_btn.pack(side="right", padx=10)
        close_btn.bind("<Button-1>", lambda e: self.close())
        close_btn.bind("<Enter>", lambda e: close_btn.config(fg="#ffffff"))
        close_btn.bind("<Leave>", lambda e: close_btn.config(fg="#888888"))

        # Position at bottom-right of parent
        self.toast.update_idletasks()
        toast_width = self.toast.winfo_reqwidth()
        toast_height = self.toast.winfo_reqheight()

        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()

        x = parent_x + parent_width - toast_width - 20
        y = parent_y + parent_height - toast_height - 50  # Above status bar

        self.toast.geometry(f"+{x}+{y}")

        # Auto-close after duration
        self.toast.after(duration, self.close)

    def close(self):
        """Close the toast."""
        try:
            self.toast.destroy()
        except:
            pass


class ToastManager:
    """Manager for showing toast notifications."""

    def __init__(self, parent: tk.Tk):
        self.parent = parent
        self._toasts = []

    def show(self, message: str, toast_type: Literal["info", "success", "warning", "error"] = "info",
             duration: int = 3000):
        """Show a toast notification."""
        toast = Toast(self.parent, message, duration, toast_type)
        self._toasts.append(toast)

    def info(self, message: str, duration: int = 3000):
        """Show an info toast."""
        self.show(message, "info", duration)

    def success(self, message: str, duration: int = 3000):
        """Show a success toast."""
        self.show(message, "success", duration)

    def warning(self, message: str, duration: int = 3000):
        """Show a warning toast."""
        self.show(message, "warning", duration)

    def error(self, message: str, duration: int = 3000):
        """Show an error toast."""
        self.show(message, "error", duration)


# Demo
if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("800x600")
    root.title("Toast Demo")

    manager = ToastManager(root)

    tk.Button(root, text="Info Toast",
              command=lambda: manager.info("This is an info message")).pack(pady=10)
    tk.Button(root, text="Success Toast",
              command=lambda: manager.success("Operation completed successfully!")).pack(pady=10)
    tk.Button(root, text="Warning Toast",
              command=lambda: manager.warning("Please check your input")).pack(pady=10)
    tk.Button(root, text="Error Toast",
              command=lambda: manager.error("An error occurred!")).pack(pady=10)

    root.mainloop()
