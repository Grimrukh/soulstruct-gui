import logging

_LOGGER = logging.getLogger("soulstruct_gui")

SET_DPI_AWARENESS = True

if SET_DPI_AWARENESS:
    try:
        from ctypes import windll
    except ImportError:
        pass
    else:
        try:
            windll.shcore.SetProcessDpiAwareness(1)
        except Exception as e:
            _LOGGER.warning(
                f"Could not set DPI awareness of system. GUI font may appear blurry on scaled Windows displays.\n"
                f"Error: {str(e)}"
            )
