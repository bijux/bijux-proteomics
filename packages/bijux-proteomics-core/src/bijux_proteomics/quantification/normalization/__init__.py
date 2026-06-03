# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Canonical quantification normalization and imputation owners."""

from __future__ import annotations

from importlib import import_module
from typing import Any

_NORMALIZATION_EXPORT_MODULES = (
    "bijux_proteomics.quantification.normalization.batch_effect",
    "bijux_proteomics.quantification.normalization.composition",
    "bijux_proteomics.quantification.normalization.imputation",
    "bijux_proteomics.quantification.normalization.normalization",
)


def __getattr__(name: str) -> Any:
    for module_path in _NORMALIZATION_EXPORT_MODULES:
        module = import_module(module_path)
        if hasattr(module, name):
            value = getattr(module, name)
            globals()[name] = value
            return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
