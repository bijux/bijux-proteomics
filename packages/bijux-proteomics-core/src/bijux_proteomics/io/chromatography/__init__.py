# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Canonical typed XIC, peak, alignment, and coelution owners."""

from __future__ import annotations

from importlib import import_module

_CHROMATOGRAPHY_EXPORT_MODULES = (
    "bijux_proteomics.io.chromatography.xic",
    "bijux_proteomics.io.chromatography.chromatographic_peak_picking",
    "bijux_proteomics.io.chromatography.retention_time_alignment",
    "bijux_proteomics.io.chromatography.chromatographic_evidence",
    "bijux_proteomics.io.chromatography.dia_fragment_coelution",
    "bijux_proteomics.io.chromatography.fragment_ratio_stability",
)


def __getattr__(name: str) -> object:
    for module_path in _CHROMATOGRAPHY_EXPORT_MODULES:
        module = import_module(module_path)
        if hasattr(module, name):
            value = getattr(module, name)
            globals()[name] = value
            return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
