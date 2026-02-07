"""
Common utilities shared across page modules.
Contains ToolTip and BaseFrame.
"""
import tkinter as tk

from ctk_compat import ctk, CTK_AVAILABLE
from config import THEME

# Use CTk frame as base if available
BaseFrame = ctk.CTkFrame if CTK_AVAILABLE else tk.Frame


class ToolTip:
    """Tooltip that follows cursor and stays visible while hovering."""
    def __init__(self, widget, text_func, delay=400):
        self.widget = widget
        self.text_func = text_func
        self.tooltip_window = None
        self._show_id = None
        self._delay = delay
        self._mouse_over = False
        # Use add="+" to not replace existing bindings
        widget.bind("<Enter>", self._on_enter, add="+")
        widget.bind("<Leave>", self._on_leave, add="+")
        widget.bind("<Motion>", self._on_motion, add="+")

    def _on_enter(self, event=None):
        """Mouse entered widget."""
        self._mouse_over = True
        self._schedule_show()

    def _on_leave(self, event=None):
        """Mouse left widget - check if really left."""
        self._mouse_over = False
        # Small delay before hiding to handle flicker
        self.widget.after(50, self._check_and_hide)

    def _on_motion(self, event=None):
        """Mouse moving over widget - update tooltip position."""
        if self.tooltip_window:
            x = self.widget.winfo_rootx() + event.x + 15
            y = self.widget.winfo_rooty() + event.y + 15
            self.tooltip_window.wm_geometry(f"+{x}+{y}")

    def _schedule_show(self):
        """Schedule tooltip to show after delay."""
        self._cancel_scheduled()
        self._show_id = self.widget.after(self._delay, self._do_show)

    def _cancel_scheduled(self):
        """Cancel any scheduled show."""
        if self._show_id:
            self.widget.after_cancel(self._show_id)
            self._show_id = None

    def _check_and_hide(self):
        """Hide only if mouse is really not over widget."""
        if not self._mouse_over:
            self._cancel_scheduled()
            self._do_hide()

    def _do_show(self):
        """Actually show the tooltip."""
        self._show_id = None
        if not self._mouse_over:
            return
        try:
            text = self.text_func()
        except Exception:
            text = None
        if text and self.tooltip_window is None:
            # Position near cursor
            try:
                x = self.widget.winfo_pointerx() + 15
                y = self.widget.winfo_pointery() + 15
            except Exception:
                x = self.widget.winfo_rootx() + 20
                y = self.widget.winfo_rooty() + 20
            self.tooltip_window = tk.Toplevel(self.widget)
            self.tooltip_window.wm_overrideredirect(True)
            self.tooltip_window.wm_geometry(f"+{x}+{y}")
            # Make tooltip non-interactive so it doesn't steal focus
            self.tooltip_window.wm_attributes("-topmost", True)
            label = tk.Label(
                self.tooltip_window,
                text=text,
                background=THEME["bg_card"],
                foreground=THEME["accent"],
                relief="solid",
                borderwidth=1,
                font=("Consolas", 10, "bold"),
                padx=8,
                pady=4
            )
            label.pack()

    def _do_hide(self):
        """Actually hide the tooltip."""
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None
