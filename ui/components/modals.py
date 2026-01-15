"""
Modal Components - Nordic Light Design System
==============================================
Themed modal dialogs replacing native tkinter dialogs.
"""

import tkinter as tk
from typing import Optional, Callable, List
from ..theme import COLORS, FONTS, SPACING, ICONS


class ModalOverlay(tk.Toplevel):
    """
    Base modal overlay with dimmed background.
    All modals should inherit from this.
    """

    def __init__(
        self,
        parent,
        title: str = "",
        width: int = 400,
        height: int = None,
        closable: bool = True,
        **kwargs
    ):
        super().__init__(parent)

        self.result = None
        self._closable = closable

        # Configure window
        self.title(title)
        self.configure(bg=COLORS.SURFACE)
        self.resizable(False, False)

        # Remove window decorations for custom look
        self.overrideredirect(True)

        # Center on parent
        self.transient(parent)
        self.grab_set()

        # Calculate position
        parent.update_idletasks()
        px = parent.winfo_rootx()
        py = parent.winfo_rooty()
        pw = parent.winfo_width()
        ph = parent.winfo_height()

        x = px + (pw - width) // 2
        y = py + (ph - (height or 200)) // 2

        self.geometry(f"{width}x{height if height else ''}+{x}+{y}")

        # Build modal structure
        self._build_structure(title, closable)

        # Bindings
        if closable:
            self.bind("<Escape>", lambda e: self.close())

        # Focus
        self.focus_set()

    def _build_structure(self, title: str, closable: bool):
        """Build the modal structure with header and content area."""
        # Outer border frame
        self._border = tk.Frame(
            self,
            bg=COLORS.BORDER,
            highlightthickness=0
        )
        self._border.pack(fill="both", expand=True, padx=1, pady=1)

        # Inner container
        self._container = tk.Frame(self._border, bg=COLORS.SURFACE)
        self._container.pack(fill="both", expand=True)

        # Header
        if title:
            header = tk.Frame(self._container, bg=COLORS.SURFACE)
            header.pack(fill="x", padx=SPACING.LG, pady=(SPACING.LG, SPACING.MD))

            tk.Label(
                header,
                text=title,
                fg=COLORS.TEXT,
                bg=COLORS.SURFACE,
                font=FONTS.H3
            ).pack(side="left")

            if closable:
                close_btn = tk.Label(
                    header,
                    text=ICONS.CLOSE,
                    fg=COLORS.TEXT_MUTED,
                    bg=COLORS.SURFACE,
                    font=(FONTS.BODY[0], 14),
                    cursor="hand2"
                )
                close_btn.pack(side="right")
                close_btn.bind("<Button-1>", lambda e: self.close())
                close_btn.bind("<Enter>", lambda e: close_btn.config(fg=COLORS.TEXT))
                close_btn.bind("<Leave>", lambda e: close_btn.config(fg=COLORS.TEXT_MUTED))

        # Content area
        self.content = tk.Frame(self._container, bg=COLORS.SURFACE)
        self.content.pack(fill="both", expand=True, padx=SPACING.LG, pady=SPACING.MD)

        # Footer area (for buttons)
        self.footer = tk.Frame(self._container, bg=COLORS.SURFACE)
        self.footer.pack(fill="x", padx=SPACING.LG, pady=(SPACING.MD, SPACING.LG))

    def close(self, result=None):
        """Close the modal and return result."""
        self.result = result
        self.grab_release()
        self.destroy()

    def wait_for_result(self):
        """Wait for modal to close and return result."""
        self.wait_window()
        return self.result


class ConfirmModal(ModalOverlay):
    """
    Confirmation dialog with Yes/No or custom buttons.
    """

    def __init__(
        self,
        parent,
        title: str = "Confirm",
        message: str = "",
        confirm_text: str = "Confirm",
        cancel_text: str = "Cancel",
        variant: str = "default",  # default, danger
        **kwargs
    ):
        super().__init__(parent, title=title, width=420, **kwargs)

        # Message
        tk.Label(
            self.content,
            text=message,
            fg=COLORS.TEXT_SECONDARY,
            bg=COLORS.SURFACE,
            font=FONTS.BODY,
            wraplength=380,
            justify="left"
        ).pack(anchor="w", pady=(0, SPACING.MD))

        # Buttons
        btn_frame = tk.Frame(self.footer, bg=COLORS.SURFACE)
        btn_frame.pack(side="right")

        # Cancel button
        cancel_btn = tk.Frame(btn_frame, bg=COLORS.SURFACE, cursor="hand2")
        cancel_btn.pack(side="left", padx=(0, SPACING.SM))
        tk.Label(
            cancel_btn,
            text=cancel_text,
            fg=COLORS.TEXT_SECONDARY,
            bg=COLORS.SURFACE,
            font=FONTS.BUTTON,
            padx=16,
            pady=8
        ).pack()
        cancel_btn.bind("<Button-1>", lambda e: self.close(False))
        for child in cancel_btn.winfo_children():
            child.bind("<Button-1>", lambda e: self.close(False))

        # Confirm button
        confirm_bg = COLORS.DANGER if variant == "danger" else COLORS.ACCENT
        confirm_btn = tk.Frame(btn_frame, bg=confirm_bg, cursor="hand2")
        confirm_btn.pack(side="left")
        tk.Label(
            confirm_btn,
            text=confirm_text,
            fg=COLORS.TEXT_INVERSE,
            bg=confirm_bg,
            font=FONTS.BUTTON,
            padx=16,
            pady=8
        ).pack()
        confirm_btn.bind("<Button-1>", lambda e: self.close(True))
        for child in confirm_btn.winfo_children():
            child.bind("<Button-1>", lambda e: self.close(True))


class AlertModal(ModalOverlay):
    """
    Alert/notification modal with single OK button.
    """

    def __init__(
        self,
        parent,
        title: str = "Alert",
        message: str = "",
        variant: str = "info",  # info, success, warning, danger
        button_text: str = "OK",
        **kwargs
    ):
        super().__init__(parent, title=title, width=400, **kwargs)

        # Variant colors
        variants = {
            "info": (COLORS.INFO, ICONS.INFO),
            "success": (COLORS.SUCCESS, ICONS.SUCCESS),
            "warning": (COLORS.WARNING, ICONS.WARNING),
            "danger": (COLORS.DANGER, ICONS.DANGER),
        }
        color, icon = variants.get(variant, variants["info"])

        # Icon and message row
        msg_frame = tk.Frame(self.content, bg=COLORS.SURFACE)
        msg_frame.pack(fill="x", pady=(0, SPACING.MD))

        tk.Label(
            msg_frame,
            text=icon,
            fg=color,
            bg=COLORS.SURFACE,
            font=(FONTS.BODY[0], 20)
        ).pack(side="left", padx=(0, SPACING.MD))

        tk.Label(
            msg_frame,
            text=message,
            fg=COLORS.TEXT,
            bg=COLORS.SURFACE,
            font=FONTS.BODY,
            wraplength=320,
            justify="left"
        ).pack(side="left", fill="x", expand=True)

        # OK button
        ok_btn = tk.Frame(self.footer, bg=COLORS.ACCENT, cursor="hand2")
        ok_btn.pack(side="right")
        tk.Label(
            ok_btn,
            text=button_text,
            fg=COLORS.TEXT_INVERSE,
            bg=COLORS.ACCENT,
            font=FONTS.BUTTON,
            padx=20,
            pady=8
        ).pack()
        ok_btn.bind("<Button-1>", lambda e: self.close(True))
        for child in ok_btn.winfo_children():
            child.bind("<Button-1>", lambda e: self.close(True))


class InputModal(ModalOverlay):
    """
    Modal with text input field.
    """

    def __init__(
        self,
        parent,
        title: str = "Input",
        message: str = "",
        placeholder: str = "",
        initial_value: str = "",
        **kwargs
    ):
        super().__init__(parent, title=title, width=420, **kwargs)

        # Message
        if message:
            tk.Label(
                self.content,
                text=message,
                fg=COLORS.TEXT_SECONDARY,
                bg=COLORS.SURFACE,
                font=FONTS.BODY,
                wraplength=380,
                justify="left"
            ).pack(anchor="w", pady=(0, SPACING.SM))

        # Input field
        self._entry = tk.Entry(
            self.content,
            font=FONTS.BODY,
            bg=COLORS.SURFACE,
            fg=COLORS.TEXT,
            insertbackground=COLORS.TEXT,
            highlightbackground=COLORS.BORDER,
            highlightthickness=1,
            relief="flat"
        )
        self._entry.pack(fill="x", pady=(0, SPACING.MD), ipady=8)
        self._entry.insert(0, initial_value)
        self._entry.focus_set()
        self._entry.bind("<Return>", lambda e: self._submit())

        # Buttons
        btn_frame = tk.Frame(self.footer, bg=COLORS.SURFACE)
        btn_frame.pack(side="right")

        # Cancel
        cancel_btn = tk.Frame(btn_frame, bg=COLORS.SURFACE, cursor="hand2")
        cancel_btn.pack(side="left", padx=(0, SPACING.SM))
        tk.Label(
            cancel_btn,
            text="Cancel",
            fg=COLORS.TEXT_SECONDARY,
            bg=COLORS.SURFACE,
            font=FONTS.BUTTON,
            padx=16,
            pady=8
        ).pack()
        cancel_btn.bind("<Button-1>", lambda e: self.close(None))
        for child in cancel_btn.winfo_children():
            child.bind("<Button-1>", lambda e: self.close(None))

        # Submit
        submit_btn = tk.Frame(btn_frame, bg=COLORS.ACCENT, cursor="hand2")
        submit_btn.pack(side="left")
        tk.Label(
            submit_btn,
            text="Submit",
            fg=COLORS.TEXT_INVERSE,
            bg=COLORS.ACCENT,
            font=FONTS.BUTTON,
            padx=16,
            pady=8
        ).pack()
        submit_btn.bind("<Button-1>", lambda e: self._submit())
        for child in submit_btn.winfo_children():
            child.bind("<Button-1>", lambda e: self._submit())

    def _submit(self):
        """Submit the input value."""
        self.close(self._entry.get())


class SelectModal(ModalOverlay):
    """
    Modal with selectable options list.
    """

    def __init__(
        self,
        parent,
        title: str = "Select",
        message: str = "",
        options: List[str] = None,
        **kwargs
    ):
        super().__init__(parent, title=title, width=400, **kwargs)

        options = options or []

        # Message
        if message:
            tk.Label(
                self.content,
                text=message,
                fg=COLORS.TEXT_SECONDARY,
                bg=COLORS.SURFACE,
                font=FONTS.BODY
            ).pack(anchor="w", pady=(0, SPACING.MD))

        # Options list
        for i, option in enumerate(options):
            opt_frame = tk.Frame(
                self.content,
                bg=COLORS.SURFACE,
                cursor="hand2"
            )
            opt_frame.pack(fill="x", pady=2)

            opt_label = tk.Label(
                opt_frame,
                text=option,
                fg=COLORS.TEXT,
                bg=COLORS.SURFACE,
                font=FONTS.BODY,
                anchor="w",
                padx=SPACING.MD,
                pady=SPACING.SM
            )
            opt_label.pack(fill="x")

            # Hover effect
            def on_enter(e, frame=opt_frame, label=opt_label):
                frame.configure(bg=COLORS.ACCENT_LIGHT)
                label.configure(bg=COLORS.ACCENT_LIGHT)

            def on_leave(e, frame=opt_frame, label=opt_label):
                frame.configure(bg=COLORS.SURFACE)
                label.configure(bg=COLORS.SURFACE)

            def on_click(e, value=option):
                self.close(value)

            opt_frame.bind("<Enter>", on_enter)
            opt_frame.bind("<Leave>", on_leave)
            opt_frame.bind("<Button-1>", on_click)
            opt_label.bind("<Enter>", on_enter)
            opt_label.bind("<Leave>", on_leave)
            opt_label.bind("<Button-1>", on_click)

        # Cancel button
        cancel_btn = tk.Frame(self.footer, bg=COLORS.CHIP_BG, cursor="hand2")
        cancel_btn.pack(side="right")
        tk.Label(
            cancel_btn,
            text="Cancel",
            fg=COLORS.TEXT_SECONDARY,
            bg=COLORS.CHIP_BG,
            font=FONTS.BUTTON,
            padx=16,
            pady=8
        ).pack()
        cancel_btn.bind("<Button-1>", lambda e: self.close(None))
        for child in cancel_btn.winfo_children():
            child.bind("<Button-1>", lambda e: self.close(None))


class ProgressModal(ModalOverlay):
    """
    Modal showing progress indicator.
    """

    def __init__(
        self,
        parent,
        title: str = "Loading",
        message: str = "Please wait...",
        **kwargs
    ):
        super().__init__(parent, title=title, width=350, closable=False, **kwargs)

        # Spinner (using Unicode)
        self._spinner_chars = ["|", "/", "-", "\\"]
        self._spinner_idx = 0

        self._spinner = tk.Label(
            self.content,
            text=self._spinner_chars[0],
            fg=COLORS.ACCENT,
            bg=COLORS.SURFACE,
            font=(FONTS.BODY[0], 24)
        )
        self._spinner.pack(pady=(0, SPACING.MD))

        # Message
        self._message = tk.Label(
            self.content,
            text=message,
            fg=COLORS.TEXT_SECONDARY,
            bg=COLORS.SURFACE,
            font=FONTS.BODY
        )
        self._message.pack()

        # Start animation
        self._animate()

    def _animate(self):
        """Animate the spinner."""
        self._spinner_idx = (self._spinner_idx + 1) % len(self._spinner_chars)
        self._spinner.configure(text=self._spinner_chars[self._spinner_idx])
        self._animation_id = self.after(100, self._animate)

    def set_message(self, message: str):
        """Update the progress message."""
        self._message.configure(text=message)

    def close(self, result=None):
        """Override to cancel animation."""
        if hasattr(self, '_animation_id'):
            self.after_cancel(self._animation_id)
        super().close(result)


# Convenience functions (replacing tkinter.messagebox)
def show_info(parent, title: str, message: str) -> bool:
    """Show info modal."""
    modal = AlertModal(parent, title=title, message=message, variant="info")
    return modal.wait_for_result()


def show_warning(parent, title: str, message: str) -> bool:
    """Show warning modal."""
    modal = AlertModal(parent, title=title, message=message, variant="warning")
    return modal.wait_for_result()


def show_error(parent, title: str, message: str) -> bool:
    """Show error modal."""
    modal = AlertModal(parent, title=title, message=message, variant="danger")
    return modal.wait_for_result()


def show_success(parent, title: str, message: str) -> bool:
    """Show success modal."""
    modal = AlertModal(parent, title=title, message=message, variant="success")
    return modal.wait_for_result()


def ask_confirm(parent, title: str, message: str, variant: str = "default") -> bool:
    """Show confirmation modal and return True/False."""
    modal = ConfirmModal(parent, title=title, message=message, variant=variant)
    return modal.wait_for_result()


def ask_input(parent, title: str, message: str = "", initial: str = "") -> Optional[str]:
    """Show input modal and return entered text or None."""
    modal = InputModal(parent, title=title, message=message, initial_value=initial)
    return modal.wait_for_result()


def ask_select(parent, title: str, options: List[str], message: str = "") -> Optional[str]:
    """Show select modal and return chosen option or None."""
    modal = SelectModal(parent, title=title, message=message, options=options)
    return modal.wait_for_result()
