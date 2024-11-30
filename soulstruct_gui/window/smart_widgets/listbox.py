from __future__ import annotations

__all__ = ["Listbox"]

import tkinter as tk
import typing as tp
from tkinter.constants import END

from .base import *
from .config import *

if tp.TYPE_CHECKING:
    from ..super_frame import SuperFrame
    from .typing import FRAMELIKE_TYPING


class Listbox(BaseWidget[tk.Listbox]):

    WIDGET_CLASS = tk.Listbox
    STYLE_FIELDS = {"bg", "fg"}

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
        # Listbox:
        values: tp.Sequence[str] = (),
        on_select_function=None,
        **listbox_kwargs,
    ):
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
            **listbox_kwargs,
        )

        for value in values:
            self.widget.insert(END, value)

        if on_select_function is not None:
            self.widget.bind("<<ListboxSelect>>", on_select_function)
