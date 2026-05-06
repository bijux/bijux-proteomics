"""Public API import surface helpers."""

from __future__ import annotations

from importlib import import_module
from typing import Any

__all__ = ["AppConfig", "create_app"]

_PUBLIC_API_EXPORTS = {
    "AppConfig": ("bijux_proteomics_runtime.api.app", "AppConfig"),
    "create_app": ("bijux_proteomics_runtime.api.app", "create_app"),
}


def __getattr__(name: str) -> Any:
    """Load API entrypoints lazily to keep route imports cycle-safe."""

    target = _PUBLIC_API_EXPORTS.get(name)
    if target is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module_name, attribute_name = target
    module = import_module(module_name)
    return getattr(module, attribute_name)
