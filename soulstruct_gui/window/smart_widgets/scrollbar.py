from __future__ import annotations

__all__ = ["Scrollbar"]

import tkinter as tk

from .base import *


class Scrollbar(BaseWidget[tk.Scrollbar]):

    WIDGET_CLASS = tk.Scrollbar
    DEFAULT_STYLE_CONFIG = None
