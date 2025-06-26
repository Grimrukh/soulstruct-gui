"""
Soulstruct GUI command-line interface (Typer).

This file is part of the *soulstruct.gui* namespace-package plug-in.
It uses a separate command: `soulstruct-gui`.

Usage examples
--------------
    soulstruct-gui                              # open full Project GUI
    soulstruct-gui ~/MyProject --maps           # open MapStudio editor
    soulstruct-gui -c                           # interactive IPython console
"""
from __future__ import annotations

import logging
from importlib.util import find_spec
from pathlib import Path
from textwrap import dedent
from typing_extensions import Annotated

import typer

from soulstruct.config import DEFAULT_PROJECT_PATH
from soulstruct.games import Game, get_game
from soulstruct.utilities.files import read_json
from soulstruct.gui.misc.game_selector import GameSelector

app = typer.Typer(
    help="Launch the Soulstruct GUI or its component editors.",
    add_completion=False,
)

_LOGGER = logging.getLogger(__name__)

# Global variables (for interactive console usage).
Project: object | None = None
Maps: object | None = None
Params: object | None = None
Lighting: object | None = None
Text: object | None = None


def _import_game_gui_submodule(game: Game):
    match game.variable_name:
        case "DARK_SOULS_PTDE":
            from soulstruct.gui import darksouls1ptde
            return darksouls1ptde
        case "DARK_SOULS_DSR":
            from soulstruct.gui import darksouls1r
            return darksouls1r
        case "BLOODBORNE":
            from soulstruct.gui import bloodborne
            return bloodborne
        case "ELDENRING":
            from soulstruct.gui import eldenring
            return eldenring
        case _:
            raise ValueError(f"Game has no GUI support: {game.variable_name}")


def _existing_project_game(project_path: Path | str | None):
    if not project_path:
        return None
    project_path = Path(project_path)
    try:
        cfg = read_json(project_path / "project_config.json")
    except FileNotFoundError:
        return None
    return get_game(cfg.get("GameName", "")) if cfg else None


@app.command("launch", rich_help_panel="GUI commands")
def gui_command(  # noqa: C901 (long but readable)
    source: Annotated[Path | None, typer.Argument(
        exists=False,
        help="Project directory or game install directory. "
             f"Defaults to {DEFAULT_PROJECT_PATH!s}.",
    )] = None,
    console: Annotated[bool, typer.Option(
        "-c", "--console",
        help="Open interactive IPython console "
             "instead of GUI windows."
        )] = False,
    maps: Annotated[bool, typer.Option("--maps", help="Open MapStudio editor.")] = False,
    params: Annotated[bool, typer.Option(
        "--params", "-p",
        help="Open Param editor."
        )] = False,
    lighting: Annotated[bool, typer.Option(
        "--lighting", "-l",
        help="Open Lighting editor."
        )] = False,
    text: Annotated[bool, typer.Option(
        "--text", "-t",
        help="Open Text editor."
        )] = False,
    modmanager: Annotated[bool, typer.Option(
        "-m", "--modmanager",
        help="Open Mod Manager."
        )] = False,
    game: Annotated[str | None, typer.Option(
        "--game", "-g",
        help="Force game for a *new* project: ptde, dsr, bb, er.",
    )] = None,
    show_console_startup: Annotated[bool, typer.Option(
        "--show-console-startup/--no-console-startup",
        help="Show help banner when launching the IPython console.",
    )] = True,
):
    """
    Launch Soulstruct’s GUI or one of its component editors.

    Without any flags this opens the full project window.
    Use `--maps`, `--params`, `--lighting`, or `--text` to jump straight
    to an individual editor, or `-c` for an IPython console only.
    """

    # Resolve default source path
    source_path: str | None = str(source) if source else DEFAULT_PROJECT_PATH

    # ------------------------------------------------------------------ #
    # 1. Choose which *game* this invocation should operate on           #
    # ------------------------------------------------------------------ #
    chosen_game: Game | None = _existing_project_game(source_path)
    if chosen_game is None and game:
        chosen_game = {
            "ptde": "darksouls1ptde",
            "dsr": "darksouls1r",
            "bb": "bloodborne",
            "er": "eldenring",
        }.get(game.lower())
        if chosen_game:
            chosen_game = get_game(chosen_game)

    if chosen_game is None:
        # Interactive prompt
        choices = ("darksouls1ptde", "darksouls1r", "bloodborne", "eldenring")
        chosen_game = GameSelector(*choices).go()

    # Defensive check
    if chosen_game is None:
        _LOGGER.error("No game selected; aborting.")
        raise typer.Exit(code=1)

    # ------------------------------------------------------------------ #
    # 2. Handle Mod-Manager flag (returns immediately)                   #
    # ------------------------------------------------------------------ #
    if modmanager:
        from soulstruct.gui.misc.mod_manager import ModManagerWindow
        ModManagerWindow(source_path).wait_window()
        return

    # ------------------------------------------------------------------ #
    # 3. Single-editor short-cuts                                        #
    # ------------------------------------------------------------------ #
    if maps:
        global Maps
        Maps = chosen_game.import_game_submodule("maps").MapStudioDirectory(source_path)
        return
    if params:
        global Params
        Params = chosen_game.import_game_submodule("params").GameParamBND(source_path)
        return
    if lighting:
        global Lighting
        Lighting = chosen_game.import_game_submodule("lighting").DrawParamDirectory(source_path)
        return
    if text:
        global Text
        Text = chosen_game.import_game_submodule("text").MSGDirectory(source_path)
        return

    # ------------------------------------------------------------------ #
    # 4. Full project (GUI or console)                                   #
    # ------------------------------------------------------------------ #
    game_gui = _import_game_gui_submodule(chosen_game)

    if console:
        _launch_console(
            project_cls=game_gui.GameDirectoryProject,
            source_path=source_path,
            show_banner=show_console_startup,
        )
    else:
        win = game_gui.ProjectWindow(source_path)
        win.wait_window()  # GUI main-loop


def _launch_console(project_cls, source_path: str | None, show_banner: bool):
    global Project
    Project = project_cls(source_path)

    if not find_spec("IPython"):
        _LOGGER.error(
            "IPython is required for the interactive console. "
            "Install it with `pip install ipython`, or omit '-c/--console' option."
        )
        raise typer.Exit(1)

    from IPython import embed

    if show_banner:
        banner = dedent(
            """
            🎮  Welcome to Soulstruct interactive console!

            `Project` gives you access to maps, params, lighting and text:
                Project.maps.parts.new_character(name="Pet Gaping Dragon", model_name="c5260")
                Project.save("maps")     # write maps back to project
                Project.export_data()    # write all data back to game

            Docs & examples → https://github.com/Grimrukh/soulstruct
            """
        )
    else:
        banner = ""

    embed(colors="neutral", banner1=banner)
