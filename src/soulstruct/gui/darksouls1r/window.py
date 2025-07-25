from __future__ import annotations

__all__ = ["ProjectWindow"]

import logging
import math

from soulstruct.darksouls1r.maps import MSB
from soulstruct.darksouls1r.maps.parts import MSBPlayerStart
from soulstruct.darksouls1r.ffx.ffxbnd import FFXBND
from soulstruct.darksouls1r.constants import CHARACTER_MODELS
from soulstruct.utilities.maths import Vector3

from soulstruct.gui.base.enums import ProjectDataType
from soulstruct.gui.base.window import ProjectWindow as _BaseProjectWindow
from .core import GameDirectoryProject
from .lighting import LightingEditor
from .links import WindowLinker
from .maps import MapsEditor
from .runtime import RuntimeManager

_LOGGER = logging.getLogger(__name__)


class ProjectWindow(_BaseProjectWindow):
    PROJECT_CLASS = GameDirectoryProject
    LINKER_CLASS = WindowLinker
    LIGHTING_EDITOR_CLASS = LightingEditor
    MAPS_EDITOR_CLASS = MapsEditor
    RUNTIME_MANAGER_CLASS = RuntimeManager
    CHARACTER_MODELS = CHARACTER_MODELS

    project: GameDirectoryProject
    runtime_tab: RuntimeManager

    RELOAD_WARP_PLAYER_START_SUFFIX = 995
    RELOAD_WARP_FLAG_SUFFIX = 5555

    def __init__(self, project_path="", game_root=None, master=None):

        super().__init__(project_path, game_root, master)

        # Ctrl + Shift + R triggers reload warp from anywhere in GUI.
        self.bind_all("<Control-R>", lambda _: self._reload_warp())

    def _build_tools_menu(self, tools_menu):
        maps_submenu = self.Menu(tearoff=0)
        self._build_maps_submenu(maps_submenu)
        tools_menu.add_cascade(label="Maps", foreground="#FFF", menu=maps_submenu)

        params_submenu = self.Menu(tearoff=0)
        self._build_params_submenu(params_submenu)
        tools_menu.add_cascade(label="Params", foreground="#FFF", menu=params_submenu)

        # events_submenu = self.Menu(tearoff=0)
        # tools_menu.add_separator()

        super()._build_tools_menu(tools_menu)

    def _build_params_submenu(self, params_menu):
        params_menu.add_command(
            label="Rename All Items/Equipment from Text",
            foreground="#FFF",
            command=self._rename_param_entries_from_text,
        )
        for param_nickname in ("Weapons", "Armor", "Rings", "Goods", "Spells"):
            params_menu.add_command(
                label=f"Rename {param_nickname} from Text",
                foreground="#FFF",
                command=lambda p=param_nickname: self._rename_param_entries_from_text(p),
            )
        return params_menu

    def _build_maps_submenu(self, maps_menu):
        maps_menu.add_command(
            label="Rebuild FFXBNDs from Maps",
            foreground="#FFF",
            command=self._rebuild_ffxbnds_from_maps,
        )
        maps_menu.add_command(
            label="Translate Vanilla Event/Region Entries with Entity IDs",
            foreground="#FFF",
            command=self._translate_all_event_region_entity_id_names,
        )
        maps_menu.add_command(
            label="Write NVMDUMPs for All Maps",
            foreground="#FFF",
            command=self._write_all_nvmdumps,
        )

    def _build_events_submenu(self, events_menu):
        events_menu.add_command(
            label="Copy Events Module to Project",
            foreground="#FFF",
            command=lambda: self.project.copy_events_submodule(with_window=self),
        )
        events_menu.add_command(
            label="Translate Vanilla Event/Region Entries with Entity IDs",
            foreground="#FFF",
            command=self._translate_all_event_region_entity_id_names,
        )

    def _rename_param_entries_from_text(self, param_nickname: str = None):
        # TODO: Add `rename_entries_from_text` method to supported games (or base class, even).
        print("Renaming entries from text...")
        self.project.params.rename_entries_from_text(self.project.text, param_nickname=param_nickname)
        if self.current_data_type == self.PROJECT_CLASS.DataType.Params:
            if (
                not param_nickname
                and self.params_tab.active_category in {"Weapons", "Armor", "Rings", "Goods", "Spells"}
                or param_nickname == self.params_tab.active_category
            ):
                self.params_tab.refresh_entries()

    def _rebuild_ffxbnds_from_maps(self):
        """Rebuild game FFXBND file for each map based on current characters in project."""
        vanilla_game_root = self.project.vanilla_game_root
        if vanilla_game_root == self.project.game_root:
            _LOGGER.warning(
                "No 'VanillaGameDirectory' given in project config. Using FFXBND files ('.bak' if possible) in "
                "standard game directory as sources, which may cause issues if you are modifying them more than once "
                "and removing the initial backups."
            )

        def _threaded_rebuild_ffxbnd():
            for map_stem, msb in self.project.maps.files.items():
                game_map = self.project.maps.GET_MAP(map_stem)
                if not game_map.ffxbnd_file_name:
                    _LOGGER.warning(f"No FFXBND file name known for map: {map_stem}. Nothing written.")
                # Load vanilla FFXBND.
                try:
                    ffxbnd = FFXBND.from_path(vanilla_game_root / "sfx" / f"{game_map.ffxbnd_file_name}.ffxbnd.dcx")
                except FileNotFoundError:
                    _LOGGER.warning(
                        f"Could not find vanilla FFXBND file for map '{map_stem}' at "
                        f"{vanilla_game_root / 'sfx' / f'{game_map.ffxbnd_file_name}.ffxbnd.dcx'}."
                        " No new FFXBND written."
                    )
                    continue
                # NOTE: We don't remove any existing FFX.
                ffxbnd.support_msb(
                    msb,
                    ffx_search_directories=[vanilla_game_root / "sfx"],
                    prefer_ffxbnd_bak=True,
                )
                ffxbnd_path = self.project.game_root / f"sfx/{game_map.ffxbnd_file_name}.ffxbnd.dcx"
                ffxbnd.write(ffxbnd_path)

        try:
            self._thread_with_loading_dialog(
                "Rebuilding FFXBNDs",
                "Rebuilding FFXBND files from current Maps data...",
                _threaded_rebuild_ffxbnd,
            )
        except Exception as ex:
            message = (f"Error occurred while rebuilding FFXBND files:\n\n"
                       f"{ex}\n\n"
                       f"Only some FFXBND files may have been written.")
            return self.CustomDialog(title="FFXBND Error", message=message)

    def _translate_all_event_region_entity_id_names(self):
        """Translate all MSB entry names that have entity IDs.

        Allows events and regions with Japanese names to be written to entities module. Parts should already be valid
        identifiers, but are checked as well anyway.
        """
        for msb in self.project.maps.files.values():
            msb.translate_entity_id_names()

    def _write_all_nvmdumps(self):
        """Write NVMDUMP files for all maps."""
        for map_stem, msb in self.project.maps.files.items():
            nvmdump_path = self.project.game_root / f"map/{map_stem}/{map_stem}.nvmdump"
            nvmdump = msb.get_nvmdump(map_stem)
            nvmdump_path.write_text(nvmdump)

    def _reload_warp(self):
        if not self.linker.hook_created:
            if (
                self.CustomDialog(
                    title="Cannot Read Position",
                    message="Game has not been hooked. Would you like to try hooking into the game now?",
                    default_output=0,
                    cancel_output=1,
                    return_output=0,
                    button_names=("Yes, hook in", "No, forget it"),
                    button_kwargs=("YES", "NO"),
                )
                == 1
            ):
                return
            if not self.linker.runtime_hook():
                return

        map_id = self.linker.get_current_map_id()
        if map_id is None:
            return self.CustomDialog("Game Not Loaded", "Could not detect player in any game map.")
        player_start_id = map_id[0] * 100000 + map_id[1] * 10000 + self.RELOAD_WARP_PLAYER_START_SUFFIX
        request_warp_flag_id = 10000000 + map_id[0] * 100000 + map_id[1] * 10000 + self.RELOAD_WARP_FLAG_SUFFIX
        current_map = self.project.maps.GET_MAP(map_id)
        current_msb_path = self.project.get_data_game_path(ProjectDataType.Maps) / f"{current_map.msb_file_stem}.msb"
        current_msb = MSB.from_path(current_msb_path)
        try:
            player_start = current_msb.find_entry_by_entity_id(player_start_id)
        except KeyError:
            return self.CustomDialog(
                "Reload Warp Failed",
                f"MSB '{current_msb_path.stem}' has no Player Start with entity ID {player_start_id}."
            )
        if not isinstance(player_start, MSBPlayerStart):
            return self.CustomDialog(
                "Reload Warp Failed",
                f"MSB '{current_msb_path.stem}' has an entity ID {player_start_id}, but it is not a Player Start."
            )
        player_x = self.linker.get_game_value("player_x")
        player_y = self.linker.get_game_value("player_y")
        player_z = self.linker.get_game_value("player_z")
        player_angle = math.degrees(self.linker.get_game_value("player_angle"))
        _LOGGER.info(f"Reloading player at {player_x}, {player_y}, {player_z} (angle {player_angle})")
        player_start.translate = Vector3([player_x, player_y, player_z])
        player_start.rotate.y = player_angle

        current_msb.write()
        self.linker.enable_flag(request_warp_flag_id)

        _LOGGER.info(
            f"Wrote MSB {current_msb_path.name} with altered Player Start {player_start_id} "
            f"and enabled flag {request_warp_flag_id}"
        )
