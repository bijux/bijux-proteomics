# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Canonical table, panel, and deterministic row-order owners."""

from __future__ import annotations

from importlib import import_module

_TABLE_EXPORT_MODULES = (
    "bijux_proteomics.io.tables.streaming_joins",
    "bijux_proteomics.io.tables.stable_outputs",
    "bijux_proteomics.io.tables.target_panel",
    "bijux_proteomics.io.tables.transition_table",
    "bijux_proteomics.io.tables.xic_target_table",
)


def __getattr__(name: str) -> object:
    for module_path in _TABLE_EXPORT_MODULES:
        module = import_module(module_path)
        if hasattr(module, name):
            value = getattr(module, name)
            globals()[name] = value
            return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
