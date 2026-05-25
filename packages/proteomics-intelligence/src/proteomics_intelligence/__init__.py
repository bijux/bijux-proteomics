"""Compatibility alias module for bijux-proteomics-intelligence."""

from __future__ import annotations

from importlib import import_module
from typing import Any

from bijux_proteomics_foundation._package_aliases import (
    alias_package_version,
    canonical_module_dir,
    install_import_aliases,
)

_ALIAS_PACKAGE = "proteomics_intelligence"
_CANONICAL_PACKAGE = "bijux_proteomics_intelligence"
_LOCAL_SUBMODULES = frozenset()

install_import_aliases(
    alias_package=_ALIAS_PACKAGE,
    canonical_package=_CANONICAL_PACKAGE,
    local_submodules=_LOCAL_SUBMODULES,
)
__version__ = alias_package_version("proteomics-intelligence")
__all__ = ["__version__"]


def __getattr__(name: str) -> Any:
    """Forward top-level compatibility lookups to the canonical intelligence package."""

    return getattr(import_module(_CANONICAL_PACKAGE), name)


def __dir__() -> list[str]:
    """Expose canonical intelligence attributes in interactive discovery."""

    return canonical_module_dir(globals(), _CANONICAL_PACKAGE)
