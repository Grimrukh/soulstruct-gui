from __future__ import annotations

__all__ = ["Entry"]

import logging
import typing as tp

import tkinter as tk

from .base import *
from .config import *

if tp.TYPE_CHECKING:
    from ..super_frame import SuperFrame
    from .typing import FRAMELIKE_TYPING

_LOGGER = logging.getLogger("soulstruct_gui")


class Entry(BaseWidget[tk.Entry]):

    WIDGET_CLASS = tk.Entry
    STYLE_FIELDS = {
        "bg",
        "fg",
        "font",
        "insertbackground",
        "disabledforeground",
        "disabledbackground",
        "readonlybackground",
    }
    DEFAULT_LABEL_CONFIG = LabelConfig(position="left")

    var: tk.StringVar
    numbers_only: bool
    integers_only: bool

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
        # Entry:
        initial_text="",
        integers_only=False,
        numbers_only=False,
        **entry_kwargs,
    ):
        if False not in {integers_only, numbers_only}:
            raise ValueError("You must specify either `integers_only` or `numbers_only` (not both).")

        if "text" in entry_kwargs:
            _LOGGER.warning(
                "'text' argument given to smart `Entry`. I recommend using `textvariable` instead to ensure "
                "you do not confuse this argument with `initial_text`."
            )

        self.var = tk.StringVar(value=initial_text)
        kwargs = dict(textvariable=self.var)
        kwargs |= entry_kwargs

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

        self.integers_only = integers_only
        self.numbers_only = numbers_only

        if integers_only:
            v_cmd = (super_frame.master.register(self._validate_entry_integers), "%P")
            self.widget.config(validate="key", validatecommand=v_cmd)
        elif numbers_only:
            v_cmd = (super_frame.master.register(self._validate_entry_numbers), "%P")
            self.widget.config(validate="key", validatecommand=v_cmd)

    @staticmethod
    def _validate_entry_integers(new_value):
        """Callback invoked whenever the Entry contents change.

        Returns True if the value of the Entry ('%P') can be interpreted as an `int` (or is empty or a minus sign).
        """
        if new_value in {"", "-"}:
            return True  # Empty strings and minus sign only is permitted (minus sign must be handled by caller).
        try:
            int(new_value)
        except ValueError:
            return False
        return True

    @staticmethod
    def _validate_entry_numbers(new_value):
        """Callback invoked whenever the Entry contents change.

        Returns True if the value of the Entry ('%P') can be interpreted as a `float` (or is empty or a minus sign).
        """
        if new_value in {"", "-"}:
            return True  # Empty strings and minus sign only is permitted (minus sign must be handled by caller).
        try:
            float(new_value)
        except ValueError:
            return False
        return True

    # TODO: Can probably add some handy numeric converter properties here.
