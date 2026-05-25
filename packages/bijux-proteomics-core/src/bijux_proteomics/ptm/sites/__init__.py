# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Canonical PTM site-mapping, ambiguity, and context owners."""

from __future__ import annotations

from importlib import import_module

_SITES_EXPORT_MODULES = (
    "bijux_proteomics.ptm.sites.ambiguity_handling",
    "bijux_proteomics.ptm.sites.context_annotation",
    "bijux_proteomics.ptm.sites.ortholog_site_conservation",
    "bijux_proteomics.ptm.sites.protein_site_mapping",
    "bijux_proteomics.ptm.sites.site_groups",
)


def __getattr__(name: str) -> object:
    for module_path in _SITES_EXPORT_MODULES:
        module = import_module(module_path)
        if hasattr(module, name):
            value = getattr(module, name)
            globals()[name] = value
            return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
