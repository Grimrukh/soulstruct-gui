__all__ = ["FRAMELIKE_TYPING"]

import typing as tp

from ..super_frame import SuperFrame
from .frame import Frame
from .toplevel import Toplevel
from .canvas import Canvas
from .notebook import Notebook

# All classes that are accepted as `framelike_parent` arguments in `BaseSmartWidget` subclasses.
FRAMELIKE_TYPING = tp.Union[SuperFrame, Frame, Toplevel, Canvas, Notebook, None]
