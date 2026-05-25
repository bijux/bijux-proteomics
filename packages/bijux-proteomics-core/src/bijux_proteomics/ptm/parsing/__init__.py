# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Canonical PTM parsing and annotation-import owners."""

from __future__ import annotations

from importlib import import_module

_PARSING_EXPORT_MODULES = (
    "bijux_proteomics.ptm.parsing.peptide_parser",
    "bijux_proteomics.ptm.parsing.site_annotation_import",
)


def __getattr__(name: str) -> object:
    for module_path in _PARSING_EXPORT_MODULES:
        module = import_module(module_path)
        if hasattr(module, name):
            value = getattr(module, name)
            globals()[name] = value
            return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
