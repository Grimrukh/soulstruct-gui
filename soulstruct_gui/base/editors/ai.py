from __future__ import annotations

import re
from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Optional

from soulstruct.base.ai.lua import LuaError
from soulstruct.base.ai.lua_scripts import LuaGoalScript, GoalType

from soulstruct_gui.base.editors.base_editor import BaseEditor, EntryRow
from soulstruct_gui.base.enums import ProjectDataType
from soulstruct_gui.base.utilities import bind_events, TkTextEditor, TagData

if TYPE_CHECKING:
    from soulstruct.base.ai.luabnd import LuaBND
    from soulstruct.base.ai.ai_directory import AIScriptDirectory


class AIScriptTkTextEditor(TkTextEditor):
    TAGS = {
        "function_def": TagData("#AABBFF", r"function [\w_]+", (0, 0)),
        "lua_word": TagData(
            "#FFBB99",
            r"(^| )(function|local|if|then|elseif|else|for|while|end|return|and|or|"
            r"not|do|break|repeat|nil|until)(?=($| ))",
            (0, 0),
        ),
        "lua_bool": TagData("#FFBB99", r"[ ,=({\[](true|false)(?=($|[ ,)}\]]))", (1, 0)),
        "number_literal": TagData("#AADDFF", r"[ ,=({\[-][\d.]+(?=($|[ ,)}\]]))", (1, 0)),
        "function_call": TagData("#C0E665", r"(^|[ ,=({\[:])[\w_]+(?=[(])", (0, 0)),
        "comment": TagData("#777777", r"--.*$", (0, 0)),
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Tag order is carefully set up.
        self.tag_configure("suspected_global", foreground="#1FBA58")
        self.tag_configure("outer_scope_name", foreground="#F091FA")
        self.tag_configure("function_arg_name", foreground="#F5B74C")
        self.tag_configure("local_name", foreground="#F97965")
        self.tag_configure("number_literal", foreground="#AADDFF")
        self.tag_configure("function_call", foreground="#C0E665")
        self.tag_configure("function_def", foreground="#AABBFF")
        self.tag_configure("lua_word", foreground="#FFBB99")
        self.tag_configure("lua_bool", foreground="#FFBB99")

    def color_syntax(self, start="1.0", end="end"):
        self._apply_name_tags()
        super().color_syntax(start, end)

    def _apply_name_tags(self):
        """Find and color local and global variables."""
        # Global
        self.highlight_pattern(
            r"[ ,=({\[]\w[\w_]+(?=($|[ ,)}\[\]]))", tag="suspected_global", start_offset=1, regexp=True
        )

        # Outer scope (up-values)
        self.tag_remove("outer_scope_name", "1.0", "end")
        outer_scope_matches = re.findall(r"^local ([\w_]+) *=", self.get("1.0", "end"), flags=re.MULTILINE)
        for match in outer_scope_matches:
            self.highlight_pattern(
                rf"[ ,=(\[]{match}(?=($|[ ,)\]]))", tag="outer_scope_name", clear=False, start_offset=1, regexp=True
            )
            self.highlight_pattern(rf"^{match}(?=($|[ ,)\]]))", tag="outer_scope_name", clear=False, regexp=True)

        # Function args and locals
        self.tag_remove("local_name", "1.0", "end")
        start_index = "1.0"
        while 1:
            function_index = self.search(r"^function [\w_]+\(", start_index, regexp=True)
            if not function_index:
                break
            next_function_index = self.search(r"^function [\w_]+\(", f"{function_index} lineend", regexp=True)
            if int(next_function_index.split(".")[0]) <= int(function_index.split(".")[0]):
                next_function_index = "end"  # finished searching
            function_text = self.get(function_index, next_function_index)

            function_args_match = re.match(r"^function [\w_]+\(([\w_, \n]+)\)", function_text, flags=re.MULTILINE)
            if function_args_match:
                function_args = function_args_match.group(1).replace("\n", "").replace(" ", "")
                for function_arg in function_args.split(","):
                    self.highlight_pattern(
                        rf"[ ,=([]{function_arg}(?=($|[: ,)[]))",
                        tag="function_arg_name",
                        start=function_index,
                        end=next_function_index,
                        clear=False,
                        start_offset=1,
                        regexp=True,
                    )

            local_matches = re.findall(r"[ \t]local ([\w_]+) *=", function_text, flags=re.MULTILINE)
            for match in local_matches:
                self.highlight_pattern(
                    rf"[\t ,=({{\[]{match}(?=($|[ ,)}}\[\]]))",
                    tag="local_name",
                    start=function_index,
                    end=next_function_index,
                    clear=False,
                    start_offset=1,
                    regexp=True,
                )

            if next_function_index == "end":
                break
            else:
                start_index = next_function_index


class AIEntryRow(EntryRow):
    """Container/manager for widgets of a single entry row in the Editor."""

    master: AIEditor

    ENTRY_ANCHOR = "center"
    ENTRY_ROW_HEIGHT = 50
    EDIT_ENTRY_ID = True
    ENTRY_TYPE_WIDTH = 5
    ENTRY_TYPE_FG = "#FFA"
    ENTRY_ID_WIDTH = 12
    ENTRY_ID_FG = "#CDF"
    ENTRY_TEXT_WIDTH = 40
    ENTRY_TEXT_FG = "#FFF"

    # noinspection PyMissingConstructor
    def __init__(self, editor: AIEditor, row_index: int, main_bindings: dict = None):
        self.master = editor
        self.STYLE_DEFAULTS = editor.STYLE_DEFAULTS

        self.row_index = row_index
        self._entry_id = None
        self._entry_text = None
        self._active = False
        self._goal_type = "battle"

        bg_color = self._get_color()

        self.row_box = editor.Frame(
            width=self.ENTRY_TYPE_WIDTH + self.ENTRY_ID_WIDTH + self.ENTRY_TEXT_WIDTH,
            height=self.ENTRY_ROW_HEIGHT,
            bg=bg_color,
            row=row_index,
            columnspan=3,
            sticky="nsew",
        )
        bind_events(self.row_box, main_bindings)

        self.type_box = editor.Frame(row=row_index, column=0, bg=bg_color, sticky="ew")
        self.type_label = editor.Label(
            self.type_box,
            text="B",
            width=self.ENTRY_TYPE_WIDTH,
            bg=bg_color,
            fg="#F33",
            sticky="ew",
            tooltip_text="Type of goal: battle (B), logic (L), or unknown (U). Left or right click to cycle "
            "between types.",
        )
        type_bindings = main_bindings.copy()
        type_bindings["<Button-1>"] = lambda _, i=row_index: self.master.set_goal_type(i)
        type_bindings["<Button-3>"] = lambda _, i=row_index: self.master.set_goal_type(i, reverse=True)
        bind_events(self.type_box, type_bindings)
        bind_events(self.type_label, type_bindings)

        self.id_box = editor.Frame(row=row_index, column=1, bg=bg_color, sticky="ew")
        self.id_label = editor.Label(
            self.id_box,
            text="",
            width=self.ENTRY_ID_WIDTH,
            bg=bg_color,
            fg=self.ENTRY_ID_FG,
            sticky="e",
        )
        id_bindings = main_bindings.copy()
        id_bindings["<Button-1>"] = lambda _, i=row_index: self.master.select_entry_row_index(i, id_clicked=True)
        # id_bindings["<Shift-Button-1>"] = lambda _, i=row_index: self.master.popout_entry_id_edit(i)
        bind_events(self.id_box, id_bindings)
        bind_events(self.id_label, id_bindings)

        self.text_box = editor.Frame(row=row_index, column=2, bg=bg_color, sticky="ew")
        bind_events(self.text_box, main_bindings)

        self.text_label = editor.Label(
            self.text_box,
            text="",
            bg=bg_color,
            fg=self.ENTRY_TEXT_FG,
            anchor="w",
            justify="left",
            width=self.ENTRY_TEXT_WIDTH,
        )
        bind_events(self.text_label, main_bindings)

        self.context_menu = editor.Menu(self.row_box)

        self.tool_tip = None

    def update_entry(self, entry_id: int, entry_text: str, goal_type=None):
        self.entry_id = entry_id
        self.entry_text = entry_text
        if goal_type is None:
            raise ValueError("Logic state cannot be `None` (suggests design problem).")
        self.goal_type = goal_type
        self._update_colors()
        self.build_entry_context_menu()

    def hide(self):
        """Called when this row has no entry to display."""
        self.row_box.grid_remove()
        self.type_box.grid_remove()
        self.type_label.grid_remove()
        self.id_box.grid_remove()
        self.id_label.grid_remove()
        self.text_box.grid_remove()
        self.text_label.grid_remove()

    def unhide(self):
        self.row_box.grid()
        self.type_box.grid()
        self.type_label.grid()
        self.id_box.grid()
        self.id_label.grid()
        self.text_box.grid()
        self.text_label.grid()

    def build_entry_context_menu(self):
        self.context_menu.delete(0, "end")
        self.context_menu.add_command(
            label="Duplicate Entry to Next ID",
            command=lambda: self.master.add_relative_entry(self.entry_id, goal_type=self.goal_type, offset=1),
        )
        self.context_menu.add_command(
            label="Delete Entry",
            command=lambda: self.master.delete_entry(self.row_index),
        )

    @property
    def _colored_widgets(self):
        return (
            self.row_box, self.id_box, self.id_label, self.text_box, self.text_label, self.type_box, self.type_label
        )

    @property
    def goal_type(self):
        return self._goal_type

    @goal_type.setter
    def goal_type(self, goal_type: GoalType):
        if goal_type != self._goal_type:
            match goal_type:
                case GoalType.Battle:
                    self.type_label.var.set("B")
                    self.type_label["fg"] = "#F33"
                case GoalType.Logic:
                    self.type_label.var.set("L")
                    self.type_label["fg"] = "#3F3"
                case GoalType.Unknown:
                    self.type_label.var.set("U")
                    self.type_label["fg"] = "#FFF"
                case _:
                    raise ValueError(f"Invalid goal type: {goal_type}")
            self._goal_type = goal_type


class AIEditor(BaseEditor):
    DATA_NAME = "AI"
    TAB_NAME = "ai"
    CATEGORY_BOX_WIDTH = 0
    ENTRY_BOX_WIDTH = 150
    ENTRY_BOX_HEIGHT = 400
    ENTRY_RANGE_SIZE = 200

    _LUA_COMPILE_ERROR_RE = re.compile(r".*\\temp:(\d+): (.*)", flags=re.DOTALL)

    ENTRY_ROW_CLASS = AIEntryRow
    entry_rows: List[AIEntryRow]

    def __init__(
        self,
        project,
        script_directory,
        allow_decompile,
        global_map_choice_func,
        linker,
        text_font_size=14,
        master=None,
        toplevel=False,
    ):
        self.script_directory = Path(script_directory)
        self.global_map_choice_func = global_map_choice_func
        self.text_font_size = text_font_size
        self.allow_decompile = allow_decompile
        self.selected_map_id = ""

        self.map_choice = None
        self.decompile_all_button = None
        self.write_all_button = None
        self.line_number = None
        self.go_to_line = None
        self.string_to_find = None
        self.script_editor_canvas = None
        self.lua_script_editor = None  # type: Optional[AIScriptTkTextEditor]
        self.confirm_button = None
        self.compile_button = None
        self.decompile_button = None
        self.write_button = None
        self.reload_button = None
        super().__init__(project, linker, master=master, toplevel=toplevel, window_title="Soulstruct AI Script Editor")

    @property
    def ai(self) -> AIScriptDirectory:
        return self._project.ai

    def refresh_categories(self):
        return

    def build(self):
        with self.set_master(sticky="nsew", row_weights=[0, 1], column_weights=[1], auto_rows=0):
            with self.set_master(pady=10, sticky="w", row_weights=[1], column_weights=[1, 1, 1, 1, 1], auto_columns=0):
                map_names = [f"{game_map.ai_file_stem} [{game_map.verbose_name}]" for game_map in self.ai.ALL_MAPS]
                self.map_choice = self.Combobox(
                    values=map_names,
                    label="Map:",
                    label_position="left",
                    width=55,
                    font=self.CONFIG.REGULAR_FONT,
                    on_select_function=self.on_map_choice,
                    sticky="w",
                    padx=(10, 30),
                )
                self.selected_map_id = self.map_choice_stem
                self.decompile_all_button = self.Button(
                    text="Decompile All" if self.allow_decompile else "Cannot Decompile",
                    bg="#622",
                    width=20,
                    padx=10,
                    command=self.decompile_all,
                    state="normal" if self.allow_decompile else "disabled",
                )
                self.write_all_button = self.Button(
                    text="Write All in Map", bg="#222", width=20, padx=10, command=self.write_all
                )
                self.Button(
                    text="Reload All in Map",
                    bg="#222",
                    width=20,
                    padx=10,
                    command=self.load_all_from_project_folder,
                )
                self.Button(
                    text="Export This Map",
                    bg="#222",
                    width=20,
                    padx=10,
                    command=self.export_selected_map,
                )

            with self.set_master(sticky="nsew", row_weights=[1], column_weights=[1, 2], auto_columns=0):
                with self.set_master(sticky="nsew", row_weights=[1], column_weights=[1]):
                    self.build_entry_frame()
                with self.set_master(
                    sticky="nsew", row_weights=[0, 1, 0, 0], column_weights=[1], padx=50, pady=10, auto_rows=0
                ):
                    with self.set_master(sticky="nsew", column_weights=[1, 1, 1], auto_columns=0, pady=5):
                        self.line_number = self.Label(
                            text="Line: None", padx=10, width=10, fg="#CCF", anchor="w", sticky="w"
                        ).var
                        self.go_to_line = self.Entry(label="Go to Line:", padx=5, width=6, sticky="w")
                        self.go_to_line.bind("<Return>", self._go_to_line)
                        self.string_to_find = self.Entry(label="Find Text:", padx=5, width=20, sticky="w")
                        self.string_to_find.bind("<Return>", self._find_string)
                    with self.set_master(sticky="nsew", row_weights=[1], column_weights=[1, 0]):
                        self.build_script_editor()
                    with self.set_master(
                        sticky="nsew", row_weights=[1], column_weights=[1, 1, 1], pady=10, auto_columns=0
                    ):
                        self.confirm_button = self.Button(
                            text="Confirm Changes",
                            bg="#222",
                            width=20,
                            padx=5,
                            command=self.confirm_selected,
                            state="disabled",
                            sticky="e",
                            tooltip_text="Confirm changes to selected script and re-color syntax. Does not save "
                            "project AI files if clicked, but the project 'Save' function (Ctrl + S) "
                            "will always confirm changes first.",
                        )
                        self.compile_button = self.Button(
                            text="Compile",
                            bg="#222",
                            width=20,
                            padx=5,
                            command=self.compile_selected,
                            state="disabled",
                            tooltip_text="Compile script and re-color syntax. Not necessary for exporting, but useful "
                            "to ensure that Lua syntax is valid. (Ctrl + Shift + C)",
                        )
                        self.decompile_button = self.Button(
                            text="Decompile",
                            bg="#822",
                            width=20,
                            padx=5,
                            command=self.decompile_selected,
                            state="disabled",
                            sticky="w",
                        )
                    with self.set_master(sticky="nsew", row_weights=[1], column_weights=[1, 1], pady=5, auto_columns=0):
                        self.write_button = self.Button(
                            text="Write to Project",
                            bg="#222",
                            width=20,
                            padx=5,
                            command=self.write_selected,
                            state="disabled",
                            sticky="e",
                            tooltip_text="Write script to 'ai_scripts' folder in your project directory, where it can "
                            "be edited by other text editors or Lua-friendly IDEs and reloaded here. "
                            "(Ctrl + W)",
                        )
                        self.reload_button = self.Button(
                            text="Reload from Project",
                            bg="#222",
                            width=20,
                            padx=5,
                            command=self.reload_selected,
                            sticky="w",
                            tooltip_text="Reload script from 'ai_scripts' folder in your project directory. If there "
                            "are unconfirmed changes in the current script, you will be asked to confirm "
                            "their loss first. (Ctrl + R)",
                        )

        self.bind_to_all_children("<Control-C>", lambda _: self.compile_selected(mimic_click=True))
        self.bind_to_all_children("<Control-w>", lambda _: self.write_selected(mimic_click=True))
        self.bind_to_all_children("<Control-r>", lambda _: self.reload_selected(mimic_click=True))

    def build_script_editor(self):
        self.script_editor_canvas = self.Canvas(
            horizontal_scrollbar=True,
            sticky="nsew",
            bg="#232323",
            borderwidth=0,
            highlightthickness=0,
            row=0,
            column=0,
            row_weights=[1],
            column_weights=[1],
        )
        editor_i_frame = self.Frame(self.script_editor_canvas, row_weights=[1], column_weights=[1])
        self.script_editor_canvas.create_window(0, 0, window=editor_i_frame, anchor="nw")
        editor_i_frame.bind("<Configure>", lambda e, c=self.script_editor_canvas: self.reset_canvas_scroll_region(c))

        self.lua_script_editor = self.CustomWidget(
            frame=editor_i_frame,
            custom_widget_class=AIScriptTkTextEditor,
            set_style_defaults=("text", "cursor"),
            row=0,
            state="disabled",
            width=400,
            height=50,
            wrap="word",
            bg="#232323",
            font=("Consolas", self.text_font_size),
        )
        vertical_scrollbar_w = self.Scrollbar(
            orient="vertical", command=self.lua_script_editor.yview, row=0, column=1, sticky="ns"
        )
        self.lua_script_editor.config(bd=0, yscrollcommand=vertical_scrollbar_w.set)
        self.link_to_scrollable(self.lua_script_editor, editor_i_frame)

        def _update_textbox_height(e):
            font_size = int(self.lua_script_editor["font"].split()[1])
            self.lua_script_editor["height"] = e.height // (font_size * 1.5)  # 1.5 line spacing

        self.script_editor_canvas.bind("<Configure>", lambda e: _update_textbox_height(e))

        self.lua_script_editor.set_callback(self._update_line_number)
        self.lua_script_editor.bind("<Control-f>", self._control_f_search)

    def _go_to_line(self, _):
        number = self.go_to_line.var.get()
        if not number:
            return
        number = int(number)
        if (
            not self.get_selected_bnd()
            or number < 1
            or int(self.lua_script_editor.index("end-1c").split(".")[0]) < number
        ):
            self.flash_bg(self.go_to_line)
            return
        self.lua_script_editor.mark_set("insert", f"{number}.0")
        self.lua_script_editor.see(f"{number}.0")
        self.lua_script_editor.highlight_line(number, "found")

    def _find_string(self, _):
        string = self.string_to_find.var.get()
        if not string or not self.get_selected_bnd():
            return
        start_line, start_char = self.lua_script_editor.index("insert").split(".")
        index = self.lua_script_editor.search(string, index=f"{start_line}.{int(start_char) + 1}")

        if index:
            self.clear_bg_tags()
            self.lua_script_editor.mark_set("insert", index)
            self.lua_script_editor.see(index)
            index_line, index_char = index.split(".")
            self.lua_script_editor.tag_add("found", index, f"{index_line}.{int(index_char) + len(string)}")
        else:
            self.flash_bg(self.string_to_find)

    def clear_bg_tags(self):
        for tag in {"found", "error"}:
            self.lua_script_editor.tag_remove(tag, "1.0", "end")

    def _update_line_number(self, *_):
        current_line = self.lua_script_editor.index("insert").split(".")[0]
        self.line_number.set(f"Line: {current_line}")

    def _control_f_search(self, _):
        if self.get_selected_bnd():
            highlighted = self.lua_script_editor.selection_get()
            self.string_to_find.var.set(highlighted)
            self.string_to_find.select_range(0, "end")
            self.string_to_find.icursor("end")
            self.string_to_find.focus_force()

    def _highlight_error(self, lineno):
        self.lua_script_editor.mark_set("insert", f"{lineno}.0")
        self.lua_script_editor.see(f"{lineno}.0")
        self.lua_script_editor.highlight_line(lineno, "error")

    def _get_current_text(self):
        """Get all current text from TextBox, minus final newline (added by Tk)."""
        return self.lua_script_editor.get(1.0, "end")[:-1]

    def _ignored_unsaved(self):
        if self._get_current_text() != self.get_goal().script:
            if (
                self.CustomDialog(
                    title="Lose Unsaved Changes?",
                    message="Current script has changed but not been saved. Lose changes?",
                    button_names=("Yes, lose changes", "No, stay here"),
                    button_kwargs=("YES", "NO"),
                    cancel_output=1,
                    default_output=1,
                )
                == 1
            ):
                return False
        return True

    def set_goal_type(self, row_index=None, goal_type=None, reverse=False):
        if row_index is None:
            row_index = self.active_row_index
        goal = self.get_goal(row_index)
        old_type = goal.goal_type
        if goal_type is None:
            if old_type == GoalType.Battle:
                goal_type = GoalType.Unknown if reverse else GoalType.Logic
            elif old_type == GoalType.Logic:
                goal_type = GoalType.Battle if reverse else GoalType.Unknown
            elif old_type == GoalType.Unknown:
                goal_type = GoalType.Logic if reverse else GoalType.Battle
        elif old_type == goal_type:
            return False
        if (goal.goal_id, goal_type) in self.get_category_data():
            self.CustomDialog(
                title="Script Type Error", message=f"A {repr(goal_type)} goal already exists with ID {goal.goal_id}."
            )
            return False
        try:
            goal.goal_type = goal_type
        except LuaError:
            if goal_type != "logic":
                raise
            if (
                self.CustomDialog(
                    title="Lose Unsaved Changes?",
                    message=f"Logic goal name must end in '_Logic'. Add suffix to name?",
                    button_names=("Yes, change name", "No, do nothing"),
                    button_kwargs=("YES", "NO"),
                    return_output=0,
                    cancel_output=1,
                    default_output=1,
                )
                == 1
            ):
                return False
            else:
                goal.goal_name += "_Logic"
                goal.goal_type = GoalType.Logic
                self.entry_rows[row_index].entry_text = goal.goal_name

        self.entry_rows[row_index].goal_type = goal_type
        return True

    def _parse_compile_error(self, error_msg):
        error_msg = error_msg.replace("\n", " ")
        match = self._LUA_COMPILE_ERROR_RE.match(error_msg)
        if match:
            self._highlight_error(int(match.group(1)))
            error_msg = match.group(2)
            return f"Line {match.group(1)}: {error_msg}"
        return error_msg

    def decompile_all(self):
        if (
            self.CustomDialog(
                title="Confirm Bulk Decompile",
                message="This will overwrite any decompiled scripts in your project's current state. Continue?",
                button_names=("Yes, continue", "No, go back"),
                button_kwargs=("YES", "NO"),
                cancel_output=1,
                default_output=1,
            )
            == 1
        ):
            return
        self.decompile_all_button["state"] = "disabled"
        self.decompile_all_button.var.set("Decompiling...")
        self.update_idletasks()
        failed_goals = []
        for goal in self.get_selected_bnd().goals:
            if not goal.bytecode:
                continue
            try:
                goal.decompile()
            except LuaError as e:
                failed_goals.append(goal)
                if (
                    self.CustomDialog(
                        title="Lua Decompile Error",
                        message=f"Error encountered while decompiling script:\n\n{str(e)}"
                        f"\n\nContinue to next goal, or abort all remaining goals?",
                        button_names=("Continue to next goal", "Abort remaining"),
                        button_kwargs=("YES", "NO" ""),
                        cancel_output=0,
                        default_output=0,
                        return_output=0,
                    )
                    == 1
                ):
                    return
        failed_goals_msg = "\n".join(f"{g.goal_id}: {g.goal_name} ({g.goal_type}" for g in failed_goals)
        if failed_goals_msg:
            self.CustomDialog(
                title="Lua Decompile Complete",
                message=f"All scripts have been decompiled except:\n\n{failed_goals_msg}",
                cancel_output=0,
                default_output=0,
                return_output=0,
            )
        else:
            self.CustomDialog(title="Lua Decompile Complete", message=f"All scripts were decompiled successfully.")
        self.decompile_all_button["state"] = "normal"
        self.decompile_all_button.var.set("Decompile All")
        if self.active_row_index is not None:
            self.update_script_text()

    def write_all(self):
        if (
            self.CustomDialog(
                title="Confirm Bulk Write",
                message=f"This will overwrite any decompiled script files saved in "
                f"'/ai_scripts/{self.selected_map_id}'.\n\nContinue?",
                button_names=("Yes, continue", "No, go back"),
                button_kwargs=("YES", "NO"),
                cancel_output=1,
                default_output=1,
            )
            == 1
        ):
            return
        self.write_all_button["state"] = "disabled"
        self.write_all_button.var.set("Writing...")
        self.update_idletasks()
        for goal in self.get_selected_bnd().goals:
            if not goal.script:
                continue
            try:
                goal.write_script(self.script_directory / f"{self.selected_map_id}/{goal.script_name}")
            except LuaError as e:
                if (
                    self.CustomDialog(
                        title="Lua Write Error",
                        message=f"Error encountered while writing script for goal {goal.goal_id}: {goal.goal_name} "
                        f"({goal.goal_type}):\n\n{str(e)}"
                        f"\n\nContinue to next goal, or abort all remaining goals?",
                        button_names=("Continue to next goal", "Abort remaining"),
                        button_kwargs=("YES", "NO" ""),
                        return_output=0,
                        cancel_output=1,
                        default_output=0,
                    )
                    == 1
                ):
                    return
        self.write_all_button["state"] = "normal"
        self.write_all_button.var.set("Write All")

    def export_selected_map(self):
        luabnd = self.get_selected_bnd()
        luabnd_path = self._project.get_data_game_path(ProjectDataType.AI) / luabnd.path.name
        luabnd.write(luabnd_path)

    def load_all_from_project_folder(self, confirm=True):
        if confirm and (
            self.CustomDialog(
                title="Confirm Lua Operation",
                message=f"This will overwrite any decompiled script in the current project state\n"
                f"that has a file in '/ai_scripts/{self.selected_map_id}'.\n\nContinue?",
                button_names=("Yes, continue", "No, go back"),
                button_kwargs=("YES", "NO"),
                return_output=0,
                cancel_output=1,
                default_output=0,
            )
            == 1
        ):
            return
        failed_goals = []
        for goal in self.get_selected_bnd().goals:
            lua_path = self.script_directory / f"{self.selected_map_id}/{goal.script_name}"
            if not lua_path.is_file():
                continue
            try:
                goal.load_script(lua_path)
            except Exception as e:
                failed_goals.append(goal)
                if (
                    self.CustomDialog(
                        title="Lua Read Error",
                        message=f"Error encountered while reading script for goal {goal.goal_id}: {goal.goal_name} "
                        f"({goal.goal_type}):\n\n{str(e)}"
                        f"\n\nContinue to next goal, or abort all remaining goals?",
                        button_names=("Continue to next goal", "Abort remaining"),
                        button_kwargs=("YES", "NO"),
                        return_output=0,
                        cancel_output=1,
                        default_output=1,
                    )
                    == 1
                ):
                    return
        failed_goals_msg = "\n".join(f"{g.goal_id}: {g.goal_name} ({g.goal_type}" for g in failed_goals)
        if failed_goals_msg:
            self.CustomDialog(
                title="Lua Load Complete",
                message=f"All scripts have been loaded from '/ai_scripts/{self.selected_map_id}' "
                f"except:\n\n{failed_goals_msg}",
            )
        else:
            self.CustomDialog(title="Lua Load Successful", message="All scripts were loaded successfully.")
        if self.active_row_index is not None:
            self.update_script_text()

    def confirm_selected(self, mimic_click=False, flash_bg=True):
        """Confirms changes to the selected script in its goal instance. Also re-colors syntax."""
        if self.confirm_button["state"] == "normal" and self.active_row_index is not None:
            if mimic_click:
                self.mimic_click(self.confirm_button)
            current_text = self._get_current_text()
            if current_text:
                goal = self.get_goal()
                goal.script = current_text
                self.lua_script_editor.color_syntax()
                if flash_bg:
                    self.flash_bg(self.lua_script_editor, "#232")

    def compile_selected(self, mimic_click=False):
        """Compile script, which is not necessary but can be used to test validity. Confirms changes first."""
        if self.compile_button["state"] == "normal" and self.active_row_index is not None:
            self.confirm_selected(mimic_click=True, flash_bg=False)
            if mimic_click:
                self.mimic_click(self.compile_button)
            goal = self.get_goal()
            goal.script = self._get_current_text()
            try:
                goal.compile(x64=not self.get_selected_bnd().is_lua_32)
                if self.allow_decompile:
                    self.decompile_button["state"] = "normal"
                self.lua_script_editor.tag_remove("error", "1.0", "end")
                self.flash_bg(self.lua_script_editor, "#223")
            except LuaError as e:
                msg = self._parse_compile_error(str(e))
                self.CustomDialog(
                    title="Lua Compile Error",
                    message=f"Error encountered while compiling script for goal {goal.goal_id}: "
                    f"{goal.goal_name} ({repr(goal.goal_type)}):\n\n{msg}",
                )

    def decompile_selected(self, mimic_click=False):
        """Decompile script from compiled bytecode. Always confirms loss of existing decompiled script first."""
        if self.decompile_button["state"] == "normal" and self.active_row_index is not None:
            if mimic_click:
                self.mimic_click(self.decompile_button)
            goal = self.get_goal()
            if goal.script:
                if (
                    self.CustomDialog(
                        title="Overwrite Script?",
                        message="Overwrite existing decompiled script?",
                        button_names=("Yes, overwrite", "No, do nothing"),
                        button_kwargs=("YES", "NO"),
                        return_output=0,
                        cancel_output=1,
                        default_output=1,
                    )
                    == 1
                ):
                    return
            try:
                goal.decompile()
                self.confirm_button["state"] = "normal"
                self.compile_button["state"] = "normal"
                self.write_button["state"] = "normal"
                self.update_script_text(goal)
            except LuaError as e:
                self.CustomDialog(
                    title="Lua Decompile Error", message=f"Error encountered while decompiling script:\n\n{str(e)}"
                )

    def write_selected(self, mimic_click=False):
        """Write selected script to project directory. Confirms changes first."""
        if self.write_button["state"] == "normal" and self.active_row_index is not None:
            self.confirm_selected(mimic_click=True)
            if mimic_click:
                self.mimic_click(self.write_button)
            goal = self.get_goal()
            try:
                goal.write_script(self.script_directory / f"{self.selected_map_id}/{goal.script_name}")
            except LuaError as e:
                self.CustomDialog(
                    title="Lua Write Error", message=f"Error encountered while writing script:\n\n{str(e)}"
                )

    def reload_selected(self, mimic_click=False):
        """Reload selected script from project directory. Confirms loss of unsaved changes first."""
        if self.reload_button["state"] == "normal" and self.active_row_index is not None:
            if mimic_click:
                self.mimic_click(self.reload_button)
            if not self._ignored_unsaved():
                return
            goal = self.get_goal()
            try:
                goal.load_script(self.script_directory / f"{self.selected_map_id}/{goal.script_name}")
                self.update_script_text(goal)
            except FileNotFoundError:
                self.CustomDialog(
                    title="Lua Read Error",
                    message=f"Decompiled script not found in '/ai_scripts/{self.selected_map_id}' directory.",
                )

    def refresh_entries(self):
        self._cancel_entry_id_edit()
        self._cancel_entry_text_edit()

        entries_to_display = self._get_category_name_range(
            first_index=self.first_display_index, last_index=self.first_display_index + self.ENTRY_RANGE_SIZE,
        )

        row = 0
        luabnd = self.get_selected_bnd()
        for entry_id, goal_type in entries_to_display:
            goal = luabnd.get_goal(entry_id, goal_type)
            self.entry_rows[row].update_entry(entry_id, goal.goal_name, goal.goal_type)
            self.entry_rows[row].unhide()
            row += 1

        self.displayed_entry_count = row
        for remaining_row in range(row, len(self.entry_rows)):
            self.entry_rows[remaining_row].hide()

        self.entry_i_frame.columnconfigure(0, weight=1)
        self.entry_i_frame.columnconfigure(1, weight=1)
        # If invalid, active row is allowed to move back by ONE. Otherwise, it's deselected.
        if self.active_row_index is not None:
            if 0 < row == self.active_row_index:
                self.select_entry_row_index(row - 1)
            elif self.active_row_index > row:
                self.select_entry_row_index(None)

        self._refresh_range_buttons()

    def select_entry_id(self, entry_id, goal_type=None, set_focus_to_text=True, edit_if_already_selected=True):
        """Select entry based on ID and set the category display range to target_row_index rows before it."""
        entry_index = self.get_entry_index(entry_id, goal_type=goal_type)
        self.refresh_entries()
        self.select_entry_row_index(
            entry_index, set_focus_to_text=set_focus_to_text, edit_if_already_selected=edit_if_already_selected
        )

    def select_entry_row_index(
        self,
        row_index: int | None,
        set_focus_to_text=True,
        edit_if_already_selected=True,
        id_clicked=False,
        check_unsaved=True,
    ):
        """Select entry from row index, based on currently displayed category and ID range."""
        old_row_index = self.active_row_index

        if check_unsaved and old_row_index != row_index and old_row_index is not None:
            if not self._ignored_unsaved():
                return

        if old_row_index is not None and row_index is not None:
            if row_index == old_row_index:
                if edit_if_already_selected:
                    if id_clicked:
                        return self._start_entry_id_edit(row_index)
                    else:
                        return self._start_entry_text_edit(row_index)
                return
        else:
            self._cancel_entry_id_edit()
            self._cancel_entry_text_edit()

        self.active_row_index = row_index

        if old_row_index is not None:
            self.entry_rows[old_row_index].active = False
        if row_index is not None:
            self.entry_rows[row_index].active = True
            if set_focus_to_text:
                self.entry_rows[row_index].text_label.focus_set()
            self.lua_script_editor["state"] = "normal"
            goal = self.get_goal(row_index)
            if self.allow_decompile:
                self.decompile_button["state"] = "normal" if goal.bytecode else "disabled"
            self.confirm_button["state"] = "normal" if goal.script else "disabled"
            self.compile_button["state"] = "normal" if goal.script else "disabled"
            self.write_button["state"] = "normal" if goal.script else "disabled"
            self.reload_button["state"] = "normal"
            self.update_script_text(goal)
        else:
            # No entry is selected.
            self.lua_script_editor.delete(1.0, "end")
            self.lua_script_editor["state"] = "disabled"
            self.decompile_button["state"] = "disabled"
            self.confirm_button["state"] = "disabled"
            self.compile_button["state"] = "disabled"
            self.write_button["state"] = "disabled"
            self.reload_button["state"] = "disabled"

    def update_script_text(self, goal=None):
        if goal is None:
            goal = self.get_goal()
        self.lua_script_editor.delete(1.0, "end")
        self.lua_script_editor.insert(1.0, goal.script)
        self.lua_script_editor.mark_set("insert", "1.0")
        self.lua_script_editor.color_syntax()

    def get_goal_id_and_type(self, row_index=None):
        if row_index is None:
            row_index = self.active_row_index
        return self.entry_rows[row_index].entry_id, self.entry_rows[row_index].goal_type

    def get_goal(self, row_index=None):
        if row_index is None:
            row_index = self.active_row_index
        goal_id, goal_type = self.get_goal_id_and_type(row_index)
        return self.get_selected_bnd().get_goal(goal_id, goal_type)

    def on_map_choice(self, event=None):
        if self.active_row_index is not None and not self._ignored_unsaved():
            game_map = self.ai.GET_MAP(self.selected_map_id)
            self.map_choice.var.set(f"{game_map.ai_file_stem} [{game_map.verbose_name}]")
            return
        self.selected_map_id = self.map_choice_stem
        if self.global_map_choice_func and event is not None:
            self.global_map_choice_func(self.map_choice_stem, ignore_tabs=("ai",))
        self.select_entry_row_index(None, check_unsaved=False)
        self.refresh_entries()
        self.entry_canvas.yview_moveto(0)

    def _add_entry(self, entry_id, text, goal_type=None, category=None, at_index=None, new_goal=None):
        if entry_id < 0:
            self.CustomDialog(title="Goal ID Error", message=f"Entry ID cannot be negative.")
            return False
        if (entry_id, goal_type) in self.get_category_data():
            self.CustomDialog(
                title="Goal ID Error", message=f"Goal ID {entry_id} with type {repr(goal_type)} already exists."
            )
            return False

        new_goal.goal_id = entry_id
        new_goal.goal_type = goal_type
        self._cancel_entry_id_edit()
        self._cancel_entry_text_edit()
        if at_index:
            self.get_selected_bnd().goals.insert(at_index, new_goal)
        else:
            self.get_selected_bnd().goals.append(new_goal)

        self._set_entry_text(entry_id, text, goal_type)
        self.select_entry_id(entry_id, goal_type=goal_type, set_focus_to_text=True, edit_if_already_selected=False)

    def add_relative_entry(self, entry_id, goal_type=None, offset=1, text=None):
        goal = self.get_selected_bnd().get_goal(entry_id, goal_type)
        if text is None:
            text = goal.goal_name  # Copies name of origin entry by default.
        goal_index = self.get_selected_bnd().goals.index(goal) + 1
        self._add_entry(
            entry_id=entry_id + offset, goal_type=goal_type, text=text, at_index=goal_index, new_goal=goal.copy()
        )

    def delete_entry(self, row_index: int | None, category=None, must_be_selected=False):
        """Deletes entry and returns it (or False upon failure) so that the action manager can undo the deletion."""
        if row_index is None:
            self.bell()
            return
        if must_be_selected and self.active_row_index is None or row_index != self.active_row_index:
            self.bell()
            return

        self._cancel_entry_id_edit()
        self._cancel_entry_text_edit()
        goal = self.get_goal(row_index)
        self.get_selected_bnd().goals.remove(goal)
        self.select_entry_row_index(None, check_unsaved=False)  # we DO deselect entries in this subclass
        self.refresh_entries()

    def get_selected_bnd(self) -> LuaBND:
        return self.ai[self.selected_map_id]

    def get_category_data(self, category=None) -> Dict[(int, bool), LuaGoalScript]:
        """Gets dictionary of goals in LuaInfo from LuaBND. Category does nothing."""
        return self.get_selected_bnd().get_goal_dict()

    def _get_category_name_range(self, category=None, first_index=None, last_index=None):
        """Always returns full dict (no previous/next buttons)."""
        return list(self.get_selected_bnd().get_goal_dict().keys())

    def get_entry_index(self, entry_id: int, goal_type=None, category=None) -> int:
        """Get index of entry. Ignores current display range."""
        if goal_type is None:
            raise ValueError(f"Goal type cannot be none (goal ID {entry_id}).")
        if (entry_id, goal_type) not in self.get_category_data():
            raise ValueError(f"Goal ID {entry_id} with type {repr(goal_type)} does not exist.")
        goal = self.get_selected_bnd().get_goal(entry_id, goal_type)
        return self.get_selected_bnd().goals.index(goal)

    def get_entry_text(self, entry_id: int, category=None, goal_type=None) -> str:
        return self.get_selected_bnd().get_goal(entry_id, goal_type).goal_name

    def _set_entry_text(self, entry_id: int, text: str, goal_type=None, category=None, update_row_index=None):
        goal = self.get_selected_bnd().get_goal(entry_id, goal_type)
        try:
            goal.goal_name = text
        except LuaError as e:
            self.CustomDialog(title="Goal Name Error", message=str(e))
            return False
        if update_row_index is not None:
            self.entry_rows[update_row_index].update_entry(entry_id, text, goal_type)
        return True

    def change_entry_text(self, row_index, new_text, category=None, record_action=True):
        """Set text of given entry index in the displayed category (if different from current)."""
        goal = self.get_goal(row_index)
        current_text = goal.goal_name
        if current_text == new_text:
            return  # Nothing to change.

        if not self._set_entry_text(goal.goal_id, new_text, goal_type=goal.goal_type, update_row_index=row_index):
            return

        if record_action:
            self.action_history.record_action(
                undo=partial(self._set_entry_text, entry_id=goal.goal_id, new_text=new_text, category=category),
                redo=partial(self._set_entry_text, entry_id=goal.goal_id, new_text=current_text, category=category),
            )
        else:
            # Also jump to given entry and record view change.
            # TODO: Need to record CURRENT view, which could be a different tab entirely.
            current_map = self.ai.GET_MAP(self.selected_map_id)
            map_choice_string = f"{current_map.ai_file_stem} [{current_map.verbose_name}]"
            current_category = self.active_category
            current_entry_id = self.get_entry_id(self.active_row_index) if self.active_row_index else None
            self.linker.jump(self.TAB_NAME, category, goal.goal_id)
            self.view_history.record_view_change(
                back=partial(
                    self.linker.jump,
                    self.TAB_NAME,
                    current_category,
                    current_entry_id,
                    lambda: self.map_choice.var.set(map_choice_string),
                ),
                forward=partial(
                    self.linker.jump,
                    self.TAB_NAME,
                    category,
                    goal.goal_id,
                    lambda: self.map_choice.var.set(map_choice_string),
                ),
            )

    def _start_entry_text_edit(self, row_index):
        if not self._e_entry_text_edit and not self._e_entry_id_edit:
            goal = self.get_goal(row_index)
            initial_text = goal.goal_name
            if "\n" in initial_text:
                return self.popout_entry_text_edit(row_index)
            self._e_entry_text_edit = self.Entry(
                self.entry_rows[row_index].text_box, initial_text=initial_text, sticky="ew", width=5
            )
            self._e_entry_text_edit.bind("<Return>", lambda e, i=row_index: self._confirm_entry_text_edit(i))
            self._e_entry_text_edit.bind("<Up>", self._entry_press_up)  # confirms edit
            self._e_entry_text_edit.bind("<Down>", self._entry_press_down)  # confirms edit
            self._e_entry_text_edit.bind("<FocusOut>", lambda e, i=row_index: self._confirm_entry_text_edit(i))
            self._e_entry_text_edit.bind("<Escape>", lambda e: self._cancel_entry_text_edit())
            self._e_entry_text_edit.focus_set()
            self._e_entry_text_edit.select_range(0, "end")

    def change_entry_id(self, row_index, new_id, category=None, record_action=True):
        # TODO: change for record action
        goal = self.get_goal(row_index)
        current_id = goal.goal_id
        if current_id == new_id:
            return False
        goal_dict = self.get_category_data()
        if (new_id, goal.goal_type) in goal_dict:
            self.CustomDialog(
                title="Entry ID Clash",
                message=f"Goal ID {new_id} with type {repr(goal.goal_type)} already exists. You must change or "
                f"delete it first.",
            )
            return False
        goal.goal_id = new_id
        self.entry_rows[row_index].update_entry(new_id, goal.goal_name, goal.goal_type)
        return True

    def _set_entry_id(self, entry_id: int, new_id: int, category=None, update_row_index=None, goal_type=None):
        """Not used here (handled directly in overridden `change_entry_id`)."""
        # TODO: may need to implement for action history.
        raise NotImplementedError

    def _get_display_categories(self):
        """Unused."""
        return []
