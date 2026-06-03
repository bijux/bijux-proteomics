# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Canonical raw-file parsing and mzML-bound extraction owners."""

from __future__ import annotations

from importlib import import_module
from typing import Any

_RAW_EXPORT_MODULES = (
    "bijux_proteomics.io.raw.deisotoping",
    "bijux_proteomics.io.raw.mgf_streaming",
    "bijux_proteomics.io.raw.mzml_reader",
    "bijux_proteomics.io.raw.noise",
    "bijux_proteomics.io.raw.run_qc",
    "bijux_proteomics.io.raw.xic_extraction",
    "bijux_proteomics.io.raw.chromatographic_peak_picking",
    "bijux_proteomics.io.raw.retention_time_alignment",
    "bijux_proteomics.io.raw.chromatographic_evidence",
    "bijux_proteomics.io.raw.dia_fragment_coelution",
    "bijux_proteomics.io.raw.fragment_ratio_stability",
    "bijux_proteomics.io.raw.precursor_isotope_fit",
    "bijux_proteomics.io.raw.raw_signal_evidence_cards",
)


def __getattr__(name: str) -> Any:
    for module_path in _RAW_EXPORT_MODULES:
        module = import_module(module_path)
        if hasattr(module, name):
            value = getattr(module, name)
            globals()[name] = value
            return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
