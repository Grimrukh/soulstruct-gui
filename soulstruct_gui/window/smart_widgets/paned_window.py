from __future__ import annotations

__all__ = ["PanedWindow"]

import tkinter as tk

from .base import *


class PanedWindow(BaseWidget[tk.PanedWindow]):

    WIDGET_CLASS = tk.PanedWindow
    USE_STYLE_DEFAULTS = False
