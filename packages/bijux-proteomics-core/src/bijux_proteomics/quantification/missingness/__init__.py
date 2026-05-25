# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Canonical quantification missingness and readiness owners."""

from __future__ import annotations

from importlib import import_module

_MISSINGNESS_EXPORT_MODULES = (
    "bijux_proteomics.quantification.missingness.missingness",
    "bijux_proteomics.quantification.missingness.peptide_profile_inconsistency",
    "bijux_proteomics.quantification.missingness.readiness",
)


def __getattr__(name: str) -> object:
    for module_path in _MISSINGNESS_EXPORT_MODULES:
        module = import_module(module_path)
        if hasattr(module, name):
            value = getattr(module, name)
            globals()[name] = value
            return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
