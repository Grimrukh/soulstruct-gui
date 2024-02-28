from __future__ import annotations

__all__ = ["MapsEditor"]

from soulstruct.eldenring import game_types

from soulstruct_gui.base.editors import MapsEditor as BaseMapsEditor


class MapsEditor(BaseMapsEditor):

    GAME_TYPES_MODULE = game_types
