from __future__ import annotations

__all__ = ["Notebook"]

import tkinter as tk
import typing as tp
from tkinter import ttk

from .base import *
from .config import *

if tp.TYPE_CHECKING:
    from ..super_frame import SuperFrame


class Notebook(BaseWidget[ttk.Notebook]):

    WIDGET_CLASS = ttk.Notebook

    # Uses `ttk.Style` stored in `SuperFrame`.
    DEFAULT_STYLE_CONFIG = None
    STYLE_FIELDS = {}
