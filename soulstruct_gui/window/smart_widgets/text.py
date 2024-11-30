from __future__ import annotations

__all__ = ["Text"]

import tkinter as tk
import typing as tp

from .base import *
from .config import *

if tp.TYPE_CHECKING:
    from ..super_frame import SuperFrame


class Text(BaseWidget[tk.Text]):

    WIDGET_CLASS = tk.Text
    USE_TEXT_STYLE_DEFAULTS = True
    USE_CURSOR_STYLE_DEFAULTS = True
    USE_ENTRY_STYLE_DEFAULTS = False

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
        # Text:
        initial_text="",
        **text_kwargs,
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
            **text_kwargs,
        )

        self.widget.insert(1.0, initial_text)
