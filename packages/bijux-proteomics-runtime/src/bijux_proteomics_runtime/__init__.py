"""Canonical runtime package for bijux proteomics execution surfaces."""

from __future__ import annotations

from importlib import import_module
from typing import Any

__all__ = ["AppConfig", "RunManager", "cli", "create_app"]

_RUNTIME_ROOT_EXPORTS = {
    "AppConfig": ("bijux_proteomics_runtime.api", "AppConfig"),
    "RunManager": ("bijux_proteomics_runtime.runs.manager", "RunManager"),
    "cli": ("bijux_proteomics_runtime.api.cli", "cli"),
    "create_app": ("bijux_proteomics_runtime.api", "create_app"),
}


def __getattr__(name: str) -> Any:
    """Load public runtime entrypoints lazily to avoid package-import cycles."""

    target = _RUNTIME_ROOT_EXPORTS.get(name)
    if target is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module_name, attribute_name = target
    module = import_module(module_name)
    return getattr(module, attribute_name)
