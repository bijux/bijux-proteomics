# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Canonical PTM regulation and regulator-inference owners."""

from __future__ import annotations

from importlib import import_module

_REGULATION_EXPORT_MODULES = (
    "bijux_proteomics.ptm.regulation.crosstalk",
    "bijux_proteomics.ptm.regulation.hotspots",
    "bijux_proteomics.ptm.regulation.kinase_inference",
    "bijux_proteomics.ptm.regulation.mechanism_classification",
    "bijux_proteomics.ptm.regulation.motif_analysis",
    "bijux_proteomics.ptm.regulation.phosphatase_inference",
    "bijux_proteomics.ptm.regulation.regulator_enrichment",
)


def __getattr__(name: str) -> object:
    for module_path in _REGULATION_EXPORT_MODULES:
        module = import_module(module_path)
        if hasattr(module, name):
            value = getattr(module, name)
            globals()[name] = value
            return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
