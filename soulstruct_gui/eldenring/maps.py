from __future__ import annotations

__all__ = ["MapsEditor"]

from soulstruct.eldenring import game_types
from soulstruct.eldenring.maps.parts import MSBPart

from soulstruct_gui.base.editors import MapsEditor as BaseMapsEditor


class MapsEditor(BaseMapsEditor):

    GAME_TYPES_MODULE = game_types
    GROUP_BIT_COUNT = MSBPart.GROUP_BIT_COUNT
