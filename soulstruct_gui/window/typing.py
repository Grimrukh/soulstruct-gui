__all__ = [
    "FRAMELIKE_TYPING",
    "FONT_TYPING",
]

import typing as tp

import tkinter as tk
from tkinter import ttk


# Widget types that can be set as the `framelike_parent` argument of `BaseSmartWidget`s.
FRAMELIKE_TYPING = tp.Union[tk.Frame, tk.Toplevel, ttk.Notebook, tk.Canvas, None]

# Accepted types for `font` arguments that are processed into `(type, size)` tuples for widgets.
# It is permitted to supply only type and/or size, and get the other from the default font.
FONT_TYPING = tuple[str | None, int | None] | str | int | None
