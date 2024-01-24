from __future__ import annotations

__all__ = [
    "ParamsEditor",
    "ParamFieldRow",
    "ParamEntryRow",
    "ParamFinder",
]

import logging
import typing as tp

from soulstruct.base.game_types import BaseParam, GAME_INT_TYPE
from soulstruct.base.params import Param, ParamRow, ParamFieldMetadata
from soulstruct.base.params.utilities import ParamFieldComparisonType, ParamFieldSearchCondition, find_param_rows

from soulstruct_gui.base.editors.base_editor import EntryRow
from soulstruct_gui.base.editors.field_editor import FieldRow, BaseFieldEditor
from soulstruct_gui.base.utilities import NameSelectionBox
from soulstruct_gui.window import SmartFrame

if tp.TYPE_CHECKING:
    from soulstruct.base.params.gameparambnd import GameParamBND

_LOGGER = logging.getLogger("soulstruct_gui")


class ParamFieldRow(FieldRow):

    def _is_default(self, field_type, value, field_nickname=""):
        # TODO: Each field should specify its default value(s).
        if field_nickname in {"EffectDuration", "UpdateInterval"}:
            return False
        elif field_type == int or issubclass(field_type, BaseParam):
            # TODO: Used to check `Flag` type in here as well, which is no longer a base type. Necessary?
            if value in (-1, 0, 1):
                # TODO: Will have some false positives.
                return True
        elif field_type == float:
            if field_nickname.endswith("Multiplier"):
                if value == 1.0:
                    return True
            else:
                if value in (0.0, 1.0):
                    return True
        return False


class ParamEntryRow(EntryRow):
    master: ParamsEditor

    ENTRY_ID_WIDTH = 10

    def __init__(self, editor: BaseFieldEditor, row_index: int, main_bindings: dict = None):
        super().__init__(editor=editor, row_index=row_index, main_bindings=main_bindings)
        self.linked_text = ""

    def update_entry(self, entry_id: int, entry_text: str):
        """Adds linked text from text data (if present and not already identical to param entry name)."""
        self.entry_id = entry_id
        text_links = self.master.linker.get_param_entry_text_links(self.entry_id)
        self.linked_text = ""
        if text_links and text_links[0].name and text_links[0].name != entry_text:
            self.linked_text = f"    {{{text_links[0].name}}}"
        self.entry_text = entry_text
        self._update_colors()
        self.build_entry_context_menu(text_links)
        self.tooltip.text = text_links[2].name if text_links and text_links[2].name else None

    @property
    def entry_text(self):
        return self._entry_text

    @entry_text.setter
    def entry_text(self, value):
        self._entry_text = value
        self.text_label.var.set(self._entry_text + (self.linked_text if self.linked_text is not None else ""))

    def build_entry_context_menu(self, text_links=()):
        super().build_entry_context_menu()
        self.context_menu.add_command(
            label="Duplicate Entry to Next Available ID",
            command=lambda: self.master.add_entry_to_next_available_id(self.entry_id),
        )
        text_links = self.master.linker.get_param_entry_text_links(self.entry_id)
        if text_links:
            self.context_menu.add_separator()
            for text_link in text_links:
                text_link.add_to_context_menu(self.context_menu, foreground=self.STYLE_DEFAULTS["fg"])
        if self.master.active_category in {"Weapons", "Armor", "Rings", "Goods", "Spells"}:
            self.context_menu.add_separator()
            self.context_menu.add_command(
                label="Edit All Text",
                command=lambda: self.master.edit_all_item_text(self.entry_id),
            )
        self.context_menu.add_separator()
        self.context_menu.add_command(
            label="Find References in Params",
            command=lambda: self.master.find_all_param_references(self.entry_id),
        )


class ParamsEditor(BaseFieldEditor):
    DATA_NAME = "Params"
    TAB_NAME = "params"
    CATEGORY_BOX_WIDTH = 400
    ENTRY_BOX_WIDTH = 350
    ENTRY_RANGE_SIZE = 300
    FIELD_NAME_WIDTH = 50
    FIELD_BOX_WIDTH = 500
    FIELD_ROW_COUNT = 185  # highest count (Params[SpecialEffects] in Bloodborne)

    FIELD_ROW_CLASS = ParamFieldRow
    field_rows: list[ParamFieldRow]
    ENTRY_ROW_CLASS = ParamEntryRow
    entry_rows: list[ParamEntryRow]

    row_conditions: list[ParamFieldSearchCondition]
    found_rows: dict[int, ParamRow]

    def __init__(self, project, linker, master=None, toplevel=False):
        self.go_to_param_id_entry = None

        self.go_to_next_found_row_button = None
        self.clear_search_button = None
        self.row_conditions = []
        self.found_rows = {}
        self.found_row_index = 0

        super().__init__(project, linker, master=master, toplevel=toplevel, window_title="Soulstruct Params Editor")

    @property
    def params(self) -> GameParamBND:
        return self._project.params

    def build(self):
        with self.set_master(sticky="nsew", row_weights=[0, 1], column_weights=[1], auto_rows=0):
            with self.set_master(pady=10, sticky="w", row_weights=[1], column_weights=[1, 1], auto_columns=0):
                self.go_to_param_id_entry = self.Entry(
                    label="Go to Param ID:", label_position="left", integers_only=True, width=15, padx=(10, 30),
                )
                self.go_to_param_id_entry.bind("<Return>", self.go_to_param_id)

                self.Button(text="Set Field Conditions", command=self.set_field_conditions, padx=10, bg="#622")
                self.go_to_next_found_row_button = self.Button(
                    text="Go to Next Hit", command=self.go_to_next_found_row, padx=10, bg="#622", state="disabled",
                )
                self.clear_search_button = self.Button(
                    text="Clear Search", command=self.clear_search, padx=10, bg="#622", state="disabled",
                )

            super().build()

    def go_to_param_id(self, event):
        param_id = event.widget.var.get()
        if not param_id or self.active_category is None:
            self.flash_bg(self.go_to_param_id_entry)
            return
        param_id = int(param_id)
        params = self.get_category_data()
        if param_id not in params:
            # Find closest ID that is less than search target.
            params_above = [p_id for p_id in params if p_id < param_id]
            if not params_above:
                self.flash_bg(self.go_to_param_id_entry)
                return
            param_id = max(p_id for p_id in params if p_id < param_id)
            self.CustomDialog("No Exact Match", f"No exact match. Found closest preceding ID: {param_id}")
        self.select_entry_id(param_id, set_focus_to_text=False, edit_if_already_selected=False)

    def set_field_conditions(self):
        """Open a window to construct or edit search conditions for Param row fields."""
        if self.active_category is None:
            self.CustomDialog("No Param Selected", "No Param category has been selected.")
            return
        param = self.params[self.active_category]
        param_finder = ParamFinder(self, param, param_name=self.active_category, initial_conditions=self.row_conditions)
        new_conditions = param_finder.go()
        if new_conditions is not None:
            self.row_conditions = new_conditions
            self.found_rows = find_param_rows(param, self.row_conditions)
            if not self.found_rows:
                self.CustomDialog("No Search Results", "No rows match the given conditions.")
            else:
                self.CustomDialog(
                    "Search Results",
                    f"Found {len(self.found_rows)} rows that match the given conditions.\n"
                    f"Click 'Go to Next Hit' to cycle through them."
                )
                self.go_to_next_found_row_button.config(state="normal")
                self.clear_search_button.config(state="normal")
                return

    def go_to_next_found_row(self):
        """Go to next condition search result. Does nothing if no search has been performed."""
        if not self.found_rows:
            # Button should not be active in this case.
            self.CustomDialog("No Search Results", "No row search has been performed.")
            return
        self.found_row_index = (self.found_row_index + 1) % len(self.found_rows)
        row_id = list(self.found_rows.keys())[self.found_row_index]
        self.select_entry_id(row_id, set_focus_to_text=False, edit_if_already_selected=False)

    def clear_search(self):
        self.row_conditions = []
        self.go_to_next_found_row_button.config(state="disabled")
        self.clear_search_button.config(state="disabled")

    def find_all_param_references(self, param_id):
        """Iterates over all params to find references to this param ID, and presents them in a pop-out list."""
        category = self.active_category
        game_type = self.params.GAME_TYPES[category]
        linking_fields = []  # type: list[tuple[str, str, ParamFieldMetadata]]
        links = {}

        # Find all (param_name, field) pairs that could possibly reference this category.
        # This could be from a static type reference or `POSSIBLE_TYPES` in a dynamic reference.
        for param_name in self.params.GAME_TYPES:
            param = self.params.get_param(param_name)
            for param_field in param.ROW_TYPE.get_binary_fields():
                metadata = param_field.metadata["param"]  # type: ParamFieldMetadata
                if metadata.dynamic_callback:
                    # Field type will be checked below (per entry).
                    if game_type in metadata.dynamic_callback.POSSIBLE_TYPES:
                        linking_fields.append((param_name, param_field.name, metadata))
                elif metadata.game_type == game_type:
                    linking_fields.append((param_name, param_field.name, metadata))

        if not linking_fields:
            self.CustomDialog(
                "No References",
                "Could not find any fields in any Params that could possibly reference this entry type.\n"
                "There may still be references elsewhere (e.g. maps, events, animation TAE).",
            )
            return

        for param_name, field_name, metadata in linking_fields:
            for row_id, row in self.params.get_param(param_name).items():
                if metadata.dynamic_callback:
                    dynamic_game_type, suffix, tooltip = metadata.dynamic_callback(row)
                    if game_type == dynamic_game_type and getattr(row, field_name) == param_id:
                        link_text = f"{param_name}[{row_id}] {field_name}"
                        # TODO: Links use param nicknames now. Make sure of that.
                        links[link_text] = (param_name, row_id, field_name)

        if not links:
            self.CustomDialog(
                "No References",
                "Could not find any references to this row in Params.\nThere may still be references elsewhere.",
            )
            return

        name_box = NameSelectionBox(self.master, names=links, list_name=f"Param References to {category}[{param_id}]")
        selected_link = name_box.go()
        if selected_link is not None:
            param_name, row_id, field_name = links[selected_link]
            self.select_category(param_name, auto_scroll=True)
            self.select_entry_id(row_id, edit_if_already_selected=False)
            self.select_field_name(field_name)

    def _get_display_categories(self):
        return self.params.GAME_TYPES

    def get_category_data(self, category=None) -> dict:
        if category is None:
            category = self.active_category
            if category is None:
                return {}
        return self.params.get_param(category).rows

    def _get_category_name_range(self, category=None, first_index=None, last_index=None) -> list:
        if category is None:
            category = self.active_category
            if category is None:
                return []
        return self.params.get_param(category).get_range(start=self.first_display_index, count=self.ENTRY_RANGE_SIZE)

    def get_entry_index(self, entry_id: int, category=None) -> int:
        """Get index of entry in category. Ignores current display range."""
        if category is None:
            category = self.active_category
            if category is None:
                raise ValueError("No param category selected.")
        if entry_id not in self.params.get_param(category).rows:
            raise ValueError(f"Param ID {entry_id} does not appear in category {category}.")
        return sorted(self.params.get_param(category).rows).index(entry_id)

    def get_entry_text(self, entry_id: int, category=None) -> str:
        if category is None:
            category = self.active_category
            if category is None:
                raise ValueError("No params category selected.")
        return self.params.get_param(category)[entry_id].Name

    def _set_entry_text(self, entry_id: int, text: str, category=None, update_row_index=None):
        if category is None:
            category = self.active_category
            if category is None:
                raise ValueError("No params category selected.")
        param_row = self.params.get_param(category)[entry_id]
        param_row.Name = text
        if category == self.active_category and update_row_index is not None:
            self.entry_rows[update_row_index].update_entry(entry_id, text)

    def _set_entry_id(self, entry_id: int, new_id: int, category=None, update_row_index=None):
        entry_data = self.params.get_param(category).pop(entry_id)
        self.params.get_param(category)[new_id] = entry_data
        if category == self.active_category and update_row_index:
            self.entry_rows[update_row_index].update_entry(new_id, entry_data.Name)
        return True

    def get_field_dict(self, entry_id: int, category=None) -> ParamRow:
        if category is None:
            category = self.active_category
            if category is None:
                raise ValueError("No params category selected.")
        return self.params.get_param(category)[entry_id]

    def get_field_display_info(self, field_dict: ParamRow, field_name) -> tuple[str, bool, GAME_INT_TYPE, str]:
        field_metadata = field_dict.get_field_metadata(field_name)  # type: ParamFieldMetadata
        if field_metadata.dynamic_callback:
            game_type, suffix, tooltip = field_metadata.dynamic_callback(field_dict)
            field_name += suffix
            tooltip = f"{field_metadata.internal_name}: {tooltip}"
        else:  # static metadata
            game_type = field_metadata.game_type
            tooltip = f"{field_metadata.internal_name}: {field_metadata.tooltip}"
        return field_name, not field_metadata.hide, game_type, tooltip

    def get_field_names(self, field_dict: ParamRow) -> list[str]:
        """NOTE: Param field names are now identical to their nicknames/display names.

        Ignores pad fields.
        """
        if not field_dict:
            return []
        field_names = []
        for field_name, field_metadata in field_dict.get_all_field_metadata().items():
            if field_metadata.is_pad:
                continue
            field_names.append(field_name)
        return field_names

    def get_field_links(self, field_type, field_value, valid_null_values=None):
        if valid_null_values is None:
            valid_null_values = {0: "Default/None", -1: "Default/None"}
        else:
            # TODO: probably want to remove this?
            print("Field type/value/null values:", field_type, field_value, valid_null_values)
        try:
            return self.linker.soulstruct_link(field_type, field_value, valid_null_values=valid_null_values)
        except IndexError:
            raise ValueError(f"Invalid link: type = {field_type}, value = {field_value}")

    def edit_all_item_text(self, item_id):
        """Active category should already be a valid item type."""
        try:
            self.linker.edit_all_item_text(self.active_category.rstrip("s"), item_id)
        except Exception as e:
            _LOGGER.warning(e)
            self.CustomDialog("Item Text Error", f"Could not edit item text. Error:\n\n{e}")
        else:
            self.refresh_entries()


class ParamFinder(SmartFrame):
    """Allows the user to construct a search query for a given Param."""

    WIDTH = 70  # characters
    HEIGHT = 20  # lines

    editor: ParamsEditor
    conditions: list[ParamFieldSearchCondition] | None

    def __init__(self, master: ParamsEditor, param: Param, param_name="List", initial_conditions=None):
        super().__init__(toplevel=True, master=master, window_title=f"Find Param in {param_name}")

        self.editor = master
        self.conditions = []

        with self.set_master(padx=20, pady=20, auto_rows=0):
            self.Label(text="Add search conditions to the list below.\nDouble click a condition to remove it.")
            with self.set_master(auto_columns=0, grid_defaults={"padx": 5}):
                self._field_nickname_combobox = self.Combobox(
                    values=param.ROW_TYPE.get_binary_field_names(),
                    initial_value="",
                    width=40,
                    font=("Consolas", 14),
                )
                self._condition_combobox = self.Combobox(
                    values=[c.value for c in ParamFieldComparisonType],
                    initial_value="==",
                    width=4,
                    font=("Consolas", 14),
                )
                self._value_entry = self.Entry(
                    width=10,
                    font=("Consolas", 14),
                    numbers_only=True,
                )
                self._add_condition_button = self.Button(
                    text="Add Condition",
                    command=self._add_condition,
                    bg="#622",
                )

            self._condition_listbox = self.Listbox(
                values=[],
                width=self.WIDTH,
                height=self.HEIGHT,
                vertical_scrollbar=True,
                selectmode="single",
                font=("Consolas", 14),
                padx=20,
                pady=20,
            )

            self._condition_listbox.bind("<Double-Button-1>", lambda e: self._remove_condition())

            with self.set_master(auto_columns=0, padx=10, pady=10, grid_defaults={"padx": 10}):
                self.Button(
                    text="Confirm", command=lambda: self.done(True), **self.editor.DEFAULT_BUTTON_KWARGS["YES"]
                )
                self.Button(
                    text="Cancel", command=lambda: self.done(False), **self.editor.DEFAULT_BUTTON_KWARGS["NO"]
                )

        if initial_conditions:
            self.conditions = initial_conditions
            for condition in initial_conditions:
                self._condition_listbox.insert("end", str(condition))

        self.bind_all("<Escape>", lambda e: self.done(False))
        self.protocol("WM_DELETE_WINDOW", lambda: self.done(False))
        self.resizable(width=False, height=False)
        self.set_geometry(relative_position=(0.5, 0.3), transient=True)

    def _add_condition(self):
        field_nickname = self._field_nickname_combobox.get()
        condition = self._condition_combobox.get()
        value = self._value_entry.var.get()
        if not field_nickname or not condition or not value:
            return  # not valid

        condition = ParamFieldSearchCondition(field_nickname, ParamFieldComparisonType(condition), float(value))
        self.conditions.append(condition)
        self._condition_listbox.insert("end", str(condition))

        self._field_nickname_combobox.set("")
        self._condition_combobox.set("==")
        self._value_entry.var.set("")

    def _remove_condition(self):
        """Remove selected entry from list."""
        selection = self._condition_listbox.curselection()
        if not selection:
            return
        self._condition_listbox.delete(selection[0])
        self.conditions.pop(selection[0])

    def go(self):
        self.wait_visibility()
        self.grab_set()
        self.mainloop()
        self.destroy()
        return self.conditions

    def done(self, confirm=True):
        if not confirm:
            self.conditions = None
        self.quit()
