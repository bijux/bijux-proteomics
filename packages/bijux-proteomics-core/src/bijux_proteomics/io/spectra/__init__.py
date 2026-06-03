# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Canonical spectrum models, matching, and annotation owners."""

from __future__ import annotations

from importlib import import_module
from typing import Any

_SPECTRA_EXPORT_MODULES = (
    "bijux_proteomics.io.spectra.spectrum_contracts",
    "bijux_proteomics.io.spectra.spectrum_entropy",
    "bijux_proteomics.io.spectra.spectrum_peak_matching",
    "bijux_proteomics.io.spectra.chimeric_spectrum",
    "bijux_proteomics.io.spectra.precursor_validation",
)


def __getattr__(name: str) -> Any:
    for module_path in _SPECTRA_EXPORT_MODULES:
        module = import_module(module_path)
        if hasattr(module, name):
            value = getattr(module, name)
            globals()[name] = value
            return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
