# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Canonical quantification matrix and design owners."""

from __future__ import annotations

from importlib import import_module

_MATRIX_EXPORT_MODULES = (
    "bijux_proteomics.quantification.matrix.core_matrix",
    "bijux_proteomics.quantification.matrix.design_matrix",
    "bijux_proteomics.quantification.matrix.matrix_archive",
    "bijux_proteomics.quantification.matrix.peptide_intensity_matrix",
    "bijux_proteomics.quantification.matrix.protein_intensity_matrix",
)


def __getattr__(name: str) -> object:
    for module_path in _MATRIX_EXPORT_MODULES:
        module = import_module(module_path)
        if hasattr(module, name):
            value = getattr(module, name)
            globals()[name] = value
            return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
