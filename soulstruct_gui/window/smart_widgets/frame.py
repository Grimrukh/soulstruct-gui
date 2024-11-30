from __future__ import annotations

__all__ = ["Frame"]

import tkinter as tk
import typing as tp

from .base import *

if tp.TYPE_CHECKING:
    from ..super_frame import SuperFrame


class Frame(BaseWidget[tk.Frame]):

    WIDGET_CLASS = tk.Frame
    IS_FRAMELIKE = True

    @classmethod
    def full_frame(
        cls,
        super_frame: SuperFrame,
        framelike_parent: FRAMELIKE_TYPING = None,
    ):
        """Create a `Frame` that fills the entire `framelike_parent` (defaults to `super_frame.current_framelike`)."""
        return cls(
            super_frame=super_frame,
            framelike_parent=framelike_parent,
            row=0,
            column=0,
            sticky="nsew",
            row_weights=[1],
            column_weights=[1],
        )
