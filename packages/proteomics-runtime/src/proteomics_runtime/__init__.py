"""Compatibility alias module for bijux-proteomics-runtime."""

from __future__ import annotations

from importlib import import_module, metadata
from typing import TYPE_CHECKING
from typing import Any

from .runtime_alias import install_runtime_aliases

_ALIAS_PACKAGE = "proteomics_runtime"
_RUNTIME_PACKAGE = "bijux_proteomics_runtime"
_LOCAL_SUBMODULES = frozenset({"__main__", "cli", "runtime_alias"})

if TYPE_CHECKING:
    from bijux_proteomics_runtime import *  # noqa: F403

install_runtime_aliases(
    alias_package=_ALIAS_PACKAGE,
    runtime_package=_RUNTIME_PACKAGE,
    local_submodules=_LOCAL_SUBMODULES,
)

try:
    __version__ = metadata.version("proteomics-runtime")
except metadata.PackageNotFoundError:
    __version__ = "0.3.6"

__all__ = ["__version__"]


def _runtime_module() -> Any:
    return import_module(_RUNTIME_PACKAGE)


def __getattr__(name: str) -> Any:
    """Forward top-level compatibility lookups to the canonical runtime package."""
    return getattr(_runtime_module(), name)


def __dir__() -> list[str]:
    """Expose canonical runtime attributes in interactive discovery."""
    return sorted(set(globals()) | set(dir(_runtime_module())))
