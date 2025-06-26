from __future__ import annotations

__all__ = ["RuntimeManager"]

from soulstruct.gui.base.runtime import RuntimeManager as _BaseRuntimeManager


class RuntimeManager(_BaseRuntimeManager):
    HOOK_CLASS = None  # no hook for PTDE
