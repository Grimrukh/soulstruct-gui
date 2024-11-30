from __future__ import annotations

import contextlib
import tkinter as tk
import typing as tp
from tkinter.constants import *
from tkinter import filedialog, messagebox, ttk

from .smart_widgets import BaseWidget, FramelikeWidget, Frame


class SuperFrame(tk.Frame):

    FileDialog = filedialog

    DEFAULT_BUTTON_KWARGS = {
        "OK": {"fg": "#FFFFFF", "bg": "#222222", "width": 20},
        "YES": {"fg": "#FFFFFF", "bg": "#442222", "width": 20},
        "NO": {"fg": "#FFFFFF", "bg": "#444444", "width": 20},
    }

    # Persistent storage for checkbutton images.
    _ON_IMAGE: tk.PhotoImage | None = None
    _OFF_IMAGE: tk.PhotoImage | None = None

    toplevel: tk.Toplevel | None
    style: ttk.Style

    grid_defaults: dict[str, tp.Any]
    current_row: int | None
    current_column: int | None

    master_frame: Frame  # always a `Frame` specifically
    current_framelike: FramelikeWidget  # Frame, Toplevel, Canvas, Notebook, ...

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
        # We have to do it here to ensure `tk` has been initialized.
        if self._ON_IMAGE is None:
            cls = self.__class__
            cls._ON_IMAGE = tk.PhotoImage(width=48, height=24)
            # noinspection PyTypeChecker
            cls._ON_IMAGE.put(("#000",), to=(0, 0, 48, 24))  # black
            # noinspection PyTypeChecker
            cls._ON_IMAGE.put(("#4F4",), to=(24, 0, 47, 23))  # green (right)
        if self._OFF_IMAGE is None:
            cls = self.__class__
            cls._OFF_IMAGE = tk.PhotoImage(width=48, height=24)
            # noinspection PyTypeChecker
            cls._OFF_IMAGE.put(("#000",), to=(0, 0, 48, 24))  # black
            # noinspection PyTypeChecker
            cls._OFF_IMAGE.put(("#D66",), to=(0, 0, 23, 23))  # red (left)

        # Current frame tracked, defaults to master frame.
        self.master_frame = self.current_framelike = Frame.full_frame(self, self).widget
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
            raise AttributeError("Cannot use protocol() method if SuperFrame was initialized without 'toplevel=True'.")
        self.toplevel.protocol(name, func)

    def resizable(self, width, height):
        if not self.toplevel:
            raise AttributeError("Cannot use resizable() method if SuperFrame was initialized without 'toplevel=True'.")
        self.toplevel.resizable(width, height)

    def withdraw(self):
        if not self.toplevel:
            raise AttributeError("Cannot use withdraw() method if SuperFrame was initialized without 'toplevel=True'.")
        self.toplevel.withdraw()

    def deiconify(self):
        if not self.toplevel:
            raise AttributeError("Cannot use deiconify() method if SuperFrame was initialized without 'toplevel=True'.")
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
        """Set the size and position of this SuperFrame, if `toplevel=True`. Should not be called otherwise.

        Should be called in your SuperFrame's constructor after all widgets have been initialized, unless you already
        know the exact dimensions you want. The SuperFrame will always attempt to remain fully visible on the screen.
        If neither `absolute_position` nor `relative_position` are given, the SuperFrame will appear centered in the
        display.

        Args:
            master (tk.BaseWidget): master of this SuperFrame, used for calculating `relative_position` and `transient`
                master. Defaults to master of `self.toplevel`.
            dimensions (tuple): pair of (width, height) values in pixels. Defaults to dimensions requested by the
                window.
            absolute_position (tuple): pair of (x, y) values in pixels on the screen, where (0, 0) is the bottom-left
                corner. Cannot be used at the same time as `relative_position`.
            relative_position (tuple): pair of (x, y) values as proportions of the size of the `master`, where (0, 0)
                is the top-left corner and (1, 1) is the bottom-right corner. If `master` does not have a mapped size,
                this argument will be ignored. Cannot be used at the same time as `absolute_position`.
            transient (bool): if True, this SuperFrame won't appear in the task bar, will always be drawn on top of its
                master, and will be automatically hidden when its master is iconified or withdrawn.
        """
        if self.toplevel is None:
            raise RuntimeError("SuperFrame was created with `toplevel=False` and has no geometry to set.")
        master = master or self.toplevel.master

        if absolute_position is not None and relative_position is not None:
            raise ValueError("You cannot specify both `absolute_position` and `relative_position` of the SuperFrame.")
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

    def get_style_kwargs(self, kwargs_dict: dict[str, tp.Any]) -> dict[str, tp.Any]:
        """Return a new dictionary that contains only keywords relevant to style (and also 'font')."""
        return {k: v for k, v in kwargs_dict.items() if k in self.STYLE_DEFAULTS or k == "font"}

    def resolve_font(
        self,
        font: tuple[str | None, int | None] | str | int | None,
        default_key: str = "label",
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

    def new_superframe(
        self,
        frame: FRAMELIKE_TYPING = None,
        super_frame_class: type[SuperFrame] = None,
        row_weights: tp.Sequence[int] = (),
        column_weights: tp.Sequence[int] = (),
        **kwargs,
    ):
        if super_frame_class is None:
            super_frame_class = SuperFrame
        elif not issubclass(super_frame_class, SuperFrame):
            raise TypeError(f"`super_frame_class` must be a subclass of `SuperFrame`, not {super_frame_class}.")
        super_frame = super_frame_class(master=frame, **kwargs)
        for i, w in enumerate(row_weights):
            super_frame.rowconfigure(i, weight=w)
        for i, w in enumerate(column_weights):
            super_frame.columnconfigure(i, weight=w)
        return super_frame

    def LoadingDialog(
        self,
        title: str,
        message: str,
        font: FONT_TYPING = None,
        style_defaults: dict[str, tp.Any] = None,
        loading_dialog_subclass: type[LoadingDialog] = None,
        **progressbar_kwargs,
    ) -> LoadingDialog:
        """Creates a child `LoadingDialog` with `style_defaults` taken from SuperFrame by default."""
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
        """Creates a child `CustomDialog` with `style_defaults` taken from SuperFrame by default."""
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
            widget.bind("<Enter>", lambda _, f=scrollable_widget: bind_to_mousewheel(f))
            widget.bind("<Leave>", lambda _, f=scrollable_widget: unbind_to_mousewheel(f))

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
        master: FRAMELIKE_TYPING | tp.Callable | str = None,
        auto_rows: int = None,
        auto_columns: int = None,
        grid_defaults: dict[str, tp.Any] = None,
        **frame_kwargs,
    ):
        """Context manager to temporarily set the master of the SuperFrame.

        Resets to previous master after use.
        """
        previous_frame = self.current_framelike

        if master is None:
            self.current_framelike = self.Frame(**frame_kwargs)
        else:
            if isinstance(master, str):
                try:
                    master = getattr(self, master)
                except AttributeError:
                    raise ValueError(
                        f"Invalid master type string: {master}. Must be one of: Frame, Toplevel, Notebook, Canvas"
                    )
            if master in {self.Frame, self.Toplevel, self.Notebook, self.Canvas}:
                self.current_framelike = master(**frame_kwargs)
            elif isinstance(master, (tk.Toplevel, ttk.Notebook, tk.Frame, tk.Canvas)):
                if frame_kwargs:
                    raise ValueError("Cannot use `set_master` keyword arguments when passing an existing `master`.")
                self.current_framelike = master
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
            yield self.current_framelike
        finally:
            self.current_row = previous_auto_row
            self.current_column = previous_auto_column
            if grid_defaults is not None:
                self.grid_defaults = previous_grid_defaults
            self.current_framelike = previous_frame

    # endregion

    # region Private Methods

    def _process_button_kwargs(
        self,
        button_kwargs: str | tuple[str] | list[str] | dict[str, tp.Any] | None
    ) -> tuple[dict[str, tp.Any]] | list[dict[str, tp.Any]] | dict[str, tp.Any] | None:
        if button_kwargs is None:
            return None
        elif isinstance(button_kwargs, str):
            try:
                return self.DEFAULT_BUTTON_KWARGS[button_kwargs],  # note tuple
            except KeyError:
                raise KeyError(f"Invalid `SuperFrame.DEFAULT_BUTTON_KWARGS` key: {button_kwargs}")
        elif isinstance(button_kwargs, (tuple, list)):
            button_kwargs = list(button_kwargs)
            for i, b in enumerate(button_kwargs):
                if isinstance(b, str):
                    try:
                        button_kwargs[i] = self.DEFAULT_BUTTON_KWARGS[b]
                    except KeyError:
                        raise KeyError(f"Invalid `SuperFrame.DEFAULT_BUTTON_KWARGS` key: {b}")
                elif not isinstance(b, dict):
                    raise TypeError(
                        f"If `button_kwargs` is a sequence, each element should be a string key to "
                        f"`SuperFrame.DEFAULT_BUTTON_KWARGS` or a dictionary of `Button` kwargs, not: {type(b)}"
                    )
            return button_kwargs
        elif not isinstance(button_kwargs, dict):
            raise TypeError(
                f"`button_kwargs` should be a dictionary of `Button` kwargs, a sequence of such dicts (one per button "
                f"name), or a string or list of strings that are keys to `SuperFrame.DEFAULT_BUTTON_KWARGS`, not: "
                f"{type(button_kwargs)}"
            )
        return button_kwargs

    # endregion
