from __future__ import annotations

__all__ = [
    "bind_to_all_children",
    "bind_to_mousewheel",
    "unbind_to_mousewheel",
    "print_widget_hierarchy",
]

import tkinter as tk


def bind_to_all_children(widget: tk.BaseWidget, sequence, func, add=None):
    """Bind given event to specified widget and all its children, recursively.

    No trivial way to unbind them all, so make this is only used for short-lived widget hierarchies.
    """
    widget.bind(sequence=sequence, func=func, add=add)
    for child in widget.winfo_children():
        bind_to_all_children(child, sequence=sequence, func=func, add=add)


def bind_to_mousewheel(widget, vertical=True, horizontal=False):
    if vertical:
        widget.bind_all("<MouseWheel>", lambda event: widget.yview_scroll(-1 * (event.delta // 120), "units"))
    if horizontal:
        widget.bind_all("<Shift-MouseWheel>", lambda event: widget.xview_scroll(-1 * (event.delta // 120), "units"))


def unbind_to_mousewheel(widget):
    widget.unbind_all("<MouseWheel>")
    widget.unbind_all("<Shift-MouseWheel>")


def print_widget_hierarchy(widget, indent=0):
    print(" " * indent + str(widget))
    for child in widget.winfo_children():
        print_widget_hierarchy(child, indent=indent + 4)
