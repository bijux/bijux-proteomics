# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Registry of interface support submodules.

This package no longer acts as a giant symbol barrel. Callers should import the
owned support module they actually depend on.
"""

from __future__ import annotations

from importlib import import_module
from types import ModuleType
from typing import Final

_SUPPORT_SUBMODULES: Final = (
    "biomarker_candidate_support",
    "contrast_resolution",
    "foundation",
    "identification",
    "imports",
    "interpretation",
    "io_and_dia",
    "multiplex_targeted",
    "output_protocol",
    "ptm_quantification",
    "review_sequences_study",
    "sequence_support",
    "targeted_panel_support",
    "targeted_selection_io",
    "timecourse_support",
    "validation_evidence_support",
    "workflow",
)

__all__ = _SUPPORT_SUBMODULES


def __getattr__(name: str) -> ModuleType:
    """Load support submodules lazily from the explicit registry."""

    if name not in _SUPPORT_SUBMODULES:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module = import_module(f"{__name__}.{name}")
    globals()[name] = module
    return module


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
