from __future__ import annotations

__all__ = ["Scale"]

import tkinter as tk
import typing as tp
from tkinter.constants import HORIZONTAL

from .base import *
from .config import *

if tp.TYPE_CHECKING:
    from ..super_frame import SuperFrame


class Scale(BaseWidget[tk.Scale]):

    WIDGET_CLASS = tk.Scale

    var: tk.DoubleVar | tk.IntVar
    is_float: bool

    def __init__(
        self,
        super_frame: SuperFrame,
        framelike_parent: FRAMELIKE_TYPING = None,
        style_config: StyleConfig | str = "default",
        label_text: str = "",
        label_config: LabelConfig | None = None,
        grid_config: GridConfig | str = None,
        vertical_scrollbar: bool = False,
        horizontal_scrollbar: bool = False,
        tooltip_text="",
        # Scale:
        limits=(0, 100),
        orientation: str = HORIZONTAL,
        variable: tk.IntVar | tk.DoubleVar = None,
        is_float: bool = None,
        **scale_kwargs,
    ):
        if variable is None:
            self.var = tk.DoubleVar() if is_float else tk.IntVar()  # will default to `IntVar` if `is_float=None`
        else:
            if is_float is not None:
                raise ValueError("Cannot pass `is_float` keyword for `SuperFrame.Scale` if `variable` is given.")
            self.var = variable

        kwargs = dict(from_=limits[0], to=limits[1], orient=orientation, variable=self.var)
        kwargs |= scale_kwargs

        super().__init__(
            super_frame=super_frame,
            framelike_parent=framelike_parent,
            style_config=style_config,
            label_text=label_text,
            label_config=label_config,
            grid_config=grid_config,
            vertical_scrollbar=vertical_scrollbar,
            horizontal_scrollbar=horizontal_scrollbar,
            tooltip_text=tooltip_text,
            **kwargs,
        )
