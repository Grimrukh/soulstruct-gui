from __future__ import annotations

__all__ = ["Label"]

import tkinter as tk
import typing as tp

from .base import *
from .config import *

if tp.TYPE_CHECKING:
    from ..super_frame import SuperFrame
    from .typing import FRAMELIKE_TYPING


class Label(BaseWidget[tk.Label]):

    WIDGET_CLASS = tk.Label
    USE_TEXT_STYLE_DEFAULTS = True

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
        # Label:
        text: str | tk.StringVar = None,
        **label_kwargs,
    ):
        if isinstance(text, str):
            self.var = tk.StringVar(value=text)
        elif isinstance(text, tk.StringVar):
            self.var = text
        else:
            raise ValueError("Label `text` must be a string (even if empty) or existing `tk.StringVar`.")

        kwargs = dict(textvariable=self.var)
        kwargs |= label_kwargs

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
