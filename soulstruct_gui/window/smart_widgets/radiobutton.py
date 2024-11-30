from __future__ import annotations

__all__ = ["Radiobutton"]

import tkinter as tk
import typing as tp

from .base import *
from .config import *

if tp.TYPE_CHECKING:
    from ..super_frame import SuperFrame


class Radiobutton(BaseWidget[tk.Radiobutton]):

    WIDGET_CLASS = tk.Radiobutton

    var: tk.IntVar

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
        # Radiobutton:
        command: tp.Callable[[], None] = None,
        int_variable: tk.IntVar = None,
        **radiobutton_kwargs,
    ):
        self.var = int_variable or tk.IntVar()
        kwargs = dict(command=command, textvariable=self.var, text="")
        kwargs |= radiobutton_kwargs

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
