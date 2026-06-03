# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Identification evidence, confidence, and search-adapter surfaces."""

from __future__ import annotations

from importlib import import_module
from typing import Any

_IDENTIFICATION_EXPORT_MODULES = (
    "bijux_proteomics.identification.adapters",
    "bijux_proteomics.identification.contracts",
    "bijux_proteomics.identification.confidence",
    "bijux_proteomics.identification.fdr",
    "bijux_proteomics.identification.peptide",
    "bijux_proteomics.identification.protein",
    "bijux_proteomics.identification.psm",
)

_IDENTIFICATION_SUBMODULES = {
    "adapters": "bijux_proteomics.identification.adapters",
    "confidence": "bijux_proteomics.identification.confidence",
    "contracts": "bijux_proteomics.identification.contracts",
    "fdr": "bijux_proteomics.identification.fdr",
    "peptide": "bijux_proteomics.identification.peptide",
    "protein": "bijux_proteomics.identification.protein",
    "psm": "bijux_proteomics.identification.psm",
}


def __getattr__(name: str) -> Any:
    submodule_path = _IDENTIFICATION_SUBMODULES.get(name)
    if submodule_path is not None:
        module = import_module(submodule_path)
        globals()[name] = module
        return module
    for module_path in _IDENTIFICATION_EXPORT_MODULES:
        module = import_module(module_path)
        if hasattr(module, name):
            value = getattr(module, name)
            globals()[name] = value
            return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
