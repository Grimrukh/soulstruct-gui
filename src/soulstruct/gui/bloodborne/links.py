from __future__ import annotations

__all__ = ["WindowLinker"]

import typing as tp

from soulstruct.containers import Binder
from soulstruct.bloodborne.game_types.map_types import *
from soulstruct.bloodborne.game_types.param_types import *

from soulstruct.gui.base.links import WindowLinker as _BaseWindowLinker, BaseLink, ParamsLink, BrokenLink

if tp.TYPE_CHECKING:
    from .window import ProjectWindow


class WindowLinker(_BaseWindowLinker):

    window: ProjectWindow

    def game_param_link(self, field_type, field_value) -> list[BaseLink]:
        """Currently identical to PTDE, but still kept separate."""
        name_extension = ""

        if field_type in {AttackParam, BehaviorParam}:
            # Try to determine Player vs. Non Player table.
            param_nickname = ""
            if field_type == AttackParam:
                if self.window.params_tab.active_category == "PlayerBehaviors":
                    param_nickname = "PlayerAttacks"
                elif self.window.params_tab.active_category == "NonPlayerBehaviors":
                    param_nickname = "NonPlayerAttacks"
            elif field_type == BehaviorParam:
                if self.window.params_tab.active_category == "Players":
                    param_nickname = "PlayerBehaviors"
            if not param_nickname:
                # Could be Player or Non Player. Provide both links.
                param_nickname = "Attacks" if field_type == AttackParam else "Behaviors"
                player_table = self.project.params.get_param(f"Player{param_nickname}")
                non_player_table = self.project.params.get_param(f"NonPlayer{param_nickname}")
                links = []
                if field_value in player_table:
                    links.append(
                        ParamsLink(
                            self,
                            param_name=f"Player{param_nickname}",
                            param_entry_id=field_value,
                            name=player_table[field_value].name,
                        )
                    )
                if field_value in non_player_table:
                    links.append(
                        ParamsLink(
                            self,
                            param_name=f"NonPlayer{param_nickname}",
                            param_entry_id=field_value,
                            name=non_player_table[field_value].name,
                        )
                    )
                if links:
                    return links
                return [BrokenLink()]

        elif field_type in {ArmorParam, WeaponParam}:
            param_nickname = field_type.get_param_nickname()
            true_param_id = (
                self.check_armor_id(field_value) if field_type == ArmorParam else self.check_weapon_id(field_value)
            )
            if true_param_id is None:
                return [BrokenLink()]  # Invalid weapon/armor ID, even considering reinforcement.
            if field_value != true_param_id:
                name_extension = "+" + str(field_value - true_param_id)
            field_value = true_param_id

        else:
            param_nickname = field_type.get_param_nickname()

        param = self.project.params.get_param(param_nickname)
        try:
            name = param[field_value].name + name_extension
        except KeyError:
            return [BrokenLink()]
        else:
            return [ParamsLink(self, param_name=param_nickname, param_entry_id=field_value, name=name)]

    def validate_model_subtype(self, model_game_type: type[MapModel], model_name: str, map_stem: str):
        """Check appropriate game model files to confirm the given model name is valid.

        Note that Character and Object models don't actually need `map_id` to validate them.
        """

        if model_game_type == CharacterModel:
            if (self.project.game_root / f"chr/{model_name}.chrbnd.dcx").is_file():
                return True
        elif model_game_type == ObjectModel:
            if (self.project.game_root / f"obj/{model_name}.objbnd.dcx").is_file():
                return True
        elif model_game_type == MapPieceModel:
            if (self.project.game_root / f"map/{map_stem}/{model_name}A{map_stem[1:3]}.flver.dcx").is_file():
                return True
        elif model_game_type == CollisionModel:
            hkxbhd_path = self.project.game_root / f"map/{map_stem}/h{map_stem}.hkxbhd"
            if hkxbhd_path.is_file():
                # NOTE: Brute-force check for name string in header file (for speed).
                with hkxbhd_path.open("r") as f:
                    if f"{model_name}{map_stem[1:3]}.hkx.dcx" in f.read():
                        return True
        elif model_game_type == NavmeshModel:
            # TODO: I don't think Bloodborne has these?
            nvmbnd_path = self.project.game_root / f"map/{map_stem}/{map_stem}.nvmbnd.dcx"
            if nvmbnd_path.is_file():
                navmesh_bnd = Binder.from_path(nvmbnd_path)
                if f"{model_name}{map_stem[1:3]}.nvm" in navmesh_bnd.get_entry_names():
                    return True

        return False
