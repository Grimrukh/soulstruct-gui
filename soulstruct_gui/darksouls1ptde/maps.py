from __future__ import annotations

__all__ = ["MapsEditor"]

from soulstruct.darksouls1ptde import game_types
from soulstruct.darksouls1ptde.game_types import ObjActParam, PlaceName, BaseDrawParam
from soulstruct.darksouls1ptde.maps.parts import MSBPart

from soulstruct_gui.base.editors.maps import MapsEditor as BaseMapsEditor


class MapsEditor(BaseMapsEditor):

    GAME_TYPES_MODULE = game_types
    GROUP_BIT_COUNT = MSBPart.GROUP_BIT_COUNT

    def get_field_links(self, field_type, field_value, valid_null_values=None) -> list:
        if field_type == ObjActParam and field_value == -1:
            # Link to ObjActParam with the same ID as its attached `MSBObject` model.
            obj_act_part = self.get_selected_field_dict()["obj_act_part"]  # type: MSBPart
            try:
                if obj_act_part is None:
                    raise KeyError(f"`obj_act_part` is None.")
            except KeyError:  # invalid or `None` part name
                pass
            else:
                field_value = int(obj_act_part.model.name[1:5])
        if valid_null_values is None:
            if field_type == PlaceName:
                valid_null_values = {-1: "Default Map Name + Force Banner"}
            elif issubclass(field_type, BaseDrawParam):
                valid_null_values = {-1: "Default/None"}
            else:
                valid_null_values = {0: "Default/None", -1: "Default/None"}
        if issubclass(field_type, BaseDrawParam) and self.active_category.endswith("MapConnections"):
            map_override = self.get_selected_field_dict().connected_map.emevd_file_stem
        else:
            map_override = None
        return self.linker.soulstruct_link(
            field_type, field_value, valid_null_values=valid_null_values, map_override=map_override,
        )
