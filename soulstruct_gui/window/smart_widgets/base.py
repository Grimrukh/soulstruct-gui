"""Base wrapper class for `tk` and `ttk` widgets, with automatic grid handling and other life-easing features.

Must be used with a `SuperFrame` parent.
"""
from __future__ import annotations

__all__ = [
    "BaseWidget",
]

import abc
import tkinter as tk
import typing as tp
from tkinter import ttk
from tkinter.constants import *

from ..tooltip import ToolTip
from ..utilities import bind_to_mousewheel, unbind_to_mousewheel
from .config import *

if tp.TYPE_CHECKING:
    from ..super_frame import SuperFrame
    from .typing import FRAMELIKE_TYPING


WIDGET_T = tp.TypeVar("WIDGET_T", bound=tk.Widget | ttk.Widget)


class BaseWidget(abc.ABC, tp.Generic[WIDGET_T]):
    """Wrapped `tk` or `ttk` widget that manages grid placement (through a master `SuperFrame` and a direct
    `framelike_parent` SuperFrame or BaseFramelikeSmartWidget parent) and style configuration."""

    # Widget class. Must be overridden in subclass and match `WIDGET_T`.
    WIDGET_CLASS: tp.ClassVar[tp.Type[tk.Widget | ttk.Widget]]
    # If enabled, `row_weights` and `column_weights` keyword arguments can be used.
    IS_FRAMELIKE: tp.ClassVar[bool] = False

    # Default style options to apply. (Only subclass-appropriate options will be used.)
    DEFAULT_STYLE_CONFIG: tp.ClassVar[StyleConfig | None] = StyleConfig()
    # `StyleConfig` fields to actually apply with `widget.config()`. Default is just 'bg'. Other common categories:
    #   - Widgets with text: {'fg', 'font'}
    #   - Widgets with a cursor: {'insertbackground'}
    #   - Widgets with different entry states: {'disabledforeground', 'disabledbackground', 'readonlybackground'}
    STYLE_FIELDS: tp.ClassVar[set[str]] = {"bg"}

    # Available subclass override for default `LabelConfig.position`.
    DEFAULT_LABEL_CONFIG: tp.ClassVar[LabelConfig | None] = LabelConfig()

    __slots__ = (
        "widget",
        "style_config",
        "label",
        "v_scrollbar",
        "h_scrollbar",
    )

    # Wrapped widget instance.
    widget: WIDGET_T
    # Recorded `StyleConfig` for children to inherit as needed.
    style_config: StyleConfig | None
    # Optional attached managed label.
    label: tk.Label | None
    # Optional attached managed scrollbars. Both may be used.
    v_scrollbar: tk.Scrollbar | None
    h_scrollbar: tk.Scrollbar | None

    def __init__(
        self,
        super_frame: SuperFrame,
        framelike_parent: FRAMELIKE_TYPING = None,
        style_config: StyleConfig | str = "default",
        label_text: str = "",
        label_config: LabelConfig | None = None,
        grid_config: GridConfig | str = None,
        vertical_scrollbar: bool = False,
        horizontal_scrollbar: bool = False,
        tooltip_text="",
        row_weights: tp.Sequence[int] = (),  # only permitted when `IS_FRAMELIKE` is True
        column_weights: tp.Sequence[int] = (),  # only permitted when `IS_FRAMELIKE` is True
        **widget_kwargs,  # passed directly to underlying tk/ttk widget class
    ):
        """Create a new 'smart' wrapped widget.

        Args:
            super_frame: Parent `SuperFrame` instance. Manages automatic row/column placement and style defaults.
            framelike_parent: Optional parent framelike wrapper for this widget.
                If not given, uses `super_frame.current_frame` or `master_frame`.
            style_config: Configuration for the widget style (font, fg, bg, etc.).
                Can also be one of the strings: "default" (use `DEFAULT_STYLE_CONFIG`), "parent"
                (use `framelike_parent.style_config`), or "off" (no style applied).
            label_text: Text to display in a label above, below, to the left, or to the right of the widget.
            label_config: Configuration for the label (font, fg, bg, position). Default is in class variable.
            grid_config: Configuration for the grid placement of the widget and label.
                Can also be set to special string "off" to disable grid placement entirely.
            vertical_scrollbar: Whether to add a vertical scrollbar to the widget.
            horizontal_scrollbar: Whether to add a horizontal scrollbar to the widget.
            tooltip_text: Text to display in a tooltip when hovering over the widget, if given.
            widget_kwargs: Passed directly to the underlying `tk` or `ttk` widget.
                Subclasses of this will make explicit at least some of these (painful to list them all).
        """

        # `widget_kwargs` should not contain keys that are managed by `StyleConfig` or `GridConfig`.
        for key in widget_kwargs:
            if key in StyleConfig.__annotations__:
                raise ValueError(f"Invalid widget keyword argument: {key}. Use `style_config.{key}` instead.")
            if key in GridConfig.__annotations__:
                raise ValueError(f"Invalid widget keyword argument: {key}. Use `grid_config.{key}` instead.")

        if isinstance(grid_config, str) and grid_config.lower() == "off":
            grid_kwargs, add_row, add_column = (grid_config or GridConfig()).parse_with_auto(super_frame)
            super_frame.current_row += add_row
            super_frame.current_column += add_column
        elif grid_config is not None and not isinstance(grid_config, GridConfig):
            raise ValueError(
                f"Invalid `grid_config` value: {repr(grid_config)}. "
                f"Must be a `GridConfig` instance, None (default), or string 'off'."
            )
        else:
            # `widget.grid()` will not even be called.
            grid_kwargs = {}

        if isinstance(style_config, str):
            match style_config.lower():
                case "default":
                    self.style_config = self.DEFAULT_STYLE_CONFIG  # frozen
                case "parent":
                    if framelike_parent is None:
                        raise ValueError("Cannot use 'parent' style when no parent framelike is given.")
                    self.style_config = framelike_parent.style_config
                case "off":
                    self.style_config = None
                case _:
                    raise ValueError(
                        f"Invalid `style_config` string option: {repr(style_config)}. "
                        f"Must be 'default', 'parent', or 'off'."
                    )
        elif isinstance(style_config, StyleConfig):
            self.style_config = style_config
        elif style_config is None:
            self.style_config = None  # no style used
        else:
            raise ValueError(
                f"Invalid `style_config` value: {repr(style_config)}. "
                f"Must be a `StyleConfig` instance, a string ('default' / 'parent' / 'off'), or None (== 'off')."
            )

        if framelike_parent is None:
            framelike = super_frame.current_framelike or super_frame.master_frame
        else:
            framelike = framelike_parent.widget

        # Unlike `style_config`, labels are disabled by just setting `label_text=""`, so we don't need to differentiate
        # between `None` and a 'default' argument here (and there's no parent inheritance).
        label_config = label_config or self.DEFAULT_LABEL_CONFIG

        if label_text:
            label_bg = label_config.bg or style_config.bg
            label_fg = label_config.fg or style_config.fg
            label_font = label_config.font or style_config.font
            inherit_bg = framelike.cget("bg")
            # We replace `framelike` entirely here, so that all uses of `framelike` below include the label.
            framelike = tk.Frame(framelike, bg=inherit_bg)
            self.label = tk.Label(framelike, text=label_text, font=label_font, fg=label_fg, bg=label_bg)
        else:
            self.label = None

        self.v_scrollbar = None
        self.h_scrollbar = None

        if vertical_scrollbar or horizontal_scrollbar:
            inherit_bg = framelike.cget("bg")
            scrolling_frame = tk.Frame(framelike, bg=inherit_bg)
            self.widget = self._create_widget(frame=scrolling_frame, **widget_kwargs, **grid_kwargs)
            self.widget.grid(row=0, column=0, sticky="nsew")
            if vertical_scrollbar:
                self.v_scrollbar = tk.Scrollbar(scrolling_frame, orient=VERTICAL, command=self.widget.yview)
                self.v_scrollbar.grid(row=0, column=1, sticky=NS)
                self.widget.config(bd=0, yscrollcommand=self.v_scrollbar.set)
            if horizontal_scrollbar:
                self.h_scrollbar = tk.Scrollbar(scrolling_frame, orient=HORIZONTAL, command=self.widget.xview)
                self.h_scrollbar.grid(row=1, column=0, sticky=EW)
                self.widget.config(bd=0, xscrollcommand=self.h_scrollbar.set)
            self.widget.bind(
                "<Enter>", lambda _, f=self.widget: bind_to_mousewheel(f, vertical_scrollbar, horizontal_scrollbar)
            )
            self.widget.bind("<Leave>", lambda _, f=self.widget: unbind_to_mousewheel(f))
            scrolling_frame.rowconfigure(0, weight=1)
            if horizontal_scrollbar:
                scrolling_frame.rowconfigure(1, weight=0)
            scrolling_frame.columnconfigure(0, weight=1)
            if vertical_scrollbar:
                scrolling_frame.columnconfigure(1, weight=0)
            if self.label:
                # Remember that `framelike` is the new label-containing frame.
                self._grid_label(framelike, self.label, scrolling_frame, label_position)
                if grid_kwargs:
                    framelike.grid(**grid_kwargs)
                # Used to set `self.widget.label = label` here, but no longer necessary.
            elif grid_kwargs:
                scrolling_frame.grid(**grid_kwargs)
        else:
            self.widget = self._create_widget(frame=framelike_parent.widget, **widget_kwargs, **grid_kwargs)
            if self.label:
                # Remember that `framelike` is the new label-containing frame.
                self._grid_label(framelike, self.label, self.widget, label_position)
                if grid_kwargs:
                    framelike.grid(**grid_kwargs)
                # Used to set `self.widget.label = label` here, but no longer necessary.
            elif grid_kwargs:
                self.widget.grid(**grid_kwargs)

        if tooltip_text:
            ToolTip(self.widget, text=tooltip_text)

        self.apply_style_config()

        if self.IS_FRAMELIKE:
            for i, w in enumerate(row_weights):
                self.widget.rowconfigure(i, weight=w)
            for i, w in enumerate(column_weights):
                self.widget.columnconfigure(i, weight=w)

    def apply_style_config(self):
        if not self.style_config:
            return
        config_kwargs = {k: v for k, v in asdict(self.style_config) if k in self.STYLE_FIELDS}
        self.widget.config(**config_kwargs)

    @classmethod
    def _create_widget(cls, **kwargs) -> WIDGET_T:
        """Wrapped widget creation. Must return the widget instance.

        Default just passes `kwargs` through and then checks style defaults.
        """
        widget = cls.WIDGET_CLASS(**kwargs)
        return widget

    @staticmethod
    def _grid_label(frame: tk.Frame, label: tk.Label, component, label_position: str):
        match label_position.lower():
            case "left":
                label.grid(row=0, column=0, padx=(0, 2))
                component.grid(row=0, column=1)
                frame.rowconfigure(0, weight=1)
                frame.columnconfigure(0, weight=0)
                frame.columnconfigure(1, weight=1)
            case "right":
                label.grid(row=0, column=1, padx=(2, 0))
                component.grid(row=0, column=0)
                frame.rowconfigure(0, weight=1)
                frame.columnconfigure(0, weight=1)
                frame.columnconfigure(1, weight=0)
            case "above":
                label.grid(row=0, column=0)
                component.grid(row=1, column=0)
                frame.rowconfigure(0, weight=0)
                frame.rowconfigure(1, weight=1)
                frame.columnconfigure(0, weight=1)
            case "below":
                label.grid(row=1, column=0)
                component.grid(row=0, column=0)
                frame.rowconfigure(0, weight=1)
                frame.rowconfigure(1, weight=0)
                frame.columnconfigure(0, weight=1)
            case _:
                raise ValueError(
                    f"Invalid label position: {repr(label_position)}. Must be 'left', 'right', 'above', or 'below'."
                )
