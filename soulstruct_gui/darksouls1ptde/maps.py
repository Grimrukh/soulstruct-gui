from __future__ import annotations

__all__ = ["MapsEditor"]

import ast
import typing as tp

from soulstruct.base.maps.msb import GroupBitSet128
from soulstruct.darksouls1ptde import game_types
from soulstruct.darksouls1ptde.game_types import Map, ObjActParam, PlaceName, BaseDrawParam
from soulstruct.darksouls1ptde.maps import MSB
from soulstruct.darksouls1ptde.maps.parts import MSBPart, MSBCollision, MSBConnectCollision

from soulstruct_gui.window import SmartFrame
from soulstruct_gui.base.editors.maps import MapsEditor as BaseMapsEditor, MapEntryRow as BaseMapEntryRow

if tp.TYPE_CHECKING:
    from soulstruct_gui.typing import *


class ConnectCollisionCreator(SmartFrame):
    """User chooses a game map and draw/display groups to create a `ConnectCollision` part from a chosen `Collision`."""

    LAST_MAP_CHOICE: tp.ClassVar[str] = None
    LAST_DRAW_DISPLAY_GROUPS: tp.ClassVar[str] = "[0]"

    collision: MSBCollision
    map_choice: Combobox
    draw_display_groups: Entry

    connect_collision: MSBConnectCollision | None  # created by `done()`

    def __init__(self, collision: MSBCollision, game_maps: tuple[Map], master=None):
        super().__init__(master=master, toplevel=True, window_title="Create Map Connection")

        self.collision = collision
        self.connect_collision = None

        map_choices = [
            f"{game_map.emevd_file_stem} [{game_map.verbose_name}]" for game_map in game_maps  # note use of EMEVD stem
        ]
        initial_map_choice = self.__class__.LAST_MAP_CHOICE
        if initial_map_choice is not None and initial_map_choice not in map_choices:
            initial_map_choice = None
        initial_groups = self.__class__.LAST_DRAW_DISPLAY_GROUPS

        with self.set_master(padx=20, pady=20, auto_rows=0, grid_defaults={"pady": 5}):
            self.Label(text=f"Collision: {self.collision.name}")
            self.map_choice = self.Combobox(
                values=map_choices,
                initial_value=initial_map_choice,
                width=40,
                label="Connected Map:",
                label_position="above",
            )
            self.draw_display_groups = self.Entry(
                initial_text=initial_groups,
                label="Draw/Display Groups:",
                label_position="above",
                width=40,
            )
            self.Button(text="Create Map Connection", command=self.done, width=30)

        self.bind_all("<Escape>", lambda e: self.done(False))
        self.protocol("WM_DELETE_WINDOW", lambda: self.done(False))
        self.resizable(width=False, height=False)
        self.set_geometry(relative_position=(0.5, 0.3), transient=True)

    def go(self) -> MSBConnectCollision | None:
        self.wait_visibility()
        self.grab_set()
        self.mainloop()
        self.destroy()
        return self.connect_collision

    def done(self, confirm=True):
        if confirm:
            try:
                self.connect_collision = self._create_connect_collision()
            except Exception as ex:
                self.error_dialog("Map Connection Error", f"Could not create Map Connection. Error:\n{ex}")
                return
        self.quit()

    def _create_connect_collision(self) -> MSBConnectCollision:
        map_stem = self.map_choice.var.get().split(" ")[0]
        area, block = int(map_stem[1:3]), int(map_stem[4:6])

        string = self.draw_display_groups.var.get()
        try:
            enabled_bits_list = ast.literal_eval(string)
        except ValueError:
            raise ValueError(
                f"Could not interpret Draw/Display Groups string as a `GroupBitSet128`: {string}"
            )
        try:
            groups = GroupBitSet128(set(enabled_bits_list))
        except (TypeError, ValueError):
            raise ValueError(
                f"Could not interpret Draw/Display Groups string as a `GroupBitSet128`: {string}"
            )

        self.__class__.LAST_MAP_CHOICE = self.map_choice.var.get()
        self.__class__.LAST_DRAW_DISPLAY_GROUPS = string

        return MSBConnectCollision(
            name=f"{self.collision.name}_[{area:02d}_{block:02d}]",
            connected_map_id=[area, block, -1, -1],
            collision=self.collision,
            model=self.collision.model,
            translate=self.collision.translate,
            rotate=self.collision.rotate,
            scale=self.collision.scale,
            draw_groups=groups,
            display_groups=groups,
        )


class MapEntryRow(BaseMapEntryRow):

    master: MapsEditor

    def build_entry_context_menu(self):
        super().build_entry_context_menu()

        # Generate a `ConnectCollision` from a `Collision`.
        msb_type, msb_subtype = self.master.active_category.split(": ")
        if msb_type == "Parts" and msb_subtype == "Collisions":
            self.context_menu.add_command(
                label="Create Map Connection",
                command=lambda: self.master.create_connect_collision(self.entry_id),
            )


class MapsEditor(BaseMapsEditor[MSB]):

    ENTRY_ROW_CLASS = MapEntryRow
    GAME_TYPES_MODULE = game_types

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
        if issubclass(field_type, BaseDrawParam) and self.active_category.endswith("ConnectCollisions"):
            map_override = self.get_selected_field_dict().connected_map.emevd_file_stem
        else:
            map_override = None
        return self.linker.soulstruct_link(
            field_type, field_value, valid_null_values=valid_null_values, map_override=map_override,
        )

    def create_connect_collision(self, entry_id: int):
        """Create a `ConnectCollision` from the given `Collision` via a user pop-up."""
        collisions = self._get_category_subtype_list()
        collision = collisions[entry_id]  # type: MSBCollision
        connect_collision = ConnectCollisionCreator(collision, self.maps.ALL_MAPS).go()
        if connect_collision:
            msb = self.get_selected_msb()
            existing_connect_collision_names = msb.connect_collisions.get_entry_names()
            if connect_collision.name in existing_connect_collision_names:
                self.error_dialog(
                    "Map Connection Name Conflict",
                    f"A Map Connection with the name '{connect_collision.name}' already exists in this MSB. Try deleting "
                    f"or editing that entry.",
                )
            else:
                msb.connect_collisions.append(connect_collision)
