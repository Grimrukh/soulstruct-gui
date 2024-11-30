from __future__ import annotations

__all__ = ["Toplevel"]

import tkinter as tk
import typing as tp

from .base import *

if tp.TYPE_CHECKING:
    from ..super_frame import SuperFrame


class Toplevel(FramelikeWidget[tk.Toplevel]):
    """NOTE: Most arguments are disabled here."""

    WIDGET_CLASS = tk.Toplevel
    DEFAULT_STYLE_CONFIG = None

    def __init__(
        self,
        super_frame: SuperFrame,
        framelike_parent: FRAMELIKE_TYPING = None,
        row_weights: tp.Sequence[int] = (),
        column_weights: tp.Sequence[int] = (),
        # Toplevel:
        title="Window Title",
        **toplevel_kwargs,
    ):
        super().__init__(
            super_frame=super_frame,
            framelike_parent=framelike_parent,
            style_config="off",
            label_text="",
            label_config=None,
            grid_config="off",
            vertical_scrollbar=False,
            horizontal_scrollbar=False,
            tooltip_text="",
            row_weights=row_weights,
            column_weights=column_weights,
            **toplevel_kwargs,
        )

        self.widget.title(title)
