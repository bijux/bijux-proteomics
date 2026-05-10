# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Compatibility alias root for canonical runtime entrypoints."""

from __future__ import annotations

from importlib import import_module, metadata
from typing import Any

_RUNTIME_PACKAGE = "bijux_proteomics_runtime"
_runtime_module = import_module(_RUNTIME_PACKAGE)

for _name in getattr(_runtime_module, "__all__", ()):
    if _name == "__version__":
        continue
    globals()[_name] = getattr(_runtime_module, _name)

__all__ = list(getattr(_runtime_module, "__all__", ()))

try:
    __version__ = metadata.version("agentic-proteins")
except metadata.PackageNotFoundError:
    __version__ = "0.3.7"


def __getattr__(name: str) -> Any:
    """Forward root-level compatibility lookups to the canonical runtime package."""

    return getattr(_runtime_module, name)


def __dir__() -> list[str]:
    """Expose canonical runtime attributes for interactive discovery."""

    return sorted(set(globals()) | set(dir(_runtime_module)))
