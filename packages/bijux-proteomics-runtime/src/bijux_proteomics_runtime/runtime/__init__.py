# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Runtime flow exports."""

from __future__ import annotations

from importlib import import_module
from typing import Any

from bijux_proteomics_runtime.core.stability import sealed

sealed()

__all__ = ["RunManager"]


def __getattr__(name: str) -> Any:
    """Load runtime entrypoints lazily to keep submodule imports cycle-safe."""

    if name != "RunManager":
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module = import_module("bijux_proteomics_runtime.runtime.control.execution")
    return getattr(module, "RunManager")
