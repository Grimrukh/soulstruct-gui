from pathlib import Path

# Set up loggers.
import soulstruct_gui._logging

try:
    with (Path(__file__).parent / "../VERSION").open("r") as _vfp:
        __version__ = _vfp.read().strip()
except FileNotFoundError:
    __version = "UNKNOWN"
