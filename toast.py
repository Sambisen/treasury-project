"""
Toast notification system - Premium Design
"""
import tkinter as tk
from typing import Literal


class Toast:
    """A professional toast notification with slide-in animation."""

    def __init__(self, parent: tk.Tk, message: str,
                 duration: int = 3000,
                 toast_type: Literal["info", "success", "warning", "error"] = "info"):
        self.parent = parent
        self.duration = duration
        self._closed = False

        # Modern color schemes
        colors = {
            "info": {
                "bg": "#1E293B",
                "fg": "#F1F5F9",
                "accent": "#3B82F6",
                "icon_bg": "#1E40AF",
            },
            "success": {
                "bg": "#14532D",
                "fg": "#F0FDF4",
                "accent": "#22C55E",
                "icon_bg": "#166534",
            },
            "warning": {
                "bg": "#451A03",
                "fg": "#FFFBEB",
                "accent": "#F59E0B",
                "icon_bg": "#92400E",
            },
            "error": {
                "bg": "#450A0A",
                "fg": "#FEF2F2",
                "accent": "#EF4444",
                "icon_bg": "#991B1B",
            },
        }
        style = colors.get(toast_type, colors["info"])

        # Icons (simple, clean)
        icons = {
            "info": "i",
            "success": "✓",
            "warning": "!",
            "error": "✕",
        }
        icon = icons.get(toast_type, "i")

        # Create toplevel window
        self.toast = tk.Toplevel(parent)
        self.toast.overrideredirect(True)
        self.toast.configure(bg=style["bg"])
        self.toast.attributes("-topmost", True)

        # Transparency
        try:
            self.toast.attributes("-alpha", 0.97)
        except:
            pass

        # Main container with padding for shadow effect
        container = tk.Frame(self.toast, bg=style["bg"])
        container.pack(fill="both", expand=True)

        # Left accent bar
        accent_bar = tk.Frame(container, bg=style["accent"], width=4)
        accent_bar.pack(side="left", fill="y")

        # Content area
        content = tk.Frame(container, bg=style["bg"])
        content.pack(side="left", fill="both", expand=True, padx=12, pady=12)

        # Icon circle
        icon_frame = tk.Frame(content, bg=style["icon_bg"], width=28, height=28)
        icon_frame.pack(side="left", padx=(0, 12))
        icon_frame.pack_propagate(False)

        icon_label = tk.Label(
            icon_frame,
            text=icon,
            font=("Segoe UI Semibold", 11),
            fg="#FFFFFF",
            bg=style["icon_bg"]
        )
        icon_label.place(relx=0.5, rely=0.5, anchor="center")

        # Text area
        text_frame = tk.Frame(content, bg=style["bg"])
        text_frame.pack(side="left", fill="both", expand=True)

        # Title based on type
        titles = {
            "info": "Information",
            "success": "Success",
            "warning": "Warning",
            "error": "Error",
        }
        title = titles.get(toast_type, "Notice")

        title_label = tk.Label(
            text_frame,
            text=title,
            font=("Segoe UI Semibold", 10),
            fg=style["accent"],
            bg=style["bg"],
            anchor="w"
        )
        title_label.pack(anchor="w")

        # Message
        msg_label = tk.Label(
            text_frame,
            text=message,
            font=("Segoe UI", 9),
            fg=style["fg"],
            bg=style["bg"],
            wraplength=280,
            justify="left",
            anchor="w"
        )
        msg_label.pack(anchor="w", pady=(2, 0))

        # Close button
        close_frame = tk.Frame(content, bg=style["bg"])
        close_frame.pack(side="right", padx=(12, 0))

        close_btn = tk.Label(
            close_frame,
            text="×",
            font=("Segoe UI", 16),
            fg="#64748B",
            bg=style["bg"],
            cursor="hand2"
        )
        close_btn.pack()
        close_btn.bind("<Button-1>", lambda e: self.close())
        close_btn.bind("<Enter>", lambda e: close_btn.config(fg="#FFFFFF"))
        close_btn.bind("<Leave>", lambda e: close_btn.config(fg="#64748B"))

        # Calculate position (bottom-right)
        self.toast.update_idletasks()
        toast_width = max(self.toast.winfo_reqwidth(), 320)
        toast_height = self.toast.winfo_reqheight()

        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()

        # Final position
        self.final_x = parent_x + parent_width - toast_width - 24
        self.final_y = parent_y + parent_height - toast_height - 60

        # Start position (off-screen to the right)
        self.start_x = parent_x + parent_width + 10
        self.current_x = self.start_x

        self.toast.geometry(f"{toast_width}x{toast_height}+{self.start_x}+{self.final_y}")

        # Slide-in animation
        self._animate_in()

        # Auto-close after duration
        self.toast.after(duration, self.close)

    def _animate_in(self):
        """Slide in from right."""
        if self._closed:
            return

        step = 20
        if self.current_x > self.final_x:
            self.current_x = max(self.final_x, self.current_x - step)
            try:
                self.toast.geometry(f"+{self.current_x}+{self.final_y}")
                self.toast.after(10, self._animate_in)
            except:
                pass
        else:
            self.current_x = self.final_x
            try:
                self.toast.geometry(f"+{self.final_x}+{self.final_y}")
            except:
                pass

    def close(self):
        """Close the toast with fade out."""
        if self._closed:
            return
        self._closed = True
        self._fade_out()

    def _fade_out(self, alpha=0.97):
        """Fade out animation."""
        if alpha > 0:
            try:
                self.toast.attributes("-alpha", alpha)
                self.toast.after(20, lambda: self._fade_out(alpha - 0.1))
            except:
                self._destroy()
        else:
            self._destroy()

    def _destroy(self):
        """Destroy the toast window."""
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
        return toast

    def info(self, message: str, duration: int = 3000):
        """Show an info toast."""
        return self.show(message, "info", duration)

    def success(self, message: str, duration: int = 3000):
        """Show a success toast."""
        return self.show(message, "success", duration)

    def warning(self, message: str, duration: int = 3000):
        """Show a warning toast."""
        return self.show(message, "warning", duration)

    def error(self, message: str, duration: int = 5000):
        """Show an error toast (longer duration by default)."""
        return self.show(message, "error", duration)


# Demo
if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("800x600")
    root.title("Toast Demo")
    root.configure(bg="#1a1a2e")

    manager = ToastManager(root)

    frame = tk.Frame(root, bg="#1a1a2e")
    frame.pack(expand=True)

    tk.Button(frame, text="Info Toast",
              command=lambda: manager.info("Data has been refreshed from Bloomberg")).pack(pady=10)
    tk.Button(frame, text="Success Toast",
              command=lambda: manager.success("Rates confirmed and saved for 2026-01-16")).pack(pady=10)
    tk.Button(frame, text="Warning Toast",
              command=lambda: manager.warning("Some values may be stale")).pack(pady=10)
    tk.Button(frame, text="Error Toast",
              command=lambda: manager.error("Failed to connect to Bloomberg API")).pack(pady=10)

    root.mainloop()
