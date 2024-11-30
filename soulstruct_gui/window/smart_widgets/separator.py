from __future__ import annotations

__all__ = ["Separator"]

from tkinter import ttk

from .base import *


class Separator(BaseWidget[ttk.Separator]):

    WIDGET_CLASS = ttk.Separator
    DEFAULT_STYLE_CONFIG = None
