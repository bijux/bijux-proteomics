# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Canonical study metadata and sample-identity ownership surfaces."""

from __future__ import annotations

from importlib import import_module
from typing import Any

_STUDY_METADATA_EXPORT_MODULES = (
    "bijux_proteomics.study.metadata.contracts",
    "bijux_proteomics.study.metadata.sample_metadata",
    "bijux_proteomics.study.metadata.sample_run_identity",
    "bijux_proteomics.study.metadata.sample_sheet_repairs",
)


def __getattr__(name: str) -> Any:
    for module_path in _STUDY_METADATA_EXPORT_MODULES:
        module = import_module(module_path)
        if hasattr(module, name):
            value = getattr(module, name)
            globals()[name] = value
            return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
