# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Canonical PTM localization scoring and risk owners."""

from __future__ import annotations

from importlib import import_module
from typing import Any

_LOCALIZATION_EXPORT_MODULES = (
    "bijux_proteomics.ptm.localization.fragment_scoring",
    "bijux_proteomics.ptm.localization.localization_scoring",
    "bijux_proteomics.ptm.localization.localization_risk",
)


def __getattr__(name: str) -> Any:
    for module_path in _LOCALIZATION_EXPORT_MODULES:
        module = import_module(module_path)
        if hasattr(module, name):
            value = getattr(module, name)
            globals()[name] = value
            return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
