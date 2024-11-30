from __future__ import annotations

__all__ = ["Combobox"]

import typing as tp

import tkinter as tk
from tkinter import ttk

from .base import *
from .config import *

if tp.TYPE_CHECKING:
    from ..super_frame import SuperFrame
    from .typing import FRAMELIKE_TYPING


class Combobox(BaseWidget[ttk.Combobox]):

    WIDGET_CLASS = ttk.Combobox
    USE_STYLE_DEFAULTS = False  # ttk
    # TODO: Get `ttk.Style` from SuperFrame.

    var: tk.StringVar

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
        # Combobox:
        values: list[str] | tuple[str, ...] = None,
        initial_value: str = None,
        readonly=True,
        width=20,
        on_select_function=None,
        **combobox_kwargs,
    ):
        initial_value = initial_value or (values[0] if values else "")
        self.var = tk.StringVar(frame, value=initial_value)

        kwargs = dict(
            values=values,
            state="readonly" if readonly else "",
            width=width,
            textvariable=self.var,
        )
        kwargs |= combobox_kwargs

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

        if on_select_function is not None:
            self.widget.bind("<<ComboboxSelected>>", on_select_function)
