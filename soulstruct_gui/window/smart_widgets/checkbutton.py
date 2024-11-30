from __future__ import annotations

__all__ = ["Checkbutton", "ClassicCheckbutton"]

import typing as tp

import tkinter as tk

from .base import *
from .config import *

if tp.TYPE_CHECKING:
    from ..super_frame import SuperFrame
    from .typing import FRAMELIKE_TYPING


class Checkbutton(BaseWidget[tk.Checkbutton]):

    WIDGET_CLASS = tk.Checkbutton

    var: tk.BooleanVar

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
        # Checkbutton:
        command: tp.Callable[[], None] = None,
        initial_state=False,
        text="",
        **checkbutton_kwargs,
    ):

        self.var = tk.BooleanVar(value=initial_state)
        kwargs = dict(
            command=command,
            text=text,
            variable=self.var,
            image=super_frame._OFF_IMAGE,
            selectimage=super_frame._ON_IMAGE,
            indicatoron=False,
            borderwidth=0,
            selectcolor="#444",
        )
        kwargs |= checkbutton_kwargs

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

    @classmethod
    def _get_default_style(cls) -> StyleConfig:
        return StyleConfig(bg="#444")


class ClassicCheckbutton(BaseWidget[tk.Checkbutton]):
    """Without my custom image, etc."""

    WIDGET_CLASS = tk.Checkbutton
    DEFAULT_LABEL_CONFIG = LabelConfig(position="left")

    var: tk.BooleanVar

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
        # Checkbutton:
        command: tp.Callable[[], None] = None,
        initial_state=False,
        text="",
        **checkbutton_kwargs,
    ):
        self.var = tk.BooleanVar(value=initial_state)
        kwargs = dict(
            command=command,
            text=text,
            variable=self.var,
        )
        kwargs |= checkbutton_kwargs

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
