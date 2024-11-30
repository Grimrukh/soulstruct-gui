from __future__ import annotations

__all__ = ["Menu"]

import tkinter as tk
import typing as tp

from .base import *
from .config import *

if tp.TYPE_CHECKING:
    from ..super_frame import SuperFrame
    from .typing import FRAMELIKE_TYPING


class Menu(BaseWidget[tk.Menu]):
    """Automatically copies `tk.Menu` widget style into the various Menu item creation methods."""

    WIDGET_CLASS = tk.Menu
    DEFAULT_STYLE_CONFIG = StyleConfig(bg="#444", fg="#FFF")
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
        # Menu:
        tearoff=0,
        **menu_kwargs,
    ):
        kwargs = dict(tearoff=tearoff)
        kwargs |= menu_kwargs

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
