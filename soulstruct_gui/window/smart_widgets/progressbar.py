from __future__ import annotations

__all__ = ["Progressbar"]

from tkinter import ttk

from .base import *


class Progressbar(BaseWidget[ttk.Progressbar]):

    WIDGET_CLASS = ttk.Progressbar
    USE_STYLE_DEFAULTS = False
