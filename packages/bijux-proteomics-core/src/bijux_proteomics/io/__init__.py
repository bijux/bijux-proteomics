# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Format, ingestion, and spectrum boundaries."""

from __future__ import annotations

from importlib import import_module

_IO_EXPORT_MODULES = (
    "bijux_proteomics.io.formats",
    "bijux_proteomics.io.format_validation",
    "bijux_proteomics.io.mgf_streaming",
    "bijux_proteomics.io.mzml_reader",
    "bijux_proteomics.io.run_qc",
    "bijux_proteomics.io.spectrum_peak_matching",
    "bijux_proteomics.io.spectra",
    "bijux_proteomics.io.spectral_library",
    "bijux_proteomics.io.target_panel",
    "bijux_proteomics.io.transition_table",
    "bijux_proteomics.io.chromatographic_peak_picking",
    "bijux_proteomics.io.xic_extraction",
)


def __getattr__(name: str) -> object:
    for module_path in _IO_EXPORT_MODULES:
        module = import_module(module_path)
        if hasattr(module, name):
            value = getattr(module, name)
            globals()[name] = value
            return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
