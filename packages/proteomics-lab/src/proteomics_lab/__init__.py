"""Compatibility alias module for bijux-proteomics-lab."""

from __future__ import annotations

from importlib import import_module, metadata
from typing import Any

from .runtime_alias import install_runtime_aliases

_ALIAS_PACKAGE = "proteomics_lab"
_RUNTIME_PACKAGE = "bijux_proteomics_lab"
_LOCAL_SUBMODULES = frozenset({"runtime_alias"})
_runtime_module = import_module(_RUNTIME_PACKAGE)

install_runtime_aliases(
    alias_package=_ALIAS_PACKAGE,
    runtime_package=_RUNTIME_PACKAGE,
    local_submodules=_LOCAL_SUBMODULES,
)

for _name in getattr(_runtime_module, "__all__", ()):
    if _name == "__version__":
        continue
    globals()[_name] = getattr(_runtime_module, _name)

try:
    __version__ = metadata.version("proteomics-lab")
except metadata.PackageNotFoundError:
    __version__ = "0.3.6"

__all__ = list(getattr(_runtime_module, "__all__", ()))


def __getattr__(name: str) -> Any:
    return getattr(_runtime_module, name)


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(dir(_runtime_module)))
