"""Adds `SmartFrame`-imbued attributes to `Tkinter` widgets."""

__all__ = [
    # var added
    "Button",
    "Checkbutton",
    "Combobox",
    "Entry",
    "Label",
    "Radiobutton",
    "Scale",

    # direct from `tk`
    "Frame",
    "Toplevel",
    "Listbox",
    "TextBox",
    "PanedWindow",
    "Scrollbar",
    "Canvas",

    # direct from `ttk`
    "Notebook",
    "Separator",
    "Progressbar",
]

import tkinter as tk
from tkinter import Frame, Toplevel, Listbox, Text as TextBox, PanedWindow, Scrollbar, Canvas
from tkinter import ttk
from tkinter.ttk import Notebook, Separator, Progressbar


class Button(ttk.Button):
    var: tk.StringVar


class Checkbutton(tk.Checkbutton):
    var: tk.BooleanVar


class Combobox(ttk.Combobox):
    var: tk.StringVar


class Entry(tk.Entry):
    var: tk.StringVar


class Label(tk.Label):
    var: tk.StringVar


class Radiobutton(tk.Radiobutton):
    var: tk.IntVar


class Scale(tk.Scale):
    var: tk.DoubleVar | tk.IntVar
