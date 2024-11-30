from __future__ import annotations

__all__ = ["LoadingDialog"]

from tkinter.constants import *


class LoadingDialog(SuperFrame):
    """Simple box with a message and a loading bar. It is destroyed when appropriate."""

    def __init__(
        self,
        master: FRAMELIKE_TYPING,
        title="Loading...",
        message="",
        font: FONT_TYPING = None,
        style_defaults=None,
        **progressbar_kwargs,
    ):
        if style_defaults:
            self.STYLE_DEFAULTS = style_defaults
        super().__init__(master=master, toplevel=True, window_title=title)

        progressbar_kwargs.setdefault("orient", HORIZONTAL)
        progressbar_kwargs.setdefault("mode", "indeterminate")
        progressbar_kwargs.setdefault("sticky", EW)

        with self.set_master(auto_rows=0, padx=20, pady=20):
            self.Label(text=message, font=font, pady=10)
            self.progress = self.Progressbar(**progressbar_kwargs)

        self.set_geometry(transient=True)