# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""HTTP API entry points."""

from __future__ import annotations

from importlib import import_module
from typing import Any

from bijux_proteomics_runtime.core.stability import stable

stable()

__all__ = ["AppConfig", "create_app"]


def __getattr__(name: str) -> Any:
    """Load API entrypoints lazily to keep product-route imports cycle-safe."""

    if name not in {"AppConfig", "create_app"}:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module = import_module("bijux_proteomics_runtime.api.app")
    return getattr(module, name)
