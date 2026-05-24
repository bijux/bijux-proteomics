# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Format, ingestion, and spectrum boundaries."""

from __future__ import annotations

from importlib import import_module

_IO_EXPORT_MODULES = (
    "bijux_proteomics.io.formats",
    "bijux_proteomics.io.format_validation",
    "bijux_proteomics.io.deisotoping",
    "bijux_proteomics.io.mgf_streaming",
    "bijux_proteomics.io.mzml_reader",
    "bijux_proteomics.io.noise",
    "bijux_proteomics.io.run_qc",
    "bijux_proteomics.io.spectrum_entropy",
    "bijux_proteomics.io.spectrum_peak_matching",
    "bijux_proteomics.io.spectra",
    "bijux_proteomics.io.target_panel",
    "bijux_proteomics.io.transition_table",
    "bijux_proteomics.io.chimeric_spectrum",
    "bijux_proteomics.io.chromatographic_evidence",
    "bijux_proteomics.io.dia_fragment_coelution",
    "bijux_proteomics.io.fragment_ratio_stability",
    "bijux_proteomics.io.precursor_isotope_fit",
    "bijux_proteomics.io.precursor_validation",
    "bijux_proteomics.io.raw_signal_evidence_cards",
    "bijux_proteomics.io.chromatographic_peak_picking",
    "bijux_proteomics.io.retention_time_alignment",
    "bijux_proteomics.io.xic_extraction",
    "bijux_proteomics.io.spectral_library",
)


def __getattr__(name: str) -> object:
    for module_path in _IO_EXPORT_MODULES:
        module = import_module(module_path)
        if hasattr(module, name):
            value = getattr(module, name)
            globals()[name] = value
            return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
