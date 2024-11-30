from __future__ import annotations

__all__ = ["Button", "TtkButton"]

import tkinter as tk
import typing as tp
from tkinter import ttk

from .base import *
from .config import *

if tp.TYPE_CHECKING:
    from ..super_frame import SuperFrame
    from .typing import FRAMELIKE_TYPING


class Button(BaseWidget[tk.Button]):

    WIDGET_CLASS = tk.Button
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
        # Button:
        command: tp.Callable[[], tp.Any] = None,
        text: str = None,
        text_padx: int = None,
        text_pady: int = None,
        **button_kwargs,
    ):
        if not command:
            raise ValueError("Button must have a `command`.")

        self.var = tk.StringVar(value=text) if text is not None else None
        kwargs = dict(command=command, textvariable=self.var, padx=text_padx, pady=text_pady)
        kwargs |= button_kwargs

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
            **button_kwargs,            
        )


class TtkButton(BaseWidget[ttk.Button]):

    WIDGET_CLASS = ttk.Button
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
        # Button:
        command: tp.Callable[[], tp.Any] = None,
        text: str = None,
        text_padx: int = None,
        text_pady: int = None,
        style: ttk.Style = None,
        **button_kwargs,
    ):
        if not command:
            raise ValueError("Button must have a `command`.")

        self.var = tk.StringVar(value=text) if text is not None else None
        kwargs = dict(command=command, textvariable=self.var, padx=text_padx, pady=text_pady, style=style)
        kwargs |= button_kwargs

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
