# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Canonical PTM quantitative and correction owners."""

from __future__ import annotations

from importlib import import_module

_QUANT_EXPORT_MODULES = (
    "bijux_proteomics.ptm.quant.abundance_correction",
    "bijux_proteomics.ptm.quant.acetylation",
    "bijux_proteomics.ptm.quant.differential_analysis",
    "bijux_proteomics.ptm.quant.occupancy_estimation",
    "bijux_proteomics.ptm.quant.oxidation",
    "bijux_proteomics.ptm.quant.site_quantification",
)


def __getattr__(name: str) -> object:
    for module_path in _QUANT_EXPORT_MODULES:
        module = import_module(module_path)
        if hasattr(module, name):
            value = getattr(module, name)
            globals()[name] = value
            return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
