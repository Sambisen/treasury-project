"""
CustomTkinter Compatibility Layer

Försöker importera CustomTkinter. Om det inte finns, faller tillbaka på
standard Tkinter med wrapper-klasser som efterliknar CustomTkinter API.

Användning:
    from ctk_compat import ctk, CTK_AVAILABLE

    # Alla CTk-klasser finns tillgängliga via ctk.*
    window = ctk.CTk()
    button = ctk.CTkButton(window, text="Click me")

    # Kontrollera om äkta CustomTkinter används
    if CTK_AVAILABLE:
        print("Kör med CustomTkinter (PROD mode)")
    else:
        print("Kör med Tkinter fallback (DEV mode)")
"""

import tkinter as tk
from tkinter import ttk
from typing import Any, Callable, Optional, Tuple, Union
import sys
import os

# ============================================================================
# FÖRSÖK IMPORTERA CUSTOMTKINTER
# ============================================================================

# Miljövariabel för att tvinga fallback-läge (bra för testning)
# Sätt FORCE_TK_FALLBACK=1 för att alltid använda Tkinter istället för CustomTkinter
FORCE_FALLBACK = os.environ.get("FORCE_TK_FALLBACK", "").lower() in ("1", "true", "yes")

if FORCE_FALLBACK:
    CTK_AVAILABLE = False
    print("[ctk_compat] FORCE_TK_FALLBACK=1 - tvingar Tkinter fallback (DEV mode)")
else:
    try:
        import customtkinter as ctk
        CTK_AVAILABLE = True
        print("[ctk_compat] CustomTkinter tillgängligt - använder PROD mode")
    except ImportError:
        CTK_AVAILABLE = False
        print("[ctk_compat] CustomTkinter saknas - använder Tkinter fallback (DEV mode)")

if not CTK_AVAILABLE:
    # ========================================================================
    # TKINTER FALLBACK IMPLEMENTATION
    # ========================================================================

    class _TkinterFallback:
        """Namespace för Tkinter fallback-klasser som efterliknar CustomTkinter API."""

        # Appearance settings (no-op i fallback)
        @staticmethod
        def set_appearance_mode(mode: str):
            """No-op - Tkinter har inte dark/light mode."""
            pass

        @staticmethod
        def set_default_color_theme(theme: str):
            """No-op - Tkinter har inte färgteman."""
            pass

        @staticmethod
        def set_widget_scaling(scale: float):
            """No-op - Tkinter hanterar inte widget scaling."""
            pass

        @staticmethod
        def set_window_scaling(scale: float):
            """No-op - Tkinter hanterar inte window scaling."""
            pass

        # ====================================================================
        # HELPER FUNCTIONS
        # ====================================================================

        @staticmethod
        def _convert_color(color: Any) -> Optional[str]:
            """Konvertera CTk färgformat till Tkinter."""
            if color is None or color == "transparent":
                return None
            if isinstance(color, (list, tuple)):
                # CTk använder (light_color, dark_color) - ta första
                return color[0] if color else None
            return str(color)

        @staticmethod
        def _filter_kwargs(kwargs: dict) -> dict:
            """Filtrera bort CTk-specifika parametrar som Tkinter inte förstår."""
            ctk_only = {
                'corner_radius', 'border_width', 'border_color', 'border_spacing',
                'fg_color', 'bg_color', 'hover_color', 'text_color', 'text_color_disabled',
                'button_color', 'button_hover_color', 'progress_color', 'scrollbar_button_color',
                'scrollbar_button_hover_color', 'dropdown_fg_color', 'dropdown_hover_color',
                'dropdown_text_color', 'dynamic_resizing', 'anchor', 'compound',
                'hover', 'state', 'variable', 'values', 'dropdown_font',
                'segmented_button_fg_color', 'segmented_button_selected_color',
                'segmented_button_selected_hover_color', 'segmented_button_unselected_color',
                'segmented_button_unselected_hover_color', 'require_redraw',
                'selected_color', 'selected_hover_color', 'unselected_color',
                'unselected_hover_color', 'checkmark_color', 'round_width_to_even_numbers',
                'round_height_to_even_numbers', 'button_length', 'orientation',
                'mode', 'determinate_speed', 'indeterminate_speed', 'wrap',
                'label_fg_color', 'label_text_color', 'label_font', 'label_anchor',
                'input_type', 'image', 'switch_width', 'switch_height'
            }
            filtered = {}
            for k, v in kwargs.items():
                if k not in ctk_only:
                    filtered[k] = v
            return filtered

        # ====================================================================
        # WINDOW CLASSES
        # ====================================================================

        class CTk(tk.Tk):
            """Fallback för CTk huvudfönster."""

            def __init__(self, fg_color=None, **kwargs):
                kwargs = _TkinterFallback._filter_kwargs(kwargs)
                super().__init__(**kwargs)
                if fg_color:
                    color = _TkinterFallback._convert_color(fg_color)
                    if color:
                        super().configure(bg=color)

            def configure(self, **kwargs):
                """Override configure to filter CTk-specific options."""
                if 'fg_color' in kwargs:
                    color = _TkinterFallback._convert_color(kwargs.pop('fg_color'))
                    if color:
                        kwargs['bg'] = color
                kwargs = _TkinterFallback._filter_kwargs(kwargs)
                if kwargs:
                    super().configure(**kwargs)

            def set_appearance_mode(self, mode: str):
                pass

        class CTkToplevel(tk.Toplevel):
            """Fallback för CTkToplevel."""

            def __init__(self, master=None, fg_color=None, **kwargs):
                kwargs = _TkinterFallback._filter_kwargs(kwargs)
                super().__init__(master, **kwargs)
                if fg_color:
                    color = _TkinterFallback._convert_color(fg_color)
                    if color:
                        super().configure(bg=color)

            def configure(self, **kwargs):
                """Override configure to filter CTk-specific options."""
                if 'fg_color' in kwargs:
                    color = _TkinterFallback._convert_color(kwargs.pop('fg_color'))
                    if color:
                        kwargs['bg'] = color
                kwargs = _TkinterFallback._filter_kwargs(kwargs)
                if kwargs:
                    super().configure(**kwargs)

        # ====================================================================
        # FRAME CLASSES
        # ====================================================================

        class CTkFrame(tk.Frame):
            """Fallback för CTkFrame."""

            def __init__(self, master=None, fg_color=None, bg_color=None,
                         corner_radius=None, border_width=None, border_color=None,
                         width=200, height=200, **kwargs):
                kwargs = _TkinterFallback._filter_kwargs(kwargs)

                # Konvertera färger
                bg = _TkinterFallback._convert_color(fg_color or bg_color)
                if bg:
                    kwargs['bg'] = bg

                if width:
                    kwargs['width'] = width
                if height:
                    kwargs['height'] = height

                super().__init__(master, **kwargs)

            def configure(self, **kwargs):
                """Override configure för att hantera CTk-parametrar."""
                if 'fg_color' in kwargs:
                    color = _TkinterFallback._convert_color(kwargs.pop('fg_color'))
                    if color:
                        kwargs['bg'] = color
                kwargs = _TkinterFallback._filter_kwargs(kwargs)
                if kwargs:
                    super().configure(**kwargs)

            def cget(self, key):
                """Override cget för att hantera CTk-parametrar."""
                if key == 'fg_color':
                    return super().cget('bg')
                return super().cget(key)

        class CTkScrollableFrame(tk.Frame):
            """Fallback för CTkScrollableFrame med scrollbar."""

            def __init__(self, master=None, fg_color=None, bg_color=None,
                         corner_radius=None, border_width=None, border_color=None,
                         width=200, height=200, orientation="vertical",
                         scrollbar_fg_color=None, scrollbar_button_color=None,
                         scrollbar_button_hover_color=None, label_text=None,
                         label_fg_color=None, label_text_color=None,
                         label_font=None, label_anchor=None, **kwargs):
                kwargs = _TkinterFallback._filter_kwargs(kwargs)

                bg = _TkinterFallback._convert_color(fg_color or bg_color)
                if bg:
                    kwargs['bg'] = bg

                super().__init__(master, **kwargs)

                # Skapa canvas och scrollbar
                self._canvas = tk.Canvas(self, highlightthickness=0)
                if bg:
                    self._canvas.configure(bg=bg)

                if orientation == "vertical":
                    self._scrollbar = ttk.Scrollbar(self, orient="vertical",
                                                     command=self._canvas.yview)
                    self._canvas.configure(yscrollcommand=self._scrollbar.set)
                    self._scrollbar.pack(side="right", fill="y")
                    self._canvas.pack(side="left", fill="both", expand=True)
                else:
                    self._scrollbar = ttk.Scrollbar(self, orient="horizontal",
                                                     command=self._canvas.xview)
                    self._canvas.configure(xscrollcommand=self._scrollbar.set)
                    self._scrollbar.pack(side="bottom", fill="x")
                    self._canvas.pack(side="top", fill="both", expand=True)

                # Inre frame för innehåll
                self._inner_frame = tk.Frame(self._canvas)
                if bg:
                    self._inner_frame.configure(bg=bg)

                self._canvas_window = self._canvas.create_window(
                    (0, 0), window=self._inner_frame, anchor="nw"
                )

                # Bind resize events
                self._inner_frame.bind("<Configure>", self._on_frame_configure)
                self._canvas.bind("<Configure>", self._on_canvas_configure)

                # Mousewheel scrolling
                self._canvas.bind_all("<MouseWheel>", self._on_mousewheel)
                self._canvas.bind_all("<Button-4>", self._on_mousewheel)
                self._canvas.bind_all("<Button-5>", self._on_mousewheel)

            def _on_frame_configure(self, event):
                self._canvas.configure(scrollregion=self._canvas.bbox("all"))

            def _on_canvas_configure(self, event):
                self._canvas.itemconfig(self._canvas_window, width=event.width)

            def _on_mousewheel(self, event):
                if event.num == 5 or event.delta < 0:
                    self._canvas.yview_scroll(1, "units")
                elif event.num == 4 or event.delta > 0:
                    self._canvas.yview_scroll(-1, "units")

            # Redirect widget placement to inner frame
            def pack(self, *args, **kwargs):
                super().pack(*args, **kwargs)

            def grid(self, *args, **kwargs):
                super().grid(*args, **kwargs)

            def place(self, *args, **kwargs):
                super().place(*args, **kwargs)

            # For adding children - de ska läggas i _inner_frame
            def winfo_children(self):
                return self._inner_frame.winfo_children()

            # Override för att barn ska hamna i inner frame
            def _get_inner_frame(self):
                return self._inner_frame

        # ====================================================================
        # WIDGET CLASSES
        # ====================================================================

        class CTkLabel(tk.Label):
            """Fallback för CTkLabel."""

            def __init__(self, master=None, text="", font=None, text_color=None,
                         fg_color=None, corner_radius=None, anchor=None,
                         compound=None, image=None, width=None, height=None,
                         wraplength=None, justify=None, padx=None, pady=None, **kwargs):
                kwargs = _TkinterFallback._filter_kwargs(kwargs)

                if text:
                    kwargs['text'] = text
                if font:
                    kwargs['font'] = font
                if text_color:
                    color = _TkinterFallback._convert_color(text_color)
                    if color:
                        kwargs['fg'] = color
                if fg_color and fg_color != "transparent":
                    color = _TkinterFallback._convert_color(fg_color)
                    if color:
                        kwargs['bg'] = color
                if anchor:
                    kwargs['anchor'] = anchor
                if compound:
                    kwargs['compound'] = compound
                if width:
                    kwargs['width'] = width
                if wraplength:
                    kwargs['wraplength'] = wraplength
                if justify:
                    kwargs['justify'] = justify
                if padx:
                    kwargs['padx'] = padx
                if pady:
                    kwargs['pady'] = pady

                # Hantera CTkImage
                if image:
                    if hasattr(image, '_light_image'):
                        kwargs['image'] = image._light_image
                    else:
                        kwargs['image'] = image

                super().__init__(master, **kwargs)

            def configure(self, **kwargs):
                if 'text_color' in kwargs:
                    color = _TkinterFallback._convert_color(kwargs.pop('text_color'))
                    if color:
                        kwargs['fg'] = color
                if 'fg_color' in kwargs:
                    color = _TkinterFallback._convert_color(kwargs.pop('fg_color'))
                    if color:
                        kwargs['bg'] = color
                kwargs = _TkinterFallback._filter_kwargs(kwargs)
                if kwargs:
                    super().configure(**kwargs)

            def cget(self, key):
                if key == 'text_color':
                    return super().cget('fg')
                if key == 'fg_color':
                    return super().cget('bg')
                return super().cget(key)

        class CTkButton(tk.Button):
            """Fallback för CTkButton."""

            def __init__(self, master=None, text="", command=None, font=None,
                         fg_color=None, hover_color=None, text_color=None,
                         text_color_disabled=None, corner_radius=None,
                         border_width=None, border_color=None, width=None,
                         height=None, state=None, image=None, compound=None,
                         anchor=None, hover=True, **kwargs):
                kwargs = _TkinterFallback._filter_kwargs(kwargs)

                if text:
                    kwargs['text'] = text
                if command:
                    kwargs['command'] = command
                if font:
                    kwargs['font'] = font
                if fg_color:
                    color = _TkinterFallback._convert_color(fg_color)
                    if color:
                        kwargs['bg'] = color
                if text_color:
                    color = _TkinterFallback._convert_color(text_color)
                    if color:
                        kwargs['fg'] = color
                if width:
                    kwargs['width'] = width
                if height:
                    kwargs['height'] = height
                if state:
                    kwargs['state'] = state
                if compound:
                    kwargs['compound'] = compound
                if anchor:
                    kwargs['anchor'] = anchor

                # Hantera CTkImage
                if image:
                    if hasattr(image, '_light_image'):
                        kwargs['image'] = image._light_image
                    else:
                        kwargs['image'] = image

                super().__init__(master, **kwargs)

            def configure(self, **kwargs):
                if 'fg_color' in kwargs:
                    color = _TkinterFallback._convert_color(kwargs.pop('fg_color'))
                    if color:
                        kwargs['bg'] = color
                if 'text_color' in kwargs:
                    color = _TkinterFallback._convert_color(kwargs.pop('text_color'))
                    if color:
                        kwargs['fg'] = color
                kwargs = _TkinterFallback._filter_kwargs(kwargs)
                if kwargs:
                    super().configure(**kwargs)

        class CTkEntry(tk.Entry):
            """Fallback för CTkEntry."""

            def __init__(self, master=None, font=None, fg_color=None, bg_color=None,
                         text_color=None, placeholder_text=None, placeholder_text_color=None,
                         corner_radius=None, border_width=None, border_color=None,
                         width=140, height=28, state=None, textvariable=None,
                         justify=None, show=None, **kwargs):
                kwargs = _TkinterFallback._filter_kwargs(kwargs)

                if font:
                    kwargs['font'] = font
                if fg_color:
                    color = _TkinterFallback._convert_color(fg_color)
                    if color:
                        kwargs['bg'] = color
                if text_color:
                    color = _TkinterFallback._convert_color(text_color)
                    if color:
                        kwargs['fg'] = color
                if width:
                    kwargs['width'] = width // 7  # Konvertera pixlar till tecken
                if state:
                    kwargs['state'] = state
                if textvariable:
                    kwargs['textvariable'] = textvariable
                if justify:
                    kwargs['justify'] = justify
                if show:
                    kwargs['show'] = show

                super().__init__(master, **kwargs)

                # Placeholder-hantering
                self._placeholder = placeholder_text
                self._placeholder_color = _TkinterFallback._convert_color(
                    placeholder_text_color) or "grey"
                self._default_fg = self.cget('fg')
                self._has_placeholder = False

                if self._placeholder:
                    self._show_placeholder()
                    self.bind("<FocusIn>", self._on_focus_in)
                    self.bind("<FocusOut>", self._on_focus_out)

            def _show_placeholder(self):
                if not self.get():
                    self.insert(0, self._placeholder)
                    self.configure(fg=self._placeholder_color)
                    self._has_placeholder = True

            def _on_focus_in(self, event):
                if self._has_placeholder:
                    self.delete(0, tk.END)
                    self.configure(fg=self._default_fg)
                    self._has_placeholder = False

            def _on_focus_out(self, event):
                if not self.get():
                    self._show_placeholder()

            def configure(self, **kwargs):
                if 'fg_color' in kwargs:
                    color = _TkinterFallback._convert_color(kwargs.pop('fg_color'))
                    if color:
                        kwargs['bg'] = color
                if 'text_color' in kwargs:
                    color = _TkinterFallback._convert_color(kwargs.pop('text_color'))
                    if color:
                        kwargs['fg'] = color
                kwargs = _TkinterFallback._filter_kwargs(kwargs)
                if kwargs:
                    super().configure(**kwargs)

        class CTkTextbox(tk.Text):
            """Fallback för CTkTextbox."""

            def __init__(self, master=None, font=None, fg_color=None, bg_color=None,
                         text_color=None, corner_radius=None, border_width=None,
                         border_color=None, width=200, height=200, state=None,
                         wrap=None, activate_scrollbars=True, scrollbar_button_color=None,
                         scrollbar_button_hover_color=None, **kwargs):
                kwargs = _TkinterFallback._filter_kwargs(kwargs)

                if font:
                    kwargs['font'] = font
                if fg_color:
                    color = _TkinterFallback._convert_color(fg_color)
                    if color:
                        kwargs['bg'] = color
                if text_color:
                    color = _TkinterFallback._convert_color(text_color)
                    if color:
                        kwargs['fg'] = color
                if width:
                    kwargs['width'] = width // 7  # Konvertera pixlar till tecken
                if height:
                    kwargs['height'] = height // 14  # Konvertera pixlar till rader
                if state:
                    kwargs['state'] = state
                if wrap:
                    kwargs['wrap'] = wrap

                super().__init__(master, **kwargs)

            def configure(self, **kwargs):
                if 'fg_color' in kwargs:
                    color = _TkinterFallback._convert_color(kwargs.pop('fg_color'))
                    if color:
                        kwargs['bg'] = color
                if 'text_color' in kwargs:
                    color = _TkinterFallback._convert_color(kwargs.pop('text_color'))
                    if color:
                        kwargs['fg'] = color
                if 'state' in kwargs:
                    state = kwargs['state']
                    if state == 'disabled':
                        kwargs['state'] = 'disabled'
                    else:
                        kwargs['state'] = 'normal'
                kwargs = _TkinterFallback._filter_kwargs(kwargs)
                if kwargs:
                    super().configure(**kwargs)

        class CTkCheckBox(tk.Checkbutton):
            """Fallback för CTkCheckBox."""

            def __init__(self, master=None, text="", font=None, command=None,
                         variable=None, onvalue=True, offvalue=False,
                         fg_color=None, hover_color=None, text_color=None,
                         text_color_disabled=None, corner_radius=None,
                         border_width=None, border_color=None, checkmark_color=None,
                         state=None, hover=True, **kwargs):
                kwargs = _TkinterFallback._filter_kwargs(kwargs)

                if text:
                    kwargs['text'] = text
                if font:
                    kwargs['font'] = font
                if command:
                    kwargs['command'] = command
                if variable:
                    kwargs['variable'] = variable
                if onvalue is not None:
                    kwargs['onvalue'] = onvalue
                if offvalue is not None:
                    kwargs['offvalue'] = offvalue
                if text_color:
                    color = _TkinterFallback._convert_color(text_color)
                    if color:
                        kwargs['fg'] = color
                if state:
                    kwargs['state'] = state

                super().__init__(master, **kwargs)

            def configure(self, **kwargs):
                if 'text_color' in kwargs:
                    color = _TkinterFallback._convert_color(kwargs.pop('text_color'))
                    if color:
                        kwargs['fg'] = color
                kwargs = _TkinterFallback._filter_kwargs(kwargs)
                if kwargs:
                    super().configure(**kwargs)

        class CTkSwitch(tk.Checkbutton):
            """Fallback för CTkSwitch (som checkbox)."""

            def __init__(self, master=None, text="", font=None, command=None,
                         variable=None, onvalue=True, offvalue=False,
                         fg_color=None, progress_color=None, button_color=None,
                         button_hover_color=None, text_color=None,
                         text_color_disabled=None, corner_radius=None,
                         border_width=None, border_color=None, state=None,
                         hover=True, switch_width=None, switch_height=None, **kwargs):
                kwargs = _TkinterFallback._filter_kwargs(kwargs)

                if text:
                    kwargs['text'] = text
                if font:
                    kwargs['font'] = font
                if command:
                    kwargs['command'] = command
                if variable:
                    kwargs['variable'] = variable
                if onvalue is not None:
                    kwargs['onvalue'] = onvalue
                if offvalue is not None:
                    kwargs['offvalue'] = offvalue
                if text_color:
                    color = _TkinterFallback._convert_color(text_color)
                    if color:
                        kwargs['fg'] = color
                if state:
                    kwargs['state'] = state

                super().__init__(master, **kwargs)

            def configure(self, **kwargs):
                if 'text_color' in kwargs:
                    color = _TkinterFallback._convert_color(kwargs.pop('text_color'))
                    if color:
                        kwargs['fg'] = color
                kwargs = _TkinterFallback._filter_kwargs(kwargs)
                if kwargs:
                    super().configure(**kwargs)

            def get(self):
                """Get current value."""
                try:
                    return self.getvar(self.cget('variable'))
                except:
                    return False

            def select(self):
                """Select the switch."""
                super().select()

            def deselect(self):
                """Deselect the switch."""
                super().deselect()

            def toggle(self):
                """Toggle the switch."""
                super().toggle()

        class CTkOptionMenu(ttk.Combobox):
            """Fallback för CTkOptionMenu."""

            def __init__(self, master=None, values=None, command=None, variable=None,
                         font=None, fg_color=None, button_color=None,
                         button_hover_color=None, text_color=None,
                         text_color_disabled=None, dropdown_fg_color=None,
                         dropdown_hover_color=None, dropdown_text_color=None,
                         dropdown_font=None, corner_radius=None, anchor=None,
                         width=None, height=None, state=None, hover=True,
                         dynamic_resizing=True, **kwargs):
                kwargs = _TkinterFallback._filter_kwargs(kwargs)

                if values:
                    kwargs['values'] = values
                if font:
                    kwargs['font'] = font
                if width:
                    kwargs['width'] = width // 7
                if state:
                    kwargs['state'] = state if state != 'normal' else 'readonly'
                else:
                    kwargs['state'] = 'readonly'

                super().__init__(master, **kwargs)

                self._command = command
                self._variable = variable

                if variable:
                    self.set(variable.get())
                elif values:
                    self.set(values[0])

                self.bind("<<ComboboxSelected>>", self._on_select)

            def _on_select(self, event):
                if self._variable:
                    self._variable.set(self.get())
                if self._command:
                    self._command(self.get())

            def configure(self, **kwargs):
                if 'values' in kwargs:
                    self['values'] = kwargs.pop('values')
                kwargs = _TkinterFallback._filter_kwargs(kwargs)
                if kwargs:
                    super().configure(**kwargs)

            def cget(self, key):
                if key == 'values':
                    return list(self['values'])
                return super().cget(key)

        class CTkSlider(tk.Scale):
            """Fallback för CTkSlider."""

            def __init__(self, master=None, from_=0, to=1, number_of_steps=None,
                         command=None, variable=None, orientation="horizontal",
                         fg_color=None, progress_color=None, button_color=None,
                         button_hover_color=None, corner_radius=None,
                         button_corner_radius=None, border_width=None,
                         width=None, height=None, state=None, hover=True, **kwargs):
                kwargs = _TkinterFallback._filter_kwargs(kwargs)

                kwargs['from_'] = from_
                kwargs['to'] = to
                kwargs['orient'] = orientation.upper()

                if command:
                    kwargs['command'] = command
                if variable:
                    kwargs['variable'] = variable
                if width and orientation == "horizontal":
                    kwargs['length'] = width
                if height and orientation == "vertical":
                    kwargs['length'] = height
                if state:
                    kwargs['state'] = state

                kwargs['showvalue'] = 0  # Dölj värde som CTk gör

                if number_of_steps:
                    resolution = (to - from_) / number_of_steps
                    kwargs['resolution'] = resolution

                super().__init__(master, **kwargs)

            def configure(self, **kwargs):
                kwargs = _TkinterFallback._filter_kwargs(kwargs)
                if kwargs:
                    super().configure(**kwargs)

        class CTkProgressBar(ttk.Progressbar):
            """Fallback för CTkProgressBar."""

            def __init__(self, master=None, orientation="horizontal",
                         determinate_speed=1, indeterminate_speed=1,
                         fg_color=None, progress_color=None, corner_radius=None,
                         border_width=None, border_color=None, width=200,
                         height=None, mode="determinate", **kwargs):
                kwargs = _TkinterFallback._filter_kwargs(kwargs)

                kwargs['orient'] = orientation.upper()
                kwargs['mode'] = mode
                kwargs['length'] = width

                super().__init__(master, **kwargs)

                self._value = 0

            def set(self, value: float):
                """Set progress value (0-1)."""
                self._value = value
                self['value'] = value * 100

            def get(self) -> float:
                """Get progress value (0-1)."""
                return self._value

            def start(self):
                """Start indeterminate animation."""
                super().start()

            def stop(self):
                """Stop indeterminate animation."""
                super().stop()

            def configure(self, **kwargs):
                kwargs = _TkinterFallback._filter_kwargs(kwargs)
                if kwargs:
                    super().configure(**kwargs)

        class CTkTabview(ttk.Notebook):
            """Fallback för CTkTabview."""

            def __init__(self, master=None, fg_color=None, bg_color=None,
                         segmented_button_fg_color=None, segmented_button_selected_color=None,
                         segmented_button_selected_hover_color=None,
                         segmented_button_unselected_color=None,
                         segmented_button_unselected_hover_color=None,
                         text_color=None, text_color_disabled=None,
                         corner_radius=None, border_width=None, border_color=None,
                         width=None, height=None, anchor=None, state=None,
                         command=None, **kwargs):
                kwargs = _TkinterFallback._filter_kwargs(kwargs)

                if width:
                    kwargs['width'] = width
                if height:
                    kwargs['height'] = height

                super().__init__(master, **kwargs)

                self._tabs = {}
                self._command = command

                if command:
                    self.bind("<<NotebookTabChanged>>", lambda e: command())

            def add(self, name: str) -> tk.Frame:
                """Add a new tab and return its frame."""
                frame = tk.Frame(self)
                super().add(frame, text=name)
                self._tabs[name] = frame
                return frame

            def tab(self, name: str) -> tk.Frame:
                """Get frame for tab by name."""
                return self._tabs.get(name)

            def delete(self, name: str):
                """Delete a tab."""
                if name in self._tabs:
                    frame = self._tabs.pop(name)
                    super().forget(frame)

            def set(self, name: str):
                """Select a tab by name."""
                if name in self._tabs:
                    super().select(self._tabs[name])

            def get(self) -> str:
                """Get name of currently selected tab."""
                current = super().select()
                for name, frame in self._tabs.items():
                    if str(frame) == current:
                        return name
                return ""

            def configure(self, **kwargs):
                kwargs = _TkinterFallback._filter_kwargs(kwargs)
                if kwargs:
                    super().configure(**kwargs)

        class CTkCanvas(tk.Canvas):
            """Fallback för CTkCanvas (direkt arv)."""
            pass

        class CTkImage:
            """Fallback för CTkImage."""

            def __init__(self, light_image=None, dark_image=None, size=None):
                self._light_image = light_image
                self._dark_image = dark_image or light_image
                self._size = size

                # Resize om PIL finns och size angiven
                if size and light_image:
                    try:
                        from PIL import Image, ImageTk
                        if isinstance(light_image, Image.Image):
                            resized = light_image.resize(size, Image.Resampling.LANCZOS)
                            self._light_image = ImageTk.PhotoImage(resized)
                        if dark_image and isinstance(dark_image, Image.Image):
                            resized = dark_image.resize(size, Image.Resampling.LANCZOS)
                            self._dark_image = ImageTk.PhotoImage(resized)
                    except ImportError:
                        pass

            def configure(self, **kwargs):
                if 'size' in kwargs:
                    self._size = kwargs['size']

            def cget(self, key):
                if key == 'size':
                    return self._size
                return None

        class CTkSegmentedButton(tk.Frame):
            """Fallback för CTkSegmentedButton."""

            def __init__(self, master=None, values=None, command=None, variable=None,
                         font=None, fg_color=None, selected_color=None,
                         selected_hover_color=None, unselected_color=None,
                         unselected_hover_color=None, text_color=None,
                         text_color_disabled=None, corner_radius=None,
                         border_width=None, state=None, dynamic_resizing=True,
                         **kwargs):
                kwargs = _TkinterFallback._filter_kwargs(kwargs)
                super().__init__(master, **kwargs)

                self._values = values or []
                self._command = command
                self._variable = variable
                self._buttons = []
                self._selected = None

                for i, value in enumerate(self._values):
                    btn = tk.Button(self, text=value, relief="flat",
                                    command=lambda v=value: self._on_click(v))
                    if font:
                        btn.configure(font=font)
                    btn.pack(side="left", padx=1)
                    self._buttons.append(btn)

                if self._values:
                    self.set(self._values[0])

            def _on_click(self, value):
                self.set(value)
                if self._command:
                    self._command(value)

            def set(self, value):
                self._selected = value
                if self._variable:
                    self._variable.set(value)
                for btn in self._buttons:
                    if btn.cget('text') == value:
                        btn.configure(relief="sunken")
                    else:
                        btn.configure(relief="flat")

            def get(self):
                return self._selected

            def configure(self, **kwargs):
                if 'values' in kwargs:
                    # Rebuild buttons
                    self._values = kwargs.pop('values')
                    for btn in self._buttons:
                        btn.destroy()
                    self._buttons = []
                    for value in self._values:
                        btn = tk.Button(self, text=value, relief="flat",
                                        command=lambda v=value: self._on_click(v))
                        btn.pack(side="left", padx=1)
                        self._buttons.append(btn)
                    if self._values:
                        self.set(self._values[0])
                kwargs = _TkinterFallback._filter_kwargs(kwargs)

        # ====================================================================
        # SPECIAL VARIABLES
        # ====================================================================

        class StringVar(tk.StringVar):
            """Alias för tk.StringVar."""
            pass

        class IntVar(tk.IntVar):
            """Alias för tk.IntVar."""
            pass

        class DoubleVar(tk.DoubleVar):
            """Alias för tk.DoubleVar."""
            pass

        class BooleanVar(tk.BooleanVar):
            """Alias för tk.BooleanVar."""
            pass

        # ====================================================================
        # CONSTANTS
        # ====================================================================

        # Text alignment
        LEFT = tk.LEFT
        RIGHT = tk.RIGHT
        CENTER = tk.CENTER
        TOP = tk.TOP
        BOTTOM = tk.BOTTOM

        # States
        NORMAL = tk.NORMAL
        DISABLED = tk.DISABLED
        READONLY = "readonly"

        # Other
        END = tk.END
        BOTH = tk.BOTH
        X = tk.X
        Y = tk.Y
        HORIZONTAL = tk.HORIZONTAL
        VERTICAL = tk.VERTICAL
        NSEW = "nsew"
        NS = "ns"
        EW = "ew"
        N = tk.N
        S = tk.S
        E = tk.E
        W = tk.W
        NW = tk.NW
        NE = tk.NE
        SW = tk.SW
        SE = tk.SE

    # Sätt ctk till fallback-klassen
    ctk = _TkinterFallback


# ============================================================================
# EXPORT
# ============================================================================

# Exportera för enkel import
__all__ = ['ctk', 'CTK_AVAILABLE']
