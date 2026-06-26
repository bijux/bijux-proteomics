# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Local provider implementations."""

from __future__ import annotations

from importlib import import_module, util
from types import ModuleType

__all__ = []


def _module_available(module_name: str) -> bool:
    try:
        return util.find_spec(module_name) is not None
    except ModuleNotFoundError:
        return False


def _optional_import(
    module_name: str,
    required_modules: tuple[str, ...],
) -> ModuleType | None:
    if not all(_module_available(name) for name in required_modules):
        return None
    try:
        return import_module(module_name)
    except ModuleNotFoundError as error:
        missing_module = (error.name or "").split(".", 1)[0]
        if not missing_module and error.args:
            message = str(error.args[0])
            prefix = "No module named "
            if message.startswith(prefix):
                missing_module = message[len(prefix) :].strip("'\"").split(".", 1)[0]
        if missing_module in required_modules:
            return None
        raise


if esmfold_module := _optional_import(
    "bijux_proteomics_runtime.providers.local.esmfold",
    ("torch", "transformers"),
):
    LocalESMFoldProvider = esmfold_module.LocalESMFoldProvider
    __all__.append("LocalESMFoldProvider")

if rosettafold_module := _optional_import(
    "bijux_proteomics_runtime.providers.local.rosettafold",
    ("torch",),
):
    LocalRoseTTAFoldProvider = rosettafold_module.LocalRoseTTAFoldProvider
    __all__.append("LocalRoseTTAFoldProvider")
