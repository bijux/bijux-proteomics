# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Compatibility alias root for canonical runtime entrypoints."""

from __future__ import annotations

from importlib import import_module, metadata
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from bijux_proteomics_runtime import AppConfig, RunManager, cli, create_app

__all__ = ["AppConfig", "RunManager", "cli", "create_app"]

try:
    __version__ = metadata.version("agentic-proteins")
except metadata.PackageNotFoundError:
    __version__ = "0.3.6"


def __getattr__(name: str) -> Any:
    """Forward compatibility root exports to the canonical runtime package lazily."""

    runtime_module = import_module("bijux_proteomics_runtime")
    return getattr(runtime_module, name)
