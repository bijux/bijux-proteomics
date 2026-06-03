# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Evidence review, reviewer exports, and structure-analysis surfaces."""

from __future__ import annotations

from importlib import import_module
from typing import Any

_REVIEW_EXPORT_MODULES = (
    "bijux_proteomics.review.evidence_graph",
    "bijux_proteomics.review.claims",
    "bijux_proteomics.review.cards",
    "bijux_proteomics.review.belief",
    "bijux_proteomics.review.explanations",
    "bijux_proteomics.review.structure_reports",
)


def __getattr__(name: str) -> Any:
    for module_path in _REVIEW_EXPORT_MODULES:
        module = import_module(module_path)
        if hasattr(module, name):
            return getattr(module, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
