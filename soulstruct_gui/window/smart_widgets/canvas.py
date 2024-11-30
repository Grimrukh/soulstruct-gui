from __future__ import annotations

__all__ = ["Canvas"]

import tkinter as tk

from .base import *


class Canvas(BaseWidget[tk.Canvas]):

    WIDGET_CLASS = tk.Canvas
    IS_FRAMELIKE = True
