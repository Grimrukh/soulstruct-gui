from __future__ import annotations

__all__ = [
    "StyleConfig",
    "LabelConfig",
    "GridConfig",
]

import typing as tp
from dataclasses import dataclass, asdict
from enum import StrEnum

if tp.TYPE_CHECKING:
    from ..super_frame import SuperFrame


# Some 'style guide' font defaults for convenience.
SMALL_FONT = ("Inconsolata Regular", 12)
REGULAR_FONT = ("Inconsolata Regular", 14)
BOLD_FONT = ("Inconsolata Bold", 14)
HEADING_FONT = ("Inconsolata Bold", 18)


@dataclass(slots=True)
class LabelConfig:
    """Font/color defaults are taken from `StyleConfig`. Note that `label_text` is passed separately (common)."""
    font: tuple[str, int] | None = None
    fg: str = ""
    bg: str = ""
    position: str | None = "above"


@dataclass(slots=True)
class GridConfig:
    """Grid configuration values, conveniently packaged together.

    `column` and `row` default to the current values in the `SuperFrame` instance, or 0 if automatic incrementing for
    that dimension is not active. If it is active, then the corresponding argument must NOT be set here.
    """
    column: int | None = 0  # default is `SuperFrame.current_column` or 0
    row: int | None = 0  # default is `SuperFrame.current_row` or 0
    columnspan: int = 1
    rowspan: int = 1
    padx: int = 0
    pady: int = 0
    ipadx: int = 0
    ipady: int = 0
    sticky: str = ""

    def parse_with_auto(self, super_frame: SuperFrame) -> tuple[dict[str, int | str], int, int]:
        """Use `SuperFrame.current_row` and `SuperFrame.current_column` to fill in missing values.

        Returns dictionary of grid kwargs, and the increments to `SuperFrame` current row/column.
        """
        grid_kwargs = asdict(self)
        add_row = 0
        add_column = 0

        current_row = super_frame.current_row
        if self.row is None:
            if current_row is not None:
                grid_kwargs["row"] = current_row
                add_row = 1
            else:
                grid_kwargs["row"] = 0
        elif current_row is not None:
            raise ValueError(f"You cannot specify `GridConfig.row` while SuperFrame `auto_rows` is active.")

        current_column = super_frame.current_column
        if self.column is None:
            if current_column is not None:
                grid_kwargs["column"] = current_column
                add_column = 1
            else:
                grid_kwargs["column"] = 0
        elif current_column is not None:
            raise ValueError(f"You cannot specify `GridConfig.column` while SuperFrame `auto_columns` is active.")

        return grid_kwargs, add_row, add_column


@dataclass(slots=True, frozen=True)
class StyleConfig:
    """Combination of real `tkinter` style options and some default font types."""

    # GENERAL:
    bg: str = "#111"
    # TEXT:
    fg: str = "#FFF"  # text foreground
    font: tuple[str, int] = REGULAR_FONT
    # CURSOR:
    insertbackground: str = "#FFF"  # text cursor background
    # ENTRY:
    disabledforeground: str = "#888"
    disabledbackground: str = "#444"
    readonlybackground: str = "#444"

    def get_copy(self, **kwargs) -> StyleConfig:
        """Create a copy of this `StyleConfig` with any desired values overridden."""
        style_dict = asdict(self)
        style_dict.update(kwargs)
        return StyleConfig(**style_dict)
