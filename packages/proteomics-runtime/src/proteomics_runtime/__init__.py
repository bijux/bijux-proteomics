"""Compatibility alias module for bijux-proteomics-runtime."""

from __future__ import annotations

from importlib import import_module
from typing import Any

from bijux_proteomics_foundation._package_aliases import (
    alias_package_version,
    canonical_module_dir,
    install_import_aliases,
)

_ALIAS_PACKAGE = "proteomics_runtime"
_CANONICAL_PACKAGE = "bijux_proteomics_runtime"
_LOCAL_SUBMODULES = frozenset({"__main__", "cli"})

install_import_aliases(
    alias_package=_ALIAS_PACKAGE,
    canonical_package=_CANONICAL_PACKAGE,
    local_submodules=_LOCAL_SUBMODULES,
)

__version__ = alias_package_version("proteomics-runtime")

__all__ = ["__version__"]


def _canonical_module() -> Any:
    return import_module(_CANONICAL_PACKAGE)


def __getattr__(name: str) -> Any:
    """Forward top-level compatibility lookups to the canonical runtime package."""

    return getattr(_canonical_module(), name)


def __dir__() -> list[str]:
    """Expose canonical runtime attributes in interactive discovery."""

    return canonical_module_dir(globals(), _CANONICAL_PACKAGE)
