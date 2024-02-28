from __future__ import annotations

__all__ = ["MapsEditor"]

from soulstruct.darksouls1r import game_types
from soulstruct.darksouls1r.game_types import ObjActParam, PlaceName, BaseDrawParam
from soulstruct.darksouls1ptde.maps.parts import MSBPart, MSBCollision

from soulstruct_gui.base.editors.maps import MapsEditor as BaseMapsEditor
from soulstruct_gui.darksouls1ptde.maps import MapConnectionCreator, MapEntryRow


class MapsEditor(BaseMapsEditor):

    GAME_TYPES_MODULE = game_types
    ENTRY_ROW_CLASS = MapEntryRow

    def get_field_links(self, field_type, field_value, valid_null_values=None) -> list:
        if field_type == ObjActParam and field_value == -1:
            # Link to ObjActParam with the object's model ID.
            obj_act_part = self.get_selected_field_dict()["obj_act_part"]  # type: MSBPart
            field_value = int(obj_act_part.model.name[1:5])

        if valid_null_values is None:
            if field_type == PlaceName:
                valid_null_values = {-1: "Default Map Name + Force Banner"}
            elif issubclass(field_type, BaseDrawParam):
                valid_null_values = {-1: "Default/None"}
            else:
                valid_null_values = {0: "Default/None", -1: "Default/None"}

        if issubclass(field_type, BaseDrawParam) and self.active_category.endswith("MapConnections"):
            map_id = [
                map_id_part if map_id_part != -1 else 0
                for map_id_part in self.get_selected_field_dict().connected_map_id
            ]
            map_override = f"m{map_id[0]:02d}_{map_id[1]:02d}_{map_id[2]:02d}_{map_id[3]:02d}"
        else:
            map_override = None
        return self.linker.soulstruct_link(
            field_type, field_value, valid_null_values=valid_null_values, map_override=map_override,
        )

    def create_map_connection(self, entry_id: int):
        """Create a `MapConnection` from the given `Collision` via a user pop-up."""
        collisions = self._get_category_subtype_list()
        collision = collisions[entry_id]  # type: MSBCollision
        map_connection = MapConnectionCreator(collision, self.maps.ALL_MAPS, master=self).go()
        if map_connection:
            msb = self.get_selected_msb()
            existing_map_connection_names = msb.map_connections.get_entry_names()
            if map_connection.name in existing_map_connection_names:
                self.error_dialog(
                    "Map Connection Name Conflict",
                    f"A Map Connection with the name '{map_connection.name}' already exists in this MSB. Try deleting "
                    f"or editing that entry.",
                )
            else:
                msb.map_connections.append(map_connection)
