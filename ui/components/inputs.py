"""
Input Components - Nordic Light Design System
==============================================
Themed form inputs with consistent styling.
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, Callable, List
from ..theme import COLORS, FONTS, SPACING


class ThemedEntry(tk.Frame):
    """
    Themed text entry with label and validation support.
    """

    def __init__(
        self,
        parent,
        label: str = "",
        placeholder: str = "",
        width: int = None,
        validate_func: Optional[Callable] = None,
        on_change: Optional[Callable] = None,
        **kwargs
    ):
        super().__init__(parent, bg=COLORS.SURFACE, **kwargs)

        self._placeholder = placeholder
        self._has_placeholder = False
        self.validate_func = validate_func
        self.on_change = on_change

        # Label
        if label:
            tk.Label(
                self,
                text=label,
                fg=COLORS.TEXT_SECONDARY,
                bg=COLORS.SURFACE,
                font=FONTS.LABEL,
                anchor="w"
            ).pack(fill="x", pady=(0, 4))

        # Entry container (for border effect)
        self._entry_frame = tk.Frame(
            self,
            bg=COLORS.BORDER,
            highlightthickness=0
        )
        self._entry_frame.pack(fill="x")

        # Entry widget
        self._entry = tk.Entry(
            self._entry_frame,
            font=FONTS.BODY,
            bg=COLORS.SURFACE,
            fg=COLORS.TEXT,
            insertbackground=COLORS.TEXT,
            relief="flat",
            highlightthickness=0
        )
        self._entry.pack(fill="x", padx=1, pady=1, ipady=8)

        if width:
            self._entry.configure(width=width)

        # Placeholder
        if placeholder:
            self._show_placeholder()

        # Bindings
        self._entry.bind("<FocusIn>", self._on_focus_in)
        self._entry.bind("<FocusOut>", self._on_focus_out)
        self._entry.bind("<KeyRelease>", self._on_key_release)

    def _show_placeholder(self):
        """Show placeholder text."""
        if not self._entry.get():
            self._entry.insert(0, self._placeholder)
            self._entry.configure(fg=COLORS.TEXT_PLACEHOLDER)
            self._has_placeholder = True

    def _hide_placeholder(self):
        """Hide placeholder text."""
        if self._has_placeholder:
            self._entry.delete(0, "end")
            self._entry.configure(fg=COLORS.TEXT)
            self._has_placeholder = False

    def _on_focus_in(self, event=None):
        """Handle focus in."""
        self._hide_placeholder()
        self._entry_frame.configure(bg=COLORS.ACCENT)

    def _on_focus_out(self, event=None):
        """Handle focus out."""
        self._entry_frame.configure(bg=COLORS.BORDER)
        if not self._entry.get() and self._placeholder:
            self._show_placeholder()
        self._validate()

    def _on_key_release(self, event=None):
        """Handle key release."""
        if self.on_change:
            self.on_change(self.get())

    def _validate(self) -> bool:
        """Run validation."""
        if self.validate_func:
            is_valid = self.validate_func(self.get())
            if not is_valid:
                self._entry_frame.configure(bg=COLORS.DANGER)
            return is_valid
        return True

    def get(self) -> str:
        """Get entry value."""
        if self._has_placeholder:
            return ""
        return self._entry.get()

    def set(self, value: str):
        """Set entry value."""
        self._hide_placeholder()
        self._entry.delete(0, "end")
        self._entry.insert(0, value)

    def clear(self):
        """Clear entry and show placeholder."""
        self._entry.delete(0, "end")
        if self._placeholder:
            self._show_placeholder()

    def set_error(self, has_error: bool = True):
        """Set error state."""
        self._entry_frame.configure(
            bg=COLORS.DANGER if has_error else COLORS.BORDER
        )


class ThemedCombobox(tk.Frame):
    """
    Themed dropdown/combobox with label support.
    """

    def __init__(
        self,
        parent,
        label: str = "",
        values: List[str] = None,
        default: str = None,
        width: int = None,
        on_change: Optional[Callable] = None,
        **kwargs
    ):
        super().__init__(parent, bg=COLORS.SURFACE, **kwargs)

        self.on_change = on_change
        values = values or []

        # Label
        if label:
            tk.Label(
                self,
                text=label,
                fg=COLORS.TEXT_SECONDARY,
                bg=COLORS.SURFACE,
                font=FONTS.LABEL,
                anchor="w"
            ).pack(fill="x", pady=(0, 4))

        # Style combobox
        style = ttk.Style()
        style.configure(
            "Nordic.TCombobox",
            fieldbackground=COLORS.SURFACE,
            background=COLORS.SURFACE,
            foreground=COLORS.TEXT,
            arrowcolor=COLORS.TEXT_MUTED,
            padding=8
        )

        # Combobox
        self._var = tk.StringVar(value=default or (values[0] if values else ""))
        self._combo = ttk.Combobox(
            self,
            textvariable=self._var,
            values=values,
            state="readonly",
            style="Nordic.TCombobox",
            font=FONTS.BODY
        )
        self._combo.pack(fill="x")

        if width:
            self._combo.configure(width=width)

        # Binding
        self._combo.bind("<<ComboboxSelected>>", self._on_select)

    def _on_select(self, event=None):
        """Handle selection change."""
        if self.on_change:
            self.on_change(self.get())

    def get(self) -> str:
        """Get selected value."""
        return self._var.get()

    def set(self, value: str):
        """Set selected value."""
        self._var.set(value)

    def set_values(self, values: List[str]):
        """Update available values."""
        self._combo.configure(values=values)


class ThemedCheckbox(tk.Frame):
    """
    Themed checkbox with custom styling.
    """

    def __init__(
        self,
        parent,
        text: str = "",
        checked: bool = False,
        on_change: Optional[Callable] = None,
        **kwargs
    ):
        super().__init__(parent, bg=COLORS.SURFACE, cursor="hand2", **kwargs)

        self._checked = checked
        self.on_change = on_change

        # Checkbox indicator
        self._indicator = tk.Label(
            self,
            text="\u2713" if checked else " ",
            fg=COLORS.TEXT_INVERSE if checked else COLORS.BORDER,
            bg=COLORS.ACCENT if checked else COLORS.SURFACE,
            font=(FONTS.BODY[0], 10),
            width=2,
            height=1,
            relief="solid",
            borderwidth=1
        )
        self._indicator.pack(side="left", padx=(0, 8))

        # Label
        if text:
            self._label = tk.Label(
                self,
                text=text,
                fg=COLORS.TEXT,
                bg=COLORS.SURFACE,
                font=FONTS.BODY
            )
            self._label.pack(side="left")
            self._label.bind("<Button-1>", self._toggle)

        # Bindings
        self.bind("<Button-1>", self._toggle)
        self._indicator.bind("<Button-1>", self._toggle)

    def _toggle(self, event=None):
        """Toggle checkbox state."""
        self._checked = not self._checked
        self._update_visual()
        if self.on_change:
            self.on_change(self._checked)

    def _update_visual(self):
        """Update visual state."""
        if self._checked:
            self._indicator.configure(
                text="\u2713",
                fg=COLORS.TEXT_INVERSE,
                bg=COLORS.ACCENT
            )
        else:
            self._indicator.configure(
                text=" ",
                fg=COLORS.BORDER,
                bg=COLORS.SURFACE
            )

    def get(self) -> bool:
        """Get checkbox state."""
        return self._checked

    def set(self, checked: bool):
        """Set checkbox state."""
        self._checked = checked
        self._update_visual()


class ThemedRadioGroup(tk.Frame):
    """
    Themed radio button group.
    """

    def __init__(
        self,
        parent,
        label: str = "",
        options: List[str] = None,
        default: str = None,
        orientation: str = "vertical",  # vertical, horizontal
        on_change: Optional[Callable] = None,
        **kwargs
    ):
        super().__init__(parent, bg=COLORS.SURFACE, **kwargs)

        self.on_change = on_change
        options = options or []

        # Label
        if label:
            tk.Label(
                self,
                text=label,
                fg=COLORS.TEXT_SECONDARY,
                bg=COLORS.SURFACE,
                font=FONTS.LABEL,
                anchor="w"
            ).pack(fill="x", pady=(0, 8))

        # Options container
        opts_frame = tk.Frame(self, bg=COLORS.SURFACE)
        opts_frame.pack(fill="x")

        self._var = tk.StringVar(value=default or (options[0] if options else ""))
        self._radios = {}

        for opt in options:
            radio_frame = tk.Frame(opts_frame, bg=COLORS.SURFACE, cursor="hand2")
            if orientation == "vertical":
                radio_frame.pack(fill="x", pady=2)
            else:
                radio_frame.pack(side="left", padx=(0, SPACING.MD))

            # Radio indicator
            indicator = tk.Label(
                radio_frame,
                text="\u25CF" if self._var.get() == opt else "\u25CB",
                fg=COLORS.ACCENT if self._var.get() == opt else COLORS.TEXT_MUTED,
                bg=COLORS.SURFACE,
                font=(FONTS.BODY[0], 12)
            )
            indicator.pack(side="left", padx=(0, 6))

            # Label
            label_widget = tk.Label(
                radio_frame,
                text=opt,
                fg=COLORS.TEXT,
                bg=COLORS.SURFACE,
                font=FONTS.BODY
            )
            label_widget.pack(side="left")

            # Store reference
            self._radios[opt] = {"frame": radio_frame, "indicator": indicator}

            # Bindings
            def make_handler(option):
                return lambda e: self._select(option)

            radio_frame.bind("<Button-1>", make_handler(opt))
            indicator.bind("<Button-1>", make_handler(opt))
            label_widget.bind("<Button-1>", make_handler(opt))

    def _select(self, option: str):
        """Select an option."""
        self._var.set(option)
        self._update_visuals()
        if self.on_change:
            self.on_change(option)

    def _update_visuals(self):
        """Update radio button visuals."""
        selected = self._var.get()
        for opt, widgets in self._radios.items():
            if opt == selected:
                widgets["indicator"].configure(
                    text="\u25CF",
                    fg=COLORS.ACCENT
                )
            else:
                widgets["indicator"].configure(
                    text="\u25CB",
                    fg=COLORS.TEXT_MUTED
                )

    def get(self) -> str:
        """Get selected option."""
        return self._var.get()

    def set(self, option: str):
        """Set selected option."""
        self._var.set(option)
        self._update_visuals()


class ThemedSpinbox(tk.Frame):
    """
    Themed numeric spinbox.
    """

    def __init__(
        self,
        parent,
        label: str = "",
        from_: float = 0,
        to: float = 100,
        increment: float = 1,
        default: float = None,
        on_change: Optional[Callable] = None,
        **kwargs
    ):
        super().__init__(parent, bg=COLORS.SURFACE, **kwargs)

        self.on_change = on_change

        # Label
        if label:
            tk.Label(
                self,
                text=label,
                fg=COLORS.TEXT_SECONDARY,
                bg=COLORS.SURFACE,
                font=FONTS.LABEL,
                anchor="w"
            ).pack(fill="x", pady=(0, 4))

        # Spinbox container
        spin_frame = tk.Frame(self, bg=COLORS.BORDER)
        spin_frame.pack(fill="x")

        self._var = tk.DoubleVar(value=default if default is not None else from_)

        self._spinbox = tk.Spinbox(
            spin_frame,
            from_=from_,
            to=to,
            increment=increment,
            textvariable=self._var,
            font=FONTS.BODY,
            bg=COLORS.SURFACE,
            fg=COLORS.TEXT,
            buttonbackground=COLORS.CHIP_BG,
            relief="flat",
            highlightthickness=0
        )
        self._spinbox.pack(fill="x", padx=1, pady=1, ipady=6)

        # Binding
        self._spinbox.bind("<KeyRelease>", self._on_value_change)
        self._spinbox.bind("<<Increment>>", self._on_value_change)
        self._spinbox.bind("<<Decrement>>", self._on_value_change)

    def _on_value_change(self, event=None):
        """Handle value change."""
        if self.on_change:
            try:
                self.on_change(self._var.get())
            except tk.TclError:
                pass

    def get(self) -> float:
        """Get current value."""
        try:
            return self._var.get()
        except tk.TclError:
            return 0

    def set(self, value: float):
        """Set value."""
        self._var.set(value)


class SearchEntry(tk.Frame):
    """
    Search input with icon and clear button.
    """

    def __init__(
        self,
        parent,
        placeholder: str = "Search...",
        on_search: Optional[Callable] = None,
        **kwargs
    ):
        super().__init__(parent, bg=COLORS.CHIP_BG, **kwargs)

        self._placeholder = placeholder
        self._has_placeholder = False
        self.on_search = on_search

        content = tk.Frame(self, bg=COLORS.CHIP_BG)
        content.pack(fill="x", padx=8, pady=4)

        # Search icon
        tk.Label(
            content,
            text="\u26B2",  # Search symbol
            fg=COLORS.TEXT_MUTED,
            bg=COLORS.CHIP_BG,
            font=(FONTS.BODY[0], 11)
        ).pack(side="left", padx=(0, 6))

        # Entry
        self._entry = tk.Entry(
            content,
            font=FONTS.BODY,
            bg=COLORS.CHIP_BG,
            fg=COLORS.TEXT,
            insertbackground=COLORS.TEXT,
            relief="flat",
            highlightthickness=0
        )
        self._entry.pack(side="left", fill="x", expand=True)

        # Clear button
        self._clear_btn = tk.Label(
            content,
            text="\u2715",
            fg=COLORS.TEXT_MUTED,
            bg=COLORS.CHIP_BG,
            font=(FONTS.BODY[0], 10),
            cursor="hand2"
        )
        # Initially hidden
        self._clear_btn.bind("<Button-1>", self._clear)

        # Show placeholder
        self._show_placeholder()

        # Bindings
        self._entry.bind("<FocusIn>", self._on_focus_in)
        self._entry.bind("<FocusOut>", self._on_focus_out)
        self._entry.bind("<KeyRelease>", self._on_key_release)
        self._entry.bind("<Return>", self._on_submit)

    def _show_placeholder(self):
        """Show placeholder."""
        if not self._entry.get():
            self._entry.insert(0, self._placeholder)
            self._entry.configure(fg=COLORS.TEXT_PLACEHOLDER)
            self._has_placeholder = True
            self._clear_btn.pack_forget()

    def _hide_placeholder(self):
        """Hide placeholder."""
        if self._has_placeholder:
            self._entry.delete(0, "end")
            self._entry.configure(fg=COLORS.TEXT)
            self._has_placeholder = False

    def _on_focus_in(self, event=None):
        """Handle focus in."""
        self._hide_placeholder()

    def _on_focus_out(self, event=None):
        """Handle focus out."""
        if not self._entry.get():
            self._show_placeholder()

    def _on_key_release(self, event=None):
        """Handle key release."""
        if self._entry.get() and not self._has_placeholder:
            self._clear_btn.pack(side="right")
        else:
            self._clear_btn.pack_forget()

    def _on_submit(self, event=None):
        """Handle Enter key."""
        if self.on_search and not self._has_placeholder:
            self.on_search(self._entry.get())

    def _clear(self, event=None):
        """Clear the search."""
        self._entry.delete(0, "end")
        self._clear_btn.pack_forget()
        self._entry.focus_set()
        if self.on_search:
            self.on_search("")

    def get(self) -> str:
        """Get search value."""
        if self._has_placeholder:
            return ""
        return self._entry.get()

    def set(self, value: str):
        """Set search value."""
        self._hide_placeholder()
        self._entry.delete(0, "end")
        self._entry.insert(0, value)
        if value:
            self._clear_btn.pack(side="right")
