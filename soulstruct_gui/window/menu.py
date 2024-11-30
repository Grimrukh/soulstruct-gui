from __future__ import annotations

__all__ = ["SmartMenu"]

import tkinter as tk


class SmartMenu(tk.Menu):
    """Menu subclass that automatically applies style defaults to kwargs passed to `tk.Menu` methods."""

    style: dict[str, str]

    def __init__(self, *args, **kwargs):
        self.style = {}
        for style_key in ("fg", "bg"):
            if style_key in kwargs:
                self.style[style_key] = kwargs[style_key]
        super().__init__(*args, **kwargs)

    def add_cascade(self, *args, **kwargs):
        self._apply_style_kwargs(**kwargs)
        super().add_cascade(*args, **kwargs)

    def add_checkbutton(self, *args, **kwargs):
        self._apply_style_kwargs(**kwargs)
        super().add_checkbutton(*args, **kwargs)

    def add_command(self, *args, **kwargs):
        self._apply_style_kwargs(**kwargs)
        super().add_command(*args, **kwargs)

    def add_radiobutton(self, *args, **kwargs):
        self._apply_style_kwargs(**kwargs)
        super().add_radiobutton(*args, **kwargs)

    def add_separator(self, *args, **kwargs):
        self._apply_style_kwargs(("bg",), **kwargs)
        super().add_separator(*args, **kwargs)

    def _apply_style_kwargs(self, only_keys=(), **kwargs):
        for key, value in self.style.items():
            if only_keys and key not in only_keys:
                continue
            kwargs.setdefault(key, value)
