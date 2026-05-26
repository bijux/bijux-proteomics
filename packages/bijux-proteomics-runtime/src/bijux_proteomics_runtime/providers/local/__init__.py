# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Local provider implementations."""

from __future__ import annotations

from importlib import import_module
from importlib import util

__all__ = []


def _module_available(module_name: str) -> bool:
    try:
        return util.find_spec(module_name) is not None
    except ModuleNotFoundError:
        return False


if _module_available("torch") and _module_available("transformers"):
    LocalESMFoldProvider = import_module(
        "bijux_proteomics_runtime.providers.local.esmfold"
    ).LocalESMFoldProvider

    __all__.append("LocalESMFoldProvider")

if _module_available("torch"):
    LocalRoseTTAFoldProvider = import_module(
        "bijux_proteomics_runtime.providers.local.rosettafold"
    ).LocalRoseTTAFoldProvider

    __all__.append("LocalRoseTTAFoldProvider")
