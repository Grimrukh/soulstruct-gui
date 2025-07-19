__all__ = [
    "DEFAULT_PROJECT_PATH",
    "DEFAULT_TEXT_EDITOR_FONT_SIZE",

    "GET_CONFIG",
    "SET_CONFIG",
]

import json
import logging
import sys
import typing as tp
from pathlib import Path

_LOGGER = logging.getLogger(__name__)

_CONFIG_FILE_NAME = "soulstruct_gui_config.json"
_SOULSTRUCT_APPDATA = Path("~/AppData/Roaming/soulstruct").expanduser()
_CONFIG_DEFAULTS = {
    "DEFAULT_PROJECT_PATH": Path("~/Documents/DefaultProject").expanduser(),
    "DEFAULT_TEXT_EDITOR_FONT_SIZE": 12,
}


def GET_CONFIG() -> dict[str, tp.Any]:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        # Look for `soulstruct_config.json` next to PyInstaller executable.
        config_path = Path(sys.executable).parent / _CONFIG_FILE_NAME
        if not config_path.exists():
            raise FileNotFoundError(f"Could not find 'soulstruct_config.json' next to Soulstruct executable.")
    else:
        # Look for `soulstruct_config.json` in user data.
        config_path = _SOULSTRUCT_APPDATA / _CONFIG_FILE_NAME
        if not config_path.exists():
            raise FileNotFoundError(f"Could not find 'soulstruct_config.json' in user data: {config_path}.")
    with config_path.open("r") as f:
        try:
            config = json.load(f)
        except json.JSONDecodeError as ex:
            raise json.JSONDecodeError(
                f"Error while loading 'soulstruct_config.json': {ex.msg}", _CONFIG_FILE_NAME, ex.lineno
            )
    # For keys ending in '_PATH', convert to Path objects.
    for k, v in config.items():
        if k.endswith("_PATH"):
            config[k] = Path(v)

    return config


def SET_CONFIG(**kwargs):
    """Update `soulstruct_config.json` with the given keyword arguments.

    Omitted arguments default to their current values, or their given default values (above) if no current value exists.
    """
    try:
        config = GET_CONFIG()
    except json.JSONDecodeError:
        _LOGGER.error(f"Error encountered while loading '{_CONFIG_FILE_NAME}'. Try fixing or deleting it.")
        raise
    except FileNotFoundError:
        config = {}
    for k, default_value in _CONFIG_DEFAULTS.items():
        if k in kwargs:
            config[k] = kwargs.pop(k)
        else:
            config.setdefault(k, default_value)
    if kwargs:
        raise KeyError(f"Invalid config key(s): {list(kwargs)}")

    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        config_path = Path(sys.executable).parent / _CONFIG_FILE_NAME
    else:
        config_path = _SOULSTRUCT_APPDATA / _CONFIG_FILE_NAME

    # Convert all Path objects to strings for JSON serialization.
    config_json = {
        k: str(v) if isinstance(v, Path) else v for k, v in config.items()
    }
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with config_path.open("w") as f:
        json.dump(config_json, f, indent=4)

try:
    __config = GET_CONFIG()
except FileNotFoundError:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        _LOGGER.info(
            f"Creating default `{_CONFIG_FILE_NAME}` file next to Soulstruct executable.\n"
            f"Set your Soulstruct GUI settings in here."
        )
    else:
        _LOGGER.info(
            f"Creating default `{_CONFIG_FILE_NAME}` file in user data: {str(Path(__file__).parent)}.\n"
            f"Set your Soulstruct GUI settings in here."
        )
    SET_CONFIG()
    __config = GET_CONFIG()
else:
    if len(__config) != len(_CONFIG_DEFAULTS):
        # Make sure we write and reload to get (and save) default values.
        SET_CONFIG()
        __config = GET_CONFIG()

DEFAULT_PROJECT_PATH = __config.get("DEFAULT_PROJECT_PATH")  # type: Path
DEFAULT_TEXT_EDITOR_FONT_SIZE = __config.get("DEFAULT_TEXT_EDITOR_FONT_SIZE")  # type: int
