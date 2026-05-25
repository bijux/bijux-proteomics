# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Canonical format, ingestion, and input-boundary owners."""

from __future__ import annotations

from importlib import import_module

_FORMATS_EXPORT_MODULES = (
    "bijux_proteomics.io.formats.proteomics_formats",
    "bijux_proteomics.io.formats.format_validation",
    "bijux_proteomics.io.formats.ingestion",
    "bijux_proteomics.io.formats.input_integrity",
    "bijux_proteomics.io.formats.spectral_library",
    "bijux_proteomics.io.formats.spectral_library_intensity_agreement",
)


def __getattr__(name: str) -> object:
    for module_path in _FORMATS_EXPORT_MODULES:
        module = import_module(module_path)
        if hasattr(module, name):
            value = getattr(module, name)
            globals()[name] = value
            return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
