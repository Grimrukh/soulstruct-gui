from __future__ import annotations

__all__ = [
    "WindowError",
    "SmartFrame",
    "SmartMenu",
    "CustomDialog",
    "ToolTip",
    "bind_to_all_children",
    "embed_component",
]

import contextlib
import logging
import tkinter as tk
import typing as tp
from ctypes import windll
from functools import wraps
from tkinter.constants import *
from tkinter import filedialog, messagebox, ttk

_LOGGER = logging.getLogger(__name__)

_GRID_KEYWORDS = {"column", "columnspan", "in", "ipadx", "ipady", "padx", "pady", "row", "rowspan", "sticky"}

SET_DPI_AWARENESS = True
if SET_DPI_AWARENESS:
    try:
        windll.shcore.SetProcessDpiAwareness(1)
    except Exception as e:
        _LOGGER.warning(
            f"Could not set DPI awareness of system. GUI font may appear blurry on scaled Windows displays.\n"
            f"Error: {str(e)}"
        )


class WindowError(Exception):
    """Exception raised by invalid `SmartFrame` state."""


def bind_to_all_children(widget: tk.BaseWidget, sequence, func, add=None):
    """Bind given event to specified widget and all its children, recursively.

    No trivial way to unbind them all, so make this is only used for short-lived widget hierarchies.
    """
    widget.bind(sequence=sequence, func=func, add=add)
    for child in widget.winfo_children():
        bind_to_all_children(child, sequence=sequence, func=func, add=add)


def _bind_to_mousewheel(widget, vertical=True, horizontal=False):
    if vertical:
        widget.bind_all("<MouseWheel>", lambda event: widget.yview_scroll(-1 * (event.delta // 120), "units"))
    if horizontal:
        widget.bind_all("<Shift-MouseWheel>", lambda event: widget.xview_scroll(-1 * (event.delta // 120), "units"))


def _unbind_to_mousewheel(widget):
    widget.unbind_all("<MouseWheel>")
    widget.unbind_all("<Shift-MouseWheel>")


def _grid_label(frame: tk.Frame, label: tk.Label, component, label_position: str):
    match label_position.lower():
        case "left":
            label.grid(row=0, column=0, padx=(0, 2))
            component.grid(row=0, column=1)
            frame.rowconfigure(0, weight=1)
            frame.columnconfigure(0, weight=0)
            frame.columnconfigure(1, weight=1)
        case "right":
            label.grid(row=0, column=1, padx=(2, 0))
            component.grid(row=0, column=0)
            frame.rowconfigure(0, weight=1)
            frame.columnconfigure(0, weight=1)
            frame.columnconfigure(1, weight=0)
        case "above":
            label.grid(row=0, column=0)
            component.grid(row=1, column=0)
            frame.rowconfigure(0, weight=0)
            frame.rowconfigure(1, weight=1)
            frame.columnconfigure(0, weight=1)
        case "below":
            label.grid(row=1, column=0)
            component.grid(row=0, column=0)
            frame.rowconfigure(0, weight=1)
            frame.rowconfigure(1, weight=0)
            frame.columnconfigure(0, weight=1)
        case _:
            raise ValueError(
                f"Invalid label position: {repr(label_position)}. Must be 'left', 'right', 'above', or 'below'."
            )


def embed_component(component_func):
    """Handles labels and scrollbars for decorated `SmartFrame` methods."""

    @wraps(component_func)
    def component_with_label(
        self: SmartFrame,
        frame: tk.Frame | None = None,
        label="",
        label_font: FONT_TYPING = None,
        label_position: str = None,
        label_fg=None,
        label_bg=None,
        vertical_scrollbar=False,
        horizontal_scrollbar=False,
        no_grid=False,
        tooltip_text="",
        **grid_style_component_kwargs,
    ):

        grid_kwargs = self.grid_defaults.copy()
        passed_grid_kwargs = {
            key: grid_style_component_kwargs.pop(key)
            for key in list(grid_style_component_kwargs.keys())
            if key in _GRID_KEYWORDS
        }
        if passed_grid_kwargs and no_grid:
            raise ValueError("If 'no_grid' is True, no grid keyword arguments can be used.")
        grid_kwargs.update(passed_grid_kwargs)

        for dim in {"row", "column"}:
            current_dim = getattr(self, "current_" + dim)
            if dim not in grid_kwargs:
                if current_dim is None:
                    grid_kwargs[dim] = 0
                else:
                    grid_kwargs[dim] = current_dim
                    setattr(self, "current_" + dim, current_dim + 1)
            elif current_dim is not None:
                raise ValueError(f"You cannot specify {dim} with a keyword while auto_{dim}s is in effect.")

        if frame is None:
            frame = self.current_frame or self.master_frame

        if label_position is None:
            if component_func.__name__ in {"Checkbutton", "Entry"}:
                label_position = "left"
            else:
                label_position = "above"

        if label:
            if label_bg is None:
                label_bg = grid_style_component_kwargs.get("bg", self.STYLE_DEFAULTS["bg"])
            if label_fg is None:
                label_fg = grid_style_component_kwargs.get("fg", self.STYLE_DEFAULTS["fg"])
            label_font = self.resolve_font(label_font, "label")
            inherit_bg = frame.cget("bg")
            frame = tk.Frame(frame, bg=inherit_bg)
            label = tk.Label(frame, text=label, font=label_font, fg=label_fg, bg=label_bg)

        if vertical_scrollbar or horizontal_scrollbar:
            inherit_bg = frame.cget("bg")
            frame_with_scrollbars = tk.Frame(frame, bg=inherit_bg)
            component = component_func(self, frame=frame_with_scrollbars, **grid_style_component_kwargs)
            component.grid(row=0, column=0, sticky="nsew")
            if vertical_scrollbar:
                vertical_scrollbar_w = tk.Scrollbar(frame_with_scrollbars, orient=VERTICAL, command=component.yview)
                vertical_scrollbar_w.grid(row=0, column=1, sticky=NS)
                component.config(bd=0, yscrollcommand=vertical_scrollbar_w.set)
            if horizontal_scrollbar:
                horizontal_scrollbar_w = tk.Scrollbar(frame_with_scrollbars, orient=HORIZONTAL, command=component.xview)
                horizontal_scrollbar_w.grid(row=1, column=0, sticky=EW)
                component.config(bd=0, xscrollcommand=horizontal_scrollbar_w.set)
            component.bind(
                "<Enter>", lambda _, f=component: _bind_to_mousewheel(f, vertical_scrollbar, horizontal_scrollbar)
            )
            component.bind("<Leave>", lambda _, f=component: _unbind_to_mousewheel(f))
            frame_with_scrollbars.rowconfigure(0, weight=1)
            if horizontal_scrollbar:
                frame_with_scrollbars.rowconfigure(1, weight=0)
            frame_with_scrollbars.columnconfigure(0, weight=1)
            if vertical_scrollbar:
                frame_with_scrollbars.columnconfigure(1, weight=0)
            if label:
                _grid_label(frame, label, frame_with_scrollbars, label_position)
                if not no_grid and grid_kwargs:
                    frame.grid(**grid_kwargs)
                component.label = label
            elif not no_grid and grid_kwargs:
                frame_with_scrollbars.grid(**grid_kwargs)
        else:
            component = component_func(self, frame=frame, **grid_style_component_kwargs)
            if label:
                _grid_label(frame, label, component, label_position)
                if not no_grid and grid_kwargs:
                    frame.grid(**grid_kwargs)
                component.label = label
            elif not no_grid and grid_kwargs:
                component.grid(**grid_kwargs)

        if tooltip_text:
            ToolTip(component, text=tooltip_text)

        return component

    return component_with_label


SMALL_FONT = ("Inconsolata Regular", 12)
REGULAR_FONT = ("Inconsolata Regular", 14)
BOLD_FONT = ("Inconsolata Bold", 14)
HEADING_FONT = ("Inconsolata Bold", 18)


# Widget types that can be set as the `frame` argument of `SmartFrame` widget wrapper methods.
MASTER_TYPING = tp.Union[tk.Frame, tk.Toplevel, ttk.Notebook, tk.Canvas, None]

# Accepted types for `font` arguments that are processed into `(type, size)` tuples for widgets.
FONT_TYPING = tuple[str | None, int | None] | str | int | None


# noinspection PyPep8Naming
class SmartFrame(tk.Frame):
    FONT_DEFAULTS = {
        "label": REGULAR_FONT,
        "heading": HEADING_FONT,
        "button": SMALL_FONT,
        "tab": REGULAR_FONT,
        "entry": REGULAR_FONT,
    }

    FileDialog = filedialog

    STYLE_DEFAULTS = {
        "bg": "#111",
        "fg": "#FFF",  # text foreground
        "insertbackground": "#FFF",  # text cursor background
        "disabledforeground": "#888",
        "disabledbackground": "#444",
        "readonlybackground": "#444",
    }

    # Menu background is a little lighter so the stupid immutable Windows black cascade arrows are visible.
    MENU_STYLE_DEFAULTS = {
        "bg": "#444",
        "fg": "#FFF",
    }

    DEFAULT_BUTTON_KWARGS = {
        "OK": {"fg": "#FFFFFF", "bg": "#222222", "width": 20},
        "YES": {"fg": "#FFFFFF", "bg": "#442222", "width": 20},
        "NO": {"fg": "#FFFFFF", "bg": "#444444", "width": 20},
    }

    _ON_IMAGE: tk.PhotoImage | None = None
    _OFF_IMAGE: tk.PhotoImage | None = None

    toplevel: tk.Toplevel | None
    style: ttk.Style
    grid_defaults: dict[str, tp.Any]
    current_row: int | None
    current_column: int | None
    master_frame: tk.Frame
    current_frame: tk.Frame

    def __init__(self, master=None, toplevel=True, window_title="Window Title", icon_data=None, **frame_kwargs):
        """My ultimate `tkinter` wrapper class."""

        # Initialize window.
        toplevel_master = master
        if toplevel:
            master = self.toplevel = tk.Toplevel(master)
            self.toplevel.title(window_title)
            self.toplevel.iconname(window_title)
            self.toplevel.focus_force()
            self.toplevel.rowconfigure(0, weight=1)
            self.toplevel.columnconfigure(0, weight=1)
            super().__init__(master, **frame_kwargs)
            if icon_data is not None:
                self.icon = tk.PhotoImage(data=icon_data)
                # noinspection PyProtectedMember,PyUnresolvedReferences
                self.toplevel.tk.call("wm", "iconphoto", self.toplevel._w, self.icon)
            self.grid(sticky="nsew")
        else:
            self.toplevel = None
            super().__init__(master, **frame_kwargs)

        self.style = ttk.Style()
        self.set_ttk_style()
        self.grid_defaults = {}
        self.current_row = None
        self.current_column = None

        # Create class-level checkbutton images, if missing.
        if self._ON_IMAGE is None:
            self.__class__._ON_IMAGE = tk.PhotoImage(width=48, height=24)
            self.__class__._ON_IMAGE.put(("#000",), to=(0, 0, 48, 24))  # black
            self.__class__._ON_IMAGE.put(("#4F4",), to=(24, 0, 47, 23))  # green (right)
        if self._OFF_IMAGE is None:
            self.__class__._OFF_IMAGE = tk.PhotoImage(width=48, height=24)
            self.__class__._OFF_IMAGE.put(("#000",), to=(0, 0, 48, 24))  # black
            self.__class__._OFF_IMAGE.put(("#D66",), to=(0, 0, 23, 23))  # red (left)

        # Current frame tracked, defaults to master frame.
        self.master_frame = self.current_frame = self.Frame(
            frame=self, row=0, column=0, sticky="nsew", row_weights=[1], column_weights=[1]
        )
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        # Disable default root if used.
        if self.toplevel and toplevel_master is None:
            # if self.winfo_screenwidth() == 3840:
            #     self.toplevel.master.tk.call('tk', 'scaling', 2.0)
            self.toplevel.master.withdraw()
        elif master is None:
            # if self.winfo_screenwidth() == 3840:
            #     self.master.tk.call('tk', 'scaling', 1.0)
            self.master.withdraw()

    def protocol(self, name, func):
        if not self.toplevel:
            raise AttributeError("Cannot use protocol() method if SmartFrame was initialized without 'toplevel=True'.")
        self.toplevel.protocol(name, func)

    def resizable(self, width, height):
        if not self.toplevel:
            raise AttributeError("Cannot use resizable() method if SmartFrame was initialized without 'toplevel=True'.")
        self.toplevel.resizable(width, height)

    def withdraw(self):
        if not self.toplevel:
            raise AttributeError("Cannot use withdraw() method if SmartFrame was initialized without 'toplevel=True'.")
        self.toplevel.withdraw()

    def deiconify(self):
        if not self.toplevel:
            raise AttributeError("Cannot use deiconify() method if SmartFrame was initialized without 'toplevel=True'.")
        self.toplevel.deiconify()

    def destroy(self):
        super().destroy()
        if self.toplevel:
            self.toplevel.destroy()

    def quit(self):
        super().quit()
        if self.toplevel:
            self.toplevel.quit()

    def set_geometry(
        self,
        master: tk.BaseWidget = None,
        dimensions: tuple[int, int] = None,
        absolute_position: tuple[int, int] = None,
        relative_position: tuple[float, float] = None,
        transient=False,
    ):
        """Set the size and position of this SmartFrame, if `toplevel=True`. Should not be called otherwise.

        Should be called in your SmartFrame's constructor after all widgets have been initialized, unless you already
        know the exact dimensions you want. The SmartFrame will always attempt to remain fully visible on the screen.
        If neither `absolute_position` nor `relative_position` are given, the SmartFrame will appear centered in the
        display.

        Args:
            master (tk.BaseWidget): master of this SmartFrame, used for calculating `relative_position` and `transient`
                master. Defaults to master of `self.toplevel`.
            dimensions (tuple): pair of (width, height) values in pixels. Defaults to dimensions requested by the
                window.
            absolute_position (tuple): pair of (x, y) values in pixels on the screen, where (0, 0) is the bottom-left
                corner. Cannot be used at the same time as `relative_position`.
            relative_position (tuple): pair of (x, y) values as proportions of the size of the `master`, where (0, 0)
                is the top-left corner and (1, 1) is the bottom-right corner. If `master` does not have a mapped size,
                this argument will be ignored. Cannot be used at the same time as `absolute_position`.
            transient (bool): if True, this SmartFrame won't appear in the task bar, will always be drawn on top of its
                master, and will be automatically hidden when its master is iconified or withdrawn.
        """
        if self.toplevel is None:
            raise RuntimeError("SmartFrame was created with `toplevel=False` and has no geometry to set.")
        master = master or self.toplevel.master

        if absolute_position is not None and relative_position is not None:
            raise ValueError("You cannot specify both `absolute_position` and `relative_position` of the SmartFrame.")
        self.toplevel.withdraw()  # Remain invisible while we figure out the geometry
        if transient:
            self.toplevel.transient(master)
        self.toplevel.update_idletasks()  # Actualize geometry information

        if dimensions is not None:
            w_width, w_height = int(dimensions[0]), int(dimensions[1])
        else:
            w_width, w_height = self.toplevel.winfo_reqwidth(), self.toplevel.winfo_reqheight()

        if relative_position is not None and master.winfo_ismapped():
            rel_x, rel_y = relative_position
            m_width = master.winfo_width()
            m_height = master.winfo_height()
            m_x = master.winfo_rootx()
            m_y = master.winfo_rooty()
            w_x = int(m_x + (m_width - w_width) * rel_x)
            w_y = int(m_y + (m_height - w_height) * rel_y)
        else:
            m_width = master.winfo_screenwidth()
            m_height = master.winfo_screenheight()
            if absolute_position is None:
                absolute_position = (m_width / 2, m_height / 2)
            w_x = int(absolute_position[0] - (w_width / 2))
            w_y = int(absolute_position[1] - (w_height / 2))

        # Ensure that this window does not go off the screen.
        if w_x + w_width > master.winfo_screenwidth():
            w_x = master.winfo_screenwidth() - w_width
        elif w_x < 0:
            w_x = 0
        if w_y + w_height > master.winfo_screenheight():
            w_y = master.winfo_screenheight() - w_height
        elif w_y < 0:
            w_y = 0
        self.toplevel.geometry(f"{w_width:d}x{w_height:d}+{w_x:d}+{w_y:d}")
        self.toplevel.deiconify()  # become visible at the desired location

    def set_ttk_style(self):
        self.style.theme_use("clam")
        self.style.configure(
            "TNotebook", background=self.STYLE_DEFAULTS["bg"], tabmargins=[2, 10, 2, 0], tabposition="nw"
        )
        self.style.configure(
            "TNotebook.Tab", background="#333", foreground="#FFF", padding=[15, 1], font=(self.FONT_DEFAULTS["tab"])
        )
        self.style.map("TNotebook.Tab", background=[("selected", "#555")], expand=[("selected", [5, 3, 3, 0])])
        self.style.configure(
            "TCombobox", foreground="#FFF",
        )
        self.style.map(
            "TCombobox", fieldbackground=[("readonly", "#222")], selectedbackground=[("readonly", "#222")],
        )
        self.option_add("*TCombobox*Listbox*background", "#222")
        self.option_add("*TCombobox*Listbox*font", (self.FONT_DEFAULTS["label"]))
        self.option_add("*TCombobox*Listbox*foreground", "#FFF")

    def start_auto_rows(self, start=0):
        self.current_row = start

    def stop_auto_rows(self):
        self.current_row = None

    def start_auto_columns(self, start=0):
        self.current_column = start

    def stop_auto_columns(self):
        self.current_column = None

    def get_style_kwargs(self, kwargs_dict) -> dict[str, tp.Any]:
        """Return a new dictionary that contains only keywords relevant to style (and also 'font')."""
        return {k: v for k, v in kwargs_dict.items() if k in self.STYLE_DEFAULTS or k == "font"}

    def set_style_defaults(self, kwargs_dict, text=False, cursor=False, entry=False):
        kwargs_dict.setdefault("bg", self.STYLE_DEFAULTS.get("bg", None))
        if text:
            kwargs_dict.setdefault("fg", self.STYLE_DEFAULTS.get("fg", None))
        if cursor:
            kwargs_dict.setdefault("insertbackground", self.STYLE_DEFAULTS.get("insertbackground", None))
        if entry:
            kwargs_dict.setdefault("disabledforeground", self.STYLE_DEFAULTS.get("disabledforeground", None))
            kwargs_dict.setdefault("disabledbackground", self.STYLE_DEFAULTS.get("disabledbackground", None))
            kwargs_dict.setdefault("readonlybackground", self.STYLE_DEFAULTS.get("readonlybackground", None))
            kwargs_dict.setdefault("font", self.FONT_DEFAULTS.get("entry", None))

    def resolve_font(
        self, font: tuple[str | None, int | None] | str | int | None, default_key: str = "label"
    ) -> tuple[str, int]:
        if font is None:
            return self.FONT_DEFAULTS[default_key]
        if isinstance(font, int):
            return self.FONT_DEFAULTS[default_key][0], font
        if isinstance(font, str):
            return font, self.FONT_DEFAULTS[default_key][1]
        return (
            font[0] if font[0] else self.FONT_DEFAULTS[default_key][0],
            font[1] if font[1] else self.FONT_DEFAULTS[default_key][1],
        )

    # region Variables

    def BooleanVar(self, master=None, value: bool = None, name: str = None):
        return tk.BooleanVar(master or self, value=value, name=name)

    def IntVar(self, master=None, value: int = None, name: str = None):
        return tk.IntVar(master or self, value=value, name=name)

    def DoubleVar(self, master=None, value: float = None, name: str = None):
        return tk.DoubleVar(master or self, value=value, name=name)

    def StringVar(self, master=None, value: str = None, name: str = None):
        return tk.StringVar(master or self, value=value, name=name)

    # endregion

    # region Widgets

    def Toplevel(
        self,
        frame: MASTER_TYPING = None,
        title="Window Title",
        row_weights: tp.Sequence[int] = (),
        column_weights: tp.Sequence[int] = (),
        **kwargs,
    ):
        """NOTE: This widget wrapper is NOT decorated with `embed_component`."""
        kwargs.setdefault("bg", self.STYLE_DEFAULTS["bg"])
        toplevel = tk.Toplevel(frame, **kwargs)
        toplevel.title(title)
        for i, w in enumerate(row_weights):
            toplevel.rowconfigure(i, weight=w)
        for i, w in enumerate(column_weights):
            toplevel.columnconfigure(i, weight=w)
        return toplevel

    @embed_component
    def Notebook(
        self,
        frame: MASTER_TYPING = None,
        row_weights: tp.Sequence[int] = (),
        column_weights: tp.Sequence[int] = (),
        **kwargs,
    ):
        notebook = ttk.Notebook(frame, **kwargs)
        for i, w in enumerate(row_weights):
            notebook.rowconfigure(i, weight=w)
        for i, w in enumerate(column_weights):
            notebook.columnconfigure(i, weight=w)
        return notebook

    @embed_component
    def Frame(
        self,
        frame: MASTER_TYPING = None,
        row_weights: tp.Sequence[int] = (),
        column_weights: tp.Sequence[int] = (),
        **kwargs,
    ):
        self.set_style_defaults(kwargs)
        frame = tk.Frame(frame, **kwargs)
        for i, w in enumerate(row_weights):
            frame.rowconfigure(i, weight=w)
        for i, w in enumerate(column_weights):
            frame.columnconfigure(i, weight=w)
        return frame

    @embed_component
    def SmartFrame(
        self,
        frame: MASTER_TYPING = None,
        smart_frame_class: type[SmartFrame] = None,
        row_weights: tp.Sequence[int] = (),
        column_weights: tp.Sequence[int] = (),
        **kwargs,
    ):
        if smart_frame_class is None:
            smart_frame_class = SmartFrame
        elif not issubclass(smart_frame_class, SmartFrame):
            raise TypeError(f"`smart_frame_class` must be a subclass of `SmartFrame`, not {smart_frame_class}.")
        smart_frame = smart_frame_class(master=frame, **kwargs)
        for i, w in enumerate(row_weights):
            smart_frame.rowconfigure(i, weight=w)
        for i, w in enumerate(column_weights):
            smart_frame.columnconfigure(i, weight=w)
        return smart_frame

    @embed_component
    def Canvas(
        self,
        frame: MASTER_TYPING = None,
        row_weights: tp.Sequence[int] = (),
        column_weights: tp.Sequence[int] = (),
        **kwargs,
    ):
        self.set_style_defaults(kwargs)
        canvas = tk.Canvas(frame, **kwargs)
        for i, w in enumerate(row_weights):
            canvas.rowconfigure(i, weight=w)
        for i, w in enumerate(column_weights):
            canvas.columnconfigure(i, weight=w)
        return canvas

    @embed_component
    def Button(
        self,
        command: tp.Callable[[], tp.Any],
        frame: MASTER_TYPING = None,
        text: str = None,
        text_padx: int = None,
        text_pady: int = None,
        font: FONT_TYPING = None,
        style: ttk.Style = None,
        **kwargs,
    ):
        self.set_style_defaults(kwargs, text=True)
        font = self.resolve_font(font, "button")
        if text is not None:
            text_var = tk.StringVar(value=text)
        else:
            text_var = None
        if style is not None:
            button = ttk.Button(
                frame, command=command, textvariable=text_var, padx=text_padx, pady=text_pady, style=style
            )
        else:
            button = tk.Button(
                frame,
                command=command,
                textvariable=text_var,
                padx=text_padx,
                pady=text_pady,
                font=font,
                **kwargs,
            )
        button.var = text_var
        return button

    @embed_component
    def Checkbutton(
        self,
        frame: MASTER_TYPING = None,
        command: tp.Callable[[], None] = None,
        initial_state=False,
        text="",
        **kwargs,
    ):
        self.set_style_defaults(kwargs)
        boolean_var = tk.BooleanVar(value=initial_state)
        kwargs["bg"] = "#444"
        kwargs["selectcolor"] = "#444"
        checkbutton = tk.Checkbutton(
            frame,
            text=text,
            variable=boolean_var,
            command=command,
            image=self._OFF_IMAGE,
            selectimage=self._ON_IMAGE,
            indicatoron=False,
            borderwidth=0,
            **kwargs,
        )
        checkbutton.var = boolean_var
        return checkbutton

    @embed_component
    def ClassicCheckbutton(
        self,
        frame: MASTER_TYPING = None,
        command: tp.Callable[[], None] = None,
        initial_state=False,
        text="",
        **kwargs,
    ):
        """Default checkbutton style, with a box and tick."""
        self.set_style_defaults(kwargs)
        boolean_var = tk.BooleanVar(value=initial_state)
        checkbutton = tk.Checkbutton(frame, text=text, variable=boolean_var, command=command, **kwargs)
        checkbutton.var = boolean_var
        return checkbutton

    @embed_component
    def Combobox(
        self,
        frame: MASTER_TYPING = None,
        values: list[str] | tuple[str, ...] = None,
        initial_value: str = None,
        readonly=True,
        width=20,
        on_select_function=None,
        **kwargs,
    ):
        state = "readonly" if readonly else ""
        initial_value = initial_value or (values[0] if values else "")
        string_var = tk.StringVar(frame, value=initial_value)
        combobox = ttk.Combobox(frame, textvariable=string_var, values=values, state=state, width=width, **kwargs)
        combobox.var = string_var
        if on_select_function is not None:
            combobox.bind("<<ComboboxSelected>>", on_select_function)
        return combobox

    def Menu(
        self,
        frame: MASTER_TYPING = None,
        tearoff=0,
        **kwargs,
    ):
        frame = frame or self.current_frame
        for key in self.MENU_STYLE_DEFAULTS:
            kwargs.setdefault(key, self.MENU_STYLE_DEFAULTS[key])
        menu = SmartMenu(frame, tearoff=tearoff, **kwargs)
        return menu

    @embed_component
    def Scrollbar(
        self,
        frame: MASTER_TYPING = None,
        **kwargs,
    ):
        frame = frame or self.current_frame
        return tk.Scrollbar(frame, **kwargs)

    @embed_component
    def Entry(
        self,
        frame: MASTER_TYPING = None,
        initial_text="",
        integers_only=False,
        numbers_only=False,
        **kwargs,
    ):
        if "text" in kwargs:
            _LOGGER.warning(
                "'text' argument given to `SmartFrame.Entry()`. I recommend using `textvariable` to ensure this "
                "argument is not mistaken for `initial_text`."
            )
        self.set_style_defaults(kwargs, text=True, cursor=True, entry=True)
        text_var = tk.StringVar(value=initial_text)
        entry = tk.Entry(frame, textvariable=text_var, **kwargs)
        entry.var = text_var
        entry.integers_only = integers_only
        if integers_only:
            if numbers_only:
                raise ValueError("Use `integers_only` or `numbers_only`, but not both.")
            v_cmd = (self.master.register(self._validate_entry_integers), "%P")
            entry.config(validate="key", validatecommand=v_cmd)
        elif numbers_only:
            v_cmd = (self.master.register(self._validate_entry_numbers), "%P")
            entry.config(validate="key", validatecommand=v_cmd)
        return entry

    @embed_component
    def Label(
        self,
        frame: MASTER_TYPING = None,
        text="",
        font: FONT_TYPING = None,
        **kwargs,
    ):
        self.set_style_defaults(kwargs, text=True)
        font = self.resolve_font(font, "label")
        if isinstance(text, str):
            string_var = tk.StringVar(value=text)
        elif isinstance(text, tk.StringVar):
            string_var = text
        else:
            raise ValueError("Text must be a string or StringVar.")
        label = tk.Label(frame, textvariable=string_var, font=font, **kwargs)
        label.var = string_var
        return label

    @embed_component
    def Listbox(
        self,
        frame: MASTER_TYPING = None,
        values: tp.Sequence[str] = (),
        on_select_function=None,
        **kwargs,
    ):
        self.set_style_defaults(kwargs, text=True)
        listbox = tk.Listbox(frame, **kwargs)
        for value in values:
            listbox.insert(END, value)
        if on_select_function is not None:
            listbox.bind("<<ListboxSelect>>", on_select_function)
        return listbox

    @embed_component
    def PanedWindow(
        self,
        frame: MASTER_TYPING = None,
        **kwargs,
    ):
        self.set_style_defaults(kwargs)
        paned_window = tk.PanedWindow(frame, **kwargs)
        return paned_window

    @embed_component
    def Radiobutton(
        self,
        frame: MASTER_TYPING = None,
        command: tp.Callable[[], None] = None,
        variable: tk.IntVar = None,
        **kwargs,
    ):
        self.set_style_defaults(kwargs)
        variable = variable or tk.IntVar()
        radiobutton = tk.Radiobutton(frame, text="", variable=variable, command=command, **kwargs)
        radiobutton.var = variable
        return radiobutton

    @embed_component
    def Separator(
        self,
        frame: MASTER_TYPING = None,
        orientation=HORIZONTAL,
        **kwargs,
    ):
        self.set_style_defaults(kwargs)
        return ttk.Separator(frame, orient=orientation)

    @embed_component
    def Progressbar(
        self,
        frame: MASTER_TYPING = None,
        **kwargs,
    ):
        return ttk.Progressbar(frame, **kwargs)

    @embed_component
    def Scale(
        self,
        frame: MASTER_TYPING = None,
        limits=(0, 100),
        orientation=HORIZONTAL,
        variable: tk.IntVar | tk.DoubleVar = None,
        is_float: bool = None,
        **kwargs,
    ):
        self.set_style_defaults(kwargs)
        if variable is None:
            variable = tk.DoubleVar() if is_float else tk.IntVar()  # will default to `IntVar` if `is_float=None`
        elif is_float is not None:
            raise ValueError("Cannot pass `is_float` keyword for `SmartFrame.Scale` if `variable` is given.")
        scale = tk.Scale(frame, from_=limits[0], to=limits[1], orient=orientation, variable=variable, **kwargs)
        scale.var = variable
        return scale

    @embed_component
    def TextBox(
        self,
        frame: MASTER_TYPING = None,
        initial_text="",
        **kwargs,
    ):
        self.set_style_defaults(kwargs, text=True, cursor=True, entry=False)
        text_box = tk.Text(frame, **kwargs)
        text_box.insert(1.0, initial_text)
        return text_box

    @embed_component
    def CustomWidget(
        self,
        frame: MASTER_TYPING = None,
        custom_widget_class: type[tk.BaseWidget] = None,
        set_style_defaults: tp.Container[str] = (),
        row_weights: tp.Sequence[int] = (),
        column_weights: tp.Sequence[int] = (),
        **kwargs,
    ):
        if custom_widget_class is None:
            # optional `frame` argument must come first for decorator, so this is required.
            raise ValueError("`custom_widget_class` cannot be None.")
        style_default_kwargs = {k: k in set_style_defaults for k in ("text", "cursor", "entry")}
        self.set_style_defaults(kwargs, **style_default_kwargs)
        custom_widget = custom_widget_class(frame, **kwargs)
        for i, w in enumerate(row_weights):
            custom_widget.rowconfigure(i, weight=w)
        for i, w in enumerate(column_weights):
            custom_widget.columnconfigure(i, weight=w)
        return custom_widget

    def LoadingDialog(
        self,
        title: str,
        message: str,
        font: FONT_TYPING = None,
        style_defaults: dict[str, tp.Any] = None,
        loading_dialog_subclass: type[LoadingDialog] = None,
        **progressbar_kwargs,
    ) -> LoadingDialog:
        """Creates a child `LoadingDialog` with `style_defaults` taken from SmartFrame by default."""
        if loading_dialog_subclass is None:
            loading_dialog_subclass = LoadingDialog
        elif not issubclass(loading_dialog_subclass, LoadingDialog):
            raise TypeError("`loading_dialog_subclass` must be a subclass of `LoadingDialog`, if given.")

        font = self.resolve_font(font, "label")

        if style_defaults is None:
            style_defaults = self.STYLE_DEFAULTS

        return loading_dialog_subclass(
            master=self,
            title=title,
            message=message,
            font=font,
            style_defaults=style_defaults,
            **progressbar_kwargs,
        )

    def CustomDialog(
        self,
        title: str,
        message: str,
        font: FONT_TYPING = None,
        button_names: tp.Sequence[str] = ("OK",),
        button_kwargs: tp.Sequence[str] = ("OK",),
        style_defaults: dict[str, tp.Any] = None,
        default_output: int = None,
        cancel_output: int = None,
        return_output: int = None,
        escape_enabled=True,
        custom_dialog_subclass: type[CustomDialog] = None,
        **kwargs,
    ):
        """Creates a child `CustomDialog` with `style_defaults` taken from SmartFrame by default."""
        if custom_dialog_subclass is None:
            custom_dialog_subclass = CustomDialog
        elif not issubclass(custom_dialog_subclass, CustomDialog):
            raise TypeError("`custom_dialog_subclass` must be a subclass of `CustomDialog`, if given.")

        font = self.resolve_font(font, "label")

        if style_defaults is None:
            style_defaults = self.STYLE_DEFAULTS
        if isinstance(button_names, str):
            button_names = (button_names,)
        button_kwargs = self._process_button_kwargs(button_kwargs)

        if cancel_output is None:
            # `cancel_output`, `default_output`, and `return_output` all default to 0 if only one button is present.
            if len(button_names) == 1:
                default_output = cancel_output = return_output = 0

        dialog = custom_dialog_subclass(
            master=self,
            title=title,
            message=message,
            font=font,
            button_names=button_names,
            button_kwargs=button_kwargs,
            style_defaults=style_defaults,
            default_output=default_output,
            cancel_output=cancel_output,
            return_output=return_output,
            escape_enabled=escape_enabled,
            **kwargs,
        )

        if self.toplevel and not self.toplevel.winfo_viewable():
            # Briefly deiconify toplevel to allow child dialog to appear.
            self.toplevel.deiconify()
            result = dialog.go()
            self.toplevel.withdraw()
            return result
        return dialog.go()  # Returns index of button clicked (or default/cancel output).

    # endregion

    # region Public Utility Methods

    @staticmethod
    def mimic_click(button: tk.Button):
        button["relief"] = SUNKEN
        button.update_idletasks()
        button.after(100, lambda: button.config(relief=RAISED))

    def flash_bg(self, widget, bg="#522", ms=100):
        if getattr(widget, "flashing", False):
            return  # already flashing
        old_bg = widget["bg"]
        widget["bg"] = bg
        widget.flashing = True
        widget.update_idletasks()
        widget.after(ms, lambda w=widget, o=old_bg: self._end_flash(w, o))

    @staticmethod
    def _end_flash(widget, old_bg):
        widget["bg"] = old_bg
        widget.flashing = False

    @staticmethod
    def reset_canvas_scroll_region(canvas):
        """Sets scrollable canvas region to the entire bounding box."""
        canvas.configure(scrollregion=canvas.bbox("all"))

    @staticmethod
    def link_to_scrollable(scrollable_widget, *widgets):
        """Registers <Enter> and <Leave> events that enable scrolling for the first widget for all following widgets."""
        for widget in widgets:
            widget.bind("<Enter>", lambda _, f=scrollable_widget: _bind_to_mousewheel(f))
            widget.bind("<Leave>", lambda _, f=scrollable_widget: _unbind_to_mousewheel(f))

    def bind_to_all_children(self, sequence, func, add=None):
        bind_to_all_children(self, sequence=sequence, func=func, add=add)

    @staticmethod
    def info_dialog(title, message, **kwargs) -> str:
        return messagebox.showinfo(title, message, **kwargs)

    @staticmethod
    def warning_dialog(title, message, **kwargs) -> str:
        return messagebox.showwarning(title, message, **kwargs)

    @staticmethod
    def error_dialog(title, message, **kwargs) -> str:
        return messagebox.showerror(title, message, **kwargs)

    @staticmethod
    def yesno_dialog(title, message, **kwargs) -> bool:
        return messagebox.askyesno(title, message, **kwargs)

    @contextlib.contextmanager
    def set_master(
        self,
        master: MASTER_TYPING | tp.Callable | str = None,
        auto_rows: int = None,
        auto_columns: int = None,
        grid_defaults: dict[str, tp.Any] = None,
        **frame_kwargs,
    ):
        """Context manager to temporarily set the master of the SmartFrame.

        Resets to previous master after use.
        """
        previous_frame = self.current_frame

        if master is None:
            self.current_frame = self.Frame(**frame_kwargs)
        else:
            if isinstance(master, str):
                try:
                    master = getattr(self, master)
                except AttributeError:
                    raise ValueError(
                        f"Invalid master type string: {master}. Must be one of: Frame, Toplevel, Notebook, Canvas"
                    )
            if master in {self.Frame, self.Toplevel, self.Notebook, self.Canvas}:
                self.current_frame = master(**frame_kwargs)
            elif isinstance(master, (tk.Toplevel, ttk.Notebook, tk.Frame, tk.Canvas)):
                if frame_kwargs:
                    raise ValueError("Cannot use `set_master` keyword arguments when passing an existing `master`.")
                self.current_frame = master
            else:
                raise TypeError("`master` can only be set to a Toplevel, Notebook, Frame, or Canvas.")

        previous_auto_row = self.current_row
        previous_auto_column = self.current_column
        self.current_row = auto_rows
        self.current_column = auto_columns

        if grid_defaults is not None:
            previous_grid_defaults = self.grid_defaults.copy()
            self.grid_defaults = grid_defaults
        else:
            previous_grid_defaults = {}

        try:
            yield self.current_frame
        finally:
            self.current_row = previous_auto_row
            self.current_column = previous_auto_column
            if grid_defaults is not None:
                self.grid_defaults = previous_grid_defaults
            self.current_frame = previous_frame

    # endregion

    # region Private Methods

    @staticmethod
    def _validate_entry_integers(new_value):
        """Callback invoked whenever the Entry contents change.

        Returns True if the value of the Entry ('%P') can be interpreted as an `int` (or is empty or a minus sign).
        """
        if new_value in {"", "-"}:
            return True  # Empty strings and minus sign only is permitted (minus sign must be handled by caller).
        try:
            int(new_value)
        except ValueError:
            return False
        return True

    @staticmethod
    def _validate_entry_numbers(new_value):
        """Callback invoked whenever the Entry contents change.

        Returns True if the value of the Entry ('%P') can be interpreted as a `float` (or is empty or a minus sign).
        """
        if new_value in {"", "-"}:
            return True  # Empty strings and minus sign only is permitted (minus sign must be handled by caller).
        try:
            float(new_value)
        except ValueError:
            return False
        return True

    def _process_button_kwargs(self, button_kwargs):
        if button_kwargs is None:
            return None
        elif isinstance(button_kwargs, str):
            try:
                return self.DEFAULT_BUTTON_KWARGS[button_kwargs],  # note tuple
            except KeyError:
                raise KeyError(f"Invalid `SmartFrame.DEFAULT_BUTTON_KWARGS` key: {button_kwargs}")
        elif isinstance(button_kwargs, (tuple, list)):
            button_kwargs = list(button_kwargs)
            for i, b in enumerate(button_kwargs):
                if isinstance(b, str):
                    try:
                        button_kwargs[i] = self.DEFAULT_BUTTON_KWARGS[b]
                    except KeyError:
                        raise KeyError(f"Invalid `SmartFrame.DEFAULT_BUTTON_KWARGS` key: {b}")
                elif not isinstance(b, dict):
                    raise TypeError(
                        f"If `button_kwargs` is a sequence, each element should be a string key to "
                        f"`SmartFrame.DEFAULT_BUTTON_KWARGS` or a dictionary of `Button` kwargs, not: {type(b)}"
                    )
            return button_kwargs
        elif not isinstance(button_kwargs, dict):
            raise TypeError(
                f"`button_kwargs` should be a dictionary of `Button` kwargs, a sequence of such dicts (one per button "
                f"name), or a string or list of strings that are keys to `SmartFrame.DEFAULT_BUTTON_KWARGS`, not: "
                f"{type(button_kwargs)}"
            )
        return button_kwargs

    # endregion


class SmartMenu(tk.Menu):
    """Menu subclass that automatically applies style defaults to kwargs passed to `tk.Menu` methods."""

    style: dict[str, str]

    def __init__(self, *args, **kwargs):
        self.style = {}
        for style_key in ("fg", "bg"):
            if style_key in kwargs:
                self.style[style_key] = kwargs[style_key]
        super().__init__(*args, **kwargs)

    def add_cascade(self, *args, **kwargs):
        self._apply_style_kwargs(**kwargs)
        super().add_cascade(*args, **kwargs)

    def add_checkbutton(self, *args, **kwargs):
        self._apply_style_kwargs(**kwargs)
        super().add_checkbutton(*args, **kwargs)

    def add_command(self, *args, **kwargs):
        self._apply_style_kwargs(**kwargs)
        super().add_command(*args, **kwargs)

    def add_radiobutton(self, *args, **kwargs):
        self._apply_style_kwargs(**kwargs)
        super().add_radiobutton(*args, **kwargs)

    def add_separator(self, *args, **kwargs):
        self._apply_style_kwargs(("bg",), **kwargs)
        super().add_separator(*args, **kwargs)

    def _apply_style_kwargs(self, only_keys=(), **kwargs):
        for key, value in self.style.items():
            if only_keys and key not in only_keys:
                continue
            kwargs.setdefault(key, value)


class LoadingDialog(SmartFrame):
    """Simple box with a message and a loading bar. It is destroyed when appropriate."""

    def __init__(
        self,
        master: MASTER_TYPING,
        title="Loading...",
        message="",
        font: FONT_TYPING = None,
        style_defaults=None,
        **progressbar_kwargs,
    ):
        if style_defaults:
            self.STYLE_DEFAULTS = style_defaults
        super().__init__(master=master, toplevel=True, window_title=title)

        progressbar_kwargs.setdefault("orient", HORIZONTAL)
        progressbar_kwargs.setdefault("mode", "indeterminate")
        progressbar_kwargs.setdefault("sticky", EW)

        with self.set_master(auto_rows=0, padx=20, pady=20):
            self.Label(text=message, font=font, pady=10)
            self.progress = self.Progressbar(**progressbar_kwargs)

        self.set_geometry(transient=True)


class CustomDialog(SmartFrame):
    def __init__(
        self,
        master: MASTER_TYPING,
        title="Custom Dialog",
        message="",
        font: FONT_TYPING = None,
        button_names=(),
        button_kwargs=(),
        style_defaults=None,
        default_output=None,
        cancel_output=None,
        return_output=None,
        escape_enabled=True,
        **kwargs,
    ):
        if kwargs:
            raise ValueError("Base `CustomDialog` class does not support any kwargs.")

        if style_defaults:
            self.STYLE_DEFAULTS = style_defaults
        if button_kwargs and len(button_names) != len(button_kwargs):
            raise ValueError("Number of `button_kwargs` dicts (if any are given) must match number of `button_names`.")
        super().__init__(toplevel=True, window_title=title, master=master)
        self.output = default_output
        self.cancel_output = cancel_output
        self.default_output = default_output

        self.build(message, font, button_names, button_kwargs)

        self.protocol("WM_DELETE_WINDOW", self.wm_delete_window)
        self.resizable(width=False, height=False)
        if escape_enabled:
            bind_to_all_children(self.toplevel, "<Escape>", lambda _: self.wm_delete_window())
        self.return_output = return_output
        bind_to_all_children(self.toplevel, "<Return>", self.return_event)

        self.set_geometry(relative_position=(0.5, 0.3), transient=True)

    def build(self, message, font, button_names, button_kwargs):
        """You can override this as desired, as long as you call `self.build_buttons()` at some point.

        Otherwise you can construct your own buttons with commands `lambda s=self, output=i: s.done(output)` for each
        button index `i`).
        """
        with self.set_master(auto_rows=0, padx=20, pady=20):
            self.Label(text=message, font=font, pady=20)
            self.build_buttons(button_names, button_kwargs)

    def build_buttons(self, button_names, button_kwargs):
        with self.set_master(auto_columns=0, pady=20):
            for i in range(len(button_names)):
                button = self.Button(
                    text=button_names[i],
                    command=lambda output=i: self.done(output),
                    padx=5,
                    **(button_kwargs[i] if button_kwargs else {}),
                )
                if i == self.default_output:
                    button["relief"] = RIDGE

    def go(self):
        self.toplevel.wait_visibility()
        self.toplevel.grab_set()
        self.toplevel.mainloop()
        self.toplevel.destroy()
        return self.output

    def return_event(self, _):
        """Event that occurs when the user presses the Enter key. Returns `self.return_output` if specified, or rings
        bell."""
        if self.return_output is None:
            self.toplevel.bell()
        else:
            self.done(self.return_output)

    def wm_delete_window(self):
        """Function that occurs when the user closes the window using the corner X, Alt-F4, etc. Returns
        `self.cancel_output` if specified, or rings bell.

        If dialog was created with `escape_enabled=True`, pressing Escape will also close the window (if.
        """
        if self.cancel_output is None:
            self.toplevel.bell()
        else:
            self.done(self.cancel_output)

    def done(self, num):
        self.output = num
        self.toplevel.quit()


class ToolTip:
    """Class that creates a tooltip for a given widget."""

    def __init__(
        self,
        main_widget,
        *child_widgets,
        text="tool tip",
        delay=500,
        wraplength=180,
        x_offset=25,
        y_offset=30,
        anchor_widget=None,
    ):
        """Entering *any* of the widgets is sufficient to trigger the tooltip, but you must leave *all* of them for it
        to time out again. The main widget will be used to determine tooltip coordinates (generally the largest)."""
        self.delay = delay
        self.wraplength = wraplength
        self.x_offset = x_offset
        self.y_offset = y_offset
        self.widgets = [main_widget] + list(child_widgets)
        self.widget_status = {id(w): False for w in self.widgets}
        self.anchor_widget = main_widget if anchor_widget is None else anchor_widget
        self.text = text
        for widget in self.widgets:
            widget.bind("<Enter>", lambda _: self.enter(widget))
            widget.bind("<Leave>", lambda _: self.leave(widget))
            widget.bind("<ButtonPress>", lambda _: self.leave(widget))
        self.schedule_id = None
        self.tip_box = None

    def enter(self, widget):
        if self.text is None:
            return
        schedule_tip = not any(self.widget_status.values())
        self.widget_status[id(widget)] = True
        if schedule_tip:
            self.schedule()

    def leave(self, widget):
        if self.text is None:
            return
        self.widget_status[id(widget)] = False
        if not any(self.widget_status.values()):
            self.unschedule()
            self.hide_tip()

    def schedule(self):
        self.unschedule()
        self.schedule_id = self.widgets[0].after(self.delay, self.show_tip)

    def unschedule(self):
        schedule_id, self.schedule_id = self.schedule_id, None
        if schedule_id:
            self.widgets[0].after_cancel(schedule_id)

    def show_tip(self, _=None):
        x, y, cx, cy = self.anchor_widget.bbox("insert")
        x += self.anchor_widget.winfo_rootx() + self.x_offset
        y += self.anchor_widget.winfo_rooty() + self.y_offset
        self.tip_box = tk.Toplevel(self.anchor_widget)
        self.tip_box.wm_overrideredirect(True)  # remove border
        self.tip_box.wm_geometry(f"+{x}+{y}")
        tip_message = tk.Label(
            self.tip_box,
            text=self.text,
            justify="left",
            bg="#FFFFFF",
            relief="solid",
            borderwidth=1,
            wraplength=self.wraplength,
        )
        tip_message.pack(ipadx=1)

    def hide_tip(self):
        tip_box, self.tip_box = self.tip_box, None
        if tip_box:
            tip_box.destroy()

    def destroy(self):
        if self.tip_box:
            self.tip_box.destroy()


def print_widget_hierarchy(widget, indent=0):
    print(" " * indent + str(widget))
    for child in widget.winfo_children():
        print_widget_hierarchy(child, indent=indent + 4)
